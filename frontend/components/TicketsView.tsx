"use client";

import React, { useState, useEffect } from "react";
import { apiRequest, Ticket } from "../lib/api";
import {
  Ticket as TicketIcon,
  Plus,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Filter,
  RefreshCw,
  MessageSquare,
  ShieldAlert,
} from "lucide-react";

interface TicketsViewProps {
  onTicketStatusChanged?: () => void;
}

export const TicketsView: React.FC<TicketsViewProps> = ({ onTicketStatusChanged }) => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [showCreateModal, setShowCreateModal] = useState(false);

  // New ticket state
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newPriority, setNewPriority] = useState("medium");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadTickets();
  }, [statusFilter, priorityFilter]);

  const loadTickets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (priorityFilter !== "all") params.append("priority", priorityFilter);

      const queryStr = params.toString() ? `?${params.toString()}` : "";
      const data = await apiRequest<Ticket[]>(`/tickets${queryStr}`);
      setTickets(data);
      onTicketStatusChanged?.();
    } catch (err) {
      console.error("Failed to load tickets:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (ticketId: number, newStatus: string) => {
    try {
      await apiRequest<Ticket>(`/tickets/${ticketId}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: newStatus,
          is_resolved: newStatus === "resolved" || newStatus === "closed",
        }),
      });
      await loadTickets();
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDescription.trim()) return;

    setCreating(true);
    try {
      await apiRequest<Ticket>("/tickets", {
        method: "POST",
        body: JSON.stringify({
          title: newTitle,
          description: newDescription,
          priority: newPriority,
        }),
      });
      setShowCreateModal(false);
      setNewTitle("");
      setNewDescription("");
      setNewPriority("medium");
      await loadTickets();
    } catch (err: any) {
      alert(`Failed to create ticket: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const priorityBadge = (priority: string) => {
    switch (priority) {
      case "urgent":
        return "bg-rose-500/20 text-rose-300 border-rose-500/30";
      case "high":
        return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "medium":
        return "bg-indigo-500/20 text-indigo-300 border-indigo-500/30";
      default:
        return "bg-slate-700 text-slate-300 border-slate-600";
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Support Tickets & Escalations
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Track inquiries escalated from the AI Chatbot or created directly for human SME support agents.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all"
        >
          <Plus className="h-4 w-4" /> Create Support Ticket
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-300">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300">Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        <button
          onClick={loadTickets}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          title="Refresh tickets"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Tickets List */}
      <div className="space-y-3">
        {tickets.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm bg-slate-900/40 rounded-3xl border border-slate-800">
            No support tickets match the selected filters.
          </div>
        ) : (
          tickets.map((ticket) => (
            <div
              key={ticket.id}
              className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 max-w-2xl">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs text-indigo-400 font-bold">
                    #{ticket.id}
                  </span>
                  <span
                    className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${priorityBadge(
                      ticket.priority
                    )}`}
                  >
                    {ticket.priority}
                  </span>
                  {ticket.conversation_id && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
                      <MessageSquare className="h-3 w-3 text-indigo-400" /> Chat #{ticket.conversation_id}
                    </span>
                  )}
                  <span className="text-xs text-slate-400 font-mono">
                    {ticket.created_at ? new Date(ticket.created_at).toLocaleString() : "-"}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white tracking-tight">
                  {ticket.title}
                </h3>
                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed whitespace-pre-line">
                  {ticket.description}
                </p>
              </div>

              {/* Status Selector */}
              <div className="flex items-center gap-3 shrink-0">
                <select
                  value={ticket.status}
                  onChange={(e) => handleStatusChange(ticket.id, e.target.value)}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-xl border focus:outline-none transition-all ${
                    ticket.status === "resolved" || ticket.status === "closed"
                      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                      : ticket.status === "in_progress"
                      ? "bg-indigo-500/15 text-indigo-300 border-indigo-500/30"
                      : "bg-amber-500/15 text-amber-300 border-amber-500/30"
                  }`}
                >
                  <option value="open">Status: Open</option>
                  <option value="in_progress">Status: In Progress</option>
                  <option value="resolved">Status: Resolved</option>
                  <option value="closed">Status: Closed</option>
                </select>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-4">Create New Support Ticket</h2>
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Ticket Subject
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Issue configuring webhook notifications"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Priority Level
                </label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                  <option value="urgent">Urgent Priority</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Detailed Description
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Provide customer context, observed behavior, and steps..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
                >
                  {creating ? "Submitting..." : "Submit Ticket"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
