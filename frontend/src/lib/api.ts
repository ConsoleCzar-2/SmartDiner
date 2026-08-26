import type { ChatRequest, ChatResponse, RestaurantResponse } from "@/types";
const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
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

export async function fetchActiveChat(restaurantId: string): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    if (!token) return null;
    
    const response = await fetch(`${API_BASE_URL}/api/chat/active?restaurant_id=${restaurantId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        return null; // Return null if it fails, maybe token expired or no active chat
    }
    return response.json();
}

export async function fetchRestaurants(): Promise<RestaurantResponse[]> {
    const response = await fetch(`${API_BASE_URL}/api/restaurants`);
    if (!response.ok) {
        throw new Error(`Failed to fetch restaurants (${response.status})`);
    }
    return response.json() as Promise<RestaurantResponse[]>;
}

export async function fetchRestaurant(id: string): Promise<RestaurantResponse> {
    const response = await fetch(`${API_BASE_URL}/api/restaurants/${id}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch restaurant (${response.status})`);
    }
    return response.json() as Promise<RestaurantResponse>;
}

export async function fetchRestaurantMenu(id: string): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/api/restaurants/${id}/menu`);
    if (!response.ok) {
        throw new Error(`Failed to fetch restaurant menu (${response.status})`);
    }
    return response.json() as Promise<any[]>;
}

export async function customerLogin(credentials: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login/user`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
    });
    if (!response.ok) {
        throw new Error("Invalid credentials");
    }
    return response.json();
}

export async function customerRegister(data: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const detail = await response.text().catch(() => "Registration failed");
        throw new Error(detail);
    }
    return response.json();
}

export async function adminLogin(credentials: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login/admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
    });
    if (!response.ok) {
        throw new Error("Invalid credentials");
    }
    return response.json();
}

export async function fetchAdminMetrics(token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/metrics`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch metrics");
    }
    return response.json();
}

export async function fetchAdminConversations(token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/conversations`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch conversations");
    }
    return response.json();
}
