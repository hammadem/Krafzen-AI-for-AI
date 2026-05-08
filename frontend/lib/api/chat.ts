import { getApiBaseUrl } from "./utils";

export interface ComplianceViolation {
    rule_id: string;
    message: string;
    suggestion: string;
}

/** USA IRC baseline screening payload from POST /chat/generate when jurisdiction is US_IRC_BASELINE */
export interface CompliancePayload {
    jurisdiction_id: string;
    jurisdiction_label: string;
    score_percent: number | null;
    status_label: string;
    passed_rules: number;
    applicable_rules: number;
    violations: ComplianceViolation[];
    suggestions: string[];
    disclaimer: string;
    layout_extract?: Record<string, unknown>;
}

export interface ChatResponse {
    session_id: string;
    message_id?: string; // ID of created assistant message (for feedback)
    original_prompt: string;
    ollama_response: string;
    validated_response: string;
    image_url: string;
    remaining_minutes?: number;
    compliance?: CompliancePayload | null;
}

export type ChatJurisdiction = "standard" | "US_IRC_BASELINE";

export async function sendChatMessage(
    message: string,
    history: { role: string, content: string, imageUrl?: string }[] = [],
    token?: string,
    sessionId?: string,
    jurisdiction?: ChatJurisdiction
): Promise<ChatResponse> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const body: Record<string, unknown> = { message, history };
    if (sessionId) body.session_id = sessionId;
    if (jurisdiction === "US_IRC_BASELINE") body.jurisdiction = "US_IRC_BASELINE";

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
                    ? 'No chat requests remaining. Subscribe to a plan to continue, or wait for your billing cycle to renew.'
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

export interface SessionMessageFromApi {
    id: string;
    role: string;
    content?: string;
    image_url?: string;
    created_at: string;
    feedback?: { reaction: 'up' | 'down'; reason?: string };
    compliance?: CompliancePayload | null;
}

export async function fetchSessionMessages(sessionId: string, token: string): Promise<SessionMessageFromApi[]> {
    const headers = { 'Authorization': `Bearer ${token}` };
    const res = await fetch(`${getApiBaseUrl()}/api/v1/chat/history/${sessionId}`, { headers });
    if (!res.ok) throw new Error("Failed to fetch messages");
    return res.json();
}

export async function submitMessageFeedback(
    messageId: string,
    reaction: 'up' | 'down',
    reason: string | undefined,
    token: string
): Promise<void> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
    };
    const res = await fetch(`${getApiBaseUrl()}/api/v1/chat/message/${messageId}/feedback`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ reaction, reason: reason || null }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || 'Failed to submit feedback');
    }
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

export const downloadDesignFile = async (
    imageUrl: string,
    fileType: 'dxf' | 'dwg',
    prompt?: string,
    token?: string
) => {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${getApiBaseUrl()}/api/v1/chat/design-file`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ image_url: imageUrl, prompt, file_type: fileType }),
    });

    if (!response.ok) {
        let errorMessage = response.statusText;
        try {
            const errorData = await response.json();
            if (errorData.detail) errorMessage = errorData.detail;
        } catch {
            // ignore
        }
        throw new Error(`Failed to download ${fileType.toUpperCase()}: ${errorMessage}`);
    }

    return await response.blob();
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
