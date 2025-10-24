/**
 * Parse phone numbers from text input
 */
export function parsePhoneNumbers(text: string): string[] {
    return text
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0);
}

/**
 * Count valid phone numbers
 */
export function countValidPhones(text: string): number {
    return parsePhoneNumbers(text).length;
}

/**
 * Remove empty lines from phone number text
 */
export function cleanPhoneNumbers(text: string): string {
    return parsePhoneNumbers(text).join("\n");
}

/**
 * Remove duplicate phone numbers
 */
export function removeDuplicatePhones(text: string): {cleaned: string; removedCount: number} {
    const lines = parsePhoneNumbers(text);
    const unique = [...new Set(lines)];
    return {
        cleaned: unique.join("\n"),
        removedCount: lines.length - unique.length,
    };
}

/**
 * Format results for clipboard
 */
export function formatResultsForClipboard(results: Array<{phone: string; status: string; message: string}>): string {
    return results.map((r) => `${r.phone}|${r.status}|${r.message}`).join("\n");
}

/**
 * Format single result for clipboard
 */
export function formatSingleResultForClipboard(phone: string, status: string, message: string): string {
    return `${phone}|${status}|${message}`;
}
