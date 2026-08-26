"use client";
import {
    CheckCircle2,
    CircleAlert,
    Leaf,
    ReceiptText,
    Users,
} from "lucide-react";
import { motion } from "framer-motion";
import type { RecommendationResult } from "@/types";
const money = (value: number) =>
    new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
    }).format(value);
export function CartPanel({
    recommendation,
}: {
    recommendation: RecommendationResult | null;
}) {
    if (!recommendation)
        return (
            <aside className="sticky top-24 rounded-3xl border border-dashed border-white/15 bg-white/[.025] p-6">
                <ReceiptText className="h-8 w-8 text-[#f6a61d]" />
                <h2 className="mt-5 text-xl font-bold text-white">
                    Live order ticket
                </h2>
                <p className="mt-2 text-sm leading-6 text-zinc-500">
                    Your solver-approved cart will appear here after the
                    concierge has screened dietary, allergen, serving, and
                    budget constraints.
                </p>
            </aside>
        );
    const optimal = recommendation.status.toLowerCase() === "optimal";
    return (
        <aside className="sticky top-24 overflow-hidden rounded-3xl border border-white/10 bg-[#f7f4ed] text-[#241f19] shadow-2xl">
            <div className="border-b border-[#241f19]/10 bg-[#f6a61d] px-5 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-[9px] font-bold uppercase tracking-[.16em] text-[#76500e]">
                            Live order ticket
                        </p>
                        <h2 className="mt-1 text-lg font-black">
                            Solver recommendation
                        </h2>
                    </div>
                    {optimal ? (
                        <CheckCircle2 className="h-5 w-5" />
                    ) : (
                        <CircleAlert className="h-5 w-5" />
                    )}
                </div>
            </div>
            <div className="p-5">
                {recommendation.reason && !optimal && (
                    <p className="mb-4 rounded-xl bg-red-500/10 p-3 text-xs text-red-700">
                        {recommendation.reason}
                    </p>
                )}
                <div className="space-y-3">
                    {recommendation.items.map((item) => (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex gap-3 border-b border-[#241f19]/8 pb-3"
                        >
                            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#241f19]/6 text-xs font-black">
                                {item.quantity}×
                            </span>
                            <div className="min-w-0 flex-1">
                                <div className="flex items-start justify-between gap-2">
                                    <p className="text-sm font-bold">
                                        {item.name}
                                    </p>
                                    <p className="text-sm font-black tabular-nums">
                                        {money(item.subtotal)}
                                    </p>
                                </div>
                                <p className="mt-1 text-[10px] text-[#6d6257]">
                                    {item.category} · {item.spice_level} spice ·{" "}
                                    {item.total_servings} servings
                                </p>
                                {item.is_veg && (
                                    <span className="mt-1 flex w-fit items-center gap-1 text-[10px] font-semibold text-emerald-700">
                                        <Leaf className="h-3 w-3" /> Vegetarian
                                    </span>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </div>
                <div className="mt-5 space-y-2 border-t border-dashed border-[#241f19]/20 pt-4 text-sm">
                    <div className="flex justify-between">
                        <span className="text-[#6d6257]">Computed total</span>
                        <span className="font-black">
                            {money(recommendation.computed_total)}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-[#6d6257]">Budget remaining</span>
                        <span className="font-black text-emerald-700">
                            {recommendation.budget_remaining === null
                                ? "—"
                                : money(recommendation.budget_remaining)}
                        </span>
                    </div>
                </div>
                <div className="mt-5 grid grid-cols-3 gap-2">
                    <div className="rounded-xl bg-[#241f19]/5 p-2 text-center">
                        <Users className="mx-auto h-3.5 w-3.5" />
                        <p className="mt-1 text-lg font-black">
                            {recommendation.total_servings}
                        </p>
                        <p className="text-[8px] font-bold uppercase tracking-[.12em] text-[#6d6257]">
                            Servings
                        </p>
                    </div>
                    <div className="rounded-xl bg-emerald-600/10 p-2 text-center">
                        <p className="text-lg font-black text-emerald-800">
                            {recommendation.veg_servings}
                        </p>
                        <p className="text-[8px] font-bold uppercase tracking-[.12em] text-emerald-700">
                            Veg
                        </p>
                    </div>
                    <div className="rounded-xl bg-[#f6a61d]/20 p-2 text-center">
                        <p className="text-lg font-black">
                            {recommendation.nonveg_servings}
                        </p>
                        <p className="text-[8px] font-bold uppercase tracking-[.12em] text-[#6d6257]">
                            Non-veg
                        </p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
