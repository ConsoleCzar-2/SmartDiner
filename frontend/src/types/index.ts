export interface ChatRequest {
    message: string;
    restaurant_id: string | null;
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
    vegan_servings?: number;
    nonveg_servings: number;
    decision_rationale?: any;
}

export interface ExtractedConstraints {
    people_count?: number | null;
    vegetarian_count?: number | null;
    vegan_count?: number | null;
    non_vegetarian_count?: number | null;
    max_budget?: number | null;
    max_spice_level?: string | null;
    allergens?: string[];
    dietary_preferences?: string[];
    [key: string]: unknown;
}

export interface CandidateComparison {
    restaurant_id: string;
    restaurant_name: string;
    cuisine?: string;
    sample_dish?: string;
    starting_price?: number;
}

export interface CrossRestaurantMeta {
    status: string;
    is_cross_restaurant?: boolean;
    comparison_summary?: string;
    candidates?: CandidateComparison[];
}

export interface ChatResponse {
    conversation_id: string | null;
    restaurant_id?: string | null;
    restaurant_name?: string | null;
    recommendation: RecommendationResult;
    explanation: string;
    extracted_constraints: ExtractedConstraints;
    cross_restaurant_meta?: CrossRestaurantMeta | null;
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

export interface AdminChatResponse {
    answer: string;
    target_source: string;
    data_sources: string[];
    metrics_summary?: any;
}

export type TimeRange = "12h" | "24h" | "today" | "7d" | "30d" | "90d" | "all" | "custom";

export interface DailyTrendPoint {
    date: string;
    revenue: number;
    orders: number;
    orders_count?: number;
}

export interface TopDishItem {
    name: string;
    category: string;
    restaurant_name?: string | null;
    quantity_sold: number;
    revenue: number;
    image_url?: string | null;
}

export interface CategoryDistributionItem {
    category: string;
    quantity_sold: number;
    revenue: number;
    percentage: number;
}

export interface SolverHealthMetrics {
    total_evaluations?: number;
    total_solves?: number;
    optimal_count: number;
    infeasible_count: number;
    feasibility_rate_pct: number;
    avg_solve_time_ms: number;
}

export interface RecentOrderItem {
    id: string;
    customer_name?: string | null;
    restaurant_name?: string | null;
    total_amount: number;
    status: string;
    created_at: string;
    items_count: number;
}

export interface AdminMetrics {
    time_range: string;
    total_orders: number;
    total_conversations: number;
    total_revenue: number;
    avg_order_value: number;
    budget_adherence_rate: number;
    total_servings_recommended: number;
    revenue_growth_pct?: number | null;
    orders_growth_pct?: number | null;
    conversations_growth_pct?: number | null;
}

export interface AdminAnalyticsResponse {
    time_range: string;
    metrics: AdminMetrics;
    daily_trends: DailyTrendPoint[];
    top_dishes: TopDishItem[];
    category_distribution: CategoryDistributionItem[];
    solver_health: SolverHealthMetrics;
    allergen_frequency: Record<string, number>;
    recent_orders: RecentOrderItem[];
}

export interface StreamStatusEvent {
    step: string;
    message: string;
}

export interface StreamCartEvent {
    recommendation: RecommendationResult;
}

export interface StreamTokenEvent {
    content: string;
}

export interface StreamDoneEvent {
    response: ChatResponse;
    telemetry?: any;
}

export interface StreamAdminMetadataEvent {
    target_source: string;
    data_sources: string[];
    metrics_summary?: any;
}

export interface StreamAdminDoneEvent {
    answer: string;
    target_source: string;
    data_sources: string[];
    metrics_summary?: any;
}

