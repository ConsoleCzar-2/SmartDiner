"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { AdminMetrics } from "@/components/admin-metrics";
import { fetchAdminMetrics, fetchAdminConversations } from "@/lib/api";

export default function AdminPage() {
    const [metrics, setMetrics] = useState<any>(null);
    const [conversations, setConversations] = useState<any[]>([]);

    useEffect(() => {
        const token = localStorage.getItem("adminToken");
        if (token) {
            fetchAdminMetrics(token).then(setMetrics).catch(console.error);
            fetchAdminConversations(token).then(setConversations).catch(console.error);
        }
    }, []);

    return (
        <main className="min-h-screen bg-[#0c1011]">
            <div className="mx-auto max-w-7xl px-5 py-10 lg:px-8">
                <div className="flex flex-wrap items-end justify-between gap-5">
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#f6a61d]">
                            SmartDiner operations
                        </p>
                        <h1 className="mt-2 text-4xl font-black tracking-[-.07em] text-white sm:text-5xl">
                            The proof is in the pass.
                        </h1>
                        <p className="mt-3 max-w-xl text-sm leading-6 text-zinc-400">
                            A narrow operational view of solver adherence,
                            budget accuracy, and the governed conversations
                            moving through the dining floor.
                        </p>
                    </div>
                    <button className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[.035] px-4 py-2.5 text-xs font-semibold text-zinc-300">
                        Last 30 days <ArrowUpRight className="h-3.5 w-3.5" />
                    </button>
                </div>
                <div className="mt-8">
                    <AdminMetrics data={metrics} />
                </div>
            </div>
        </main>
    );
}
