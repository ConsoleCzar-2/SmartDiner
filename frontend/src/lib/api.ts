import type { ChatRequest, ChatResponse, RestaurantResponse } from "@/types";
const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export async function sendChatMessage(
    payload: ChatRequest,
): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const detail = await response.text().catch(() => "");
        throw new Error(
            detail || `Recommendation request failed (${response.status}).`,
        );
    }
    return response.json() as Promise<ChatResponse>;
}

export async function fetchRestaurants(): Promise<RestaurantResponse[]> {
    const response = await fetch(`${API_BASE_URL}/api/restaurants`);
    if (!response.ok) {
        throw new Error("Failed to fetch restaurants.");
    }
    return response.json();
}
