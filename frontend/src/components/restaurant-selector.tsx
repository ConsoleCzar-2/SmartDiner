"use client";
import { ArrowRight, Check, MapPin, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fetchRestaurants } from "@/lib/api";
import type { RestaurantResponse } from "@/types";

export function RestaurantSelector() {
    const [restaurants, setRestaurants] = useState<RestaurantResponse[]>([]);
    const [selected, setSelected] = useState<RestaurantResponse | null>(null);
    const router = useRouter();

    useEffect(() => {
        fetchRestaurants()
            .then((data) => {
                setRestaurants(data);
                if (data.length > 0) {
                    setSelected(data[0]);
                }
            })
            .catch(console.error);
    }, []);

    const continueToChat = () => {
        if (selected) {
            router.push(`/chat?restaurant_id=${selected.id}`);
        }
    };
    return (
        <section className="grid gap-8 lg:grid-cols-[1.05fr_.95fr] lg:items-center">
            <div>
                <div className="mb-6 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#f6a61d]">
                    <span className="h-px w-8 bg-[#f6a61d]" /> Governed dining
                    intelligence
                </div>
                <h1 className="max-w-2xl font-serif text-5xl leading-[.9] tracking-[-.07em] text-white sm:text-7xl">
                    Bring the whole <em className="text-[#f6a61d]">table</em>{" "}
                    into balance.
                </h1>
                <p className="mt-7 max-w-xl text-base leading-7 text-zinc-400">
                    Tell SmartDiner the group, the budget, and the dietary
                    boundaries. The governed pipeline returns the strongest safe
                    menu combination—without guessing at the math.
                </p>
                <div className="mt-8 flex flex-wrap gap-3 text-xs text-zinc-400">
                    <span className="rounded-full border border-white/10 bg-white/[.03] px-3 py-2">
                        Allergen screening first
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/[.03] px-3 py-2">
                        ILP-optimised cart
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/[.03] px-3 py-2">
                        Grounded explanation
                    </span>
                </div>
            </div>
            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#1c1510] via-[#121719] to-[#0d1011] p-5 shadow-2xl sm:p-7">
                <div className="absolute right-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-[#f6a61d]/10 blur-3xl" />
                <div className="relative">
                    <div className="mb-5 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#f6a61d]">
                                Start with a venue
                            </p>
                            <h2 className="mt-1 text-xl font-bold text-white">
                                Select the dining room
                            </h2>
                        </div>
                        <Sparkles className="h-5 w-5 text-[#f6a61d]" />
                    </div>
                    <div className="space-y-2">
                        {restaurants.map((restaurant, index) => {
                            const active =
                                selected && restaurant.id === selected.id;
                            return (
                                <motion.button
                                    key={restaurant.id}
                                    whileHover={{ y: -2 }}
                                    whileTap={{ scale: 0.99 }}
                                    onClick={() => setSelected(restaurant)}
                                    className={cn(
                                        "flex w-full items-center gap-3 rounded-2xl border p-3 text-left transition",
                                        active
                                            ? "border-[#f6a61d]/70 bg-[#f6a61d] text-[#24190b]"
                                            : "border-white/10 bg-white/[.035] text-zinc-100 hover:border-white/25 hover:bg-white/[.06]",
                                    )}
                                >
                                    <span
                                        className={cn(
                                            "grid h-9 w-9 shrink-0 place-items-center rounded-xl text-[10px] font-black",
                                            active
                                                ? "bg-black/10"
                                                : "bg-white/8 text-zinc-300",
                                        )}
                                    >
                                        {String(index + 1).padStart(2, "0")}
                                    </span>
                                    <span className="min-w-0 flex-1">
                                        <span className="block text-sm font-bold">
                                            {restaurant.name}
                                        </span>
                                        <span
                                            className={cn(
                                                "mt-1 flex items-center gap-1 text-[11px]",
                                                active
                                                    ? "text-[#60420f]"
                                                    : "text-zinc-500",
                                            )}
                                        >
                                            <MapPin className="h-3 w-3" />
                                            {restaurant.cuisine_type ||
                                                "Various"}
                                        </span>
                                    </span>
                                    <span
                                        className={cn(
                                            "grid h-5 w-5 place-items-center rounded-full border",
                                            active
                                                ? "border-[#60420f]/40 bg-white/25"
                                                : "border-white/20",
                                        )}
                                    >
                                        {active && (
                                            <Check className="h-3 w-3" />
                                        )}
                                    </span>
                                </motion.button>
                            );
                        })}
                    </div>
                    {selected && (
                        <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-4">
                            <p className="text-[9px] font-bold uppercase tracking-[.16em] text-[#f6a61d]">
                                Selected preview
                            </p>
                            <div className="mt-2 flex items-center justify-between gap-4">
                                <div>
                                    <p className="font-bold text-white">
                                        {selected.name}
                                    </p>
                                    <p className="mt-1 text-xs leading-5 text-zinc-400">
                                        {selected.cuisine_type} cuisine
                                    </p>
                                </div>
                                <span className="rounded-full bg-white/8 px-2.5 py-1 text-[10px] font-semibold text-zinc-300">
                                    {selected.cuisine_type}
                                </span>
                            </div>
                        </div>
                    )}
                    <Button
                        onClick={continueToChat}
                        disabled={!selected}
                        className="mt-5 w-full bg-[#f6a61d] text-[#24190b] hover:bg-[#ffc152]"
                    >
                        Plan this table <ArrowRight className="ml-1 h-4 w-4" />
                    </Button>
                </div>
            </div>
        </section>
    );
}
