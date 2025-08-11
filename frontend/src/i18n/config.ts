export const locales = ['en', 'ru'] as const;
export type Locale = (typeof locales)[number];

export const localeNames: Record<Locale, string> = {
    en: 'English',
    ru: 'Русский'
};

export const defaultLocale: Locale = 'en';

export function isValidLocale(locale: string): locale is Locale {
    return locales.includes(locale as Locale);
}