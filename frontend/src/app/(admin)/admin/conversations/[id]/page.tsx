"use client";

import React, { useEffect, useState, use } from "react";
import { fetchAdminConversation, fetchAdminAuditLogs } from "@/lib/api";
import { User, Bot, FileJson, ArrowLeft, Terminal, LayoutPanelLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import WormLogViewer from "@/components/admin/WormLogViewer";

export default function ConversationDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const [conversation, setConversation] = useState<any>(null);
    const [auditLogs, setAuditLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    
    // Modal state
    const [selectedLog, setSelectedLog] = useState<any | null>(null);
    const [viewMode, setViewMode] = useState<'ui' | 'json'>('ui');

    useEffect(() => {
        const token = localStorage.getItem("adminToken");
        if (token) {
            Promise.all([
                fetchAdminConversation(token, id),
                fetchAdminAuditLogs(token, id)
            ])
            .then(([convData, logData]) => {
                setConversation(convData);
                const logs = logData.logs || [];
                logs.sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
                setAuditLogs(logs);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
        }
    }, [id]);

    const handleViewSpecificLog = (messageIndex: number) => {
        // The messageIndex is the index of the ASSISTANT message
        const specificLog = auditLogs[messageIndex];
        if (specificLog) {
            setSelectedLog(specificLog);
        } else {
            alert("No audit log found for this specific message. It might still be processing.");
        }
    };

    if (loading) {
        return <div className="p-8 text-zinc-500">Loading conversation details...</div>;
    }

    if (!conversation) {
        return <div className="p-8 text-red-500">Conversation not found.</div>;
    }

    return (
        <div className="p-8 max-w-5xl mx-auto">
            <button 
                onClick={() => router.push('/admin/conversations')}
                className="mb-6 flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition"
            >
                <ArrowLeft className="h-4 w-4" /> Back to all conversations
            </button>

            <div className="mb-8 flex items-end justify-between border-b border-white/10 pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">
                        Chat History
                    </h1>
                    <p className="text-sm text-zinc-400">
                        {conversation.customer_name} @ {conversation.restaurant_name || conversation.restaurant_id}
                    </p>
                </div>
                <div className="text-right text-xs text-zinc-500">
                    <p>ID: {conversation.id}</p>
                    <p>{new Date(conversation.created_at).toLocaleString()}</p>
                </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/[.02] p-6 max-h-[70vh] overflow-y-auto space-y-6">
                {conversation.messages && conversation.messages.length > 0 ? (
                    (() => {
                        let assistantMsgIndex = 0;
                        return conversation.messages.map((msg: any, idx: number) => {
                            const isAssistant = msg.role === "assistant";
                            const currentIndex = isAssistant ? assistantMsgIndex++ : -1;
                            
                            return (
                                <div key={idx} className={`flex gap-4 ${isAssistant ? '' : 'justify-end'}`}>
                                    {isAssistant && (
                                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#f6a61d]/20 text-[#f6a61d]">
                                            <Bot className="h-5 w-5" />
                                        </div>
                                    )}
                                    <div className={`flex flex-col gap-1 max-w-[80%] ${isAssistant ? '' : 'items-end'}`}>
                                        <div
                                            className={`rounded-2xl px-5 py-3 text-sm ${
                                                isAssistant
                                                    ? "bg-white/[0.05] text-zinc-200 border border-white/[0.05]"
                                                    : "bg-[#f6a61d] text-[#1e170d] font-medium"
                                            }`}
                                        >
                                            {msg.content}
                                        </div>
                                        {isAssistant && (
                                            <button 
                                                onClick={() => handleViewSpecificLog(currentIndex)}
                                                className="flex items-center gap-1.5 self-start text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 mt-2 ml-2 transition bg-emerald-500/10 px-2 py-1 rounded"
                                            >
                                                <FileJson className="h-3.5 w-3.5" /> 
                                                View WORM Log
                                            </button>
                                        )}
                                    </div>
                                    {!isAssistant && (
                                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-zinc-400">
                                            <User className="h-5 w-5" />
                                        </div>
                                    )}
                                </div>
                            );
                        });
                    })()
                ) : (
                    <p className="text-zinc-500 text-center py-4">No messages in this conversation yet.</p>
                )}
            </div>

            {/* Modal for WORM Log */}
            {selectedLog !== null && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
                    <div className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-white/10 bg-zinc-900 shadow-2xl">
                        
                        {/* Header */}
                        <div className="flex items-center justify-between border-b border-white/10 p-5 bg-zinc-950">
                            <div>
                                <h2 className="text-lg font-semibold text-white">Immutable WORM Audit Log</h2>
                                <p className="text-xs text-zinc-500 mt-1">Logged at: {new Date(selectedLog.timestamp).toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'medium'})}</p>
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
                                    onClick={() => setSelectedLog(null)}
                                    className="rounded p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                                </button>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-6 bg-zinc-900">
                            <WormLogViewer log={selectedLog} viewMode={viewMode} />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
