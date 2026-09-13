"use client";

import React from "react";
import { SolverHealthMetrics } from "@/types";
import { Cpu, ShieldCheck, AlertTriangle, ShieldAlert } from "lucide-react";

interface SolverHealthCardProps {
    health: SolverHealthMetrics;
    allergenFrequency?: Record<string, number>;
}

export function SolverHealthCard({ health, allergenFrequency = {} }: SolverHealthCardProps) {
    const feasibilityRate = health?.feasibility_rate_pct ?? 100;
    const optimalCount = health?.optimal_count ?? 0;
    const infeasibleCount = health?.infeasible_count ?? 0;
    const avgSolveTime = health?.avg_solve_time_ms ?? 0;

    const allergenEntries = Object.entries(allergenFrequency).sort((a, b) => b[1] - a[1]);

    return (
        <div className="rounded-2xl border border-white/10 bg-white/[.025] p-6 backdrop-blur-md">
            <div className="flex items-center justify-between pb-4 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-[#f6a61d]" />
                    <h2 className="text-base font-bold text-white tracking-tight">
                        Solver Adherence & Safety
                    </h2>
                </div>
                <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                        feasibilityRate >= 95
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : feasibilityRate >= 80
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    }`}
                >
                    {feasibilityRate >= 95 ? (
                        <ShieldCheck className="h-3 w-3" />
                    ) : (
                        <AlertTriangle className="h-3 w-3" />
                    )}
                    {feasibilityRate}% Feasible
                </span>
            </div>

            {/* Feasibility Progress Bar */}
            <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-zinc-400">
                    <span>Optimization Feasibility Rate</span>
                    <span className="font-mono font-bold text-white">{feasibilityRate}%</span>
                </div>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/10">
                    <div
                        className="h-full rounded-full bg-gradient-to-r from-[#f6a61d] to-emerald-400 transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(0, feasibilityRate))}%` }}
                    />
                </div>
            </div>

            {/* Solver Telemetry Stats */}
            <div className="mt-5 grid grid-cols-3 gap-3 border-t border-white/5 pt-4 text-center">
                <div className="rounded-xl border border-white/5 bg-white/[.02] p-2.5">
                    <p className="text-[10px] uppercase tracking-wider text-zinc-500">Optimal</p>
                    <p className="mt-1 font-mono text-base font-bold text-emerald-400">
                        {optimalCount}
                    </p>
                </div>
                <div className="rounded-xl border border-white/5 bg-white/[.02] p-2.5">
                    <p className="text-[10px] uppercase tracking-wider text-zinc-500">Infeasible</p>
                    <p className="mt-1 font-mono text-base font-bold text-rose-400">
                        {infeasibleCount}
                    </p>
                </div>
                <div className="rounded-xl border border-white/5 bg-white/[.02] p-2.5">
                    <p className="text-[10px] uppercase tracking-wider text-zinc-500">Avg Solve</p>
                    <p className="mt-1 font-mono text-base font-bold text-zinc-200">
                        {avgSolveTime}ms
                    </p>
                </div>
            </div>

            {/* Top Allergens Excluded Section */}
            <div className="mt-5 border-t border-white/5 pt-4">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-zinc-300">
                    <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                    <span>Customer Allergen Exclusions</span>
                </div>
                {allergenEntries.length > 0 ? (
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                        {allergenEntries.slice(0, 6).map(([allergen, count]) => (
                            <span
                                key={allergen}
                                className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[.03] px-2.5 py-1 text-xs text-zinc-300"
                            >
                                <span className="font-medium">{allergen}</span>
                                <span className="rounded-full bg-white/10 px-1.5 py-0.2 text-[10px] font-mono text-amber-300">
                                    {count}
                                </span>
                            </span>
                        ))}
                    </div>
                ) : (
                    <p className="mt-2 text-xs text-zinc-500">
                        No allergen exclusion patterns registered in current period.
                    </p>
                )}
            </div>
        </div>
    );
}
