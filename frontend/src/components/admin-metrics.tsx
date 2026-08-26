import { Activity, BadgeIndianRupee, ShieldCheck } from "lucide-react";
const metrics = [
    {
        label: "Solved orders",
        value: "1,284",
        detail: "+18.6% this month",
        icon: Activity,
    },
    {
        label: "Budget accuracy",
        value: "99.8%",
        detail: "Within declared cap",
        icon: BadgeIndianRupee,
    },
    {
        label: "Hallucination rate",
        value: "0.0%",
        detail: "Grounded outputs only",
        icon: ShieldCheck,
    },
];
export function AdminMetrics() {
    return (
        <div className="grid gap-4 md:grid-cols-3">
            {metrics.map(({ label, value, detail, icon: Icon }) => (
                <div
                    key={label}
                    className="rounded-2xl border border-white/10 bg-white/[.035] p-5"
                >
                    <div className="flex items-center justify-between">
                        <p className="text-xs font-semibold text-zinc-400">
                            {label}
                        </p>
                        <Icon className="h-4 w-4 text-[#f6a61d]" />
                    </div>
                    <p className="mt-6 text-3xl font-black tracking-[-.05em] text-white">
                        {value}
                    </p>
                    <p className="mt-2 text-[11px] text-emerald-300">
                        {detail}
                    </p>
                </div>
            ))}
        </div>
    );
}
