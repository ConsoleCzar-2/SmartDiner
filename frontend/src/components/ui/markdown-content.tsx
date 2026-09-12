"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownContentProps {
    content: string;
    variant?: "user" | "assistant";
    className?: string;
}

export function MarkdownContent({
    content,
    variant = "assistant",
    className = "",
}: MarkdownContentProps) {
    if (!content) return null;

    const isUser = variant === "user";

    return (
        <div className={`markdown-content break-words leading-relaxed ${className}`}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    p: ({ children }) => (
                        <p className={`mb-2.5 last:mb-0 ${isUser ? "text-inherit" : "text-zinc-200"}`}>
                            {children}
                        </p>
                    ),
                    h1: ({ children }) => (
                        <h1
                            className={`mt-4 mb-2 text-base font-bold first:mt-0 tracking-tight ${
                                isUser ? "text-[#171207]" : "text-white"
                            }`}
                        >
                            {children}
                        </h1>
                    ),
                    h2: ({ children }) => (
                        <h2
                            className={`mt-3.5 mb-1.5 text-sm font-bold first:mt-0 tracking-tight ${
                                isUser ? "text-[#171207]" : "text-white"
                            }`}
                        >
                            {children}
                        </h2>
                    ),
                    h3: ({ children }) => (
                        <h3
                            className={`mt-3 mb-1 text-xs sm:text-sm font-semibold first:mt-0 ${
                                isUser ? "text-[#171207] font-bold" : "text-amber-300"
                            }`}
                        >
                            {children}
                        </h3>
                    ),
                    h4: ({ children }) => (
                        <h4
                            className={`mt-2.5 mb-1 text-xs font-semibold first:mt-0 ${
                                isUser ? "text-[#171207]" : "text-zinc-200"
                            }`}
                        >
                            {children}
                        </h4>
                    ),
                    ul: ({ children }) => (
                        <ul className="my-2 list-disc pl-5 space-y-1 last:mb-0">
                            {children}
                        </ul>
                    ),
                    ol: ({ children }) => (
                        <ol className="my-2 list-decimal pl-5 space-y-1 last:mb-0">
                            {children}
                        </ol>
                    ),
                    li: ({ children }) => (
                        <li className={`text-xs sm:text-sm leading-relaxed ${isUser ? "text-inherit" : "text-zinc-300"}`}>
                            {children}
                        </li>
                    ),
                    strong: ({ children }) => (
                        <strong className={`font-bold ${isUser ? "text-[#171207]" : "text-white"}`}>
                            {children}
                        </strong>
                    ),
                    em: ({ children }) => (
                        <em className={`italic ${isUser ? "text-inherit" : "text-zinc-300"}`}>
                            {children}
                        </em>
                    ),
                    hr: () => (
                        <hr className={`my-3.5 border-t ${isUser ? "border-black/20" : "border-white/15"}`} />
                    ),
                    blockquote: ({ children }) => (
                        <blockquote
                            className={`my-2.5 border-l-2 pl-3.5 italic ${
                                isUser
                                    ? "border-black/30 text-zinc-900"
                                    : "border-amber-500/60 text-zinc-400"
                            }`}
                        >
                            {children}
                        </blockquote>
                    ),
                    code: ({ children, className }) => {
                        const isInline = !className;
                        if (isInline) {
                            return (
                                <code
                                    className={`rounded px-1.5 py-0.5 font-mono text-[11px] ${
                                        isUser
                                            ? "bg-black/15 text-zinc-950 font-semibold"
                                            : "bg-black/40 text-amber-300 border border-white/10"
                                    }`}
                                >
                                    {children}
                                </code>
                            );
                        }
                        return (
                            <code className="font-mono text-xs text-zinc-200">
                                {children}
                            </code>
                        );
                    },
                    pre: ({ children }) => (
                        <pre
                            className={`my-2.5 overflow-x-auto rounded-xl p-3 text-xs font-mono ${
                                isUser
                                    ? "bg-black/20 text-zinc-950"
                                    : "bg-black/60 text-zinc-200 border border-white/10"
                            }`}
                        >
                            {children}
                        </pre>
                    ),
                    table: ({ children }) => (
                        <div className="my-3 overflow-x-auto">
                            <table className="w-full border-collapse text-left text-xs">
                                {children}
                            </table>
                        </div>
                    ),
                    th: ({ children }) => (
                        <th
                            className={`border-b px-3 py-2 font-semibold ${
                                isUser
                                    ? "border-black/20 bg-black/10 text-zinc-950"
                                    : "border-white/15 bg-white/[0.05] text-white"
                            }`}
                        >
                            {children}
                        </th>
                    ),
                    td: ({ children }) => (
                        <td
                            className={`border-b px-3 py-1.5 ${
                                isUser
                                    ? "border-black/10 text-zinc-900"
                                    : "border-white/10 text-zinc-300"
                            }`}
                        >
                            {children}
                        </td>
                    ),
                    a: ({ href, children }) => (
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`underline underline-offset-2 transition ${
                                isUser
                                    ? "text-zinc-950 hover:text-black font-semibold"
                                    : "text-amber-400 hover:text-amber-300"
                            }`}
                        >
                            {children}
                        </a>
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
