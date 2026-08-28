"use client";

import React, { useEffect, useState } from "react";
import { fetchAdminConversations, fetchAdminAuditLogs } from "@/lib/api";
import { ChevronRight, Terminal, LayoutPanelLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import WormLogViewer from "@/components/admin/WormLogViewer";

export default function ConversationsPage() {
    const [conversations, setConversations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    const [selectedAuditLogs, setSelectedAuditLogs] = useState<any[] | null>(null);
    const [loadingLogs, setLoadingLogs] = useState(false);
    const [viewMode, setViewMode] = useState<'ui' | 'json'>('ui');

    const handleViewAllLogs = async (conversationId: string) => {
        setLoadingLogs(true);
        setSelectedAuditLogs([]); 
        try {
            const token = localStorage.getItem("adminToken");
            if (token) {
                const data = await fetchAdminAuditLogs(token, conversationId);
                const logs = data.logs || [];
                logs.sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
                setSelectedAuditLogs(logs);
            }
        } catch (err) {
            console.error("Failed to fetch audit logs:", err);
            setSelectedAuditLogs(null);
        } finally {
            setLoadingLogs(false);
        }
    };

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
                <p className="text-sm text-zinc-400">Review historical solver outputs and LLM constraints per conversation.</p>
            </div>

            <div className="overflow-hidden rounded-xl border border-white/10 bg-white/[.03]">
                <table className="min-w-[760px] w-full text-left">
                    <thead className="border-b border-white/8 text-[9px] font-bold uppercase tracking-[.15em] text-zinc-600">
                        <tr>
                            <th className="px-5 py-3">ID / Time</th>
                            <th className="px-4 py-3">Venue</th>
                            <th className="px-4 py-3">Customer</th>
                            <th className="px-4 py-3 text-right">Items in Cart</th>
                            <th className="px-5 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading && (
                            <tr>
                                <td colSpan={5} className="px-5 py-8 text-center text-zinc-500">
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
                                        {new Date(conv.created_at).toLocaleString(undefined, {
                                            dateStyle: 'medium',
                                            timeStyle: 'short'
                                        })}
                                    </p>
                                </td>
                                <td className="px-4 py-4 font-medium text-[#f6a61d]">
                                    {conv.restaurant_name || conv.restaurant_id || "Unknown"}
                                </td>
                                <td className="px-4 py-4 text-zinc-300">
                                    {conv.customer_name || "Unknown"}
                                </td>
                                <td className="px-4 py-4 text-right font-semibold text-white">
                                    {conv.current_cart ? conv.current_cart.length : 0} items
                                </td>
                                <td className="px-5 py-4 text-right flex items-center justify-end gap-2">
                                    <button
                                        onClick={() => handleViewAllLogs(conv.id)}
                                        className="inline-flex items-center gap-1 rounded bg-white/[0.08] px-3 py-1.5 text-xs font-medium text-emerald-400 transition hover:bg-white/[0.15]"
                                    >
                                        All Logs
                                    </button>
                                    <button
                                        onClick={() => router.push(`/admin/conversations/${conv.id}`)}
                                        className="inline-flex items-center gap-1 rounded bg-white/[0.08] px-3 py-1.5 text-xs font-medium text-white transition hover:bg-white/[0.15]"
                                    >
                                        View Chat <ChevronRight className="h-3 w-3" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {!loading && conversations.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-5 py-8 text-center text-zinc-500">
                                    No conversations found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal for All WORM Logs */}
            {selectedAuditLogs !== null && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
                    <div className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-white/10 bg-zinc-900 shadow-2xl">
                        
                        {/* Header */}
                        <div className="flex items-center justify-between border-b border-white/10 p-5 bg-zinc-950">
                            <div>
                                <h2 className="text-lg font-semibold text-white">All Conversation Logs</h2>
                                <p className="text-xs text-zinc-500 mt-1">Full Immutable WORM Trail</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="flex items-center bg-zinc-800 rounded-lg p-1">
                                    <button 
                                        onClick={() => setViewMode('ui')}
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${viewMode === 'ui' ? 'bg-[#f6a61d] text-zinc-900' : 'text-zinc-400 hover:text-white'}`}
                                    >
                                        <LayoutPanelLeft className="h-4 w-4" /> UI View
                                    </button>
                                    <button 
                                        onClick={() => setViewMode('json')}
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${viewMode === 'json' ? 'bg-[#f6a61d] text-zinc-900' : 'text-zinc-400 hover:text-white'}`}
                                    >
                                        <Terminal className="h-4 w-4" /> Raw JSON
                                    </button>
                                </div>
                                <button
                                    onClick={() => setSelectedAuditLogs(null)}
                                    className="rounded p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                                </button>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-6 bg-zinc-900">
                            {loadingLogs ? (
                                <div className="text-center text-zinc-500 py-12">Loading secure audit logs...</div>
                            ) : selectedAuditLogs.length === 0 ? (
                                <div className="text-center text-zinc-500 py-12">No audit logs found for this conversation.</div>
                            ) : (
                                selectedAuditLogs.map((log: any, idx: number) => (
                                    <WormLogViewer key={idx} log={log} viewMode={viewMode} />
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
