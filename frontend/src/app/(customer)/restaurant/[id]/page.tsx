"use client";

import { useEffect, useState, use } from "react";
import { fetchRestaurant, fetchRestaurantMenu, addToCart, fetchActiveCart, patchCart } from "@/lib/api";
import { Navbar } from "@/components/navbar";
import { Loader2, Flame, Leaf, UtensilsCrossed, Utensils, AlertTriangle, Plus, Minus, Sprout, Drumstick } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function RestaurantMenuPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = use(params);
    const router = useRouter();
    const [restaurant, setRestaurant] = useState<any>(null);
    const [menuItems, setMenuItems] = useState<any[]>([]);
    const [cartItems, setCartItems] = useState<any[]>([]);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const [resData, menuData, cartData] = await Promise.all([
                    fetchRestaurant(id),
                    fetchRestaurantMenu(id),
                    fetchActiveCart(id).catch(() => null)
                ]);
                setRestaurant(resData);
                setMenuItems(menuData);
                if (cartData) {
                    setConversationId(cartData.conversation_id);
                    setCartItems(cartData.cart || []);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        
        loadInitialData();

        const handleCartUpdate = () => {
            fetchActiveCart(id).then(cartData => {
                if (cartData) {
                    setConversationId(cartData.conversation_id);
                    setCartItems(cartData.cart || []);
                }
            }).catch(console.error);
        };

        window.addEventListener('cartUpdated', handleCartUpdate);
        return () => window.removeEventListener('cartUpdated', handleCartUpdate);
    }, [id]);

    const getCartQuantity = (itemId: string) => {
        const item = cartItems.find((ci: any) => ci.menu_item_id === itemId || ci.id === itemId);
        return item ? item.quantity : 0;
    };

    const handleUpdateQuantity = async (itemId: string, currentQuantity: number, delta: number) => {
        const newQuantity = currentQuantity + delta;
        
        // If adding a new item, use addToCart which fetches item details from DB
        if (currentQuantity === 0 && delta > 0) {
            if (typeof window !== "undefined" && !localStorage.getItem("userToken")) {
                toast.error("Please sign in to add items to your cart");
                return;
            }
            try {
                const data = await addToCart({ restaurant_id: id, menu_item_id: itemId, quantity: 1 });
                setConversationId(data.conversation_id);
                setCartItems(data.cart);
                toast.success("Added to cart");
            } catch(e: any) {
                toast.error("Please sign in to add items to your cart");
            }
            return;
        }

        if (!conversationId) return;

        // Optimistic update for existing items
        setCartItems(current => {
            const existing = current.find(ci => ci.menu_item_id === itemId || ci.id === itemId);
            if (existing) {
                return current.map(item => 
                    (item.menu_item_id === itemId || item.id === itemId) 
                        ? { ...item, quantity: newQuantity } 
                        : item
                ).filter(item => item.quantity > 0);
            }
            return current;
        });

        try {
            const data = await patchCart(conversationId, [{ id: itemId, quantity: newQuantity }]);
            setCartItems(data.cart);
        } catch(e: any) {
            toast.error("Failed to update cart");
            fetchActiveCart(id).then(d => {
                if(d) setCartItems(d.cart || []);
            });
        }
    };

    if (loading) {
        return (
            <main className="min-h-screen bg-[#0c1011]">
                <Navbar />
                <div className="flex h-[80vh] items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-[#f6a61d]" />
                </div>
            </main>
        );
    }

    if (!restaurant) {
        return (
            <main className="min-h-screen bg-[#0c1011]">
                <Navbar />
                <div className="flex h-[80vh] items-center justify-center text-white">
                    Restaurant not found.
                </div>
            </main>
        );
    }

    // Group items by category
    const groupedMenu = menuItems.reduce((acc, item) => {
        if (!acc[item.category]) acc[item.category] = [];
        acc[item.category].push(item);
        return acc;
    }, {} as Record<string, any[]>);

    return (
        <main className="min-h-screen bg-[#0c1011] pb-32">
            <Navbar />
            
            {/* Hero Section */}
            <div className="relative h-64 w-full overflow-hidden sm:h-80 lg:h-96">
                <div className="absolute inset-0 bg-gradient-to-t from-[#0c1011] via-[#0c1011]/60 to-transparent z-10" />
                {restaurant.image_url ? (
                    <Image
                        src={restaurant.image_url}
                        alt={restaurant.name}
                        fill
                        className="object-cover"
                        priority
                    />
                ) : (
                    <div className="h-full w-full bg-zinc-800" />
                )}
                <div className="absolute bottom-0 left-0 z-20 w-full p-5 lg:p-12">
                    <div className="mx-auto max-w-7xl">
                        <span className="mb-3 inline-block rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold tracking-wider text-white backdrop-blur-md">
                            {restaurant.cuisine_type}
                        </span>
                        <h1 className="text-4xl font-black tracking-tight text-white sm:text-6xl">
                            {restaurant.name}
                        </h1>
                        {restaurant.address && (
                            <p className="mt-3 max-w-2xl text-sm font-medium text-zinc-300 sm:text-base">
                                {restaurant.address}
                            </p>
                        )}
                        {restaurant.description && (
                            <p className="mt-3 max-w-2xl text-sm text-zinc-400 sm:text-base">
                                {restaurant.description}
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Menu Section */}
            <div className="mx-auto mt-8 max-w-7xl px-5 lg:px-12">
                {Object.entries(groupedMenu).map(([category, items]) => (
                    <div key={category} className="mb-12">
                        <h2 className="mb-6 text-2xl font-bold text-white border-b border-white/10 pb-2">
                            {category}
                        </h2>
                        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                            {(items as any[]).map((item: any) => (
                                <div
                                    key={item.id}
                                    className="flex flex-col overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02] transition-colors hover:bg-white/[0.04]"
                                >
                                    {item.image_url ? (
                                        <div className="relative h-48 w-full bg-zinc-900">
                                            <Image
                                                src={item.image_url}
                                                alt={item.name}
                                                fill
                                                className={`object-cover ${!item.is_available ? 'grayscale opacity-40' : ''}`}
                                            />
                                        </div>
                                    ) : (
                                        <div className="flex h-48 w-full items-center justify-center bg-white/[0.03]">
                                            <Utensils className={`h-10 w-10 ${!item.is_available ? 'text-white/10' : 'text-white/20'}`} />
                                        </div>
                                    )}
                                    <div className="flex flex-1 flex-col p-5">
                                        <div className="flex items-start justify-between gap-4">
                                            <h3 className="text-lg font-bold text-zinc-100">
                                                {item.name}
                                            </h3>
                                            <span className="shrink-0 font-medium text-[#f6a61d]">
                                                ₹{item.price.toFixed(2)}
                                            </span>
                                        </div>
                                        <p className="mt-2 flex-1 text-sm text-zinc-400 line-clamp-3">
                                            {item.description}
                                        </p>
                                        <div className="mt-4 flex flex-wrap gap-2">
                                            {item.dietary_preference === "Vegetarian" && (
                                                <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-400 border border-emerald-500/20">
                                                    <Leaf className="h-3 w-3" /> Veg
                                                </span>
                                            )}
                                            {item.dietary_preference === "Vegan" && (
                                                <span className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-1 text-[10px] font-semibold text-green-400 border border-green-500/20">
                                                    <Sprout className="h-3 w-3" /> Vegan
                                                </span>
                                            )}
                                            {item.dietary_preference === "Non-Vegetarian" && (
                                                <span className="flex items-center gap-1 rounded-full bg-red-500/10 px-2.5 py-1 text-[10px] font-semibold text-red-400 border border-red-500/20">
                                                    <Drumstick className="h-3 w-3" /> Non-Veg
                                                </span>
                                            )}
                                            {item.spice_level !== "None" && (
                                                <span className="flex items-center gap-1 rounded-full bg-red-500/10 px-2.5 py-1 text-[10px] font-semibold text-red-400 border border-red-500/20">
                                                    <Flame className="h-3 w-3" /> {item.spice_level}
                                                </span>
                                            )}
                                            {item.allergens && item.allergens.length > 0 && (
                                                <span className="flex items-center gap-1 rounded-full bg-orange-500/10 px-2.5 py-1 text-[10px] font-semibold text-orange-400 border border-orange-500/20">
                                                    <AlertTriangle className="h-3 w-3" /> {item.allergens.join(", ")}
                                                </span>
                                            )}
                                        </div>
                                        <div className="mt-5">
                                            {!item.is_available ? (
                                                <div className="w-full rounded-xl border border-red-500/20 bg-red-500/10 py-2 text-center text-sm font-semibold text-red-400">
                                                    Out of Stock
                                                </div>
                                            ) : getCartQuantity(item.id) > 0 ? (
                                                <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-1">
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        onClick={() => handleUpdateQuantity(item.id, getCartQuantity(item.id), -1)}
                                                        className="h-8 w-8 hover:bg-white/10 hover:text-[#f6a61d]"
                                                    >
                                                        <Minus className="h-4 w-4" />
                                                    </Button>
                                                    <span className="text-sm font-bold w-8 text-center">{getCartQuantity(item.id)}</span>
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        onClick={() => handleUpdateQuantity(item.id, getCartQuantity(item.id), 1)}
                                                        className="h-8 w-8 hover:bg-white/10 hover:text-[#f6a61d]"
                                                    >
                                                        <Plus className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            ) : (
                                                <Button 
                                                    variant="outline"
                                                    onClick={() => handleUpdateQuantity(item.id, 0, 1)}
                                                    className="w-full rounded-xl border-white/10 bg-white/5 hover:bg-white/10 hover:text-white"
                                                >
                                                    Add to Cart
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Floating Action Button */}
            <div className="fixed bottom-8 right-8 z-50">
                <Button
                    onClick={() => router.push(`/chat?restaurant_id=${id}`)}
                    className="group flex h-14 w-14 items-center justify-center overflow-hidden rounded-full bg-[#f6a61d] p-0 font-bold text-[#1e170d] shadow-[0_0_40px_rgba(246,166,29,0.3)] transition-all duration-300 hover:w-[220px] hover:bg-[#ffc152]"
                >
                    <UtensilsCrossed className="h-6 w-6 shrink-0" />
                    <span className="max-w-0 overflow-hidden whitespace-nowrap transition-all duration-300 group-hover:ml-3 group-hover:max-w-[200px]">
                        Talk to AI Concierge
                    </span>
                </Button>
            </div>
        </main>
    );
}
