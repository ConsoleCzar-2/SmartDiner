import React from 'react';

export default function WormLogViewer({ log, viewMode }: { log: any; viewMode: 'ui' | 'json' }) {
    if (viewMode === 'json') {
        return (
            <pre className="overflow-x-auto text-xs text-emerald-400 bg-black/50 p-6 rounded-lg border border-white/5 mb-6">
                {JSON.stringify(log, null, 2)}
            </pre>
        );
    }

    return (
        <div className="space-y-6 mb-12 border-b border-white/10 pb-12 last:border-0">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-xs text-zinc-500 uppercase tracking-wider font-bold">Snapshot Timestamp:</span>
                <span className="text-sm font-medium text-white">{new Date(log.timestamp).toLocaleString()}</span>
            </div>
            <div className="grid grid-cols-2 gap-6">

                {/* Extracted Constraints */}
                <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                    <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-500"></span> Extracted Constraints
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                        <div><span className="text-zinc-500">Budget:</span> <span className="font-semibold text-white">₹{log.extracted_constraints?.max_budget}</span></div>
                        <div><span className="text-zinc-500">People:</span> <span className="font-semibold text-white">{log.extracted_constraints?.people_count}</span></div>
                        <div><span className="text-zinc-500">Veg:</span> <span className="font-semibold text-emerald-400">{log.extracted_constraints?.vegetarian_count}</span></div>
                        <div><span className="text-zinc-500">Vegan:</span> <span className="font-semibold text-green-300">{log.extracted_constraints?.vegan_count ?? 0}</span></div>
                        <div><span className="text-zinc-500">Non-Veg:</span> <span className="font-semibold text-red-400">{log.extracted_constraints?.non_vegetarian_count}</span></div>
                        <div><span className="text-zinc-500">Spice:</span> <span className="font-semibold text-orange-400">{log.extracted_constraints?.max_spice_level}</span></div>
                    </div>
                    {(log.extracted_constraints?.preferred_categories?.length > 0 || log.extracted_constraints?.preferred_cuisines?.length > 0) && (
                        <div className="mt-4 pt-4 border-t border-white/5 text-xs">
                            <div className="text-zinc-500 mb-1">Preferences:</div>
                            <div className="text-zinc-300">
                                {log.extracted_constraints?.preferred_categories?.join(", ")} {log.extracted_constraints?.preferred_cuisines?.join(", ")}
                            </div>
                        </div>
                    )}
                    {(log.extracted_constraints?.allergens?.length > 0) && (
                        <div className="mt-4 pt-4 border-t border-white/5 text-xs">
                            <div className="text-zinc-500 mb-1">Allergens:</div>
                            <div className="text-red-400 font-medium">
                                {log.extracted_constraints?.allergens?.join(", ")}
                            </div>
                        </div>
                    )}
                    {(log.extracted_constraints?.excluded_dishes?.length > 0) && (
                        <div className="mt-4 pt-4 border-t border-white/5 text-xs">
                            <div className="text-zinc-500 mb-1">Excluded Dishes:</div>
                            <div className="text-zinc-400 line-through decoration-red-500/50">
                                {log.extracted_constraints?.excluded_dishes?.join(", ")}
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
                            <span className={`font-bold ${log.solver_output?.status === 'Optimal' ? 'text-emerald-400' : 'text-red-400'}`}>
                                {log.solver_output?.status}
                            </span>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/5 p-3 rounded-lg">
                                <div className="text-zinc-500 mb-1">Computed Cost</div>
                                <div className="font-bold text-white text-base">₹{log.solver_output?.total_cost}</div>
                            </div>
                            <div className="bg-white/5 p-3 rounded-lg">
                                <div className="text-zinc-500 mb-1">Total Servings</div>
                                <div className="font-bold text-white text-base">{log.solver_output?.total_servings}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Decision Rationale */}
            {log.solver_output?.decision_rationale && (
                <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                    <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Decision Rationale (Math Bounds)
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                        {Object.entries(log.solver_output.decision_rationale).map(([key, value]) => (
                            <div key={key} className="flex justify-between items-center bg-white/5 px-4 py-3 rounded-lg">
                                <span className="text-zinc-500 capitalize">{key.replace(/_/g, ' ')}</span>
                                <span className="font-mono text-emerald-400 font-semibold">{String(value)}</span>
                            </div>
                        ))}
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
                    <p className="text-xs text-zinc-500">No items recommended (Solver likely failed).</p>
                )}
            </div>

            {/* LLM Explanation */}
            <div className="bg-black/30 border border-white/10 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span> LLM Explanation
                </h3>
                <p className="text-sm text-zinc-300 italic">
                    "{log.llm_explanation}"
                </p>
            </div>
        </div>
    );
}
