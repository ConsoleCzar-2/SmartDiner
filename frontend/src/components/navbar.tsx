"use client";
import Link from "next/link";
import { Bot, MessageSquare, Sparkles, Moon, User } from "lucide-react";
import { usePathname, useSearchParams, useRouter, useParams } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import { cn } from "@/lib/utils";

const links = [
    { href: "/", label: "Dine", icon: Sparkles },
    { href: "/chat", label: "Concierge", icon: MessageSquare },
];

function NavbarContent() {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const restaurantId = searchParams.get("restaurant_id");

    return (
        <nav className="hidden items-center gap-1 rounded-full border border-white/10 bg-white/[.035] p-1 md:flex">
            {links.map(({ href, label, icon: Icon }) => {
                const isChat = href === "/chat";
                const targetHref = isChat && restaurantId ? `/chat?restaurant_id=${restaurantId}` : href;
                const isDisabled = isChat && !restaurantId;

                return (
                    <Link
                        key={href}
                        href={isDisabled ? "#" : targetHref}
                        onClick={(e) => {
                            if (isDisabled) {
                                e.preventDefault();
                                alert("Please select a restaurant first to use the Concierge.");
                            }
                        }}
                        className={cn(
                            "flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold transition",
                            pathname === href
                                ? "bg-[#f6a61d] text-[#1e170d]"
                                : "text-zinc-400 hover:bg-white/8 hover:text-white",
                            isDisabled && "cursor-not-allowed opacity-50 hover:bg-transparent hover:text-zinc-400"
                        )}
                    >
                        <Icon className="h-3.5 w-3.5" />
                        {label}
                    </Link>
                );
            })}
        </nav>
    );
}

import { ShoppingCart, ListOrdered } from "lucide-react";
import { CartDrawer } from "./cart-drawer";

function NavbarActions({ isLoggedIn, userName, onLogout }: { isLoggedIn: boolean, userName: string, onLogout: () => void }) {
    const searchParams = useSearchParams();
    const params = useParams();
    const restaurantId = searchParams.get("restaurant_id") || (params?.id as string);
    const [cartOpen, setCartOpen] = useState(false);

    return (
        <>
            <button className="hidden rounded-full border border-white/10 bg-white/[.05] p-2 text-zinc-400 transition hover:bg-white/[.1] hover:text-white sm:block">
                <Moon className="h-4 w-4" />
            </button>
            {isLoggedIn ? (
                <div className="flex items-center gap-3">
                    {restaurantId && (
                        <button 
                            onClick={() => setCartOpen(true)}
                            className="rounded-full border border-white/10 bg-white/[.05] p-2 text-zinc-400 transition hover:bg-white/[.1] hover:text-[#f6a61d]"
                        >
                            <ShoppingCart className="h-4 w-4" />
                        </button>
                    )}
                    <Link
                        href="/orders"
                        className="rounded-full border border-white/10 bg-white/[.05] p-2 text-zinc-400 transition hover:bg-white/[.1] hover:text-white"
                        title="My Orders"
                    >
                        <ListOrdered className="h-4 w-4" />
                    </Link>
                    <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[.03] px-3 py-1.5">
                        <User className="h-4 w-4 text-zinc-400" />
                        <span className="text-sm font-semibold text-zinc-300">{userName || "Customer"}</span>
                    </div>
                    <button
                        onClick={onLogout}
                        className="rounded-full border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs font-semibold text-red-400 transition hover:bg-red-500/20"
                    >
                        Sign Out
                    </button>
                </div>
            ) : (
                <Link
                    href="/login"
                    className="rounded-full bg-white/[.05] px-4 py-2 text-xs font-semibold text-white transition hover:bg-white/[.1]"
                >
                    Sign In
                </Link>
            )}
            
            {restaurantId && (
                <CartDrawer 
                    restaurantId={restaurantId} 
                    isOpen={cartOpen} 
                    onClose={() => setCartOpen(false)} 
                />
            )}
        </>
    );
}

export function Navbar() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [userName, setUserName] = useState("");
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem("userToken");
        const name = localStorage.getItem("userName");
        setIsLoggedIn(!!token);
        if (name) setUserName(name);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("userToken");
        localStorage.removeItem("userName");
        setIsLoggedIn(false);
        router.push("/");
    };

    return (
        <header className="sticky top-0 z-30 border-b border-white/8 bg-[#0c1011]/80 backdrop-blur-xl">
            <div className="relative mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
                <div className="flex flex-1 items-center justify-start">
                    <Link href="/" className="flex items-center gap-2.5">
                        <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f6a61d] text-[#171207] shadow-[0_0_28px_rgba(246,166,29,.22)]">
                            <Bot className="h-5 w-5" />
                        </span>
                        <span>
                            <span className="block text-sm font-black tracking-[-.06em] text-white">
                                Smart<span className="text-[#f6a61d]">Diner</span>
                            </span>
                            <span className="block text-[8px] font-semibold uppercase tracking-[.18em] text-zinc-500">
                                governed dining
                            </span>
                        </span>
                    </Link>
                </div>
                
                <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
                    <Suspense fallback={<nav className="hidden md:flex" />}>
                        <NavbarContent />
                    </Suspense>
                </div>
                
                <div className="flex flex-1 items-center justify-end gap-4">
                    <Suspense fallback={null}>
                        <NavbarActions isLoggedIn={isLoggedIn} userName={userName} onLogout={handleLogout} />
                    </Suspense>
                </div>
            </div>
        </header>
    );
}
