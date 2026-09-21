"use client";

import React, { useState, useEffect } from "react";
import { apiRequest, AnalyticsDashboard } from "../lib/api";
import {
  BarChart3,
  MessageSquare,
  Ticket,
  Zap,
  CheckCircle2,
  FileText,
  Clock,
  TrendingUp,
  RefreshCw,
  Layers,
} from "lucide-react";

export const AnalyticsView: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const res = await apiRequest<AnalyticsDashboard>("/analytics/dashboard");
      setData(res);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!data && loading) {
    return (
      <div className="p-12 text-center text-slate-400 text-sm">
        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-400" />
        Calculating tenant analytics...
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Tenant Analytics & AI Performance
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time insights on support volume, automated AI resolution rates, and knowledge base utilization.
          </p>
        </div>

        <button
          onClick={loadAnalytics}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-300 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          Refresh Stats
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Conversations
            </span>
            <div className="h-8 w-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <MessageSquare className="h-4 w-4 text-indigo-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {data?.total_conversations || 0}
          </div>
          <div className="text-xs text-indigo-400 font-medium mt-1">
            Avg {data?.avg_messages_per_conversation || 0} msgs / session
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Total Messages
            </span>
            <div className="h-8 w-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-cyan-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {data?.total_messages || 0}
          </div>
          <div className="text-xs text-cyan-400 font-medium mt-1">
            Customer inquiries & AI responses
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Resolution Rate
            </span>
            <div className="h-8 w-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {data?.resolution_rate_pct || 100}%
          </div>
          <div className="text-xs text-emerald-400 font-medium mt-1">
            {data?.resolved_tickets || 0} of {data?.total_tickets || 0} tickets resolved
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Avg AI Latency
            </span>
            <div className="h-8 w-8 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <Zap className="h-4 w-4 text-amber-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {data?.avg_ai_latency_ms || 450}ms
          </div>
          <div className="text-xs text-amber-400 font-medium mt-1">
            Local Ollama Llama 3.1 generation
          </div>
        </div>
      </div>

      {/* 7-Day Activity Trend Bar Chart */}
      <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">
              7-Day Support Activity Trend
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Daily breakdown of conversations, messages, and escalated tickets.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-semibold">
            <div className="flex items-center gap-1.5 text-indigo-400">
              <span className="h-2.5 w-2.5 rounded-sm bg-indigo-500" /> Conversations
            </div>
            <div className="flex items-center gap-1.5 text-cyan-400">
              <span className="h-2.5 w-2.5 rounded-sm bg-cyan-400" /> Messages
            </div>
            <div className="flex items-center gap-1.5 text-amber-400">
              <span className="h-2.5 w-2.5 rounded-sm bg-amber-400" /> Tickets
            </div>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-3 h-48 items-end pt-8 pb-2 border-b border-slate-800">
          {data?.activity_trend.map((point, idx) => {
            const maxVal = Math.max(
              ...data.activity_trend.map((p) => Math.max(p.conversations, p.messages, p.tickets)),
              4
            );
            const convHeight = Math.max((point.conversations / maxVal) * 100, 8);
            const msgHeight = Math.max((point.messages / maxVal) * 100, 8);
            const ticketHeight = Math.max((point.tickets / maxVal) * 100, 8);

            return (
              <div key={idx} className="flex flex-col items-center gap-2 h-full justify-end">
                <div className="w-full flex items-end justify-center gap-1.5 h-full">
                  <div
                    style={{ height: `${convHeight}%` }}
                    className="w-3 rounded-t-md bg-indigo-500 transition-all"
                    title={`${point.conversations} conversations`}
                  />
                  <div
                    style={{ height: `${msgHeight}%` }}
                    className="w-3 rounded-t-md bg-cyan-400 transition-all"
                    title={`${point.messages} messages`}
                  />
                  <div
                    style={{ height: `${ticketHeight}%` }}
                    className="w-3 rounded-t-md bg-amber-400 transition-all"
                    title={`${point.tickets} tickets`}
                  />
                </div>
                <span className="text-[11px] font-semibold text-slate-400">{point.date}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Ticket Status Breakdown & Knowledge Base Usage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Ticket Breakdown */}
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <Ticket className="h-4 w-4 text-indigo-400" /> Ticket Status Distribution
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-amber-400">Open Tickets</span>
                <span className="text-white font-mono">{data?.ticket_status_breakdown.open || 0}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  style={{
                    width: `${
                      data?.total_tickets ? ((data.ticket_status_breakdown.open / data.total_tickets) * 100) : 0
                    }%`,
                  }}
                  className="h-full bg-amber-400 rounded-full"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-indigo-400">In Progress</span>
                <span className="text-white font-mono">{data?.ticket_status_breakdown.in_progress || 0}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  style={{
                    width: `${
                      data?.total_tickets ? ((data.ticket_status_breakdown.in_progress / data.total_tickets) * 100) : 0
                    }%`,
                  }}
                  className="h-full bg-indigo-500 rounded-full"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-emerald-400">Resolved</span>
                <span className="text-white font-mono">{data?.ticket_status_breakdown.resolved || 0}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  style={{
                    width: `${
                      data?.total_tickets ? ((data.ticket_status_breakdown.resolved / data.total_tickets) * 100) : 0
                    }%`,
                  }}
                  className="h-full bg-emerald-400 rounded-full"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Knowledge Base Chunks */}
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <Layers className="h-4 w-4 text-cyan-400" /> Vector Index Summary
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-slate-400 font-semibold mb-1">Total Documents</div>
              <div className="text-2xl font-bold text-white font-mono">
                {data?.total_documents || 0}
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-slate-400 font-semibold mb-1">ChromaDB Chunks</div>
              <div className="text-2xl font-bold text-indigo-400 font-mono">
                {data?.total_document_chunks || 0}
              </div>
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            All document chunks are indexed with 768-dimensional embeddings generated locally via <code className="text-indigo-300">nomic-embed-text</code>.
          </p>
        </div>
      </div>
    </div>
  );
};
