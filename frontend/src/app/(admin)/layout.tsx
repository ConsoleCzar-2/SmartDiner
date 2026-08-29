"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, MessageSquare, LogOut, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import "../globals.css";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [isLoading, setIsLoading] = useState(true);
    const [userName, setUserName] = useState("");

    useEffect(() => {
        const token = localStorage.getItem("adminToken");
        const name = localStorage.getItem("userName");
        if (!token && pathname !== "/login") {
            router.push("/login");
        } else {
            if (name) setUserName(name);
            setIsLoading(false);
        }
    }, [pathname, router]);

    if (isLoading) {
        return (
            <html lang="en">
                <body>
                    <div className="flex min-h-screen items-center justify-center bg-[#0c1011]">
                        <Loader2 className="h-6 w-6 animate-spin text-[#f6a61d]" />
                    </div>
                </body>
            </html>
        );
    }

    if (pathname === "/admin/login") {
        return (
            <html lang="en">
                <body>{children}</body>
            </html>
        );
    }

    return (
        <html lang="en">
            <body>
                <div className="flex min-h-screen bg-[#0c1011]">
                    <aside className="w-64 border-r border-white/10 bg-[#0c1011] flex flex-col">
                        <div className="p-6 border-b border-white/10">
                            <span className="block text-sm font-black tracking-[-.06em] text-white">
                                Smart<span className="text-[#f6a61d]">Diner</span> admin
                            </span>
                        </div>
                        <nav className="flex-1 space-y-2 p-4">
                            <Link
                                href="/admin"
                                className={cn(
                                    "flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition",
                                    pathname === "/admin"
                                        ? "bg-white/10 text-white"
                                        : "text-zinc-400 hover:bg-white/5 hover:text-white"
                                )}
                            >
                                <LayoutDashboard className="h-4 w-4" />
                                Dashboard
                            </Link>
                            <Link
                                href="/admin/conversations"
                                className={cn(
                                    "flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition",
                                    pathname.startsWith("/admin/conversations")
                                        ? "bg-white/10 text-white"
                                        : "text-zinc-400 hover:bg-white/5 hover:text-white"
                                )}
                            >
                                <MessageSquare className="h-4 w-4" />
                                Conversations
                            </Link>
                            <Link
                                href="/admin/menu-manager"
                                className={cn(
                                    "flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition",
                                    pathname.startsWith("/admin/menu-manager")
                                        ? "bg-white/10 text-white"
                                        : "text-zinc-400 hover:bg-white/5 hover:text-white"
                                )}
                            >
                                <LayoutDashboard className="h-4 w-4" />
                                Menu Manager
                            </Link>
                        </nav>
                        <div className="p-4 border-t border-white/10">
                            <div className="mb-4 flex items-center gap-3 px-4">
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-white font-bold">
                                    {userName ? userName.charAt(0).toUpperCase() : "A"}
                                </div>
                                <span className="text-sm font-semibold text-zinc-300">
                                    {userName || "Admin"}
                                </span>
                            </div>
                            <button
                                onClick={() => {
                                    localStorage.removeItem("adminToken");
                                    localStorage.removeItem("userName");
                                    router.push("/login");
                                }}
                                className="flex w-full items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium text-red-400 hover:bg-red-400/10 transition"
                            >
                                <LogOut className="h-4 w-4" />
                                Log out
                            </button>
                        </div>
                    </aside>
                    <main className="flex-1 overflow-y-auto">
                        {children}
                    </main>
                </div>
            </body>
        </html>
    );
}
