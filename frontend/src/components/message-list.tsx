"use client";

import { Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import type { ConversationMessage } from "@/types";

interface MessageListProps {
    messages: ConversationMessage[];
    isLoading: boolean;
    error: string | null;
}

export function MessageList({ messages, isLoading, error }: MessageListProps) {
    return (
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
            {messages.map((message) => (
                <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={
                        message.role === "user"
                            ? "ml-auto max-w-[82%] rounded-2xl rounded-tr-md bg-[#f6a61d] px-4 py-3 text-sm text-[#24190b]"
                            : "max-w-[90%] rounded-2xl rounded-tl-md border border-white/8 bg-white/[.035] px-4 py-3 text-sm leading-6 text-zinc-300"
                    }
                >
                    {message.role === "assistant" && (
                        <span className="mb-1 flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[.15em] text-[#f6a61d]">
                            <Sparkles className="h-3 w-3" /> verified explanation
                        </span>
                    )}
                    {message.content}
                </motion.div>
            ))}
            {isLoading && (
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-[#f6a61d]" />{" "}
                    Screening menu constraints…
                </div>
            )}
            {error && (
                <div className="rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-xs leading-5 text-red-200">
                    {error}
                </div>
            )}
        </div>
    );
}
