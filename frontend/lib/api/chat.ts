const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatResponse {
    original_prompt: string;
    ollama_response: string;
    validated_response: string;
    image_url: string;
}

export async function sendChatMessage(
    message: string,
    history: { role: string, content: string, imageUrl?: string }[] = [],
    token?: string
): Promise<ChatResponse> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/chat/generate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
            message,
            history
        }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate response');
    }

    return response.json();
}

export const downloadDxf = async (imageUrl: string, prompt?: string, token?: string) => {
    try {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/chat/dxf`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ image_url: imageUrl, prompt }),
        });

        if (!response.ok) {
            throw new Error(`Failed to download DXF: ${response.statusText}`);
        }

        return await response.blob();
    } catch (error) {
        console.error('Error downloading DXF:', error);
        throw error;
    }
};

export async function transcribeAudio(audioBlob: Blob, token?: string): Promise<string> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'rec.webm');

    const headers: Record<string, string> = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/transcribe`, {
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
