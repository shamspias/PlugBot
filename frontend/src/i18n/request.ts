import {getRequestConfig} from 'next-intl/server';
import {isValidLocale, defaultLocale, type Locale} from './config';

export default getRequestConfig(async ({locale}) => {
    const candidate = locale ?? defaultLocale;
    const resolvedLocale: Locale = isValidLocale(candidate) ? candidate : defaultLocale;

    return {
        locale: resolvedLocale,
        messages: (await import(`./locales/${resolvedLocale}.json`)).default
    };
});
