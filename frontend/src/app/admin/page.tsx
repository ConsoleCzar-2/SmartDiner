import { ArrowUpRight, MoreHorizontal } from "lucide-react";
import { Navbar } from "@/components/navbar";
import { AdminMetrics } from "@/components/admin-metrics";
const conversations = [
    {
        id: "CNV-88241",
        venue: "Kasa Ember",
        input: "5 people · 2 vegetarian · ₹2,000",
        outcome: "Optimal",
        total: "₹1,840",
        time: "4 min ago",
    },
    {
        id: "CNV-88238",
        venue: "Rasa Table",
        input: "3 people · gluten-aware · ₹1,600",
        outcome: "Optimal",
        total: "₹1,420",
        time: "21 min ago",
    },
    {
        id: "CNV-88232",
        venue: "Mizu Social",
        input: "8 people · vegan split · ₹3,000",
        outcome: "Infeasible",
        total: "—",
        time: "42 min ago",
    },
];
export default function AdminPage() {
    return (
        <main className="min-h-screen bg-[#0c1011]">
            <Navbar />
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
                    <AdminMetrics />
                </div>
                <section className="mt-5 overflow-hidden rounded-3xl border border-white/10 bg-white/[.03]">
                    <div className="flex items-center justify-between border-b border-white/8 px-5 py-4">
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-[.15em] text-zinc-500">
                                Recent conversations
                            </p>
                            <h2 className="mt-1 text-lg font-bold text-white">
                                Traceable recommendation ledger
                            </h2>
                        </div>
                        <span className="rounded-full border border-white/10 px-3 py-1.5 text-[10px] font-semibold text-zinc-400">
                            Live audit trail
                        </span>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="min-w-[760px] w-full text-left">
                            <thead className="border-b border-white/8 text-[9px] font-bold uppercase tracking-[.15em] text-zinc-600">
                                <tr>
                                    <th className="px-5 py-3">Conversation</th>
                                    <th className="px-4 py-3">Venue</th>
                                    <th className="px-4 py-3">Constraints</th>
                                    <th className="px-4 py-3">Result</th>
                                    <th className="px-4 py-3 text-right">
                                        Cart
                                    </th>
                                    <th className="px-5 py-3" />
                                </tr>
                            </thead>
                            <tbody>
                                {conversations.map((conversation) => (
                                    <tr
                                        key={conversation.id}
                                        className="border-b border-white/[.06] text-xs transition hover:bg-white/[.035]"
                                    >
                                        <td className="px-5 py-4">
                                            <p className="font-bold text-zinc-100">
                                                {conversation.id}
                                            </p>
                                            <p className="mt-1 text-[10px] text-zinc-600">
                                                {conversation.time}
                                            </p>
                                        </td>
                                        <td className="px-4 py-4 text-zinc-300">
                                            {conversation.venue}
                                        </td>
                                        <td className="px-4 py-4 text-zinc-500">
                                            {conversation.input}
                                        </td>
                                        <td className="px-4 py-4">
                                            <span
                                                className={
                                                    conversation.outcome ===
                                                    "Optimal"
                                                        ? "rounded-full bg-emerald-400/10 px-2 py-1 text-[9px] font-bold uppercase tracking-[.1em] text-emerald-300"
                                                        : "rounded-full bg-red-400/10 px-2 py-1 text-[9px] font-bold uppercase tracking-[.1em] text-red-300"
                                                }
                                            >
                                                {conversation.outcome}
                                            </span>
                                        </td>
                                        <td className="px-4 py-4 text-right font-bold text-white">
                                            {conversation.total}
                                        </td>
                                        <td className="px-5 py-4 text-right">
                                            <MoreHorizontal className="ml-auto h-4 w-4 text-zinc-500" />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            </div>
        </main>
    );
}
