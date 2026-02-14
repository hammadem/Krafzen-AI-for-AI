
// frontend/lib/security/crypto.ts

/**
 * Security & Cryptography Utilities
 * Implements "Zero-Leak" standards using Web Crypto API.
 */

// Generate a cryptographically secure session ID (64-bit entropy min).
// We'll use 16 bytes (128 bits) to be safe and collission resistant.
export function generateSessionId(): string {
    if (typeof window === 'undefined') return ''; // Server-side guard
    const array = new Uint8Array(16);
    window.crypto.getRandomValues(array);
    return Array.from(array)
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
}

// Generate a random encryption key for AES-GCM
export async function generateEncryptionKey(): Promise<CryptoKey> {
    return window.crypto.subtle.generateKey(
        {
            name: 'AES-GCM',
            length: 256,
        },
        true,
        ['encrypt', 'decrypt']
    );
}

// Export key to string (for storage/transmission if needed, though we aim for memory-only)
export async function exportKey(key: CryptoKey): Promise<string> {
    const exported = await window.crypto.subtle.exportKey('jwk', key);
    return JSON.stringify(exported);
}

// Import key from string
export async function importKey(jwkString: string): Promise<CryptoKey> {
    const jwk = JSON.parse(jwkString);
    return window.crypto.subtle.importKey(
        'jwk',
        jwk,
        { name: 'AES-GCM', length: 256 },
        true,
        ['encrypt', 'decrypt']
    );
}

// Encrypt data using AES-256-GCM
export async function encryptData(data: string, key: CryptoKey): Promise<{ cipherText: string; iv: string }> {
    const encoder = new TextEncoder();
    const encodedData = encoder.encode(data);
    const iv = window.crypto.getRandomValues(new Uint8Array(12)); // 96-bit IV for GCM

    const encryptedBuffer = await window.crypto.subtle.encrypt(
        {
            name: 'AES-GCM',
            iv: iv,
        },
        key,
        encodedData
    );

    return {
        cipherText: arrayBufferToBase64(encryptedBuffer),
        iv: arrayBufferToBase64(iv.buffer),
    };
}

// Decrypt data using AES-256-GCM
export async function decryptData(cipherText: string, iv: string, key: CryptoKey): Promise<string> {
    const encryptedExample = base64ToArrayBuffer(cipherText);
    const ivBuffer = base64ToArrayBuffer(iv);

    const decryptedBuffer = await window.crypto.subtle.decrypt(
        {
            name: 'AES-GCM',
            iv: ivBuffer,
        },
        key,
        encryptedExample
    );

    const decoder = new TextDecoder();
    return decoder.decode(decryptedBuffer);
}

// Helpers
function arrayBufferToBase64(buffer: ArrayBuffer): string {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary_string = window.atob(base64);
    const len = binary_string.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}
