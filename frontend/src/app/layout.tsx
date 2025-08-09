import type {Metadata} from 'next';
import {Inter} from 'next/font/google';
import './globals.css';
import {AuthProvider} from '@/contexts/AuthContext';
import Navigation from '@/components/Navigation';

const inter = Inter({subsets: ['latin']});

export const metadata: Metadata = {
    title: 'PlugBot',
    description: 'Manage and connect Dify bots with Telegram',
    icons: {icon: '/favicon.ico'}
};

export default function RootLayout({
                                       children,
                                   }: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
        <body className={inter.className}>
        <AuthProvider>
            <div className="min-h-screen bg-gray-50">
                <Navigation/>
                <main>{children}</main>
            </div>
        </AuthProvider>
        </body>
        </html>
    );
}