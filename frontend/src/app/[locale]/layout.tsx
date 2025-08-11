import type {Metadata} from 'next';
import {Inter} from 'next/font/google';
import {NextIntlClientProvider} from 'next-intl';
import {getMessages} from 'next-intl/server';
import '../globals.css';
import {AuthProvider} from '@/contexts/AuthContext';
import Navigation from '@/components/Navigation';

const inter = Inter({subsets: ['latin']});

export const metadata: Metadata = {
    title: 'PlugBot',
    description: 'Manage and connect Dify bots with Telegram',
    icons: {icon: '/favicon.ico'}
};

export default async function LocaleLayout({
                                               children,
                                               params: {locale}
                                           }: {
    children: React.ReactNode;
    params: { locale: string };
}) {
    const messages = await getMessages();

    return (
        <html lang={locale}>
        <body className={inter.className}>
        <NextIntlClientProvider messages={messages}>
            <AuthProvider>
                <div className="min-h-screen bg-gray-50">
                    <Navigation/>
                    <main>{children}</main>
                </div>
            </AuthProvider>
        </NextIntlClientProvider>
        </body>
        </html>
    );
}