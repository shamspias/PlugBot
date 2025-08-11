'use client';

import {useLocale} from 'next-intl';
import {useRouter, usePathname} from 'next/navigation';
import {locales, localeNames, type Locale} from '@/i18n/config';
import {Globe} from 'lucide-react';
import {useState, useRef, useEffect, useMemo} from 'react';

export default function LanguageSwitcher() {
    const locale = useLocale() as Locale;
    const router = useRouter();
    const pathname = usePathname() || '/';
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Build a regex like: ^/(en|ru|de)(?=/|$)
    const localePattern = useMemo(
        () => new RegExp(`^/(${locales.join('|')})(?=/|$)`),
        []
    );

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleLanguageChange = (newLocale: Locale) => {
        // Safely remove the *leading* locale segment only
        const pathWithoutLocale = pathname.replace(localePattern, '') || '/';

        // Navigate to the new locale path
        const target =
            pathWithoutLocale === '/' ? `/${newLocale}` : `/${newLocale}${pathWithoutLocale}`;

        router.push(target);
        setIsOpen(false);
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                aria-label="Change language"
                aria-expanded={isOpen}
            >
                <Globe className="w-4 h-4"/>
                <span className="text-sm font-medium">{localeNames[locale]}</span>
                <svg
                    className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/>
                </svg>
            </button>

            {isOpen && (
                <div
                    className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                    {locales.map((loc) => (
                        <button
                            key={loc}
                            onClick={() => handleLanguageChange(loc as Locale)}
                            className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors flex items-center justify-between ${
                                loc === locale ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                            }`}
                        >
                            <span>{localeNames[loc as Locale]}</span>
                            {loc === locale && (
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                                    <path
                                        fillRule="evenodd"
                                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                            )}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
