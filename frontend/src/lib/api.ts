import type { 
    ChatRequest, 
    ChatResponse, 
    RestaurantResponse, 
    AdminAnalyticsResponse, 
    StreamStatusEvent, 
    StreamCartEvent, 
    StreamDoneEvent, 
    StreamAdminMetadataEvent, 
    StreamAdminDoneEvent 
} from "@/types";

function resolveApiBaseUrl(): string {
    const configuredUrl =
        process.env.NEXT_PUBLIC_API_URL ??
        process.env.NEXT_PUBLIC_API_BASE_URL;

    if (configuredUrl) {
        return configuredUrl.replace(/\/$/, "");
    }

    // Default fallback so Vercel builds do not crash during SSG
    return "http://127.0.0.1:8000";
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

export async function streamChatMessage(
    payload: ChatRequest,
    callbacks: {
        onStatus?: (data: StreamStatusEvent) => void;
        onCart?: (data: StreamCartEvent) => void;
        onToken?: (token: string) => void;
        onDone?: (data: StreamDoneEvent) => void;
        onError?: (err: Error) => void;
    }
): Promise<void> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { "Authorization": `Bearer ${token}` } : {})
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const detail = await response.text().catch(() => "");
            throw new Error(detail || `Streaming request failed (${response.status})`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error("Response body is not readable");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const blocks = buffer.split("\n\n");
            buffer = blocks.pop() || "";

            for (const block of blocks) {
                if (!block.trim()) continue;
                const lines = block.split("\n");
                let eventType = "message";
                let dataStr = "";

                for (const line of lines) {
                    if (line.startsWith("event:")) {
                        eventType = line.replace("event:", "").trim();
                    } else if (line.startsWith("data:")) {
                        dataStr = line.replace("data:", "").trim();
                    }
                }

                if (!dataStr) continue;

                try {
                    const parsed = JSON.parse(dataStr);
                    if (eventType === "status" && callbacks.onStatus) {
                        callbacks.onStatus(parsed);
                    } else if (eventType === "cart" && callbacks.onCart) {
                        callbacks.onCart(parsed);
                    } else if (eventType === "token" && callbacks.onToken) {
                        callbacks.onToken(parsed.content || "");
                    } else if (eventType === "done" && callbacks.onDone) {
                        callbacks.onDone(parsed);
                    }
                } catch (parseError) {
                    console.error("Failed to parse SSE JSON payload:", parseError, dataStr);
                }
            }
        }
    } catch (err: any) {
        if (callbacks.onError) {
            callbacks.onError(err);
        } else {
            throw err;
        }
    }
}


export async function fetchActiveChat(restaurantId?: string | null): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    if (!token) return null;
    
    const url = restaurantId 
        ? `${API_BASE_URL}/api/chat/active?restaurant_id=${restaurantId}`
        : `${API_BASE_URL}/api/chat/active`;
    const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        return null; // Return null if it fails, maybe token expired or no active chat
    }
    return response.json();
}

export async function abandonActiveChat(conversationId?: string | null): Promise<boolean> {
    const token = typeof window !== "undefined" ? localStorage.getItem("userToken") : null;
    if (!token) return false;
    
    const url = conversationId 
        ? `${API_BASE_URL}/api/chat/abandon?conversation_id=${conversationId}`
        : `${API_BASE_URL}/api/chat/abandon`;
        
    const response = await fetch(url, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });
    return response.ok;
}

export async function sendAdminInsightChat(message: string): Promise<any> {
    const token = typeof window !== "undefined" ? localStorage.getItem("adminToken") : null;
    const response = await fetch(`${API_BASE_URL}/api/admin/insights/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ message })
    });
    if (!response.ok) {
        const detail = await response.text().catch(() => "");
        throw new Error(detail || `Admin insight request failed (${response.status})`);
    }
    return response.json();
}

export async function streamAdminInsightChat(
    message: string,
    callbacks: {
        onStatus?: (data: { step: string; message: string }) => void;
        onMetadata?: (data: StreamAdminMetadataEvent) => void;
        onToken?: (token: string) => void;
        onDone?: (data: StreamAdminDoneEvent) => void;
        onError?: (err: Error) => void;
    }
): Promise<void> {
    const token = typeof window !== "undefined" ? localStorage.getItem("adminToken") : null;
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/insights/chat/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { "Authorization": `Bearer ${token}` } : {})
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            const detail = await response.text().catch(() => "");
            throw new Error(detail || `Streaming insight failed (${response.status})`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error("Response body is not readable");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const blocks = buffer.split("\n\n");
            buffer = blocks.pop() || "";

            for (const block of blocks) {
                if (!block.trim()) continue;
                const lines = block.split("\n");
                let eventType = "message";
                let dataStr = "";

                for (const line of lines) {
                    if (line.startsWith("event:")) {
                        eventType = line.replace("event:", "").trim();
                    } else if (line.startsWith("data:")) {
                        dataStr = line.replace("data:", "").trim();
                    }
                }

                if (!dataStr) continue;

                try {
                    const parsed = JSON.parse(dataStr);
                    if (eventType === "status" && callbacks.onStatus) {
                        callbacks.onStatus(parsed);
                    } else if (eventType === "metadata" && callbacks.onMetadata) {
                        callbacks.onMetadata(parsed);
                    } else if (eventType === "token" && callbacks.onToken) {
                        callbacks.onToken(parsed.content || "");
                    } else if (eventType === "done" && callbacks.onDone) {
                        callbacks.onDone(parsed);
                    }
                } catch (parseError) {
                    console.error("Failed to parse SSE JSON payload:", parseError, dataStr);
                }
            }
        }
    } catch (err: any) {
        if (callbacks.onError) {
            callbacks.onError(err);
        } else {
            throw err;
        }
    }
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

export async function fetchAdminMetrics(
    token: string,
    timeRange: string = "30d",
    startDate?: string,
    endDate?: string
): Promise<any> {
    let url = `${API_BASE_URL}/api/admin/metrics?time_range=${timeRange}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch metrics");
    }
    return response.json();
}

export async function fetchAdminAnalytics(
    token: string,
    timeRange: string = "30d",
    startDate?: string,
    endDate?: string
): Promise<AdminAnalyticsResponse> {
    let url = `${API_BASE_URL}/api/admin/analytics?time_range=${timeRange}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch analytics");
    }
    return response.json() as Promise<AdminAnalyticsResponse>;
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

export async function addToCart(payload: { restaurant_id: string, menu_item_id: string, quantity: number }): Promise<any> {
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
