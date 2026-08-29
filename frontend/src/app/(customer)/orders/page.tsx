"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/navbar";
import { fetchOrderHistory } from "@/lib/api";
import { format } from "date-fns";
import { Receipt, Clock, MapPin } from "lucide-react";

export default function OrdersPage() {
    const [orders, setOrders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadOrders();
    }, []);

    const loadOrders = async () => {
        try {
            const data = await fetchOrderHistory();
            setOrders(data.orders || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-[#0c1011] text-white">
            <Navbar />
            <div className="mx-auto max-w-4xl px-5 py-12 lg:px-8">
                <h1 className="text-3xl font-black mb-8 flex items-center gap-3">
                    <Receipt className="h-8 w-8 text-[#f6a61d]" />
                    Order History
                </h1>

                {loading ? (
                    <div className="text-zinc-500">Loading orders...</div>
                ) : orders.length === 0 ? (
                    <div className="text-zinc-500 bg-white/5 rounded-2xl p-8 text-center">
                        You haven't placed any orders yet.
                    </div>
                ) : (
                    <div className="space-y-6">
                        {orders.map((order, idx) => (
                            <div key={idx} className="rounded-2xl border border-white/10 bg-white/[.02] p-6 shadow-xl">
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/10 pb-4 mb-4 gap-4">
                                    <div>
                                        <p className="text-[#f6a61d] font-bold flex items-center gap-2 mb-1">
                                            <MapPin className="h-4 w-4" /> 
                                            {order.restaurant_name || "Restaurant"}
                                        </p>
                                        <p className="text-xs text-zinc-400 flex items-center gap-2">
                                            <Clock className="h-3 w-3" />
                                            {format(new Date(order.created_at), "MMM d, yyyy 'at' h:mm a")}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <span className="inline-block px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-xs font-bold uppercase tracking-wider mb-2">
                                            {order.status}
                                        </span>
                                        <p className="text-2xl font-black">₹{order.total_amount}</p>
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    {order.items.map((item: any, i: number) => (
                                        <div key={i} className="flex justify-between items-center text-sm">
                                            <div className="flex items-center gap-3">
                                                <span className="w-6 h-6 rounded bg-white/10 flex items-center justify-center font-bold text-xs text-zinc-300">
                                                    {item.quantity}x
                                                </span>
                                                <span>{item.name}</span>
                                            </div>
                                            <span className="font-semibold text-zinc-400">₹{item.subtotal}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </main>
    );
}
