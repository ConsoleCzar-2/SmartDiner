export interface ChatRequest {
    message: string;
    restaurant_id: string;
    conversation_id: string | null;
}
export interface RecommendedItem {
    id: string;
    name: string;
    category: string;
    quantity: number;
    unit_price: number;
    subtotal: number;
    dietary_preference: string;
    spice_level: string;
    serving_size: number;
    total_servings: number;
    image_url?: string | null;
}
export interface RecommendationResult {
    status: "Optimal" | "Infeasible" | string;
    reason: string;
    items: RecommendedItem[];
    computed_total: number;
    budget_remaining: number | null;
    total_servings: number;
    veg_servings: number;
    nonveg_servings: number;
}
export interface ExtractedConstraints {
    people_count?: number | null;
    vegetarian_count?: number | null;
    max_budget?: number | null;
    max_spice_level?: string | null;
    allergens?: string[];
    dietary_preferences?: string[];
    [key: string]: unknown;
}
export interface ChatResponse {
    conversation_id: string | null;
    recommendation: RecommendationResult;
    explanation: string;
    extracted_constraints: ExtractedConstraints;
}
export interface ConversationMessage {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    createdAt: string;
}

export interface RestaurantResponse {
    id: string;
    name: string;
    cuisine_type: string | null;
    image_url: string | null;
}
