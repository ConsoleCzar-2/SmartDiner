import { Activity, BadgeIndianRupee, ShieldCheck } from "lucide-react";

export function AdminMetrics({ data }: { data?: any }) {
    if (!data) return null;

    const metrics = [
        {
            label: "Total Orders",
            value: data.total_orders.toString(),
            detail: "Completed transactions",
            icon: Activity,
        },
        {
            label: "Total Revenue",
            value: `₹${data.total_revenue.toFixed(2)}`,
            detail: "Gross volume",
            icon: BadgeIndianRupee,
        },
        {
            label: "Total Conversations",
            value: data.total_conversations.toString(),
            detail: "Governed pipeline runs",
            icon: ShieldCheck,
        },
    ];

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
