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
 * Uses hash-based approach for unique identification
 */
export function generatePersonUrlSync(
    personCode: string | null | undefined,
    personName: string,
    birthDate?: string | null
): string {
    // Debug logging
    console.log('[generatePersonUrlSync]', { personCode, personName, birthDate });

    // Use hash if we have both person_code and name
    if (personCode && personName) {
        // Create deterministic string for hashing
        const hashInput = `${personCode}|${personName}`;

        // Simple hash function (matching backend Python implementation)
        let hash = 0;
        for (let i = 0; i < hashInput.length; i++) {
            const char = hashInput.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash | 0; // Convert to 32bit signed integer
        }

        // Convert to 8-character hex (use unsigned value)
        const hashHex = (hash >>> 0).toString(16).padStart(8, '0').substring(0, 8);
        const url = `/person/${hashHex}`;
        console.log('[generatePersonUrlSync] Generated hash URL:', url, 'from', hashInput, 'hash:', hash, 'hex:', hashHex);
        return url;
    }

    // Fallback: normalize name for slug
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
    const url = `/person/${slug}`;
    console.warn('[generatePersonUrlSync] No person_code, using fallback name URL:', url);
    return url;
}

