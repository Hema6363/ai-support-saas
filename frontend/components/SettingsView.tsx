"use client";

import React, { useState, useEffect } from "react";
import { apiRequest, User, SubscriptionPlan, SubscriptionStatus } from "../lib/api";
import {
  Settings as SettingsIcon,
  Shield,
  Bot,
  Zap,
  CreditCard,
  CheckCircle2,
  Sparkles,
  Building2,
  Webhook,
  HardDrive,
  Check,
} from "lucide-react";

interface SettingsViewProps {
  user: User | null;
  systemHealth: any;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ user, systemHealth }) => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [upgradeLoading, setUpgradeLoading] = useState<string | null>(null);
  const [upgradeSuccess, setUpgradeSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadPlansAndSubscription();
  }, []);

  const loadPlansAndSubscription = async () => {
    try {
      const [plansData, subData] = await Promise.all([
        apiRequest<SubscriptionPlan[]>("/payments/plans"),
        apiRequest<SubscriptionStatus>("/payments/subscription-status"),
      ]);
      setPlans(plansData);
      setSubscription(subData);
    } catch (err) {
      console.error("Failed to load subscription info:", err);
    }
  };

  const handleUpgrade = async (planId: string) => {
    setUpgradeLoading(planId);
    setUpgradeSuccess(null);
    try {
      const res = await apiRequest<{ checkout_url: string; mode: string }>("/payments/create-checkout-session", {
        method: "POST",
        body: JSON.stringify({ plan_id: planId }),
      });

      if (res.mode === "sandbox_simulated") {
        setUpgradeSuccess(`Plan simulated upgrade to ${planId.toUpperCase()} activated!`);
        await loadPlansAndSubscription();
      } else if (res.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch (err: any) {
      alert(`Checkout failed: ${err.message}`);
    } finally {
      setUpgradeLoading(null);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Tenant Settings & Subscription Plans
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your company profile, inspect local AI engine configurations, and view subscription limits.
        </p>
      </div>

      {upgradeSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5" />
            <span>{upgradeSuccess}</span>
          </div>
          <button onClick={() => setUpgradeSuccess(null)} className="text-emerald-400 font-bold">
            ✕
          </button>
        </div>
      )}

      {/* Grid: Tenant Details & AI Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Tenant Profile */}
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
          <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <Building2 className="h-4 w-4 text-indigo-400" /> Multi-Tenant Workspace
          </h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Tenant Account ID:</span>
              <span className="font-mono text-white font-bold">#{user?.tenant_id || 1}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Admin Email:</span>
              <span className="text-white font-medium">{user?.email}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Current Plan:</span>
              <span className="text-indigo-400 font-bold uppercase">
                {subscription?.plan || "Starter"}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400">Tenant Isolation Status:</span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Active & Enforced
              </span>
            </div>
          </div>
        </div>

        {/* Local AI Engine Status */}
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
          <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <Bot className="h-4 w-4 text-cyan-400" /> Local AI Architecture
          </h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Chat Generation Model:</span>
              <span className="font-mono text-white font-semibold">llama3.1:8b (Local Ollama)</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Embedding Vector Model:</span>
              <span className="font-mono text-white font-semibold">nomic-embed-text (768-dim)</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Vector Database:</span>
              <span className="font-mono text-white font-semibold">ChromaDB (Isolated Collection)</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400">Cloud API Dependency:</span>
              <span className="text-emerald-400 font-semibold">0% (Completely Local)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Subscription Plans */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-indigo-400" /> SaaS Subscription Plans
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const isCurrent = (subscription?.plan || "starter") === plan.id;

            return (
              <div
                key={plan.id}
                className={`p-6 rounded-3xl border transition-all flex flex-col justify-between ${
                  isCurrent
                    ? "bg-slate-900 border-indigo-500 shadow-xl shadow-indigo-500/10"
                    : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-base font-bold text-white">{plan.name}</h3>
                    {isCurrent && (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        Current Plan
                      </span>
                    )}
                  </div>

                  <div className="mb-4">
                    <span className="text-3xl font-extrabold text-white font-mono">
                      ${plan.price_monthly}
                    </span>
                    <span className="text-xs text-slate-400 ml-1">/ month</span>
                  </div>

                  <ul className="space-y-2.5 mb-6 text-xs text-slate-300">
                    {plan.features.map((feat, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={isCurrent || upgradeLoading !== null}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-semibold transition-all ${
                    isCurrent
                      ? "bg-slate-800 text-slate-400 cursor-default"
                      : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25"
                  }`}
                >
                  {upgradeLoading === plan.id
                    ? "Processing..."
                    : isCurrent
                    ? "Active Subscription"
                    : `Upgrade to ${plan.name}`}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
