import type { Metadata } from "next";
import "./globals.css";

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
            <body>{children}</body>
        </html>
    );
}
