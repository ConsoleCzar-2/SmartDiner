"use client";

import { ArrowLeft, Plus, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Navbar } from "@/components/navbar";
import { CartPanel } from "@/components/cart-panel";
import { ChatPanel } from "@/components/chat-panel";
import { sendChatMessage, fetchRestaurants } from "@/lib/api";
import type {
    ChatResponse,
    ConversationMessage,
    RecommendationResult,
} from "@/types";

const initialMessages: ConversationMessage[] = [
    {
        id: "hello",
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

    const [messages, setMessages] = useState<ConversationMessage[]>(initialMessages);
    const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
    const [constraints, setConstraints] = useState<any>(null);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [restaurant, setRestaurant] = useState<{ id: string; name: string; image_url: string | null }>({ id: "", name: "", image_url: null });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const token = localStorage.getItem("userToken");
        if (!token) {
            router.push("/login");
            return;
        }

        if (!restaurantId) {
            router.push("/");
            return;
        }

        fetchRestaurants()
            .then((data) => {
                const found = data.find((r) => r.id === restaurantId);
                if (found) {
                    setRestaurant({ id: found.id, name: found.name, image_url: found.image_url });
                    import("@/lib/api").then(({ fetchActiveChat }) => {
                        fetchActiveChat(found.id).then((chatData) => {
                            if (chatData && chatData.conversation_id) {
                                setConversationId(chatData.conversation_id);
                                if (chatData.history && chatData.history.length > 0) {
                                    setMessages(chatData.history);
                                }
                                if (chatData.current_constraints) {
                                    setConstraints(chatData.current_constraints);
                                }
                                if (chatData.current_cart && chatData.current_cart.length > 0) {
                                    // Reconstruct recommendation result
                                    const total = chatData.current_cart.reduce((sum: number, item: any) => sum + item.subtotal, 0);
                                    setRecommendation({
                                        status: "Optimal",
                                        reason: "Restored from draft",
                                        items: chatData.current_cart,
                                        computed_total: total,
                                        budget_remaining: chatData.current_constraints?.max_budget ? chatData.current_constraints.max_budget - total : null,
                                        total_servings: 0,
                                        veg_servings: 0,
                                        nonveg_servings: 0
                                    });
                                }
                            }
                        }).catch(console.error);
                    });
                } else {
                    router.push("/");
                }
            })
            .catch((err) => {
                console.error(err);
                router.push("/");
            });
    }, [restaurantId, router]);

    const clearChat = () => {
        setConversationId(null);
        setMessages(initialMessages);
        setRecommendation(null);
        setConstraints(null);
        setError(null);
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
                restaurant_id: restaurant.id,
                conversation_id: conversationId,
            });
            setConversationId(response.conversation_id);
            setRecommendation(response.recommendation);
            if (response.extracted_constraints) {
                setConstraints(response.extracted_constraints);
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

    if (!restaurant.id) return null; // Wait for redirect or fetch to complete

    return (
        <div className="mx-auto max-w-7xl px-5 py-8 lg:px-8">
            <Link
                href="/"
                className="inline-flex items-center gap-2 text-xs font-semibold text-zinc-500 transition hover:text-[#f6a61d]"
            >
                <ArrowLeft className="h-3.5 w-3.5" /> Change venue
            </Link>
            <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
                <div className="flex items-center gap-4">
                    {restaurant.image_url && (
                        <img 
                            src={restaurant.image_url} 
                            alt={restaurant.name} 
                            className="h-16 w-16 rounded-lg object-cover border border-zinc-800"
                        />
                    )}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#f6a61d]">
                            Ordering at {restaurant.name}
                        </p>
                        <h1 className="mt-2 text-3xl font-black tracking-[-.06em] text-white sm:text-4xl">
                            Tell us what the table needs.
                        </h1>
                    </div>
                </div>
                <div className="flex flex-col items-end gap-3">
                    {conversationId && (
                        <button 
                            onClick={clearChat}
                            className="flex items-center gap-2 rounded-full border border-zinc-700 bg-zinc-800/50 px-4 py-2 text-xs font-semibold tracking-wide text-zinc-300 transition hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-400">
                            <Plus className="h-4 w-4" />
                            Start fresh conversation
                        </button>
                    )}
                </div>
            </div>
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
            <Suspense fallback={<div className="p-8 text-white">Loading chat...</div>}>
                <ChatContent />
            </Suspense>
        </main>
    );
}
