import type { ChatRequest, ChatResponse, RestaurantResponse } from "@/types";

function resolveApiBaseUrl(): string {
    const configuredUrl =
        process.env.NEXT_PUBLIC_API_URL ??
        process.env.NEXT_PUBLIC_API_BASE_URL;

    if (configuredUrl) {
        return configuredUrl.replace(/\/$/, "");
    }

    // Local default for development only.
    if (process.env.NODE_ENV !== "production") {
        return "http://127.0.0.1:8000";
    }

    throw new Error(
        "Missing NEXT_PUBLIC_API_URL (or NEXT_PUBLIC_API_BASE_URL) in production environment.",
    );
}

const API_BASE_URL = resolveApiBaseUrl();
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

export async function fetchAdminConversation(token: string, conversationId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/conversations/${conversationId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch conversation");
    }
    return response.json();
}

export async function fetchAdminAuditLogs(token: string, conversationId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/audit-logs/${conversationId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch audit logs");
    }
    return response.json();
}

// --- Cart APIs ---

export async function fetchActiveCart(restaurantId: string): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    if (!token) return { conversation_id: null, cart: [] };
    const response = await fetch(`${API_BASE_URL}/api/cart?restaurant_id=${restaurantId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) throw new Error("Failed to fetch cart");
    return response.json();
}

export async function addToCart(payload: { restaurant_id: string, menu_item_id: string, quantity: int }): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    const response = await fetch(`${API_BASE_URL}/api/cart/add`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Failed to add to cart");
    return response.json();
}

export async function patchCart(conversationId: string, items: { id: string, quantity: number }[]): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    const response = await fetch(`${API_BASE_URL}/api/cart/${conversationId}`, {
        method: "PATCH",
        headers: { 
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ items }),
    });
    if (!response.ok) throw new Error("Failed to patch cart");
    return response.json();
}

// --- Order APIs ---

export async function checkoutOrder(conversationId: string): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    const response = await fetch(`${API_BASE_URL}/api/orders/checkout`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ conversation_id: conversationId }),
    });
    if (!response.ok) {
        const err = await response.text().catch(() => "");
        throw new Error(err || "Failed to checkout");
    }
    return response.json();
}

export async function fetchOrderHistory(): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    if (!token) return { orders: [], total_count: 0 };
    const response = await fetch(`${API_BASE_URL}/api/orders/history`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) throw new Error("Failed to fetch order history");
    return response.json();
}

// --- Admin Menu APIs ---

export async function adminCreateMenuItem(token: string, restaurantId: string, formData: FormData): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/restaurants/${restaurantId}/menu`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData, // FormData does not need Content-Type header, fetch sets it automatically with boundary
    });
    if (!response.ok) throw new Error("Failed to create menu item");
    return response.json();
}

export async function adminUpdateMenuItem(token: string, restaurantId: string, itemId: string, formData: FormData): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/restaurants/${restaurantId}/menu/${itemId}`, {
        method: "PATCH",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData,
    });
    if (!response.ok) throw new Error("Failed to update menu item");
    return response.json();
}

export async function adminDeleteMenuItem(token: string, restaurantId: string, itemId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/admin/restaurants/${restaurantId}/menu/${itemId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        const d = await response.text();
        throw new Error(d);
    }
}

export async function adminFetchAllergens(token: string): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/api/admin/allergens`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        const d = await response.text();
        throw new Error(d);
    }
    return response.json();
}
