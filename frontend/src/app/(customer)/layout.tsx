import type { Metadata } from "next";
import { Toaster } from "sonner";
import { Analytics } from "@vercel/analytics/next";
import "../globals.css";

export const metadata: Metadata = {
    title: "SmartDiner — Governed dining intelligence",
    description:
        "An AI-powered restaurant assistant with solver-verified recommendations.",
};
export default function RootLayout({
    children,
}: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="en">
            <body>
                {children}
                <Toaster position="bottom-right" />
                <Analytics />
            </body>
        </html>
    );
}
