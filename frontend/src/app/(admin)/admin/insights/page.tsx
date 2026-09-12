"use client";

import { useState, useRef, useEffect } from "react";
import { Sparkles, Send, Bot, User, Database, ShieldCheck, Loader2, ArrowRight } from "lucide-react";
import { sendAdminInsightChat } from "@/lib/api";
import { MarkdownContent } from "@/components/ui/markdown-content";

interface InsightMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    targetSource?: string;
    dataSources?: string[];
    timestamp: string;
}

const SUGGESTED_QUERIES = [
    "What are our top-selling dishes and total revenue?",
    "Summarize total LLM token usage and average solver latency",
    "What is our solver feasibility rate and average solve times?",
    "Break down our menu items across categories and average prices",
    "Give me an executive business and operational summary"
];

export default function AdminInsightsPage() {
    const [messages, setMessages] = useState<InsightMessage[]>([
        {
            id: "welcome",
            role: "assistant",
            content: "Welcome to **SmartDiner Admin AI Insights**!\n\nI can query your **PostgreSQL business records** (orders, revenue, customer volume, dishes) and your **GCS WORM audit logs** (token burn, solver decisions, system latencies). Ask me any operational or financial question!",
            targetSource: "SYSTEM",
            dataSources: ["PostgreSQL Database", "GCS WORM Audit Logs"],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
    ]);
    const [inputMessage, setInputMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSend = async (queryText?: string) => {
        const text = (queryText || inputMessage).trim();
        if (!text || isLoading) return;

        setError(null);
        const userMsg: InsightMessage = {
            id: `user-${Date.now()}`,
            role: "user",
            content: text,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages((prev) => [...prev, userMsg]);
        setInputMessage("");
        setIsLoading(true);

        try {
            const data = await sendAdminInsightChat(text);
            const assistantMsg: InsightMessage = {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: data.answer,
                targetSource: data.target_source,
                dataSources: data.data_sources || [],
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } catch (err: any) {
            setError(err.message || "Failed to generate business insights.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen flex-col bg-[#0c1011] text-zinc-100">
            {/* Top Header */}
            <header className="flex items-center justify-between border-b border-white/10 px-8 py-4 bg-[#0c1011]/80 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#f6a61d] text-[#171207] shadow-[0_0_20px_rgba(246,166,29,0.25)]">
                        <Sparkles className="h-5 w-5" />
                    </span>
                    <div>
                        <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                            Admin AI Executive Insights
                            <span className="rounded-full bg-[#f6a61d]/15 px-2.5 py-0.5 text-[10px] font-semibold text-[#f6a61d] border border-[#f6a61d]/30">
                                Dual-Source Grounded
                            </span>
                        </h1>
                        <p className="text-xs text-zinc-400">
                            PostgreSQL Aggregations + GCS WORM Audit Logs synthesized via Gemini 3.5 Flash Lite
                        </p>
                    </div>
                </div>
            </header>

            {/* Chat Body */}
            <div className="flex-1 overflow-y-auto px-6 py-6 lg:px-12 space-y-6">
                {/* Suggested Chips (shown if only welcome message) */}
                {messages.length === 1 && (
                    <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-3">
                            Suggested Executive Questions
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                            {SUGGESTED_QUERIES.map((query, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleSend(query)}
                                    className="flex items-center justify-between gap-3 text-left rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-xs text-zinc-300 hover:bg-white/[0.08] hover:text-white transition group"
                                >
                                    <span>{query}</span>
                                    <ArrowRight className="h-3.5 w-3.5 text-zinc-500 group-hover:text-[#f6a61d] transition shrink-0" />
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Messages List */}
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        {msg.role === "assistant" && (
                            <span className="grid h-8 w-8 place-items-center rounded-lg bg-zinc-800 text-[#f6a61d] border border-white/10 shrink-0">
                                <Bot className="h-4 w-4" />
                            </span>
                        )}

                        <div className={`max-w-2xl space-y-2`}>
                                <div
                                    className={`rounded-2xl px-5 py-3.5 text-xs sm:text-sm leading-relaxed ${
                                        msg.role === "user"
                                            ? "bg-[#f6a61d] text-[#171207] font-medium"
                                            : "bg-white/[0.04] text-zinc-200 border border-white/10"
                                    }`}
                                >
                                    <MarkdownContent 
                                        content={msg.content} 
                                        variant={msg.role === "user" ? "user" : "assistant"} 
                                    />
                                </div>

                            {/* Source Attribution Badges for Assistant */}
                            {msg.role === "assistant" && msg.dataSources && msg.dataSources.length > 0 && (
                                <div className="flex flex-wrap items-center gap-2 pt-1 text-[10px]">
                                    {msg.targetSource && msg.targetSource !== "SYSTEM" && (
                                        <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-amber-400 border border-amber-500/20 font-medium">
                                            Route: {msg.targetSource}
                                        </span>
                                    )}
                                    {msg.dataSources.map((source, i) => (
                                        <span
                                            key={i}
                                            className="flex items-center gap-1 rounded-full bg-white/[0.05] px-2 py-0.5 text-zinc-400 border border-white/10"
                                        >
                                            <Database className="h-2.5 w-2.5 text-cyan-400" />
                                            {source}
                                        </span>
                                    ))}
                                    <span className="text-zinc-500 ml-auto">{msg.timestamp}</span>
                                </div>
                            )}
                        </div>

                        {msg.role === "user" && (
                            <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/10 text-white shrink-0">
                                <User className="h-4 w-4" />
                            </span>
                        )}
                    </div>
                ))}

                {isLoading && (
                    <div className="flex items-center gap-3 text-zinc-400 text-xs pl-2">
                        <Loader2 className="h-4 w-4 animate-spin text-[#f6a61d]" />
                        <span>Analyzing data sources and formulating executive insights...</span>
                    </div>
                )}

                {error && (
                    <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-400">
                        {error}
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="border-t border-white/10 bg-[#0c1011]/90 p-4 backdrop-blur-xl">
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSend();
                    }}
                    className="mx-auto flex max-w-4xl items-center gap-3"
                >
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Ask about revenue, popular dishes, token usage, or solver performance..."
                        disabled={isLoading}
                        className="flex-1 rounded-full border border-white/15 bg-white/[0.05] px-5 py-3 text-xs sm:text-sm text-white placeholder:text-zinc-500 focus:border-[#f6a61d] focus:outline-none focus:ring-1 focus:ring-[#f6a61d] transition"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !inputMessage.trim()}
                        className="grid h-11 w-11 place-items-center rounded-full bg-[#f6a61d] text-[#171207] hover:bg-[#e09315] disabled:opacity-40 disabled:hover:bg-[#f6a61d] transition shadow-[0_0_20px_rgba(246,166,29,0.2)]"
                    >
                        {isLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
