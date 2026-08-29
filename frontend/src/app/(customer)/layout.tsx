import type { Metadata } from "next";
import { Toaster } from "sonner";
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
            </body>
        </html>
    );
}
