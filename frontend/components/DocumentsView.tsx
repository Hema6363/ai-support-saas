"use client";

import React, { useState, useEffect } from "react";
import { apiRequest, DocumentItem } from "../lib/api";
import {
  Upload,
  FileText,
  Trash2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  HardDrive,
  FileSpreadsheet,
  FileCode,
  Layers,
} from "lucide-react";

interface DocumentsViewProps {
  onDocumentsUpdated?: () => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({ onDocumentsUpdated }) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<DocumentItem[]>("/documents");
      setDocuments(data);
      onDocumentsUpdated?.();
    } catch (err: any) {
      setError(err.message || "Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setUploadProgress("Uploading file & extracting text...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploadProgress("Chunking & generating vector embeddings with nomic-embed...");
      const newDoc = await apiRequest<DocumentItem>("/documents/upload", {
        method: "POST",
        body: formData,
      });

      setUploadProgress("Indexing vectors into ChromaDB...");
      await loadDocuments();
      setUploadProgress(null);
    } catch (err: any) {
      setError(err.message || "Document upload and indexing failed.");
    } finally {
      setUploading(false);
      setUploadProgress(null);
      e.target.value = "";
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm("Are you sure you want to delete this document and its vector embeddings?")) {
      return;
    }
    try {
      await apiRequest(`/documents/${docId}`, { method: "DELETE" });
      await loadDocuments();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleReindex = async (docId: number) => {
    try {
      await apiRequest(`/documents/${docId}/reindex`, { method: "POST" });
      await loadDocuments();
    } catch (err: any) {
      alert(`Re-indexing failed: ${err.message}`);
    }
  };

  const handleUploadSamplePolicy = async () => {
    setUploading(true);
    setUploadProgress("Creating & indexing Sample SME SaaS Policy document...");
    setError(null);

    const sampleContent = `
# Acme Cloud SaaS Customer Support & Policy Manual

1. Subscription Plans & Pricing
- Starter Plan: Free forever, up to 5 documents, 500 AI queries/month.
- Pro Plan: $49/month, up to 50 documents, 5,000 AI queries/month, priority support.
- Enterprise Plan: $199/month, unlimited documents, 50,000 AI queries/month, custom SLA, dedicated support.

2. Refund and Cancellation Policy
- All paid monthly subscriptions come with a 14-day no-questions-asked money-back guarantee.
- Annual subscriptions can be cancelled within 30 days for a full refund.
- To request a refund, customers must submit a support ticket with invoice ID.

3. Technical Support Hours and Response Times
- Standard Support is available Monday to Friday from 9:00 AM to 6:00 PM EST.
- Enterprise Priority Support is monitored 24/7 with a 1-hour critical response SLA.
- Support tickets are escalated to human engineering specialists when automated resolution is incomplete.

4. Data Privacy & Security
- All customer documents are stored in tenant-isolated PostgreSQL and ChromaDB vector spaces.
- Data is encrypted in transit (TLS 1.3) and at rest (AES-256).
- Customer data is NEVER shared between tenants and is never used for public model training.
`.trim();

    const blob = new Blob([sampleContent], { type: "text/plain" });
    const file = new File([blob], "acme_saas_support_policy.txt", { type: "text/plain" });

    const formData = new FormData();
    formData.append("file", file);

    try {
      await apiRequest<DocumentItem>("/documents/upload", {
        method: "POST",
        body: formData,
      });
      await loadDocuments();
    } catch (err: any) {
      setError(err.message || "Failed to upload sample policy.");
    } finally {
      setUploading(false);
      setUploadProgress(null);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Knowledge Base & Ingestion
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Upload PDF, DOCX, or TXT documents. Content is parsed, embedded with nomic-embed, and indexed in ChromaDB.
          </p>
        </div>

        <button
          onClick={handleUploadSamplePolicy}
          disabled={uploading}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-indigo-300 text-xs font-semibold shadow-md transition-all disabled:opacity-50"
        >
          <Sparkles className="h-4 w-4 text-indigo-400" />
          Load Sample SME Policy
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Dropzone */}
      <div className="relative group border-2 border-dashed border-slate-700/80 hover:border-indigo-500/50 rounded-3xl p-8 text-center bg-slate-900/40 hover:bg-slate-900/70 transition-all">
        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt,.md,.csv,.json"
          onChange={handleFileUpload}
          disabled={uploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        />
        <div className="flex flex-col items-center pointer-events-none">
          <div className="h-14 w-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <Upload className="h-6 w-6 text-indigo-400" />
          </div>
          <h3 className="text-base font-semibold text-white">
            {uploading ? uploadProgress : "Upload Support & Knowledge Documents"}
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm">
            Drag & drop or click to browse. Supports PDF, Word (.docx), Markdown, Plain Text. Max 25 MB.
          </p>
        </div>
      </div>

      {/* Documents Table */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-400" />
            <h2 className="text-sm font-bold text-white">
              Indexed Documents ({documents.length})
            </h2>
          </div>
          <button
            onClick={loadDocuments}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            title="Refresh list"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No documents uploaded yet. Upload a company manual or click "Load Sample SME Policy" to begin.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">Document</th>
                  <th className="px-6 py-3.5">Size</th>
                  <th className="px-6 py-3.5">Vector Chunks</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Uploaded</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
                          <FileText className="h-4 w-4 text-indigo-400" />
                        </div>
                        <div>
                          <div className="font-semibold text-white text-sm truncate max-w-xs">
                            {doc.original_filename}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            Tenant #{doc.tenant_id} • ID #{doc.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-300 font-mono">
                      {formatBytes(doc.file_size)}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-indigo-300 font-semibold font-mono text-xs">
                        {doc.chunk_count} chunks
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                          doc.status === "PROCESSED"
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : doc.status === "PROCESSING"
                            ? "bg-amber-500/15 text-amber-400 border border-amber-500/30 animate-pulse"
                            : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                        }`}
                      >
                        {doc.status === "PROCESSED" && <CheckCircle2 className="h-3 w-3" />}
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-400 font-mono">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "-"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleReindex(doc.id)}
                          className="p-1.5 text-slate-400 hover:text-indigo-300 hover:bg-slate-800 rounded-lg transition-colors"
                          title="Re-index document vectors"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                          title="Delete document and vector chunks"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
