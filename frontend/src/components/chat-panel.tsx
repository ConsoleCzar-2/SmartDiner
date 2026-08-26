"use client";

import { Bot, Send } from "lucide-react";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import type { ConversationMessage } from "@/types";
import { MessageList } from "./message-list";

interface ChatPanelProps {
    messages: ConversationMessage[];
    isLoading: boolean;
    error: string | null;
    onSend: (message: string) => void;
}

export function ChatPanel({
    messages,
    isLoading,
    error,
    onSend,
}: ChatPanelProps) {
    const [input, setInput] = useState("");

    const submit = () => {
        const message = input.trim();
        if (!message || isLoading) return;
        onSend(message);
        setInput("");
    };

    return (
        <section className="flex min-h-[620px] flex-col rounded-3xl border border-white/10 bg-[#111718]/80 shadow-xl">
            <div className="flex items-center justify-between border-b border-white/8 px-5 py-4">
                <div className="flex items-center gap-3">
                    <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f6a61d]/12 text-[#f6a61d]">
                        <Bot className="h-5 w-5" />
                    </span>
                    <div>
                        <p className="text-sm font-bold text-white">
                            Diner Concierge
                        </p>
                        <p className="text-[10px] font-semibold uppercase tracking-[.14em] text-emerald-300">
                            Governed AI pipeline
                        </p>
                    </div>
                </div>
                <span className="text-[10px] font-medium text-zinc-500">
                    Safety before suggestions
                </span>
            </div>

            <MessageList messages={messages} isLoading={isLoading} error={error} />

            <div className="border-t border-white/8 p-4">
                <div className="rounded-2xl border border-white/10 bg-black/20 p-2 focus-within:border-[#f6a61d]/60">
                    <Textarea
                        value={input}
                        onChange={(event) => setInput(event.target.value)}
                        onKeyDown={(event) => {
                            if (event.key === "Enter" && !event.shiftKey) {
                                event.preventDefault();
                                submit();
                            }
                        }}
                        placeholder="e.g. Food for 5, 2 vegetarian, ₹2,000 budget"
                        className="min-h-20 resize-none border-0 bg-transparent text-sm text-white placeholder:text-zinc-600 focus-visible:ring-0"
                    />
                    <div className="flex items-center justify-between px-2 pb-1">
                        <span className="text-[10px] text-zinc-600">
                            Enter to send · Shift+Enter for a new line
                        </span>
                        <Button
                            size="sm"
                            onClick={submit}
                            disabled={!input.trim() || isLoading}
                            className="h-8 gap-2 rounded-xl bg-[#f6a61d] px-4 text-xs font-bold text-[#24190b] hover:bg-[#e59815]"
                        >
                            Send <Send className="h-3 w-3" />
                        </Button>
                    </div>
                </div>
            </div>
        </section>
    );
}
