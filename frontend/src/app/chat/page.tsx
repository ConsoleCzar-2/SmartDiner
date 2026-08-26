"use client";

import { ArrowLeft, ShieldCheck } from "lucide-react";
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
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [restaurant, setRestaurant] = useState({ id: "", name: "" });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!restaurantId) {
            router.push("/");
            return;
        }

        fetchRestaurants()
            .then((data) => {
                const found = data.find((r) => r.id === restaurantId);
                if (found) {
                    setRestaurant({ id: found.id, name: found.name });
                } else {
                    router.push("/");
                }
            })
            .catch((err) => {
                console.error(err);
                router.push("/");
            });
    }, [restaurantId, router]);

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
                <div>
                    <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#f6a61d]">
                        Ordering at {restaurant.name}
                    </p>
                    <h1 className="mt-2 text-3xl font-black tracking-[-.06em] text-white sm:text-4xl">
                        Tell us what the table needs.
                    </h1>
                </div>
                <span className="flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/[.06] px-3 py-2 text-[10px] font-semibold uppercase tracking-[.12em] text-emerald-300">
                    <ShieldCheck className="h-3.5 w-3.5" /> Safety filter active
                </span>
            </div>
            <div className="mt-7 grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_390px]">
                <ChatPanel
                    messages={messages}
                    isLoading={isLoading}
                    error={error}
                    onSend={submit}
                />
                <CartPanel recommendation={recommendation} />
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
