"use client";

import React, { useState, useEffect } from "react";
import { apiRequest, clearTokens, User } from "../lib/api";
import { Navbar } from "../components/Navbar";
import { Sidebar, NavTab } from "../components/Sidebar";
import { AuthModal } from "../components/AuthModal";
import { ChatView } from "../components/ChatView";
import { DocumentsView } from "../components/DocumentsView";
import { TicketsView } from "../components/TicketsView";
import { AnalyticsView } from "../components/AnalyticsView";
import { SettingsView } from "../components/SettingsView";
import { Sparkles, Bot, Shield, FileText, Ticket } from "lucide-react";

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<NavTab>("chat");
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [documentCount, setDocumentCount] = useState<number>(0);
  const [openTicketCount, setOpenTicketCount] = useState<number>(0);

  useEffect(() => {
    checkCurrentUser();
    checkHealth();
  }, []);

  useEffect(() => {
    if (user) {
      refreshCounts();
    }
  }, [user, activeTab]);

  const checkCurrentUser = async () => {
    try {
      const profile = await apiRequest<User>("/auth/me");
      setUser(profile);
    } catch {
      setUser(null);
    }
  };

  const checkHealth = async () => {
    try {
      const health = await apiRequest<any>("/health");
      setSystemHealth(health);
    } catch (err) {
      console.error("Health check failed:", err);
    }
  };

  const refreshCounts = async () => {
    try {
      const [docs, tickets] = await Promise.all([
        apiRequest<any[]>("/documents"),
        apiRequest<any[]>("/tickets?status=open"),
      ]);
      setDocumentCount(docs.length);
      setOpenTicketCount(tickets.length);
    } catch {
      // ignore
    }
  };

  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem("refresh_token") || "";
      await apiRequest("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // ignore
    }
    clearTokens();
    setUser(null);
    setShowAuthModal(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        user={user}
        onLogout={handleLogout}
        onOpenAuth={() => setShowAuthModal(true)}
        systemHealth={systemHealth}
      />

      {/* Main Layout Body */}
      <div className="flex-1 flex overflow-hidden">
        {user ? (
          <>
            <Sidebar
              activeTab={activeTab}
              onTabChange={setActiveTab}
              openTicketCount={openTicketCount}
              documentCount={documentCount}
            />

            <main className="flex-1 overflow-y-auto bg-slate-950/40">
              {activeTab === "chat" && <ChatView onTicketCreated={refreshCounts} />}
              {activeTab === "documents" && (
                <DocumentsView onDocumentsUpdated={refreshCounts} />
              )}
              {activeTab === "tickets" && (
                <TicketsView onTicketStatusChanged={refreshCounts} />
              )}
              {activeTab === "analytics" && <AnalyticsView />}
              {activeTab === "settings" && (
                <SettingsView user={user} systemHealth={systemHealth} />
              )}
            </main>
          </>
        ) : (
          /* Unauthenticated Landing / Call to Action */
          <div className="flex-1 flex items-center justify-center p-6 bg-gradient-to-b from-slate-900/50 to-slate-950">
            <div className="max-w-xl text-center space-y-6 p-8 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-2xl shadow-indigo-950/40">
              <div className="h-16 w-16 rounded-3xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 mx-auto shadow-xl shadow-indigo-500/25">
                <div className="h-full w-full bg-slate-950 rounded-[22px] flex items-center justify-center">
                  <Bot className="h-8 w-8 text-indigo-400" />
                </div>
              </div>

              <div className="space-y-2">
                <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
                  AI Customer Support SaaS
                </h1>
                <p className="text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
                  Enterprise-grade multi-tenant customer support platform powered 100% locally by{" "}
                  <strong className="text-indigo-400 font-semibold">Ollama Llama 3.1</strong>,{" "}
                  <strong className="text-cyan-400 font-semibold">nomic-embed-text</strong>, and{" "}
                  <strong className="text-purple-400 font-semibold">ChromaDB</strong>.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3 text-left py-2">
                <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80">
                  <Shield className="h-4 w-4 text-indigo-400 mb-1.5" />
                  <div className="text-xs font-bold text-white">Multi-Tenant</div>
                  <div className="text-[10px] text-slate-400">Strict data isolation</div>
                </div>
                <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80">
                  <FileText className="h-4 w-4 text-cyan-400 mb-1.5" />
                  <div className="text-xs font-bold text-white">RAG Ingestion</div>
                  <div className="text-[10px] text-slate-400">PDF, DOCX & TXT</div>
                </div>
                <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80">
                  <Ticket className="h-4 w-4 text-amber-400 mb-1.5" />
                  <div className="text-xs font-bold text-white">Auto-Escalate</div>
                  <div className="text-[10px] text-slate-400">Integrated Ticketing</div>
                </div>
              </div>

              <button
                onClick={() => setShowAuthModal(true)}
                className="w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold text-sm shadow-xl shadow-indigo-600/30 transition-all flex items-center justify-center gap-2"
              >
                <Sparkles className="h-4 w-4" /> Get Started / Sign In
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Authentication Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={(profile) => {
          setUser(profile);
          setShowAuthModal(false);
        }}
      />
    </div>
  );
}
