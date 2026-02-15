import { getApiBaseUrl } from "./utils";

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
        const errorData = await response.json().catch(() => ({}));
        const detail = errorData?.detail;
        const message = typeof detail === 'string'
            ? detail
            : Array.isArray(detail) && detail[0]?.msg
                ? detail[0].msg
                : response.status === 402
                    ? 'No chat requests remaining. Upgrade your plan or wait for your trial to end.'
                    : 'Failed to generate response';
        throw new Error(message);
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

export async function fetchChatHistory(token: string): Promise<Array<{ id: string; title?: string; created_at: string; updated_at: string }>> {
    const headers = { 'Authorization': `Bearer ${token}` };
    const url = `${getApiBaseUrl()}/api/v1/chat/history`;
    const res = await fetch(url, { headers });
    if (!res.ok) {
        // 401: token invalid/expired or backend auth mismatch — return empty so chat still works with a new session
        if (res.status === 401) {
            if (typeof window !== "undefined") {
                console.warn("Chat history: unauthorized (401). Using empty history. Check backend Supabase JWT config if this persists.");
            }
            return [];
        }
        let detail = `Failed to fetch history (${res.status})`;
        try {
            const body = await res.json();
            if (body?.detail) {
                const d = body.detail;
                detail += typeof d === 'string' ? `: ${d}` : `: ${d?.error ?? JSON.stringify(d)}`;
            }
        } catch {
            try {
                detail += `: ${await res.text()}`;
            } catch {
                // ignore
            }
        }
        throw new Error(detail);
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
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
                // Only try to parse JSON for error responses
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (e) {
                // Ignore json parse error, use statusText
            }
            throw new Error(`Failed to download DXF: ${errorMessage}`);
        }

        // For successful responses, return the binary blob directly
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
