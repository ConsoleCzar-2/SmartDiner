"use client";
import {
    CheckCircle2,
    CircleAlert,
    Leaf,
    ReceiptText,
    Users,
    Beef,
    Drumstick,
    Sprout,
    Flame,
} from "lucide-react";
import { motion } from "framer-motion";
import type { RecommendationResult } from "@/types";
const money = (value: number) =>
    new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
    }).format(value);

const SpiceIndicator = ({ level }: { level: string }) => {
    if (!level || level === "Any") return null;

    if (level === "None") {
        return (
            <span className="inline-flex items-center gap-0.5 text-[#6d6257]" title="No spice">
                <Flame className="h-3 w-3 opacity-40" />
                <span>None spice</span>
            </span>
        );
    }
    
    let count = 1;
    let color = "text-yellow-600";
    if (level === "Medium") { count = 2; color = "text-orange-500"; }
    else if (level === "High") { count = 3; color = "text-red-500"; }
    else if (level === "Extreme") { count = 4; color = "text-red-700"; }

    return (
        <span className="inline-flex items-center gap-0.5" title={`${level} spice`}>
            <span className={`inline-flex ${color}`}>
                {Array.from({ length: count }).map((_, i) => (
                    <Flame key={i} className="h-3 w-3" />
                ))}
            </span>
            <span className="ml-0.5 text-[#6d6257]">{level} spice</span>
        </span>
    );
};
import { useState, useEffect } from "react";
import { patchCart } from "@/lib/api";
import { toast } from "sonner";
import { Plus, Minus } from "lucide-react";

