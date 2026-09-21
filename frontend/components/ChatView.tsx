"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  apiRequest,
  Conversation,
  Message,
  Citation,
  Ticket,
} from "../lib/api";
import {
  Bot,
  User as UserIcon,
  Send,
  Plus,
  Trash2,
  Ticket as TicketIcon,
  Sparkles,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Zap,
  CheckCircle2,
} from "lucide-react";

interface ChatViewProps {
  onTicketCreated?: () => void;
}

export const ChatView: React.FC<ChatViewProps> = ({ onTicketCreated }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState<Record<number, boolean>>({});
  const [escalating, setEscalating] = useState(false);
  const [escalateSuccess, setEscalateSuccess] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isInitialLoadRef = useRef(false);

  useEffect(() => {
    if (!isInitialLoadRef.current) {
      isInitialLoadRef.current = true;
      loadConversations();
    }
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      loadConversationMessages(activeConversationId);
    } else {
      setMessages([]);
    }
  }, [activeConversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const loadConversations = async (targetActiveId?: number) => {
    try {
      const data = await apiRequest<Conversation[]>("/conversations");
      setConversations(data);
      if (targetActiveId !== undefined) {
        if (targetActiveId !== null) {
          setActiveConversationId(targetActiveId);
        }
      } else {
        setActiveConversationId((currentActiveId) => {
          if (currentActiveId && data.some((c) => c.id === currentActiveId)) {
            return currentActiveId;
          }
          return data.length > 0 ? data[0].id : null;
        });
      }
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  const loadConversationMessages = async (convId: number) => {
    try {
      const data = await apiRequest<Conversation>(`/conversations/${convId}`);
      setMessages(data.messages || []);
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  const handleStartNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInputValue("");
    setEscalateSuccess(null);
  };

  const handleDeleteConversation = async (convId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiRequest(`/conversations/${convId}`, { method: "DELETE" });
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        handleStartNewConversation();
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputValue;
    if (!textToSend.trim() || loading) return;

    setInputValue("");
    setLoading(true);
    setEscalateSuccess(null);

    // Optimistic user message
    const tempUserMsg: Message = {
      id: Date.now(),
      conversation_id: activeConversationId || 0,
      tenant_id: 0,
      role: "user",
      content: textToSend,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await apiRequest<{
        conversation_id: number;
        user_message: Message;
        assistant_message: Message;
        citations: Citation[];
        suggest_escalation: boolean;
        latency_ms: number;
      }>("/chat", {
        method: "POST",
        body: JSON.stringify({
          conversation_id: activeConversationId,
          message: textToSend,
        }),
      });

      const isNewThread = !activeConversationId;
      if (isNewThread) {
        setActiveConversationId(res.conversation_id);
        await loadConversations(res.conversation_id);
      }

      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMsg.id),
        res.user_message,
        res.assistant_message,
      ]);
    } catch (err: any) {
      console.error("Chat error:", err);
      const errorMsg: Message = {
        id: Date.now() + 1,
        conversation_id: activeConversationId || 0,
        tenant_id: 0,
        role: "assistant",
        content: `Error: ${err.message || "Failed to reach local AI service."}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleEscalateToTicket = async () => {
    if (!activeConversationId) return;
    setEscalating(true);
    setEscalateSuccess(null);

    try {
      const ticket = await apiRequest<Ticket>("/tickets/escalate-from-conversation", {
        method: "POST",
        body: JSON.stringify({
          conversation_id: activeConversationId,
          priority: "high",
        }),
      });

      setEscalateSuccess(`Support Ticket #${ticket.id} created and dispatched to human agents!`);
      onTicketCreated?.();
    } catch (err: any) {
      alert(`Escalation failed: ${err.message}`);
    } finally {
      setEscalating(false);
    }
  };

  const toggleCitation = (msgId: number) => {
    setExpandedCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const parseCitations = (citationsStr?: string): Citation[] => {
    if (!citationsStr) return [];
    try {
      return JSON.parse(citationsStr);
    } catch {
      return [];
    }
  };

  const starterPrompts = [
    "What is our customer refund and cancellation policy?",
    "How does a customer upgrade their subscription plan?",
    "What are our technical support hours and response SLAs?",
    "How are customer data and encryption handled?",
  ];

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden">
      {/* Conversation History Sidebar */}
      <div className="w-72 border-r border-slate-800 bg-slate-900/70 flex flex-col shrink-0">
        <div className="p-3.5 border-b border-slate-800">
          <button
            onClick={handleStartNewConversation}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Plus className="h-4 w-4" /> New Conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Recent Inquiries
          </div>
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-400">
              No conversations yet. Start a new chat to test the AI support agent.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = activeConversationId === conv.id;
              const formattedTime = conv.updated_at
                ? new Date(conv.updated_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "Active";

              return (
                <div
                  key={conv.id}
                  onClick={() => setActiveConversationId(conv.id)}
                  className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all ${
                    isActive
                      ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <p className="text-xs font-semibold truncate">{conv.title}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      {formattedTime}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-400 rounded-md transition-opacity"
                    title="Delete thread"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col bg-slate-950/60 overflow-hidden">
        {/* Chat Header */}
        <div className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-900/40 backdrop-blur-md">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Bot className="h-4 w-4 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white">
                {conversations.find((c) => c.id === activeConversationId)?.title ||
                  "New AI Support Session"}
              </h2>
              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                <span className="text-emerald-400">● Live Ollama Llama 3.1</span>
                <span>•</span>
                <span>Tenant Isolation Enforced</span>
              </div>
            </div>
          </div>

          {activeConversationId && (
            <button
              onClick={handleEscalateToTicket}
              disabled={escalating}
              className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-semibold transition-all disabled:opacity-50"
            >
              <TicketIcon className="h-3.5 w-3.5" />
              {escalating ? "Escalating..." : "Escalate to Support Ticket"}
            </button>
          )}
        </div>

        {escalateSuccess && (
          <div className="mx-6 mt-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{escalateSuccess}</span>
            </div>
            <button
              onClick={() => setEscalateSuccess(null)}
              className="text-emerald-400 hover:text-white text-xs font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center max-w-lg mx-auto text-center">
              <div className="h-16 w-16 rounded-3xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-xl shadow-indigo-500/20 mb-4">
                <div className="h-full w-full bg-slate-950 rounded-[22px] flex items-center justify-center">
                  <Bot className="h-8 w-8 text-indigo-400" />
                </div>
              </div>
              <h3 className="text-lg font-bold text-white mb-2">
                Ask your SME Knowledge Base
              </h3>
              <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                The local support agent answers questions using only your company documents with zero hallucinations and source citations.
              </p>

              <div className="w-full space-y-2 text-left">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1">
                  Suggested Prompts:
                </div>
                {starterPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(prompt)}
                    className="w-full p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/30 text-xs text-slate-300 text-left transition-all flex items-center justify-between group"
                  >
                    <span>{prompt}</span>
                    <Sparkles className="h-3.5 w-3.5 text-slate-400 group-hover:text-indigo-400" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === "user";
              const citations = parseCitations(msg.citations);
              const isExpanded = expandedCitations[msg.id] ?? false;

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
                >
                  {!isUser && (
                    <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 p-0.5 shrink-0 shadow-md">
                      <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                        <Bot className="h-4 w-4 text-indigo-400" />
                      </div>
                    </div>
                  )}

                  <div
                    className={`max-w-2xl rounded-2xl p-4 space-y-2 shadow-md ${
                      isUser
                        ? "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-tr-none"
                        : "bg-slate-900/90 border border-slate-800 text-slate-200 rounded-tl-none"
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap leading-relaxed">
                      {msg.content}
                    </div>

                    {/* Metadata footer */}
                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-white/5">
                      <span>
                        {msg.created_at
                          ? new Date(msg.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : ""}
                      </span>
                      {!isUser && msg.latency_ms !== undefined && msg.latency_ms > 0 && (
                        <span className="flex items-center gap-1 text-slate-400">
                          <Zap className="h-3 w-3 text-amber-400" /> {msg.latency_ms}ms
                        </span>
                      )}
                    </div>

                    {/* Source Citations Accordion */}
                    {!isUser && citations.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-800">
                        <button
                          onClick={() => toggleCitation(msg.id)}
                          className="flex items-center justify-between w-full py-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                        >
                          <span className="flex items-center gap-1.5">
                            <BookOpen className="h-3.5 w-3.5" />
                            {citations.length} Verified Source {citations.length === 1 ? "Citation" : "Citations"}
                          </span>
                          {isExpanded ? (
                            <ChevronUp className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5" />
                          )}
                        </button>

                        {isExpanded && (
                          <div className="mt-2 space-y-2">
                            {citations.map((c, idx) => (
                              <div
                                key={idx}
                                className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs space-y-1"
                              >
                                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
                                  <span className="truncate text-indigo-300">📄 {c.filename}</span>
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                                    Section {c.chunk_index + 1}
                                  </span>
                                </div>
                                <p className="text-[11px] text-slate-400 italic bg-slate-900/50 p-1.5 rounded border border-slate-800/60">
                                  "{c.snippet}"
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="h-8 w-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-slate-300 font-bold text-xs">
                      <UserIcon className="h-4 w-4 text-slate-400" />
                    </div>
                  )}
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 p-0.5 shrink-0 shadow-md">
                <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                  <Bot className="h-4 w-4 text-indigo-400 animate-pulse" />
                </div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-xs text-slate-400 flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-indigo-500 animate-ping" />
                <span>Searching knowledge base & synthesizing with Llama 3.1...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/70 backdrop-blur-md">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2 max-w-4xl mx-auto"
          >
            <input
              type="text"
              placeholder="Ask the AI customer support agent a question..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={loading}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !inputValue.trim()}
              className="h-11 px-5 rounded-2xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all disabled:opacity-40"
            >
              <Send className="h-4 w-4" /> Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
