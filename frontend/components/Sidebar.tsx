"use client";

import React from "react";
import {
  MessageSquare,
  FileText,
  Ticket,
  BarChart3,
  Settings,
  Sparkles,
  Zap,
} from "lucide-react";

export type NavTab = "chat" | "documents" | "tickets" | "analytics" | "settings";

interface SidebarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  openTicketCount?: number;
  documentCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  openTicketCount = 0,
  documentCount = 0,
}) => {
  const navItems = [
    {
      id: "chat" as NavTab,
      label: "AI Support Agent",
      icon: MessageSquare,
      badge: "Llama 3.1",
      badgeColor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    },
    {
      id: "documents" as NavTab,
      label: "Knowledge Base",
      icon: FileText,
      count: documentCount,
    },
    {
      id: "tickets" as NavTab,
      label: "Support Tickets",
      icon: Ticket,
      count: openTicketCount,
      countColor: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    },
    {
      id: "analytics" as NavTab,
      label: "Tenant Analytics",
      icon: BarChart3,
    },
    {
      id: "settings" as NavTab,
      label: "Settings & Plans",
      icon: Settings,
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col justify-between p-4 shrink-0">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`h-4 w-4 ${
                    isActive ? "text-indigo-400" : "text-slate-400"
                  }`}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${item.badgeColor}`}
                >
                  {item.badge}
                </span>
              )}
              {item.count !== undefined && item.count > 0 && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full border font-bold ${
                    item.countColor || "bg-slate-800 text-slate-300 border-slate-700"
                  }`}
                >
                  {item.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* RAG Engine Info Card */}
      <div className="p-3.5 rounded-2xl bg-gradient-to-br from-slate-800/90 to-slate-900/90 border border-slate-700/60 shadow-lg">
        <div className="flex items-center gap-2 mb-2">
          <div className="h-6 w-6 rounded-lg bg-indigo-500/20 flex items-center justify-center">
            <Zap className="h-3.5 w-3.5 text-indigo-400" />
          </div>
          <span className="text-xs font-bold text-white">Local RAG Engine</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed mb-2.5">
          Queries strictly search your tenant knowledge base using nomic embeddings and ChromaDB.
        </p>
        <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-800">
          <span>Privacy: Zero Leakage</span>
          <span className="text-emerald-400 font-semibold">100% Local AI</span>
        </div>
      </div>
    </aside>
  );
};
