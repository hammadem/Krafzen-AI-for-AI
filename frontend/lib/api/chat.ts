// Get API URL from environment variable
// In production/staging, this MUST be set in Vercel environment variables
// For local development, it defaults to localhost
const getApiBaseUrl = (): string => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    // If API URL is not set, check if we're in production
    if (!apiUrl) {
        // In browser/client-side, check if we're on a production domain
        if (typeof window !== 'undefined') {
            const isProduction = window.location.hostname !== 'localhost' &&
                !window.location.hostname.includes('127.0.0.1');

            if (isProduction) {
                console.error('NEXT_PUBLIC_API_URL is not set in production environment!');
                console.error('Current hostname:', window.location.hostname);
                // Don't throw - let the fetch fail gracefully so we can show a better error
                // The staging backend should be: https://krafzen-api-staging.onrender.com
                return 'https://krafzen-api-staging.onrender.com';
            }
        }

        // Default to localhost for local development
        return 'http://localhost:8000';
    }

    return apiUrl;
};

export interface ChatResponse {
    session_id: string;
    original_prompt: string;
    ollama_response: string;
    validated_response: string;
    image_url: string;
    remaining_minutes?: number;
}

export async function sendChatMessage(
    message: string,
    history: { role: string, content: string, imageUrl?: string }[] = [],
    token?: string,
    sessionId?: string
): Promise<ChatResponse> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const body: Record<string, unknown> = { message, history };
    if (sessionId) body.session_id = sessionId;

    const response = await fetch(`${getApiBaseUrl()}/api/v1/chat/generate`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate response');
    }

    return response.json();
}

export async function createChatSession(title: string = "New Chat", token: string) {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
    const res = await fetch(`${getApiBaseUrl()}/api/v1/chat/session`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ title })
    });
    if (!res.ok) throw new Error("Failed to create session");
    return res.json();
}

export async function fetchChatHistory(token: string) {
    const headers = { 'Authorization': `Bearer ${token}` };
    const res = await fetch(`${getApiBaseUrl()}/api/v1/chat/history`, { headers });
    if (!res.ok) throw new Error("Failed to fetch history");
    return res.json();
}

export async function fetchSessionMessages(sessionId: string, token: string) {
    const headers = { 'Authorization': `Bearer ${token}` };
    const res = await fetch(`${getApiBaseUrl()}/api/v1/chat/history/${sessionId}`, { headers });
    if (!res.ok) throw new Error("Failed to fetch messages");
    return res.json();
}

export async function updateChatSessionTitle(sessionId: string, title: string, token: string) {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
    const res = await fetch(`${getApiBaseUrl()}/api/v1/chat/history/${sessionId}/title`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ title })
    });
    if (!res.ok) throw new Error("Failed to update session title");
    return res.json();
}

export async function deleteChatSession(sessionId: string, token: string) {
    const headers = { 'Authorization': `Bearer ${token}` };
    const res = await fetch(`${getApiBaseUrl()}/api/v1/chat/history/${sessionId}`, {
        method: 'DELETE',
        headers
    });
    if (!res.ok) throw new Error("Failed to delete session");
    return res.json();
}

export const downloadDxf = async (imageUrl: string, prompt?: string, token?: string) => {
    try {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${getApiBaseUrl()}/api/v1/chat/dxf`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ image_url: imageUrl, prompt }),
        });

        if (!response.ok) {
            let errorMessage = response.statusText;
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (e) {
                // Ignore json parse error, use statusText
            }
            throw new Error(`Failed to download DXF: ${errorMessage}`);
        }

        return await response.blob();
    } catch (error) {
        console.error('Error downloading DXF:', error);
        throw error;
    }
};

export async function transcribeAudio(audioBlob: Blob, token?: string): Promise<string> {
    const formData = new FormData();
    const extension = audioBlob.type.includes('mp4') ? 'mp4' : 'webm';
    formData.append('file', audioBlob, `rec.${extension}`);

    const headers: Record<string, string> = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${getApiBaseUrl()}/api/v1/transcribe`, {
        method: 'POST',
        headers,
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Transcription failed');
    }

    const data = await response.json();
    return data.text;
}