export function CartPanel({
    recommendation,
    constraints,
    conversationId,
}: {
    recommendation: RecommendationResult | null;
    constraints?: any | null;
    conversationId?: string | null;
}) {
    const [localRec, setLocalRec] = useState<RecommendationResult | null>(null);

    useEffect(() => {
        setLocalRec(recommendation);
    }, [recommendation]);

    if (!localRec)
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
        
    const optimal = localRec.status.toLowerCase() === "optimal";

    const updateQuantity = async (itemId: string, newQuantity: number) => {
        if (!conversationId) return;
        
        // Optimistic update
        setLocalRec((current) => {
            if (!current) return current;
            const updatedItems = current.items.map(item => {
                if (item.id === itemId) {
                    const diff = newQuantity - item.quantity;
                    return { 
                        ...item, 
                        quantity: newQuantity,
                        subtotal: (item.unit_price) * newQuantity
                    };
                }
                return item;
            }).filter(item => item.quantity > 0);
            
            const newTotal = updatedItems.reduce((acc, item) => acc + item.subtotal, 0);
            
            return {
                ...current,
                items: updatedItems,
                computed_total: newTotal,
                budget_remaining: constraints?.max_budget ? constraints.max_budget - newTotal : null,
            };
        });

        try {
            await patchCart(conversationId, [{ id: itemId, quantity: newQuantity }]);
            toast.success("Cart updated");
            window.dispatchEvent(new Event('cartUpdated'));
        } catch(e: any) {
            toast.error("Failed to update cart");
            // Revert state on failure by relying on the next recommendation or fetching it (simplified here)
        }
    };

    return (
        <aside className="sticky top-24 flex max-h-[calc(100vh-6rem)] flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#f7f4ed] text-[#241f19] shadow-2xl">
            <div className="shrink-0 border-b border-[#241f19]/10 bg-[#f6a61d] px-5 py-4">
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
            
            <div className="flex-1 overflow-y-auto p-5">
                {localRec.reason && !optimal && (
                    <p className="mb-4 rounded-xl bg-red-500/10 p-3 text-xs text-red-700">
                        {localRec.reason}
                    </p>
                )}
                <div className="space-y-3">
                    {localRec.items.map((item) => (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex gap-3 border-b border-[#241f19]/8 pb-3"
                        >
                            {item.image_url ? (
                                <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg">
                                    <img src={item.image_url} alt={item.name} className="h-full w-full object-cover" />
                                </div>
                            ) : null}
                            
                            <div className="flex flex-1 justify-between">
                                <div>
                                    <p className="text-sm font-bold">{item.name}</p>
                                    <div className="mt-1 flex items-center gap-1.5 text-[10px] text-[#6d6257]">
                                        <span>{item.category}</span>
                                        <span>·</span>
                                        <SpiceIndicator level={item.spice_level} />
                                        <span>·</span>
                                        <span>{item.total_servings} servings</span>
                                    </div>
                                    {item.dietary_preference === 'Vegetarian' && (
                                        <span className="mt-1 flex w-fit items-center gap-1 text-[10px] font-semibold text-emerald-700">
                                            <Leaf className="h-3 w-3" /> Vegetarian
                                        </span>
                                    )}
                                    {item.dietary_preference === 'Vegan' && (
                                        <span className="mt-1 flex w-fit items-center gap-1 text-[10px] font-semibold text-green-700">
                                            <Sprout className="h-3 w-3" /> Vegan
                                        </span>
                                    )}
                                    {item.dietary_preference === 'Non-Vegetarian' && (
                                        <span className="mt-1 flex w-fit items-center gap-1 text-[10px] font-semibold text-red-600">
                                            <Drumstick className="h-3 w-3" /> Non-Vegetarian
                                        </span>
                                    )}
                                </div>
                                
                                <div className="flex flex-col items-end justify-between">
                                    <p className="text-sm font-black tabular-nums">
                                        {money(item.subtotal)}
                                    </p>
                                    <div className="flex items-center gap-3 mt-2 bg-[#241f19]/5 rounded-full px-2 py-1">
                                        <button 
                                            onClick={() => updateQuantity(item.id, item.quantity - 1)}
                                            className="hover:text-[#f6a61d]"
                                        >
                                            <Minus className="h-3 w-3" />
                                        </button>
                                        <span className="text-xs font-black">{item.quantity}</span>
                                        <button 
                                            onClick={() => updateQuantity(item.id, item.quantity + 1)}
                                            className="hover:text-[#f6a61d]"
                                        >
                                            <Plus className="h-3 w-3" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
            
            <div className="shrink-0 bg-[#f7f4ed] p-5 pt-0">
                <div className="space-y-2 border-t border-dashed border-[#241f19]/20 pt-4 text-sm">
                    <div className="flex justify-between">
                        <span className="text-[#6d6257]">Computed total</span>
                        <span className="font-black">
                            {money(localRec.computed_total)}
                        </span>
                    </div>
                    {constraints?.max_budget && (
                        <div className="flex justify-between">
                            <span className="text-[#6d6257]">Total budget</span>
                            <span className="font-bold text-zinc-500">
                                {money(constraints.max_budget)}
                            </span>
                        </div>
                    )}
                    <div className="flex justify-between border-t border-dashed border-[#241f19]/20 pt-2">
                        <span className="text-[#6d6257]">Budget remaining</span>
                        <span className={`font-black ${localRec.budget_remaining && localRec.budget_remaining < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                            {localRec.budget_remaining === null
                                ? "—"
                                : (localRec.budget_remaining < 0 ? "-" + money(Math.abs(localRec.budget_remaining)) : money(localRec.budget_remaining))}
                        </span>
                    </div>
                </div>
                <div className="mt-4 grid grid-cols-4 gap-2">
                    <div className="rounded-xl bg-[#241f19]/5 p-2 text-center">
                        <Users className="mx-auto h-3.5 w-3.5" />
                        <p className="mt-1 text-lg font-black">
                            {constraints?.people_count || 1}
                        </p>
                        <p className="text-[8px] font-bold uppercase tracking-[.12em] text-[#6d6257]">
                            People
                        </p>
                    </div>
                    <div className="rounded-xl bg-emerald-600/10 p-2 text-center">
                        <p className="text-lg font-black text-emerald-800">
                            {constraints?.vegetarian_count || 0}
                        </p>
                        <p className="text-[8px] font-bold uppercase tracking-[.12em] text-emerald-700">
                            Veg
                        </p>
                    </div>
                    <div className="rounded-xl bg-green-600/10 p-2 text-center">
                        <p className="text-lg font-black text-green-800">
                            {constraints?.vegan_count || 0}
                        </p>
                        <p className="text-[8px] font-bold uppercase tracking-[.12em] text-green-700">
                            Vegan
                        </p>
                    </div>
                    <div className="rounded-xl bg-rose-600/10 p-2 text-center">
                        <p className="text-lg font-black text-rose-800">
                            {constraints?.non_vegetarian_count || 0}
                        </p>
                        <p className="text-[8px] font-bold uppercase tracking-[.12em] text-rose-700">
                            Non-veg
                        </p>
                    </div>
                </div>
                {conversationId && (
                    <div className="mt-4">
                        <button
                            onClick={async () => {
                                try {
                                    const { checkoutOrder } = await import('@/lib/api');
                                    await checkoutOrder(conversationId);
                                    window.location.href = '/orders';
                                } catch(e: any) {
                                    toast.error(e.message);
                                }
                            }}
                            className="w-full rounded-xl bg-[#241f19] py-3.5 text-sm font-bold text-white transition hover:bg-[#241f19]/80"
                        >
                            Place Order
                        </button>
                    </div>
                )}
            </div>
        </aside>
    );
}
