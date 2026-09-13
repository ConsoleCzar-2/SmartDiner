"use client";

import React from "react";
import { TopDishItem } from "@/types";
import { Award } from "lucide-react";

interface TopDishesTableProps {
    items: TopDishItem[];
    currencySymbol?: string;
}

export function TopDishesTable({ items, currencySymbol = "₹" }: TopDishesTableProps) {
    if (!items || items.length === 0) {
        return (
            <div className="flex h-48 items-center justify-center rounded-2xl border border-white/10 bg-white/[.02] text-sm text-zinc-500">
                No dish volume recorded for this time range.
            </div>
        );
    }

    return (
        <div className="rounded-2xl border border-white/10 bg-white/[.025] p-6 backdrop-blur-md">
            <div className="flex items-center justify-between pb-4 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <Award className="h-4 w-4 text-[#f6a61d]" />
                    <h2 className="text-base font-bold text-white tracking-tight">
                        Top Dishes Leaderboard
                    </h2>
                </div>
                <span className="text-xs text-zinc-500 font-mono">
                    {items.length} items ranked
                </span>
            </div>

            <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-xs">
                    <thead>
                        <tr className="border-b border-white/5 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                            <th className="pb-3 pl-2">#</th>
                            <th className="pb-3">Dish Name</th>
                            <th className="pb-3">Category</th>
                            <th className="pb-3 text-right">Qty Sold</th>
                            <th className="pb-3 text-right pr-2">Revenue</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {items.map((dish, idx) => (
                                <tr
                                    key={`${dish.name}-${idx}`}
                                    className="group hover:bg-white/[.02] transition-colors"
                                >
                                    <td className="py-3 pl-2 font-mono font-bold">
                                        <span
                                            className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] ${
                                                idx === 0
                                                    ? "bg-[#f6a61d] text-zinc-950 font-black"
                                                    : idx === 1
                                                    ? "bg-zinc-300 text-zinc-950"
                                                    : idx === 2
                                                    ? "bg-amber-700/80 text-white"
                                                    : "text-zinc-500"
                                            }`}
                                        >
                                            {idx + 1}
                                        </span>
                                    </td>
                                    <td className="py-3">
                                        <div className="font-medium text-white group-hover:text-[#f6a61d] transition-colors">
                                            {dish.name}
                                        </div>
                                        {dish.restaurant_name && (
                                            <div className="text-[10px] text-zinc-500 font-normal mt-0.5">
                                                {dish.restaurant_name}
                                            </div>
                                        )}
                                    </td>
                                    <td className="py-3">
                                        <span className="inline-block rounded-md border border-white/10 bg-white/[.04] px-2 py-0.5 text-[10px] text-zinc-400">
                                            {dish.category || "General"}
                                        </span>
                                    </td>
                                    <td className="py-3 text-right font-mono text-zinc-300">
                                        {dish.quantity_sold}
                                    </td>
                                    <td className="py-3 text-right font-mono font-bold text-white pr-2">
                                        {currencySymbol}{dish.revenue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                                    </td>
                                </tr>
                            ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
