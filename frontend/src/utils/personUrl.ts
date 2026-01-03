/**
 * Generate GDPR-safe person profile URL
 * Uses SHA256 hash of person code to avoid exposing full personal code
 */

/**
 * Simple hash function for browser-side URL generation
 * For production, consider using a proper crypto library
 */
async function simpleHash(str: string): Promise<string> {
    if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
        // Use Web Crypto API in browser
        const encoder = new TextEncoder();
        const data = encoder.encode(str);
        const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex.substring(0, 16); // First 16 chars
    }
    // Fallback for server-side or old browsers: use fragment + slug
    return str.substring(0, 6); // Just use first 6 chars (birth date)
}

/**
 * Generate person profile URL
 * @param personCode - Person code from registry (e.g., "120585-12345")
 * @param personName - Person's full name (for fallback slug)
 * @returns Promise<string> - URL safe identifier
 */
export async function generatePersonUrl(personCode: string | null, personName: string): Promise<string> {
    if (!personCode) {
        // If no person code, use slugified name (not ideal, but fallback)
        const slug = personName.toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/(^-|-$)/g, '');
        return `/person/${slug}`;
    }

    try {
        const hash = await simpleHash(personCode);
        return `/person/${hash}`;
    } catch (e) {
        // Fallback: use fragment + slug
        const fragment = personCode.substring(0, 6);
        const slug = personName.toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/(^-|-$)/g, '');
        return `/person/${fragment}-${slug}`;
    }
}

/**
 * Synchronous version for simpler cases
 * Uses birth_date-slug approach: YYYYMMDD-name-slug
 */
export function generatePersonUrlSync(
    personCode: string | null | undefined,
    personName: string,
    birthDate?: string | null
): string {
    // Debug logging
    console.log('[generatePersonUrlSync]', { personCode, personName, birthDate });

    // Normalize Latvian characters in name
    const normalizeName = (name: string) => {
        return name.toLowerCase()
            .replace(/ā/g, 'a')
            .replace(/č/g, 'c')
            .replace(/ē/g, 'e')
            .replace(/ģ/g, 'g')
            .replace(/ī/g, 'i')
            .replace(/ķ/g, 'k')
            .replace(/ļ/g, 'l')
            .replace(/ņ/g, 'n')
            .replace(/š/g, 's')
            .replace(/ū/g, 'u')
            .replace(/ž/g, 'z')
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/(^-|-$)/g, '');
    };

    const slug = normalizeName(personName);

    // Try to use birth_date if available
    if (birthDate) {
        // Convert YYYY-MM-DD to YYYYMMDD
        const fragment = birthDate.replace(/-/g, '');
        const url = `/person/${fragment}-${slug}`;
        console.log('[generatePersonUrlSync] Generated URL with birth_date:', url);
        return url;
    }

    // Fallback: try to extract from person_code if it starts with DDMMYY
    if (personCode && personCode.length >= 6) {
        const fragment = personCode.substring(0, 6);
        const url = `/person/${fragment}-${slug}`;
        console.log('[generatePersonUrlSync] Generated URL with person_code fragment:', url);
        return url;
    }

    // Last resort: just use name slug
    const url = `/person/${slug}`;
    console.warn('[generatePersonUrlSync] No birth_date or person_code, using fallback URL:', url);
    return url;
}
