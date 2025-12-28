const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatResponse {
    original_prompt: str;
    ollama_response: str;
    validated_response: str;
    image_url: str;
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate response');
    }

    return response.json();
}
