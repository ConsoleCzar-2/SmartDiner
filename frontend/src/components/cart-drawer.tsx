"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { fetchActiveCart, patchCart, checkoutOrder } from "@/lib/api";
import { X, Plus, Minus, ShoppingCart } from "lucide-react";
import { useRouter } from "next/navigation";

export function CartDrawer({
    restaurantId,
    isOpen,
    onClose,
}: {
    restaurantId: string;
    isOpen: boolean;
    onClose: () => void;
}) {
    const [cartItems, setCartItems] = useState<any[]>([]);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [mounted, setMounted] = useState(false);
    const router = useRouter();

    useEffect(() => {
        setMounted(true);
    }, []);

    const loadCart = async () => {
        if (!restaurantId || !isOpen) return;
        setLoading(true);
        try {
            const data = await fetchActiveCart(restaurantId);
            setConversationId(data.conversation_id);
            setCartItems(data.cart || []);
        } catch (e) {
            console.error("Failed to load cart", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadCart();
    }, [isOpen, restaurantId]);

    const updateQuantity = async (id: string, newQuantity: number) => {
        if (!conversationId) return;
        
        // Optimistic update
        setCartItems(current => 
            current.map(item => {
                if (item.id === id || item.menu_item_id === id) {
                    return { ...item, quantity: newQuantity };
                }
                return item;
            }).filter(item => item.quantity > 0)
        );

        try {
            const data = await patchCart(conversationId, [{ id, quantity: newQuantity }]);
            setCartItems(data.cart);
        } catch(e) {
            console.error("Failed to update cart", e);
            loadCart(); // revert
        }
    };

    const handleCheckout = async () => {
        if (!conversationId) return;
        try {
            setLoading(true);
            await checkoutOrder(conversationId);
            router.push("/orders");
            onClose();
        } catch (e: any) {
            alert(e.message);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen || !mounted) return null;

    const total = cartItems.reduce((acc, item) => acc + (item.subtotal || (item.quantity * item.unit_price)), 0);

    return createPortal(
        <div className="fixed inset-0 z-[100] flex justify-end">
            <div className="absolute inset-0 bg-black/50" onClick={onClose} />
            <div className="relative flex h-full w-full max-w-md flex-col bg-[#0c1011] shadow-2xl text-white">
                <div className="flex items-center justify-between border-b border-white/10 p-5">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <ShoppingCart className="h-5 w-5" /> Your Cart
                    </h2>
                    <button onClick={onClose} className="rounded-full p-2 hover:bg-white/10">
                        <X className="h-5 w-5" />
                    </button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-5 space-y-4">
                    {loading && cartItems.length === 0 ? (
                        <p className="text-zinc-500">Loading...</p>
                    ) : cartItems.length === 0 ? (
                        <p className="text-zinc-500 text-center mt-10">Your cart is empty.</p>
                    ) : (
                        cartItems.map((item, idx) => (
                            <div key={idx} className="flex gap-4 border-b border-white/10 pb-4">
                                {item.image_url && (
                                    <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg">
                                        <img src={item.image_url} alt={item.name} className="h-full w-full object-cover" />
                                    </div>
                                )}
                                <div className="flex flex-1 justify-between">
                                    <div>
                                        <p className="font-bold">{item.name}</p>
                                        <p className="text-sm text-zinc-400">₹{item.unit_price} x {item.quantity}</p>
                                    </div>
                                    <div className="flex flex-col items-end justify-between">
                                        <p className="font-black">₹{item.subtotal || (item.quantity * item.unit_price)}</p>
                                        <div className="flex items-center gap-3 mt-2 bg-white/5 rounded-full px-2 py-1">
                                            <button 
                                                onClick={() => {
                                                    updateQuantity(item.id || item.menu_item_id, item.quantity - 1);
                                                    window.dispatchEvent(new Event('cartUpdated'));
                                                }}
                                                className="hover:text-[#f6a61d]"
                                            >
                                                <Minus className="h-4 w-4" />
                                            </button>
                                            <span className="text-sm">{item.quantity}</span>
                                            <button 
                                                onClick={() => {
                                                    updateQuantity(item.id || item.menu_item_id, item.quantity + 1);
                                                    window.dispatchEvent(new Event('cartUpdated'));
                                                }}
                                                className="hover:text-[#f6a61d]"
                                            >
                                                <Plus className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
                
                {cartItems.length > 0 && (
                    <div className="border-t border-white/10 p-5">
                        <div className="flex justify-between mb-4">
                            <span className="text-zinc-400">Total</span>
                            <span className="text-xl font-black">₹{total}</span>
                        </div>
                        <button
                            onClick={handleCheckout}
                            disabled={loading}
                            className="w-full rounded-xl bg-[#f6a61d] py-3.5 text-sm font-bold text-[#0c1011] transition hover:bg-[#f6a61d]/80 disabled:opacity-50"
                        >
                            {loading ? "Processing..." : "Checkout"}
                        </button>
                    </div>
                )}
            </div>
        </div>,
        document.body
    );
}
