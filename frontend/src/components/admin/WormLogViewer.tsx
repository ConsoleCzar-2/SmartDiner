import React, { useState } from 'react';
import { Database, Cpu, Sparkles, MessageSquare, Terminal, Layers, ShieldCheck, Clock, Coins, Copy, Check, Zap, Filter, CheckCircle2, XCircle, Key, Info } from 'lucide-react';

function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async (e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    };

    return (
        <button
            onClick={handleCopy}
            type="button"
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-md border transition shadow-sm backdrop-blur-md ${
                copied
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : "bg-zinc-800/90 hover:bg-zinc-700/90 text-zinc-300 hover:text-white border-zinc-600/50"
            }`}
            title="Copy to clipboard"
        >
            {copied ? (
                <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-emerald-400 font-semibold">Copied!</span>
                </>
            ) : (
                <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>{label}</span>
                </>
            )}
        </button>
    );
}

export default function WormLogViewer({ log, viewMode }: { log: any; viewMode: 'ui' | 'json' }) {
    if (viewMode === 'json') {
        const jsonString = JSON.stringify(log, null, 2);
        return (
            <div className="relative mb-6 group">
                <div className="absolute top-3 right-3 z-10">
                    <CopyButton text={jsonString} label="Copy JSON" />
                </div>
                <pre className="overflow-x-auto text-xs text-emerald-400 bg-black/60 p-6 pt-12 rounded-xl border border-white/10 font-mono leading-relaxed shadow-inner">
                    {jsonString}
                </pre>
            </div>
        );
    }

    const telemetry = log.pipeline_telemetry || {};
    const intent = log.intent || telemetry.intent;
    const sqlQueries = telemetry.sql_queries || [];
    const llmCalls = telemetry.llm_calls || [];
    const solverRationale = log.solver_output?.decision_rationale || telemetry.solver_decision;
    const cacheHits = telemetry.cache_hits || log.cache_hits || [];

    // Safe extraction helpers supporting multiple formats (direct vs token_usage object)
    const getPromptTokens = (call: any): number => 
        Number(call.prompt_tokens ?? call.token_usage?.prompt_tokens ?? 0);

    const getCompletionTokens = (call: any): number => 
        Number(call.completion_tokens ?? call.token_usage?.completion_tokens ?? 0);

    const getTotalTokens = (call: any): number => {
        const direct = call.total_tokens ?? call.token_usage?.total_tokens;
        if (direct !== undefined && direct !== null) return Number(direct);
        return getPromptTokens(call) + getCompletionTokens(call);
    };

    const getLatencyMs = (call: any): number => {
        const val = call.latency_ms ?? call.duration_ms ?? call.time_ms ?? 0;
        return typeof val === 'number' ? val : parseFloat(val) || 0;
    };

    // Calculate total token and latency consumption for this turn
    const totalPromptTokens = llmCalls.reduce((acc: number, call: any) => acc + getPromptTokens(call), 0);
    const totalCompletionTokens = llmCalls.reduce((acc: number, call: any) => acc + getCompletionTokens(call), 0);
    const grandTotalTokens = llmCalls.reduce((acc: number, call: any) => acc + getTotalTokens(call), 0);
    const totalLatencyMs = llmCalls.reduce((acc: number, call: any) => acc + getLatencyMs(call), 0);

    return (
        <div className="space-y-6 mb-12 border-b border-white/10 pb-12 last:border-0">
            {/* Header Snapshot Meta */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-black/40 border border-white/10 rounded-xl p-4">
                <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#f6a61d]/10 text-[#f6a61d] border border-[#f6a61d]/20">
                        <ShieldCheck className="h-4 w-4" />
                    </span>
                    <div>
                        <div className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">Snapshot Timestamp</div>
                        <div className="text-sm font-semibold text-white">{new Date(log.timestamp).toLocaleString()}</div>
                    </div>
                </div>
                <div className="flex items-center gap-3 text-xs">
                    <div className="bg-zinc-800/80 px-3 py-1.5 rounded-lg border border-zinc-700">
                        <span className="text-zinc-500">Conversation:</span> <span className="font-mono text-zinc-300">{log.conversation_id?.slice(0, 8)}...</span>
                    </div>
                    {log.restaurant_id && (
                        <div className="bg-zinc-800/80 px-3 py-1.5 rounded-lg border border-zinc-700">
                            <span className="text-zinc-500">Venue:</span> <span className="font-mono text-zinc-300">{log.restaurant_id?.slice(0, 8)}...</span>
                        </div>
                    )}
                </div>
            </div>

            {/* User Input & Intent Classification */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                <div className="lg:col-span-2 bg-black/30 border border-white/10 rounded-xl p-5">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
                        <MessageSquare className="h-3.5 w-3.5 text-[#f6a61d]" /> User Input Prompt
                    </h3>
                    <p className="text-sm font-medium text-zinc-200 bg-white/5 rounded-lg p-3.5 border border-white/5">
                        &ldquo;{log.user_message || 'N/A'}&rdquo;
                    </p>
                </div>

                {intent && (
                    <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
                            <Sparkles className="h-3.5 w-3.5 text-blue-400" /> Pipeline Intent
                        </h3>
                        <div className="space-y-2 text-xs">
                            <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg">
                                <span className="text-zinc-500">Classified:</span>
                                <span className="font-bold text-blue-400 uppercase tracking-wide">{intent.intent}</span>
                            </div>
                            <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg">
                                <span className="text-zinc-500">Confidence:</span>
                                <span className="font-semibold text-emerald-400">{Math.round((intent.confidence || 1) * 100)}%</span>
                            </div>
                            {intent.reason && (
                                <p className="text-[11px] text-zinc-400 mt-1 italic">
                                    &ldquo;{intent.reason}&rdquo;
                                </p>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Constraints & Solver Output */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Extracted Constraints */}
                <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                    <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-500"></span> Extracted Constraints
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                        <div><span className="text-zinc-500">Budget:</span> <span className="font-semibold text-white">₹{log.extracted_constraints?.max_budget ?? 'N/A'}</span></div>
                        <div><span className="text-zinc-500">People:</span> <span className="font-semibold text-white">{log.extracted_constraints?.people_count ?? 1}</span></div>
                        <div><span className="text-zinc-500">Veg:</span> <span className="font-semibold text-emerald-400">{log.extracted_constraints?.vegetarian_count ?? 0}</span></div>
                        <div><span className="text-zinc-500">Vegan:</span> <span className="font-semibold text-green-300">{log.extracted_constraints?.vegan_count ?? 0}</span></div>
                        <div><span className="text-zinc-500">Non-Veg:</span> <span className="font-semibold text-red-400">{log.extracted_constraints?.non_vegetarian_count ?? 0}</span></div>
                        <div><span className="text-zinc-500">Spice:</span> <span className="font-semibold text-orange-400">{log.extracted_constraints?.max_spice_level ?? 'Any'}</span></div>
                    </div>
                    {(log.extracted_constraints?.preferred_categories?.length > 0 || log.extracted_constraints?.preferred_cuisines?.length > 0) && (
                        <div className="mt-4 pt-4 border-t border-white/5 text-xs">
                            <div className="text-zinc-500 mb-1">Preferences:</div>
                            <div className="text-zinc-300 flex flex-wrap gap-1.5 mt-1">
                                {log.extracted_constraints?.preferred_cuisines?.map((c: string) => (
                                    <span key={c} className="rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 text-[11px] font-medium">{c}</span>
                                ))}
                                {log.extracted_constraints?.preferred_categories?.map((cat: string) => (
                                    <span key={cat} className="rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 text-[11px] font-medium">{cat}</span>
                                ))}
                            </div>
                        </div>
                    )}
                    {log.extracted_constraints?.excluded_allergens?.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/5 text-xs">
                            <div className="text-zinc-500 mb-1">Excluded Allergens:</div>
                            <div className="flex flex-wrap gap-1.5 mt-1">
                                {log.extracted_constraints.excluded_allergens.map((alg: string) => (
                                    <span key={alg} className="rounded bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 text-[11px] font-medium">
                                        ✕ {alg}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                    {log.extracted_constraints?.specific_dish_requests?.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/5 text-xs">
                            <div className="text-zinc-500 mb-1">Requested Dishes:</div>
                            <div className="text-amber-400 font-medium">
                                {log.extracted_constraints.specific_dish_requests.join(", ")}
                            </div>
                        </div>
                    )}
                </div>

                {/* Solver Output */}
                <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                    <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-500"></span> Solver Output
                    </h3>
                    <div className="space-y-4 text-xs">
                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-lg">
                            <span className="text-zinc-400">Status</span>
                            <span className={`font-bold uppercase tracking-wider px-2.5 py-1 rounded ${log.solver_output?.status === 'Optimal' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                                {log.solver_output?.status}
                            </span>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/5 p-3 rounded-lg">
                                <div className="text-zinc-500 mb-1">Computed Cost</div>
                                <div className="font-bold text-white text-base">₹{log.solver_output?.total_cost ?? 0}</div>
                            </div>
                            <div className="bg-white/5 p-3 rounded-lg">
                                <div className="text-zinc-500 mb-1">Total Servings</div>
                                <div className="font-bold text-white text-base">{log.solver_output?.total_servings ?? 0}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Decision Rationale (Math Bounds & Clean Formatting) */}
            {solverRationale && Object.keys(solverRationale).length > 0 && (
                <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                    <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Solver Decision Telemetry
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs">
                        {Object.entries(solverRationale).map(([key, value]) => {
                            if (typeof value === 'object' && value !== null) {
                                if (Array.isArray(value)) {
                                    if (key === 'safety_notes') {
                                        return (
                                            <div key={key} className="flex flex-col gap-2 bg-amber-500/10 border border-amber-500/20 p-3.5 rounded-lg md:col-span-2">
                                                <span className="text-amber-400 font-semibold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                                                    <ShieldCheck className="h-3.5 w-3.5" />
                                                    Safety Exclusions & Guardrails
                                                </span>
                                                <div className="space-y-1.5">
                                                    {value.map((subItem: any, ni: number) => (
                                                        <p key={ni} className="text-xs text-amber-200 flex items-start gap-1.5">
                                                            <span>⚠️</span>
                                                            <span>{String(subItem)}</span>
                                                        </p>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    }
                                    if (key === 'categories_activated') {
                                        return (
                                            <div key={key} className="flex flex-col gap-2 bg-white/5 p-3.5 rounded-lg md:col-span-2">
                                                <span className="text-zinc-400 font-semibold uppercase tracking-wider text-[10px]">
                                                    Categories Activated
                                                </span>
                                                <div className="flex flex-wrap gap-2">
                                                    {value.map((cat: any, ci: number) => (
                                                        <span key={ci} className="inline-flex items-center gap-1.5 rounded-md bg-purple-500/15 text-purple-300 border border-purple-500/30 px-3 py-1 text-xs font-medium">
                                                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                                                            {String(cat)}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    }
                                    return (
                                        <div key={key} className="flex flex-col gap-2 bg-white/5 p-3.5 rounded-lg md:col-span-2">
                                            <span className="text-zinc-400 font-semibold uppercase tracking-wider text-[10px]">
                                                {key.replace(/_/g, ' ')}
                                            </span>
                                            <div className="flex flex-wrap gap-2">
                                                {value.map((subItem: any, ni: number) => (
                                                    <span key={ni} className="inline-flex items-center gap-1.5 rounded bg-black/40 px-2.5 py-1 text-[11px] font-mono text-zinc-300 border border-white/5">
                                                        {String(subItem)}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                }

                                const formatSubVal = (val: any): string => {
                                    if (val === null || val === undefined) return 'N/A';
                                    if (typeof val !== 'object') return String(val);
                                    if ('limit' in val && 'used' in val) {
                                        return `₹${val.used} / ₹${val.limit}`;
                                    }
                                    if ('actual' in val && 'floor' in val) {
                                        return `${val.actual} (min ${val.floor}${val.cap !== undefined ? `, max ${val.cap}` : ''})`;
                                    }
                                    if ('delivered' in val && 'required' in val) {
                                        return `${val.delivered} delivered (min ${val.required})`;
                                    }
                                    return Object.entries(val).map(([k, v]) => `${k}: ${v}`).join(', ');
                                };

                                return (
                                    <div key={key} className="flex flex-col gap-2 bg-white/5 p-3.5 rounded-lg md:col-span-2">
                                        <span className="text-zinc-400 font-semibold uppercase tracking-wider text-[10px]">
                                            {key.replace(/_/g, ' ')}
                                        </span>
                                        <div className="flex flex-wrap gap-2">
                                            {Object.entries(value).map(([subK, subV]) => (
                                                <span key={subK} className="inline-flex items-center gap-1.5 rounded bg-black/40 px-2.5 py-1 text-[11px] font-mono text-emerald-300 border border-emerald-500/20">
                                                    <span className="text-zinc-400 font-medium">{subK.replace(/_/g, ' ')}:</span> {formatSubVal(subV)}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                );
                            }
                            return (
                                <div key={key} className="flex justify-between items-center bg-white/5 px-4 py-3 rounded-lg">
                                    <span className="text-zinc-400 capitalize">{key.replace(/_/g, ' ')}</span>
                                    <span className="font-mono text-emerald-400 font-semibold">{String(value)}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Compiled SQL Query & DB Performance Card */}
            {sqlQueries.length > 0 && (
                <div className="bg-black/30 border border-white/10 rounded-xl p-5 space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Database className="h-4 w-4 text-amber-400" /> Compiled SQL Query & Execution Telemetry
                        </h3>
                        <span className="text-xs text-zinc-500 font-mono bg-white/5 px-2.5 py-1 rounded-md border border-white/5">
                            {sqlQueries.length} {sqlQueries.length === 1 ? "query" : "queries"} executed
                        </span>
                    </div>

                    {sqlQueries.map((sq: any, i: number) => (
                        <div key={i} className="space-y-3.5">
                            {/* Stats & Filters Bar */}
                            <div className="flex flex-col gap-2.5 bg-zinc-900/70 p-3.5 rounded-xl border border-white/5 text-xs">
                                <div className="flex flex-wrap items-center gap-2.5">
                                    <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/15 px-2.5 py-1 font-mono text-amber-300 font-medium border border-amber-500/30">
                                        <Clock className="h-3 w-3 text-amber-400" /> {sq.duration_ms} ms
                                    </span>
                                    <span className="inline-flex items-center gap-1 rounded-md bg-zinc-800/90 px-2.5 py-1 text-zinc-200 border border-zinc-700/80 font-mono">
                                        <Layers className="h-3 w-3 text-zinc-400" /> Rows Returned: <strong className="text-white font-bold">{sq.rows_returned}</strong>
                                    </span>
                                </div>

                                {sq.filters_applied && sq.filters_applied.length > 0 && (
                                    <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-white/5">
                                        <div className="flex items-center gap-1 text-[11px] text-zinc-400 font-semibold uppercase tracking-wider mr-1.5">
                                            <Filter className="h-3.5 w-3.5 text-amber-400" />
                                            <span>Filters:</span>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-1.5">
                                            {sq.filters_applied.map((filterStr: string, fIdx: number) => {
                                                const hasColon = filterStr.includes(":");
                                                const [key, ...valParts] = hasColon ? filterStr.split(":") : [filterStr, ""];
                                                const val = valParts.join(":");

                                                return (
                                                    <React.Fragment key={fIdx}>
                                                        {fIdx > 0 && (
                                                            <span className="text-zinc-600 font-mono text-xs select-none mx-0.5">|</span>
                                                        )}
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-zinc-800/90 border border-zinc-700/80 text-[11px] shadow-sm">
                                                            {hasColon ? (
                                                                <>
                                                                    <span className="text-zinc-400 font-mono">{key}</span>
                                                                    <span className="text-zinc-500">:</span>
                                                                    <span className="text-white font-semibold font-mono">
                                                                        {key.includes("budget") || key.includes("price") ? `₹${parseFloat(val).toLocaleString()}` : val}
                                                                    </span>
                                                                </>
                                                            ) : (
                                                                <span className="text-white font-semibold font-mono">
                                                                    {filterStr}
                                                                </span>
                                                            )}
                                                        </span>
                                                    </React.Fragment>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* SQL Query Snippet */}
                            {sq.compiled_sql && (
                                <div className="rounded-xl overflow-hidden border border-zinc-800/90 bg-zinc-950 shadow-inner">
                                    <div className="flex items-center justify-between px-3.5 py-2 bg-zinc-900/90 border-b border-zinc-800/80">
                                        <span className="text-[11px] font-mono text-zinc-400 flex items-center gap-1.5">
                                            <Terminal className="h-3.5 w-3.5 text-zinc-400" /> PostgreSQL Parameterized Query
                                        </span>
                                        <CopyButton text={sq.compiled_sql} label="Copy SQL Query" />
                                    </div>
                                    <pre className="overflow-x-auto p-4 font-mono text-[11px] leading-relaxed text-zinc-200 selection:bg-amber-500/30">
                                        {sq.compiled_sql}
                                    </pre>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* In-Memory Cache & Query Acceleration Card */}
            <div className="bg-black/30 border border-white/10 rounded-xl p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Zap className="h-4 w-4 text-emerald-400" /> In-Memory Menu Cache Telemetry
                        </h3>
                        <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-md bg-zinc-800 text-zinc-300 border border-zinc-700">
                            Tier: L2 Filter Cache
                        </span>
                    </div>
                    <span className="text-xs text-zinc-500 font-mono bg-white/5 px-2.5 py-1 rounded-md border border-white/5">
                        {cacheHits.length > 0 ? `${cacheHits.length} cache ${cacheHits.length === 1 ? 'event' : 'events'} recorded` : "Direct query"}
                    </span>
                </div>

                {cacheHits.length > 0 ? (
                    <div className="space-y-3">
                        {cacheHits.map((ch: any, i: number) => {
                            const isHit = ch.status === "HIT" || ch.hit === true;
                            return (
                                <div
                                    key={i}
                                    className={`rounded-xl p-4 space-y-3 text-xs bg-zinc-900/80 border transition-all ${
                                        isHit
                                            ? "border-emerald-500/40 shadow-sm shadow-emerald-950/30"
                                            : "border-rose-500/40 shadow-sm shadow-rose-950/30"
                                    }`}
                                >
                                    <div className="flex flex-wrap items-center justify-between gap-2.5">
                                        <div className="flex flex-wrap items-center gap-2">
                                            {/* Hit / Miss Status Badge */}
                                            <span
                                                className={`inline-flex items-center gap-1.5 font-bold uppercase tracking-wider px-2.5 py-1 rounded-md text-[11px] shadow-sm ${
                                                    isHit
                                                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                                        : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                                }`}
                                            >
                                                {isHit ? (
                                                    <>
                                                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                                                        CACHE HIT
                                                    </>
                                                ) : (
                                                    <>
                                                        <XCircle className="h-3.5 w-3.5 text-rose-400" />
                                                        CACHE MISS (POPULATED)
                                                    </>
                                                )}
                                            </span>

                                            <span className="text-zinc-300 font-mono text-[11px] bg-zinc-800/90 px-2 py-0.5 rounded border border-zinc-700/70">
                                                {ch.cache_type || "IN_MEMORY_MENU_FILTER"}
                                            </span>
                                        </div>

                                        <div className="flex flex-wrap items-center gap-2 font-mono text-zinc-400 text-[11px]">
                                            {ch.duration_ms !== undefined && (
                                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded bg-zinc-800/90 border border-zinc-700/60 ${isHit ? "text-emerald-300" : "text-amber-300"}`}>
                                                    <Clock className="h-3 w-3" />
                                                    {isHit ? `${ch.duration_ms} ms (retrieval)` : `${ch.duration_ms} ms (db + store)`}
                                                </span>
                                            )}
                                            {ch.ttl_remaining_s !== undefined && (
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-zinc-800/90 border border-zinc-700/60 text-zinc-300">
                                                    TTL left: <strong className="text-white">{ch.ttl_remaining_s}s</strong>
                                                </span>
                                            )}
                                            {ch.ttl_s !== undefined && (
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-zinc-800/90 border border-zinc-700/60 text-zinc-300">
                                                    TTL: <strong className="text-white">{ch.ttl_s}s</strong>
                                                </span>
                                            )}
                                            {ch.items_count !== undefined && (
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-zinc-800/90 border border-zinc-700/60 text-zinc-300">
                                                    Indexed Items: <strong className="text-white">{ch.items_count}</strong>
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {ch.key && (
                                        <div className="bg-black/60 rounded-lg p-2.5 border border-white/5 flex items-center justify-between gap-2 overflow-hidden">
                                            <div className="flex items-center gap-2 overflow-hidden min-w-0">
                                                <Key className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                                                <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold shrink-0">Key:</span>
                                                <code className="text-[11px] font-mono text-zinc-200 truncate select-all" title={ch.key}>
                                                    {ch.key}
                                                </code>
                                            </div>
                                            <div className="shrink-0">
                                                <CopyButton text={ch.key} label="Copy Key" />
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="flex items-center justify-between bg-zinc-900/60 border border-white/10 rounded-lg p-4 text-xs">
                        <div className="flex items-center gap-2.5">
                            <span className="inline-flex items-center gap-1 font-bold uppercase tracking-wider px-2.5 py-1 rounded text-[11px] bg-zinc-800 text-zinc-400 border border-zinc-700">
                                NO CACHE INTERCEPT
                            </span>
                            <span className="text-zinc-300">
                                Direct database query executed without cache interception.
                            </span>
                        </div>
                        <span className="text-zinc-500 font-mono text-[11px]">0.0 ms</span>
                    </div>
                )}

                {/* Architectural Note */}
                <div className="bg-zinc-950/70 border border-white/10 rounded-xl p-3.5 space-y-2 text-xs">
                    <div className="flex items-center gap-2 text-zinc-200 font-semibold text-[12px]">
                        <Info className="h-4 w-4 text-[#f6a61d] shrink-0" />
                        <span>SmartDiner Dual-Tier Caching Architecture:</span>
                    </div>
                    <ul className="space-y-1.5 pl-6 list-disc text-zinc-400 text-[11px] leading-relaxed">
                        <li>
                            <strong className="text-white font-semibold">L2 Dynamic Filter Cache</strong> (shown above): Optimizes AI recommendation queries per user constraint set with a <span className="font-mono text-zinc-200 font-medium">300s TTL</span>.
                        </li>
                        <li>
                            <strong className="text-white font-semibold">L1 Full Catalog Cache</strong> (<code className="font-mono text-zinc-200 bg-white/10 px-1.5 py-0.5 rounded text-[10px] border border-white/10">MENU_CACHE</code>, <span className="font-mono text-zinc-200 font-medium">300s TTL</span>): Serves customer browsing pages with eager-loaded relational joins to prevent <strong>N+1</strong> database queries.
                        </li>
                    </ul>
                </div>
            </div>

            {/* LLM Token Usage & Latency Card */}
            {llmCalls.length > 0 && (
                <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                    <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Cpu className="h-4 w-4 text-purple-400" /> LLM Execution & Token Tracking
                        </h3>
                        <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono text-zinc-400 bg-white/5 px-3 py-1.5 rounded-lg border border-white/5">
                            <Coins className="h-3.5 w-3.5 text-yellow-500" />
                            <span>Total Tokens: <strong className="text-white font-bold">{grandTotalTokens.toLocaleString()}</strong></span>
                            <span className="text-zinc-600">|</span>
                            <span className="text-blue-300">Prompt: {totalPromptTokens.toLocaleString()}</span>
                            <span className="text-zinc-600">|</span>
                            <span className="text-emerald-300">Completion: {totalCompletionTokens.toLocaleString()}</span>
                            {totalLatencyMs > 0 && (
                                <>
                                    <span className="text-zinc-600">|</span>
                                    <span className="text-amber-400 flex items-center gap-1 font-semibold">
                                        <Clock className="h-3 w-3" />
                                        {totalLatencyMs >= 1000 ? `${(totalLatencyMs / 1000).toFixed(2)}s` : `${Math.round(totalLatencyMs)}ms`}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {llmCalls.map((call: any, idx: number) => {
                            const pTokens = getPromptTokens(call);
                            const cTokens = getCompletionTokens(call);
                            const tTokens = getTotalTokens(call);
                            const latency = getLatencyMs(call);
                            const formattedLatency = latency >= 1000 ? `${(latency / 1000).toFixed(2)}s` : `${Math.round(latency)}ms`;

                            return (
                                <div key={idx} className="rounded-xl bg-white/[0.04] p-4 border border-white/10 text-xs space-y-3 shadow-sm hover:border-white/20 transition flex flex-col justify-between">
                                    <div className="space-y-2.5">
                                        {/* Step Title & Latency */}
                                        <div className="flex items-center justify-between gap-2 border-b border-white/5 pb-2.5">
                                            <span className="font-bold text-purple-300 capitalize tracking-wide text-xs flex items-center gap-1.5">
                                                <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                                                {call.step?.replace(/_/g, ' ')}
                                            </span>
                                            <span className="font-mono text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded text-[11px] font-semibold flex items-center gap-1">
                                                <Clock className="h-3 w-3" />
                                                {formattedLatency}
                                            </span>
                                        </div>

                                        {/* Model & Temperature Info */}
                                        <div className="flex items-center justify-between gap-2 text-[10px] font-mono">
                                            <span className="text-zinc-400 bg-black/40 px-2 py-0.5 rounded border border-white/5 truncate max-w-[68%]" title={call.model || 'N/A'}>
                                                Model: <span className="text-zinc-200">{call.model || 'N/A'}</span>
                                            </span>
                                            {call.temperature !== undefined && (
                                                <span className="text-zinc-400 bg-black/40 px-2 py-0.5 rounded border border-white/5 shrink-0 whitespace-nowrap">
                                                    Temp: <span className="text-zinc-200">{call.temperature}</span>
                                                </span>
                                            )}
                                        </div>

                                        {/* Token Usage Breakdown Badges */}
                                        <div className="pt-1">
                                            <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-semibold mb-1.5">
                                                Token Usage
                                            </div>
                                            <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
                                                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-2 text-center">
                                                    <div className="text-[9px] text-blue-400/80 uppercase font-medium">Prompt</div>
                                                    <div className="font-bold text-blue-300 mt-0.5">{pTokens.toLocaleString()}</div>
                                                </div>
                                                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2 text-center">
                                                    <div className="text-[9px] text-emerald-400/80 uppercase font-medium">Completion</div>
                                                    <div className="font-bold text-emerald-300 mt-0.5">{cTokens.toLocaleString()}</div>
                                                </div>
                                                <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-2 text-center">
                                                    <div className="text-[9px] text-purple-400/80 uppercase font-medium">Total</div>
                                                    <div className="font-bold text-purple-200 mt-0.5">{tTokens.toLocaleString()}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Prompt preview if available */}
                                    {call.prompt_preview && (
                                        <div className="pt-2 border-t border-white/5 mt-2">
                                            <div className="flex items-center justify-between mb-1.5">
                                                <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">
                                                    Prompt Preview
                                                </span>
                                                <CopyButton text={call.prompt_preview} label="Copy Prompt" />
                                            </div>
                                            <pre className="text-[11px] font-mono text-zinc-300 bg-black/60 p-2.5 rounded-lg border border-white/5 whitespace-pre-wrap break-words resize-y overflow-y-auto min-h-[68px] max-h-[220px] h-[78px] leading-relaxed select-text [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-zinc-700/80 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-600 [&::-webkit-scrollbar-track]:bg-black/30">
                                                {call.prompt_preview}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Recommended Cart */}
            <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#f6a61d]"></span> Recommended Cart
                </h3>
                {log.recommended_cart && log.recommended_cart.length > 0 ? (
                    <table className="w-full text-left text-xs">
                        <thead className="text-zinc-500 border-b border-white/10">
                            <tr>
                                <th className="pb-2 font-medium">Item</th>
                                <th className="pb-2 font-medium">Qty</th>
                                <th className="pb-2 font-medium text-right">Price</th>
                                <th className="pb-2 font-medium text-right">Subtotal</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {log.recommended_cart.map((item: any, i: number) => (
                                <tr key={i}>
                                    <td className="py-3">
                                        <div className="font-medium text-white">{item.name}</div>
                                        <div className="text-[10px] text-zinc-500 mt-0.5">{item.category} • {item.dietary_preference || (item.is_veg ? 'Veg' : 'Non-Veg')}</div>
                                    </td>
                                    <td className="py-3 font-medium text-zinc-300">{item.quantity}x</td>
                                    <td className="py-3 text-right text-zinc-400">₹{item.unit_price}</td>
                                    <td className="py-3 text-right font-semibold text-white">₹{item.subtotal}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p className="text-xs text-zinc-500">No items recommended (Solver likely failed or empty cart).</p>
                )}
            </div>

            {/* LLM Explanation */}
            <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span> LLM Explanation
                </h3>
                <p className="text-sm text-zinc-300 italic bg-white/5 rounded-lg p-3.5 border border-white/5">
                    &ldquo;{log.llm_explanation}&rdquo;
                </p>
            </div>
        </div>
    );
}
