"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { customerLogin, adminLogin, customerRegister } from "@/lib/api";

export default function LoginPage() {
    const [tab, setTab] = useState<"customer" | "staff">("customer");
    const [isRegistering, setIsRegistering] = useState(false);
    
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            if (tab === "staff") {
                const data = await adminLogin({ email, password });
                if (data.access_token) {
                    localStorage.setItem("adminToken", data.access_token);
                    if (data.user_name) localStorage.setItem("userName", data.user_name);
                    router.push("/admin");
                }
            } else {
                if (isRegistering) {
                    await customerRegister({ name, email, password, default_preferences: {} });
                    // Auto login after register
                    const data = await customerLogin({ email, password });
                    if (data.access_token) {
                        localStorage.setItem("userToken", data.access_token);
                        if (data.user_name) localStorage.setItem("userName", data.user_name);
                        router.push("/");
                    }
                } else {
                    const data = await customerLogin({ email, password });
                    if (data.access_token) {
                        localStorage.setItem("userToken", data.access_token);
                        if (data.user_name) localStorage.setItem("userName", data.user_name);
                        router.push("/");
                    }
                }
            }
        } catch (err: any) {
            setError(err.message || "Invalid credentials");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-[calc(100vh-64px)] items-center justify-center p-4">
            <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white/[.02] p-8 backdrop-blur-2xl">
                <div className="text-center">
                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f6a61d] text-[#171207] shadow-[0_0_28px_rgba(246,166,29,.22)]">
                        <Bot className="h-6 w-6" />
                    </div>
                    <h1 className="text-2xl font-black tracking-tight text-white">
                        Welcome to Smart<span className="text-[#f6a61d]">Diner</span>
                    </h1>
                    <p className="mt-2 text-sm text-zinc-400">
                        {tab === "customer" 
                            ? (isRegistering ? "Create an account to save your dietary profile" : "Sign in to access your Concierge")
                            : "Authorized personnel only"}
                    </p>
                </div>

                <div className="mt-8 flex rounded-xl bg-black/40 p-1">
                    <button
                        onClick={() => { setTab("customer"); setError(""); }}
                        className={cn(
                            "flex-1 rounded-lg py-2 text-sm font-semibold transition-all",
                            tab === "customer" ? "bg-white/[.08] text-white shadow-sm" : "text-zinc-500 hover:text-zinc-300"
                        )}
                    >
                        Customer
                    </button>
                    <button
                        onClick={() => { setTab("staff"); setError(""); }}
                        className={cn(
                            "flex-1 rounded-lg py-2 text-sm font-semibold transition-all",
                            tab === "staff" ? "bg-white/[.08] text-white shadow-sm" : "text-zinc-500 hover:text-zinc-300"
                        )}
                    >
                        Staff
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    {error && (
                        <div className="rounded-lg bg-red-500/10 p-3 text-center text-sm font-medium text-red-400">
                            {error}
                        </div>
                    )}
                    
                    {tab === "customer" && isRegistering && (
                        <div>
                            <label className="mb-1.5 block text-xs font-semibold text-zinc-300">Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white transition focus:border-[#f6a61d] focus:outline-none focus:ring-1 focus:ring-[#f6a61d]"
                                placeholder="Jane Doe"
                            />
                        </div>
                    )}

                    <div>
                        <label className="mb-1.5 block text-xs font-semibold text-zinc-300">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white transition focus:border-[#f6a61d] focus:outline-none focus:ring-1 focus:ring-[#f6a61d]"
                            placeholder="you@example.com"
                        />
                    </div>
                    <div>
                        <label className="mb-1.5 block text-xs font-semibold text-zinc-300">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white transition focus:border-[#f6a61d] focus:outline-none focus:ring-1 focus:ring-[#f6a61d]"
                            placeholder="••••••••"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="mt-2 w-full rounded-xl bg-[#f6a61d] py-3 text-sm font-bold text-[#1e170d] transition hover:bg-[#f6a61d]/90 disabled:opacity-50"
                    >
                        {loading ? "Processing..." : (tab === "customer" && isRegistering ? "Create Account" : "Sign In")}
                    </button>
                </form>

                {tab === "customer" && (
                    <div className="mt-6 text-center text-xs text-zinc-500">
                        {isRegistering ? "Already have an account? " : "Don't have an account? "}
                        <button
                            onClick={() => setIsRegistering(!isRegistering)}
                            className="font-semibold text-[#f6a61d] hover:underline"
                        >
                            {isRegistering ? "Sign In" : "Register"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
