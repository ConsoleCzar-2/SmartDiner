"use client";

import { useEffect, useState } from "react";
import { fetchAdminConversations } from "@/lib/api";

export default function ConversationsPage() {
    const [conversations, setConversations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem("adminToken");
        if (token) {
            fetchAdminConversations(token)
                .then(setConversations)
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, []);

    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-white">Conversation Audit Log</h1>
                <p className="text-sm text-zinc-400">Review historical solver outputs and LLM constraints.</p>
            </div>

            <div className="overflow-hidden rounded-xl border border-white/10 bg-white/[.03]">
                <table className="min-w-[760px] w-full text-left">
                    <thead className="border-b border-white/8 text-[9px] font-bold uppercase tracking-[.15em] text-zinc-600">
                        <tr>
                            <th className="px-5 py-3">ID / Time</th>
                            <th className="px-4 py-3">Venue</th>
                            <th className="px-4 py-3">Constraints</th>
                            <th className="px-4 py-3 text-right">Items in Cart</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading && (
                            <tr>
                                <td colSpan={4} className="px-5 py-8 text-center text-zinc-500">
                                    Loading...
                                </td>
                            </tr>
                        )}
                        {!loading && conversations.map((conv) => (
                            <tr
                                key={conv.id}
                                className="border-b border-white/[.06] text-xs transition hover:bg-white/[.035]"
                            >
                                <td className="px-5 py-4">
                                    <p className="font-bold text-zinc-100">
                                        {conv.id.split("-")[0]}...
                                    </p>
                                    <p className="mt-1 text-[10px] text-zinc-600">
                                        {new Date(conv.created_at).toLocaleString()}
                                    </p>
                                </td>
                                <td className="px-4 py-4 text-zinc-300">
                                    {conv.restaurant_id || "Unknown"}
                                </td>
                                <td className="px-4 py-4 text-zinc-400">
                                    <pre className="text-[10px] max-w-xs overflow-x-auto">
                                        {JSON.stringify(conv.current_constraints, null, 2)}
                                    </pre>
                                </td>
                                <td className="px-4 py-4 text-right font-semibold text-white">
                                    {conv.current_cart ? conv.current_cart.length : 0} items
                                </td>
                            </tr>
                        ))}
                        {!loading && conversations.length === 0 && (
                            <tr>
                                <td colSpan={4} className="px-5 py-8 text-center text-zinc-500">
                                    No conversations found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
