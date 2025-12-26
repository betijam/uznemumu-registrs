/**
 * Parse birth date from masked Latvian identity number
 * Format: DDMMYY-****
 * Example: 290800-**** → 29.08.2000
 */
export function parseBirthDateFromPersonCode(personCode: string | null | undefined): string | null {
    if (!personCode || typeof personCode !== 'string') {
        return null;
    }

    // Extract DDMMYY from format like "290800-****"
    const match = personCode.match(/^(\d{2})(\d{2})(\d{2})/);
    if (!match) {
        return null;
    }

    const day = match[1];
    const month = match[2];
    const year = match[3];

    // Determine century: if YY > current year's last 2 digits, it's 19YY, else 20YY
    const currentYear = new Date().getFullYear();
    const currentYearLastTwo = currentYear % 100;
    const yearNum = parseInt(year, 10);

    const fullYear = yearNum > currentYearLastTwo ? `19${year}` : `20${year}`;

    return `${day}.${month}.${fullYear}`;
}

/**
 * Calculate age from person code
 */
export function calculateAgeFromPersonCode(personCode: string | null | undefined): number | null {
    const birthDateStr = parseBirthDateFromPersonCode(personCode);
    if (!birthDateStr) {
        return null;
    }

    const [day, month, year] = birthDateStr.split('.').map(n => parseInt(n, 10));
    const birthDate = new Date(year, month - 1, day);
    const today = new Date();

    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }

    return age;
}
