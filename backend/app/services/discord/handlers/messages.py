"""Message handlers for Discord bot."""

from datetime import datetime
import discord

from ....models.conversation import Conversation, Message
from ....utils.logger import get_logger

logger = get_logger(__name__)


class MessageHandlers:
    """Handles all Discord message operations."""

    def __init__(self, discord_service):
        self.service = discord_service
        self.bot = discord_service.bot
        self.db = discord_service.db
        self.dify_service = discord_service.dify_service
        self.auth_manager = discord_service.auth_manager

    async def handle_message(self, message: discord.Message):
        """Handle incoming Discord messages."""
        # Skip bot messages and commands
        if message.author.bot:
            return

        if message.content.startswith('!'):
            return

        user_id = str(message.author.id)

        # Check authentication if required
        if self.bot.auth_required:
            can_proceed = await self.auth_manager.auth_gate(message, self.bot)
            if not can_proceed:
                return

        # Get or create conversation
        conversation = self._get_or_create_conversation(message)

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message.content,
            discord_message_id=str(message.id),
            discord_channel_id=str(message.channel.id)
        )
        self.db.add(user_message)
        self.db.commit()

        # Process with Dify
        await self._process_dify_response(message, conversation, message.content)

    async def handle_attachment(self, message: discord.Message):
        """Handle file attachments in Discord messages."""
        if not self.bot.enable_file_upload:
            embed = discord.Embed(
                description="File uploads are disabled for this bot.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return

        for attachment in message.attachments:
            if attachment.size > 15 * 1024 * 1024:  # 15MB limit
                embed = discord.Embed(
                    description="File size exceeds 15MB limit.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                continue

            # Download file
            file_data = await attachment.read()

            # Upload to Dify
            result = await self.dify_service.upload_file(
                file_data=file_data,
                filename=attachment.filename,
                user_id=f"discord_{message.author.id}"
            )

            if not result:
                embed = discord.Embed(
                    description="❌ Failed to upload file.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                continue

            # Process the file with caption if provided
            caption = message.content if message.content else f"Please analyze this file: {attachment.filename}"

            conversation = self._get_or_create_conversation(message)

            files_payload = [{
                "type": "document" if not attachment.content_type.startswith("image/") else "image",
                "transfer_method": "local_file",
                "upload_file_id": result.get("id")
            }]

            await self._process_dify_response_with_files(
                message, conversation, caption, files_payload
            )

    def _get_or_create_conversation(self, message: discord.Message) -> Conversation:
        """Get or create active conversation for Discord channel."""
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        guild_id = str(message.guild.id) if message.guild else None

        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.discord_channel_id == channel_id,
                Conversation.bot_id == self.bot.id,
                Conversation.is_active == True,
                Conversation.platform == 'discord'
            )
            .first()
        )

        if not conversation:
            conversation = Conversation(
                bot_id=self.bot.id,
                discord_channel_id=channel_id,
                discord_guild_id=guild_id,
                discord_user_id=user_id,
                discord_username=str(message.author),
                platform='discord',
                dify_user_id=f"discord_{user_id}",
            )
            self.db.add(conversation)
            self.db.commit()

        return conversation

    async def _process_dify_response(self, message: discord.Message, conversation, content: str):
        """Process response from Dify service for Discord."""
        response_text = ""
        sent_message = None
        last_update_length = 0

        try:
            # Start typing indicator
            async with message.channel.typing():
                async for event in self.dify_service.send_message(
                        message=content,
                        conversation_id=conversation.dify_conversation_id,
                        user_id=conversation.dify_user_id,
                ):
                    if event.get("event") == "message":
                        response_text += event.get("answer", "")

                        # For streaming mode, update message periodically
                        if self.bot.response_mode == "streaming":
                            if not sent_message:
                                # Send initial message
                                embed = discord.Embed(
                                    description=response_text[:4000] or "...",
                                    color=discord.Color.blue()
                                )
                                sent_message = await message.channel.send(embed=embed)
                                last_update_length = len(response_text)
                            elif len(response_text) - last_update_length > 100:
                                # Update message every 100 characters
                                embed = discord.Embed(
                                    description=response_text[:4000],
                                    color=discord.Color.blue()
                                )
                                await sent_message.edit(embed=embed)
                                last_update_length = len(response_text)

                    elif event.get("event") == "message_end":
                        if not conversation.dify_conversation_id:
                            conversation.dify_conversation_id = event.get("conversation_id")

                        # Save assistant message
                        assistant_message = Message(
                            conversation_id=conversation.id,
                            role="assistant",
                            content=response_text,
                            dify_message_id=event.get("message_id"),
                            discord_message_id=str(sent_message.id) if sent_message else None,
                            discord_channel_id=str(message.channel.id),
                            tokens_used=event.get("metadata", {}).get("usage", {}).get("total_tokens"),
                        )
                        self.db.add(assistant_message)
                        conversation.message_count += 2
                        conversation.last_message_at = datetime.utcnow()
                        self.db.commit()

                    elif event.get("event") == "error":
                        embed = discord.Embed(
                            description=f"❌ Error: {event.get('message', 'Unknown error')}",
                            color=discord.Color.red()
                        )
                        await message.channel.send(embed=embed)
                        return

            # Final update or send if blocking mode
            if response_text:
                if self.bot.response_mode == "blocking" or not sent_message:
                    # Handle long responses by splitting into multiple messages
                    if len(response_text) > 4000:
                        chunks = [response_text[i:i + 4000] for i in range(0, len(response_text), 4000)]
                        for i, chunk in enumerate(chunks):
                            embed = discord.Embed(
                                description=chunk,
                                color=discord.Color.blue()
                            )
                            if i == 0:
                                embed.set_footer(text=f"Part {i + 1}/{len(chunks)}")
                            await message.channel.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            description=response_text,
                            color=discord.Color.blue()
                        )
                        await message.channel.send(embed=embed)
                else:
                    # Final update for streaming mode
                    if response_text != last_update_length:
                        embed = discord.Embed(
                            description=response_text[:4000],
                            color=discord.Color.blue()
                        )
                        await sent_message.edit(embed=embed)
            else:
                embed = discord.Embed(
                    description="I couldn't generate a response. Please try again.",
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            embed = discord.Embed(
                description="❌ An error occurred. Please try again.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)

    async def _process_dify_response_with_files(self, message, conversation, query_text, files):
        """Process Dify response with file attachments."""
        # Similar to _process_dify_response but with files parameter
        response_text = ""
        sent_message = None

        try:
            async with message.channel.typing():
                async for event in self.dify_service.send_message(
                        message=query_text,
                        conversation_id=conversation.dify_conversation_id,
                        user_id=conversation.dify_user_id,
                        files=files,
                ):
                    # Process similar to regular message
                    # ... (implementation similar to above)
                    pass

        except Exception as e:
            logger.error(f"Error processing file message: {e}")
            embed = discord.Embed(
                description="❌ An error occurred processing the file.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
