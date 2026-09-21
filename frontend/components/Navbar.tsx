"use client";

import React from "react";
import { User } from "../lib/api";
import { Bot, CheckCircle2, LogOut, Shield, Sparkles } from "lucide-react";

interface NavbarProps {
  user: User | null;
  onLogout: () => void;
  onOpenAuth: () => void;
  systemHealth: { database: string; chromadb: string; ollama: { status: string } } | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onLogout,
  onOpenAuth,
  systemHealth,
}) => {
  const isHealthy =
    systemHealth?.database === "ok" &&
    systemHealth?.chromadb === "ok" &&
    systemHealth?.ollama?.status === "healthy";

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
          <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
            <Bot className="h-5 w-5 text-indigo-400" />
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg text-white tracking-tight">AutoSupport</span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Local AI RAG
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            SME Enterprise Customer Support Platform
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* System Health Indicator */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
          <span
            className={`h-2 w-2 rounded-full ${
              isHealthy ? "bg-emerald-400 shadow-[0_0_8px_#34d399]" : "bg-amber-400 animate-pulse"
            }`}
          />
          <span className="text-slate-300 font-medium">
            {isHealthy ? "Llama 3.1 & Chroma Ready" : "Checking AI Engines..."}
          </span>
        </div>

        {user ? (
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-semibold text-white">
                {user.full_name || user.email}
              </div>
              <div className="text-xs text-indigo-400 font-medium flex items-center justify-end gap-1">
                <Shield className="h-3 w-3" /> Tenant #{user.tenant_id} • {user.role.toUpperCase()}
              </div>
            </div>
            <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-sm text-white shadow-md">
              {(user.full_name || user.email)[0].toUpperCase()}
            </div>
            <button
              onClick={onLogout}
              title="Log out"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-sm font-semibold shadow-lg shadow-indigo-500/25 transition-all"
          >
            <Sparkles className="h-4 w-4" /> Sign In / Register
          </button>
        )}
      </div>
    </header>
  );
};
