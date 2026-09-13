"use client";

import React, { useState } from "react";
import { TimeRange } from "@/types";
import { Calendar, ChevronDown, Check } from "lucide-react";

interface TimeRangePickerProps {
    value: TimeRange;
    onChange: (range: TimeRange, customStart?: string, customEnd?: string) => void;
    startDate?: string;
    endDate?: string;
    isLoading?: boolean;
}

const PRESET_RANGES: { key: TimeRange; label: string }[] = [
    { key: "12h", label: "12 Hours" },
    { key: "today", label: "Today" },
    { key: "7d", label: "7 Days" },
    { key: "30d", label: "30 Days" },
    { key: "90d", label: "90 Days" },
    { key: "all", label: "All Time" },
];

export function TimeRangePicker({
    value,
    onChange,
    startDate,
    endDate,
    isLoading = false
}: TimeRangePickerProps) {
    const [isCustomOpen, setIsCustomOpen] = useState(false);
    const [localStart, setLocalStart] = useState(startDate || "");
    const [localEnd, setLocalEnd] = useState(endDate || "");

    const handlePresetClick = (key: TimeRange) => {
        setIsCustomOpen(false);
        onChange(key);
    };

    const handleApplyCustom = (e: React.FormEvent) => {
        e.preventDefault();
        if (!localStart) return;
        setIsCustomOpen(false);
        onChange("custom", localStart, localEnd || localStart);
    };

    return (
        <div className="relative inline-flex items-center">
            <div className="flex flex-wrap items-center gap-1 rounded-full border border-white/10 bg-white/[.03] p-1 backdrop-blur-md">
                <div className="hidden sm:flex items-center pl-2.5 pr-1 text-zinc-500">
                    <Calendar className="h-3.5 w-3.5" />
                </div>

                {PRESET_RANGES.map(({ key, label }) => {
                    const isActive = value === key;
                    return (
                        <button
                            key={key}
                            onClick={() => handlePresetClick(key)}
                            disabled={isLoading}
                            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-all duration-200 ${
                                isActive
                                    ? "bg-[#f6a61d] text-zinc-950 font-bold shadow-md shadow-[#f6a61d]/20"
                                    : "text-zinc-400 hover:text-white hover:bg-white/[.05]"
                            } ${isLoading ? "opacity-60 cursor-not-allowed" : ""}`}
                        >
                            {label}
                        </button>
                    );
                })}

                {/* Custom Date Range Toggle */}
                <button
                    onClick={() => setIsCustomOpen(!isCustomOpen)}
                    disabled={isLoading}
                    className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold transition-all duration-200 ${
                        value === "custom"
                            ? "bg-[#f6a61d] text-zinc-950 font-bold shadow-md shadow-[#f6a61d]/20"
                            : "text-zinc-400 hover:text-white hover:bg-white/[.05]"
                    } ${isLoading ? "opacity-60 cursor-not-allowed" : ""}`}
                >
                    <span>{value === "custom" && localStart ? `${localStart.slice(5)} to ${localEnd ? localEnd.slice(5) : "now"}` : "Custom"}</span>
                    <ChevronDown className="h-3 w-3" />
                </button>
            </div>

            {/* Custom Date Range Popover */}
            {isCustomOpen && (
                <div className="absolute right-0 top-full mt-2 w-72 rounded-2xl border border-white/15 bg-[#121719]/95 p-4 shadow-2xl backdrop-blur-xl z-40">
                    <form onSubmit={handleApplyCustom} className="space-y-3">
                        <div className="flex items-center justify-between pb-2 border-b border-white/10">
                            <span className="text-xs font-bold text-white uppercase tracking-wider">
                                Custom Date Range
                            </span>
                        </div>

                        <div>
                            <label className="block text-[11px] font-medium text-zinc-400 mb-1">
                                Start Date
                            </label>
                            <input
                                type="date"
                                value={localStart}
                                onChange={(e) => setLocalStart(e.target.value)}
                                required
                                className="w-full rounded-lg border border-white/10 bg-white/[.04] px-3 py-1.5 text-xs text-white focus:border-[#f6a61d] focus:outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-[11px] font-medium text-zinc-400 mb-1">
                                End Date
                            </label>
                            <input
                                type="date"
                                value={localEnd}
                                onChange={(e) => setLocalEnd(e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-white/[.04] px-3 py-1.5 text-xs text-white focus:border-[#f6a61d] focus:outline-none"
                            />
                        </div>

                        <div className="flex items-center justify-end gap-2 pt-2">
                            <button
                                type="button"
                                onClick={() => setIsCustomOpen(false)}
                                className="rounded-lg px-2.5 py-1 text-xs text-zinc-400 hover:text-white"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="flex items-center gap-1 rounded-lg bg-[#f6a61d] px-3 py-1 text-xs font-bold text-zinc-950 hover:bg-[#e59816] transition-colors"
                            >
                                <Check className="h-3 w-3" />
                                Apply
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}
