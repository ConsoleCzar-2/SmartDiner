"use client";

import React, { useState } from "react";
import { DailyTrendPoint } from "@/types";
import { TrendingUp, IndianRupee, ShoppingBag, Calendar, ArrowUpRight } from "lucide-react";

interface AnalyticsChartProps {
    data: DailyTrendPoint[];
    currencySymbol?: string;
}

function createSmoothSpline(pts: { x: number; y: number }[]): string {
    if (pts.length === 0) return "";
    if (pts.length === 1) {
        return `M ${pts[0].x - 20},${pts[0].y} L ${pts[0].x + 20},${pts[0].y}`;
    }
    if (pts.length === 2) {
        return `M ${pts[0].x},${pts[0].y} L ${pts[1].x},${pts[1].y}`;
    }

    let path = `M ${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[Math.max(i - 1, 0)];
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const p3 = pts[Math.min(i + 2, pts.length - 1)];

        const cp1x = p1.x + (p2.x - p0.x) / 5;
        const cp1y = p1.y + (p2.y - p0.y) / 5;
        const cp2x = p2.x - (p3.x - p1.x) / 5;
        const cp2y = p2.y - (p3.y - p1.y) / 5;

        path += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
    }
    return path;
}

export function AnalyticsChart({ data, currencySymbol = "₹" }: AnalyticsChartProps) {
    const [viewMode, setViewMode] = useState<"revenue" | "orders">("revenue");
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

    if (!data || data.length === 0) {
        return (
            <div className="flex h-72 items-center justify-center rounded-2xl border border-white/10 bg-white/[.02] text-sm text-zinc-500">
                No trend data available for this timeframe.
            </div>
        );
    }

    // Safely extract numbers to avoid any NaN calculations
    const cleanData = data.map((d) => ({
        date: d.date || "",
        revenue: Number.isFinite(Number(d.revenue)) ? Number(d.revenue) : 0,
        orders: Number.isFinite(Number(d.orders ?? d.orders_count)) ? Number(d.orders ?? d.orders_count) : 0,
    }));

    const values = cleanData.map((d) => (viewMode === "revenue" ? d.revenue : d.orders));
    const maxValFound = Math.max(...values, 0);
    const maxValue = viewMode === "revenue" ? Math.max(maxValFound, 500) : Math.max(maxValFound, 4);
    const minValue = 0;
    const range = maxValue - minValue || 1;

    // SVG coordinates
    const chartHeight = 220;
    const chartWidth = 760;
    const paddingLeft = 55;
    const paddingRight = 30;
    const paddingTop = 25;
    const paddingBottom = 35;

    const availableWidth = chartWidth - paddingLeft - paddingRight;
    const availableHeight = chartHeight - paddingTop - paddingBottom;

    const points = cleanData.map((d, index) => {
        const x = cleanData.length === 1
            ? chartWidth / 2
            : paddingLeft + (index / (cleanData.length - 1)) * availableWidth;
        const val = viewMode === "revenue" ? d.revenue : d.orders;
        const normalized = Math.max(0, Math.min(1, (val - minValue) / range));
        const y = chartHeight - paddingBottom - normalized * availableHeight;
        return { x, y, date: d.date, revenue: d.revenue, orders: d.orders, val };
    });

    const pathD = createSmoothSpline(points);
    const areaD = points.length > 1
        ? `${pathD} L ${points[points.length - 1].x.toFixed(1)},${chartHeight - paddingBottom} L ${points[0].x.toFixed(1)},${chartHeight - paddingBottom} Z`
        : "";

    const totalMetric = values.reduce((sum, v) => sum + v, 0);
    const avgMetric = values.length > 0 ? Math.round((totalMetric / values.length) * 100) / 100 : 0;
    
    // Find peak item
    let peakIndex = 0;
    values.forEach((v, i) => {
        if (v > values[peakIndex]) peakIndex = i;
    });
    const peakMetric = values[peakIndex] || 0;
    const peakDate = cleanData[peakIndex]?.date || "";

    const strokeColor = viewMode === "revenue" ? "#f6a61d" : "#10b981";
    const gradientId = viewMode === "revenue" ? "revGradient" : "ordGradient";

    // Format grid labels
    const formatGridValue = (val: number) => {
        if (!Number.isFinite(val)) return "0";
        if (viewMode === "revenue") {
            if (val >= 100000) return `₹${(val / 1000).toFixed(0)}k`;
            if (val >= 1000) return `₹${(val / 1000).toFixed(1)}k`;
            return `₹${Math.round(val)}`;
        }
        return `${Math.round(val)}`;
    };

    // Determine label step to avoid crowded X-axis labels
    const labelStep = cleanData.length > 18 ? Math.ceil(cleanData.length / 8) : 1;

    return (
        <div className="rounded-2xl border border-white/10 bg-white/[.025] p-6 backdrop-blur-md">
            {/* Header: Title & View Mode Toggle */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-white/5">
                <div>
                    <div className="flex items-center gap-2">
                        <TrendingUp className={`h-4 w-4 ${viewMode === "revenue" ? "text-[#f6a61d]" : "text-emerald-400"}`} />
                        <h2 className="text-base font-bold text-white tracking-tight">
                            Performance Trends
                        </h2>
                    </div>
                    <p className="mt-1 text-xs text-zinc-400">
                        {viewMode === "revenue" ? "Monetary revenue generation over time" : "Order throughput volume over time"}
                    </p>
                </div>

                <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/[.04] p-1">
                    <button
                        onClick={() => setViewMode("revenue")}
                        className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition-all ${
                            viewMode === "revenue"
                                ? "bg-[#f6a61d] text-zinc-950 font-bold shadow-md shadow-[#f6a61d]/20"
                                : "text-zinc-400 hover:text-white"
                        }`}
                    >
                        <IndianRupee className="h-3 w-3" />
                        Revenue
                    </button>
                    <button
                        onClick={() => setViewMode("orders")}
                        className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition-all ${
                            viewMode === "orders"
                                ? "bg-emerald-400 text-zinc-950 font-bold shadow-md shadow-emerald-400/20"
                                : "text-zinc-400 hover:text-white"
                        }`}
                    >
                        <ShoppingBag className="h-3 w-3" />
                        Orders
                    </button>
                </div>
            </div>

            {/* Quick Summary Strip */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-4 border-b border-white/5">
                <div className="rounded-xl border border-white/5 bg-white/[.015] p-3.5">
                    <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider">
                        {viewMode === "revenue" ? "Total Revenue" : "Total Orders"}
                    </p>
                    <p className="mt-1 text-xl font-black text-white">
                        {viewMode === "revenue"
                            ? `${currencySymbol}${totalMetric.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                            : `${totalMetric.toLocaleString("en-IN")} ${totalMetric === 1 ? "order" : "orders"}`}
                    </p>
                </div>
                <div className="rounded-xl border border-white/5 bg-white/[.015] p-3.5">
                    <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider">
                        Period Average
                    </p>
                    <p className="mt-1 text-xl font-black text-zinc-200">
                        {viewMode === "revenue"
                            ? `${currencySymbol}${avgMetric.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                            : `${avgMetric.toLocaleString("en-IN")} / slot`}
                    </p>
                </div>
                <div className="rounded-xl border border-white/5 bg-white/[.015] p-3.5">
                    <div className="flex items-center justify-between">
                        <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider">
                            Peak Interval
                        </p>
                        {peakDate && (
                            <span className="text-[10px] text-zinc-500 font-mono">
                                {peakDate}
                            </span>
                        )}
                    </div>
                    <p className={`mt-1 text-xl font-black ${viewMode === "revenue" ? "text-[#f6a61d]" : "text-emerald-400"}`}>
                        {viewMode === "revenue"
                            ? `${currencySymbol}${peakMetric.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                            : `${peakMetric.toLocaleString("en-IN")} orders`}
                    </p>
                </div>
            </div>

            {/* Chart SVG */}
            <div className="relative mt-6 w-full">
                <svg
                    viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                    className="w-full h-64 overflow-visible"
                    preserveAspectRatio="none"
                >
                    <defs>
                        <linearGradient id="revGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#f6a61d" stopOpacity="0.32" />
                            <stop offset="60%" stopColor="#f6a61d" stopOpacity="0.08" />
                            <stop offset="100%" stopColor="#f6a61d" stopOpacity="0.0" />
                        </linearGradient>
                        <linearGradient id="ordGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#10b981" stopOpacity="0.32" />
                            <stop offset="60%" stopColor="#10b981" stopOpacity="0.08" />
                            <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                        </linearGradient>
                        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                            <feDropShadow dx="0" dy="3" stdDeviation="4" floodColor={strokeColor} floodOpacity="0.25" />
                        </filter>
                    </defs>

                    {/* Horizontal Reference Gridlines */}
                    {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                        const y = chartHeight - paddingBottom - ratio * availableHeight;
                        const val = minValue + ratio * range;
                        return (
                            <g key={ratio}>
                                <line
                                    x1={paddingLeft}
                                    y1={y}
                                    x2={chartWidth - paddingRight}
                                    y2={y}
                                    stroke="rgba(255, 255, 255, 0.05)"
                                    strokeDasharray="4 4"
                                />
                                <text
                                    x={paddingLeft - 8}
                                    y={y + 3.5}
                                    textAnchor="end"
                                    className="text-[10px] fill-zinc-500 font-mono"
                                >
                                    {formatGridValue(val)}
                                </text>
                            </g>
                        );
                    })}

                    {/* Gradient Area Fill */}
                    {areaD && <path d={areaD} fill={`url(#${gradientId})`} />}

                    {/* Smooth Spline Curve */}
                    <path
                        d={pathD}
                        fill="none"
                        stroke={strokeColor}
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        filter="url(#glow)"
                    />

                    {/* Hover Crosshair Guideline */}
                    {hoveredIndex !== null && points[hoveredIndex] && (
                        <line
                            x1={points[hoveredIndex].x}
                            y1={paddingTop}
                            x2={points[hoveredIndex].x}
                            y2={chartHeight - paddingBottom}
                            stroke={strokeColor}
                            strokeWidth="1.5"
                            strokeDasharray="3 3"
                            strokeOpacity="0.6"
                        />
                    )}

                    {/* Interactive Data Points */}
                    {points.map((p, idx) => {
                        const isHovered = hoveredIndex === idx;
                        const showLabel = idx % labelStep === 0 || idx === points.length - 1;

                        return (
                            <g key={idx}>
                                {/* Invisible larger target for easy hovering */}
                                <circle
                                    cx={p.x}
                                    cy={p.y}
                                    r={14}
                                    fill="transparent"
                                    className="cursor-pointer"
                                    onMouseEnter={() => setHoveredIndex(idx)}
                                    onMouseLeave={() => setHoveredIndex(null)}
                                />

                                {/* Outer halo on hover */}
                                {isHovered && (
                                    <circle
                                        cx={p.x}
                                        cy={p.y}
                                        r={8}
                                        fill={strokeColor}
                                        fillOpacity="0.25"
                                        className="animate-pulse"
                                    />
                                )}

                                {/* Inner point */}
                                <circle
                                    cx={p.x}
                                    cy={p.y}
                                    r={isHovered ? 5 : 3.5}
                                    fill={isHovered ? "#ffffff" : strokeColor}
                                    stroke="#0c1011"
                                    strokeWidth={isHovered ? 2.5 : 1.5}
                                    className="transition-all duration-150 pointer-events-none"
                                />

                                {/* X-axis Label */}
                                {showLabel && (
                                    <text
                                        x={p.x}
                                        y={chartHeight - 12}
                                        textAnchor="middle"
                                        className={`text-[10px] font-mono transition-colors ${
                                            isHovered ? "fill-white font-bold" : "fill-zinc-500"
                                        }`}
                                    >
                                        {p.date}
                                    </text>
                                )}
                            </g>
                        );
                    })}
                </svg>

                {/* Floating Glassmorphism Tooltip */}
                {hoveredIndex !== null && points[hoveredIndex] && (
                    <div
                        className="pointer-events-none absolute -top-4 rounded-xl border border-white/20 bg-[#121719]/95 px-3.5 py-2.5 shadow-2xl backdrop-blur-lg transition-all z-30"
                        style={{
                            left: `${Math.min(92, Math.max(8, (points[hoveredIndex].x / chartWidth) * 100))}%`,
                            transform: "translate(-50%, -100%)",
                        }}
                    >
                        <div className="flex items-center gap-1.5 text-[11px] text-zinc-400 font-mono">
                            <Calendar className="h-3 w-3 text-zinc-500" />
                            <span>{points[hoveredIndex].date}</span>
                        </div>
                        <div className="mt-1 flex items-baseline gap-2">
                            <span className="text-sm font-black text-white">
                                {currencySymbol}{points[hoveredIndex].revenue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </span>
                            <span className="inline-block rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-semibold text-zinc-300">
                                {points[hoveredIndex].orders} {points[hoveredIndex].orders === 1 ? "order" : "orders"}
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
