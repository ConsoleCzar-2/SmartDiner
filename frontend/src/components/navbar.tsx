"use client";
import Link from "next/link";
import { Bot, LayoutDashboard, MessageSquare, Sparkles } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
    { href: "/", label: "Dine", icon: Sparkles },
    { href: "/chat", label: "Concierge", icon: MessageSquare },
    { href: "/admin", label: "Operations", icon: LayoutDashboard },
];

export function Navbar() {
    const pathname = usePathname();
    return (
        <header className="sticky top-0 z-30 border-b border-white/8 bg-[#0c1011]/80 backdrop-blur-xl">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
                <Link href="/" className="flex items-center gap-2.5">
                    <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f6a61d] text-[#171207] shadow-[0_0_28px_rgba(246,166,29,.22)]">
                        <Bot className="h-5 w-5" />
                    </span>
                    <span>
                        <span className="block text-sm font-black tracking-[-.06em] text-white">
                            smart<span className="text-[#f6a61d]">diner</span>
                        </span>
                        <span className="block text-[8px] font-semibold uppercase tracking-[.18em] text-zinc-500">
                            governed dining
                        </span>
                    </span>
                </Link>
                <nav className="hidden items-center gap-1 rounded-full border border-white/10 bg-white/[.035] p-1 md:flex">
                    {links.map(({ href, label, icon: Icon }) => (
                        <Link
                            key={href}
                            href={href}
                            className={cn(
                                "flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold transition",
                                pathname === href
                                    ? "bg-[#f6a61d] text-[#1e170d]"
                                    : "text-zinc-400 hover:bg-white/8 hover:text-white",
                            )}
                        >
                            <Icon className="h-3.5 w-3.5" />
                            {label}
                        </Link>
                    ))}
                </nav>
                <div className="rounded-full border border-emerald-400/20 bg-emerald-400/[.08] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[.15em] text-emerald-300">
                    System aligned
                </div>
            </div>
        </header>
    );
}
