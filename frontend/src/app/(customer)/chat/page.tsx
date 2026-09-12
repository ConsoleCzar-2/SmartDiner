"use client";

import { ArrowLeft, Plus, ShieldCheck, Sparkles, Store, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Navbar } from "@/components/navbar";
import { CartPanel } from "@/components/cart-panel";
import { ChatPanel } from "@/components/chat-panel";
import { sendChatMessage, fetchRestaurants, abandonActiveChat } from "@/lib/api";
import type {
    ChatResponse,
    ConversationMessage,
    RecommendationResult,
    CrossRestaurantMeta,
} from "@/types";

const globalInitialMessages: ConversationMessage[] = [
    {
        id: "hello-global",
        role: "assistant",
        content:
            "Welcome to **SmartDiner AI Concierge**!\n\nYou can ask me to order from any specific restaurant (e.g. *'Order biryani from Spice Garden'*), or let me search and optimize across all venues for the best value, highest ratings, or specific dietary needs (e.g. *'Find the cheapest biryani for 3 people'* or *'Best vegan dinner under 1000'*).",
        createdAt: new Date().toISOString(),
    },
];

const scopedInitialMessages: ConversationMessage[] = [
    {
        id: "hello-scoped",
        role: "assistant",
        content:
            "Tell me about your table: party size, budget, vegetarian split, allergens, or spice preferences. I’ll use the governed pipeline to find a safe, optimal combination.",
        createdAt: new Date().toISOString(),
    },
];

function ChatContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const restaurantId = searchParams.get("restaurant_id");

    const [messages, setMessages] = useState<ConversationMessage[]>(
        restaurantId ? scopedInitialMessages : globalInitialMessages
    );
    const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
    const [constraints, setConstraints] = useState<any>(null);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [restaurant, setRestaurant] = useState<{ id: string; name: string; image_url: string | null }>({
        id: restaurantId || "",
        name: restaurantId ? "Loading restaurant..." : "SmartDiner Concierge",
        image_url: null,
    });
    const [crossMeta, setCrossMeta] = useState<CrossRestaurantMeta | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const applyActiveChat = (chatData: any, matchedRestaurant?: any) => {
        if (!chatData || !chatData.conversation_id) return;
        setConversationId(chatData.conversation_id);
        if (chatData.history && chatData.history.length > 0) {
            setMessages(chatData.history);
        }
        if (chatData.current_constraints) {
            setConstraints(chatData.current_constraints);
        }
        if (chatData.current_cart && chatData.current_cart.length > 0) {
            const total = chatData.current_cart.reduce((sum: number, item: any) => sum + (item.subtotal || 0), 0);
            let veg_servings = 0;
            let vegan_servings = 0;
            let nonveg_servings = 0;
            for (const item of chatData.current_cart) {
                const s = item.total_servings || (item.quantity * (item.serving_size || 1));
                if (item.dietary_preference === "Vegetarian") veg_servings += s;
                else if (item.dietary_preference === "Vegan") vegan_servings += s;
                else nonveg_servings += s;
            }
            setRecommendation({
                status: "Optimal",
                reason: "Restored from draft",
                items: chatData.current_cart,
                computed_total: total,
                budget_remaining: chatData.current_constraints?.max_budget ? Math.round((chatData.current_constraints.max_budget - total) * 100) / 100 : null,
                total_servings: veg_servings + vegan_servings + nonveg_servings,
                veg_servings,
                vegan_servings,
                nonveg_servings,
            });
        }
        if (matchedRestaurant) {
            setRestaurant({
                id: matchedRestaurant.id,
                name: matchedRestaurant.name,
                image_url: matchedRestaurant.image_url,
            });
        }
    };

    useEffect(() => {
        const token = localStorage.getItem("userToken");
        if (!token) {
            router.push("/login");
            return;
        }

        if (restaurantId) {
            fetchRestaurants()
                .then((data) => {
                    const found = data.find((r) => r.id === restaurantId);
                    if (found) {
                        setRestaurant({ id: found.id, name: found.name, image_url: found.image_url });
                        import("@/lib/api").then(({ fetchActiveChat }) => {
                            fetchActiveChat(found.id).then((chatData) => {
                                applyActiveChat(chatData, found);
                            }).catch(console.error);
                        });
                    }
                })
                .catch(console.error);
        } else {
            // Global Concierge Mode — check for active global session
            import("@/lib/api").then(({ fetchActiveChat, fetchRestaurants }) => {
                fetchRestaurants().then((allR) => {
                    fetchActiveChat(null).then((chatData) => {
                        if (chatData && chatData.conversation_id) {
                            const rFound = chatData.restaurant_id ? allR.find(r => r.id === chatData.restaurant_id) : null;
                            applyActiveChat(chatData, rFound);
                        }
                    }).catch(console.error);
                }).catch(console.error);
            });
        }
    }, [restaurantId, router]);

    const clearChat = () => {
        if (conversationId) {
            abandonActiveChat(conversationId).catch(console.error);
        }
        setConversationId(null);
        setRestaurant({ id: "", name: "SmartDiner Concierge", image_url: null });
        setMessages(globalInitialMessages);
        setRecommendation(null);
        setConstraints(null);
        setCrossMeta(null);
        setError(null);
        window.history.replaceState(null, '', '/chat');
    };

    const handleFinalizeRestaurant = (rId: string, rName: string) => {
        setRestaurant(prev => ({ ...prev, id: rId, name: rName }));
        setCrossMeta(null);
        window.history.replaceState(null, '', `/chat?restaurant_id=${rId}`);
    };

    const submit = async (message: string) => {
        setError(null);
        setMessages((current) => [
            ...current,
            {
                id: crypto.randomUUID(),
                role: "user",
                content: message,
                createdAt: new Date().toISOString(),
            },
        ]);
        setIsLoading(true);
        try {
            const response: ChatResponse = await sendChatMessage({
                message,
                restaurant_id: restaurant.id || null,
                conversation_id: conversationId,
            });
            setConversationId(response.conversation_id);
            setRecommendation(response.recommendation);
            if (response.extracted_constraints) {
                setConstraints(response.extracted_constraints);
            }
            setCrossMeta(response.cross_restaurant_meta || null);
            if (response.restaurant_id && response.restaurant_name && response.restaurant_id !== restaurant.id) {
                const newRestId = response.restaurant_id;
                const newRestName = response.restaurant_name;
                fetchRestaurants().then(allR => {
                    const match = allR.find(r => r.id === newRestId);
                    setRestaurant({
                        id: newRestId,
                        name: newRestName,
                        image_url: match?.image_url || null
                    });
                }).catch(() => {
                    setRestaurant({
                        id: newRestId,
                        name: newRestName,
                        image_url: null
                    });
                });
                window.history.replaceState(null, '', `/chat?restaurant_id=${newRestId}`);
            }

            setMessages((current) => [
                ...current,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: response.explanation,
                    createdAt: new Date().toISOString(),
                },
            ]);
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to reach the recommendation service.",
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="mx-auto max-w-7xl px-5 py-8 lg:px-8">
            <div className="flex items-center justify-between">
                <Link
                    href="/"
                    className="inline-flex items-center gap-2 text-xs font-semibold text-zinc-500 transition hover:text-[#f6a61d]"
                >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    {restaurant.id ? "Change venue" : "Browse all restaurants"}
                </Link>

                {!restaurant.id && (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#f6a61d]/10 px-3 py-1 text-xs font-semibold text-[#f6a61d] border border-[#f6a61d]/20">
                        <Sparkles className="h-3.5 w-3.5" />
                        Cross-Restaurant Mode Active
                    </span>
                )}
            </div>

            <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
                <div className="flex items-center gap-4">
                    {restaurant.image_url ? (
                        <img 
                            src={restaurant.image_url} 
                            alt={restaurant.name} 
                            className="h-16 w-16 rounded-xl object-cover border border-zinc-800"
                        />
                    ) : (
                        <div className="grid h-16 w-16 place-items-center rounded-xl bg-[#f6a61d]/10 border border-[#f6a61d]/20 text-[#f6a61d]">
                            <Sparkles className="h-7 w-7" />
                        </div>
                    )}
                    <div>
                        {restaurant.id ? (
                            <div className="flex items-center gap-2">
                                <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#f6a61d]">
                                    Dining at {restaurant.name}
                                </p>
                                <button 
                                    onClick={clearChat}
                                    className="text-[5px] font-medium text-zinc-400 hover:text-[#f6a61d] underline decoration-zinc-600 transition"
                                    title="Switch back to global concierge across all restaurants"
                                >
                                    (Switch to all restaurants)
                                </button>
                            </div>
                        ) : (
                            <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#f6a61d]">
                                AI Concierge Service
                            </p>
                        )}
                        <h1 className="mt-1 text-2xl font-black tracking-[-.06em] text-white sm:text-3xl">
                            {restaurant.id ? "Tell us what the table needs." : "Discover & dine across any restaurant."}
                        </h1>
                    </div>
                </div>
                <div className="flex flex-col items-end gap-3">
                    {(conversationId || restaurant.id) && (
                        <button 
                            onClick={clearChat}
                            className="flex items-center gap-2 rounded-full border border-zinc-700 bg-zinc-800/50 px-4 py-2 text-xs font-semibold tracking-wide text-zinc-300 transition hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-400">
                            <Plus className="h-4 w-4" />
                            Start fresh conversation
                        </button>
                    )}
                </div>
            </div>

            {/* Cross-Restaurant Winner & Finalization Banner */}
            {crossMeta && crossMeta.candidates && crossMeta.candidates.length > 0 && (
                <div className="mt-6 rounded-2xl border border-[#f6a61d]/30 bg-[#f6a61d]/5 p-4 sm:p-5 backdrop-blur-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="space-y-1">
                            <span className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-[#f6a61d]">
                                <Store className="h-3.5 w-3.5" />
                                Optimal Venue Match
                            </span>
                            <h3 className="text-sm font-bold text-white">
                                {restaurant.name ? `Selected Venue: ${restaurant.name}` : "Multiple Venues Compared"}
                            </h3>
                            <p className="text-xs text-zinc-400">
                                {crossMeta.comparison_summary}
                            </p>
                        </div>
                        {restaurant.id && (
                            <button
                                onClick={() => handleFinalizeRestaurant(restaurant.id, restaurant.name)}
                                className="inline-flex items-center gap-2 rounded-full bg-[#f6a61d] px-4 py-2 text-xs font-bold text-[#171207] hover:bg-[#e09315] transition shadow-[0_0_20px_rgba(246,166,29,0.2)]"
                            >
                                <CheckCircle className="h-4 w-4" />
                                Lock In & Order from {restaurant.name}
                            </button>
                        )}
                    </div>
                </div>
            )}

            <div className="mt-7 grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_390px]">
                <ChatPanel
                    messages={messages}
                    isLoading={isLoading}
                    error={error}
                    onSend={submit}
                />
                <CartPanel recommendation={recommendation} constraints={constraints} conversationId={conversationId} />
            </div>
        </div>
    );
}

export default function ChatPage() {
    return (
        <main className="min-h-screen bg-[#0c1011]">
            <Navbar />
            <Suspense fallback={<div className="p-8 text-white">Loading concierge...</div>}>
                <ChatContent />
            </Suspense>
        </main>
    );
}
