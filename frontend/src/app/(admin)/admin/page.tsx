"use client";

import { useEffect, useState, useCallback } from "react";
import { 
    Activity, 
    BadgeIndianRupee, 
    ShieldCheck, 
    ArrowUpRight, 
    ArrowDownRight, 
    Clock, 
    RefreshCw, 
    ShoppingBag
} from "lucide-react";
import { fetchAdminAnalytics } from "@/lib/api";
import { TimeRange, AdminAnalyticsResponse } from "@/types";
import { TimeRangePicker } from "@/components/admin/time-range-picker";
import { AnalyticsChart } from "@/components/admin/analytics-chart";
import { TopDishesTable } from "@/components/admin/top-dishes-table";
import { SolverHealthCard } from "@/components/admin/solver-health-card";

export default function AdminPage() {
    const [timeRange, setTimeRange] = useState<TimeRange>("30d");
    const [startDate, setStartDate] = useState<string>("");
    const [endDate, setEndDate] = useState<string>("");
    const [analytics, setAnalytics] = useState<AdminAnalyticsResponse | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    const loadData = useCallback(async (range: TimeRange, customStart?: string, customEnd?: string) => {
        const token = localStorage.getItem("adminToken");
        if (!token) {
            setIsLoading(false);
            return;
        }
        setIsLoading(true);
        try {
            const data = await fetchAdminAnalytics(token, range, customStart, customEnd);
            setAnalytics(data);
        } catch (err) {
            console.error("Failed to load admin analytics:", err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData(timeRange, startDate, endDate);
    }, [timeRange, startDate, endDate, loadData]);

    const handleRangeChange = (range: TimeRange, customStart?: string, customEnd?: string) => {
        setTimeRange(range);
        if (customStart !== undefined) setStartDate(customStart);
        if (customEnd !== undefined) setEndDate(customEnd);
        loadData(range, customStart, customEnd);
    };

    const handleRefresh = () => {
        loadData(timeRange, startDate, endDate);
    };

    const formatGrowth = (pct?: number | null) => {
        if (pct == null) return null;
        const isPositive = pct >= 0;
        return (
            <span
                className={`inline-flex items-center gap-0.5 text-xs font-semibold ${
                    isPositive ? "text-emerald-400" : "text-rose-400"
                }`}
            >
                {isPositive ? (
                    <ArrowUpRight className="h-3 w-3" />
                ) : (
                    <ArrowDownRight className="h-3 w-3" />
                )}
                {Math.abs(pct)}%
                <span className="text-[10px] text-zinc-500 font-normal ml-0.5">vs prev period</span>
            </span>
        );
    };

    const metrics = analytics?.metrics;

    return (
        <main className="min-h-screen bg-[#0c1011] text-zinc-100 pb-16">
            <div className="mx-auto max-w-7xl px-5 py-10 lg:px-8">
                {/* Header with Title and Interactive Time-Range Controls */}
                <div className="flex flex-wrap items-end justify-between gap-6 pb-8 border-b border-white/5">
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="inline-block h-2 w-2 rounded-full bg-[#f6a61d] animate-pulse" />
                            <p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#f6a61d]">
                                SmartDiner Executive Operations
                            </p>
                        </div>
                        <h1 className="mt-2 text-3xl font-black tracking-[-.05em] text-white sm:text-4xl">
                            The proof is in the pass.
                        </h1>
                        <p className="mt-2 max-w-xl text-sm leading-6 text-zinc-400">
                            Real-time intelligence on meal combination adherence, budget accuracy,
                            solver feasibility, and transaction volume across the dining floor.
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                        <TimeRangePicker
                            value={timeRange}
                            onChange={handleRangeChange}
                            startDate={startDate}
                            endDate={endDate}
                            isLoading={isLoading}
                        />
                        <button
                            onClick={handleRefresh}
                            disabled={isLoading}
                            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/[.03] text-zinc-400 hover:text-white hover:bg-white/[.07] transition-all"
                            title="Refresh data"
                        >
                            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin text-[#f6a61d]" : ""}`} />
                        </button>
                    </div>
                </div>

                {/* KPI Overview Metric Cards */}
                <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {/* Total Revenue */}
                    <div className="rounded-2xl border border-white/10 bg-white/[.025] p-5 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-zinc-400">Total Revenue</p>
                            <BadgeIndianRupee className="h-4 w-4 text-[#f6a61d]" />
                        </div>
                        <p className="mt-4 text-3xl font-black tracking-tight text-white">
                            ₹{(metrics?.total_revenue ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </p>
                        <div className="mt-3 flex items-center justify-between">
                            {formatGrowth(metrics?.revenue_growth_pct)}
                        </div>
                    </div>

                    {/* Total Orders */}
                    <div className="rounded-2xl border border-white/10 bg-white/[.025] p-5 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-zinc-400">Total Orders</p>
                            <Activity className="h-4 w-4 text-[#f6a61d]" />
                        </div>
                        <p className="mt-4 text-3xl font-black tracking-tight text-white">
                            {metrics?.total_orders ?? 0}
                        </p>
                        <div className="mt-3 flex items-center justify-between">
                            {formatGrowth(metrics?.orders_growth_pct)}
                        </div>
                    </div>

                    {/* Average Order Value */}
                    <div className="rounded-2xl border border-white/10 bg-white/[.025] p-5 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-zinc-400">Avg Order Value</p>
                            <ShoppingBag className="h-4 w-4 text-[#f6a61d]" />
                        </div>
                        <p className="mt-4 text-3xl font-black tracking-tight text-white">
                            ₹{(metrics?.avg_order_value ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </p>
                        <div className="mt-3">
                            <span className="text-[11px] text-zinc-500">Per completed order</span>
                        </div>
                    </div>

                    {/* Governed Conversations */}
                    <div className="rounded-2xl border border-white/10 bg-white/[.025] p-5 backdrop-blur-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-zinc-400">Active Conversations</p>
                            <ShieldCheck className="h-4 w-4 text-[#f6a61d]" />
                        </div>
                        <p className="mt-4 text-3xl font-black tracking-tight text-white">
                            {metrics?.total_conversations ?? 0}
                        </p>
                        <div className="mt-3 flex items-center justify-between">
                            {formatGrowth(metrics?.conversations_growth_pct)}
                        </div>
                    </div>
                </div>

                {/* Performance Trends Chart */}
                <div className="mt-6">
                    <AnalyticsChart data={analytics?.daily_trends ?? []} />
                </div>

                {/* Two-Column Grid: Top Dishes & Solver Health */}
                <div className="mt-6 grid gap-6 lg:grid-cols-2">
                    <TopDishesTable items={analytics?.top_dishes ?? []} />
                    <SolverHealthCard
                        health={analytics?.solver_health ?? {
                            total_solves: 0,
                            optimal_count: 0,
                            infeasible_count: 0,
                            feasibility_rate_pct: 100,
                            avg_solve_time_ms: 0
                        }}
                        allergenFrequency={analytics?.allergen_frequency ?? {}}
                    />
                </div>

                {/* Recent Orders Activity Feed */}
                {analytics?.recent_orders && analytics.recent_orders.length > 0 && (
                    <div className="mt-6 rounded-2xl border border-white/10 bg-white/[.025] p-6 backdrop-blur-md">
                        <div className="flex items-center justify-between pb-4 border-b border-white/5">
                            <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 text-[#f6a61d]" />
                                <h2 className="text-base font-bold text-white tracking-tight">
                                    Recent Floor Transactions
                                </h2>
                            </div>
                            <span className="text-xs text-zinc-500 font-mono">
                                Latest {analytics.recent_orders.length} orders
                            </span>
                        </div>
                        <div className="mt-4 overflow-x-auto">
                            <table className="w-full text-left text-xs">
                                <thead>
                                    <tr className="border-b border-white/5 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                                        <th className="pb-3 pl-2 w-32">Order Ref</th>
                                        <th className="pb-3">Venue</th>
                                        <th className="pb-3 w-32">Items</th>
                                        <th className="pb-3 w-40">Time</th>
                                        <th className="pb-3 w-28 text-center">Status</th>
                                        <th className="pb-3 text-right pr-2 w-36">Total Value</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {analytics.recent_orders.map((order) => (
                                        <tr
                                            key={order.id}
                                            className="group hover:bg-white/[.02] transition-colors"
                                        >
                                            <td className="py-3.5 pl-2 font-mono">
                                                <span 
                                                    className="inline-block rounded bg-white/[.04] px-2 py-0.5 text-[11px] text-zinc-300 border border-white/5 font-mono"
                                                    title={order.id}
                                                >
                                                    #...{order.id.slice(-6)}
                                                </span>
                                            </td>
                                            <td className="py-3.5 font-medium text-white group-hover:text-[#f6a61d] transition-colors">
                                                {order.restaurant_name || "SmartDiner Kitchen"}
                                            </td>
                                            <td className="py-3.5 text-zinc-400 font-mono">
                                                {order.items_count} {order.items_count === 1 ? "item" : "items"}
                                            </td>
                                            <td className="py-3.5 text-zinc-400 font-mono text-[11px]">
                                                {order.created_at ? new Date(order.created_at).toLocaleDateString("en-IN", {
                                                    month: "short",
                                                    day: "numeric",
                                                    hour: "2-digit",
                                                    minute: "2-digit"
                                                }) : "-"}
                                            </td>
                                            <td className="py-3.5 text-center">
                                                <span className="inline-block rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-[10px] font-bold text-emerald-400 capitalize">
                                                    {order.status}
                                                </span>
                                            </td>
                                            <td className="py-3.5 text-right font-mono font-bold text-white text-sm pr-2">
                                                ₹{order.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
