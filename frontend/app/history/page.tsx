"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { listAnalyses, deleteAnalysesBulk, type Analysis } from "@/lib/api";
import { ArrowRight, Clock, CheckCircle2, FileText, Trash2, Loader2 } from "lucide-react";

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<Analysis[] | null>(null);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await listAnalyses();
      setAnalyses(data);
      setSelected(new Set());
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (error) {
    return (
      <div className="text-center py-20 text-slate-500 text-sm">
        Could not connect to the API. Make sure the backend is running.
      </div>
    );
  }

  if (analyses === null) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="text-center py-20 space-y-4">
        <FileText className="w-10 h-10 text-slate-300 mx-auto" />
        <p className="text-slate-500 text-sm">No analyses yet.</p>
        <Link
          href="/"
          className="inline-block text-sm text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
        >
          Analyze your first transcript →
        </Link>
      </div>
    );
  }

  const allSelected = selected.size === analyses.length;

  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(analyses!.map((a) => a.id)));
  }

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleBulkDelete() {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} ${selected.size === 1 ? "analysis" : "analyses"}? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await deleteAnalysesBulk(Array.from(selected));
      await load();
    } catch {
      alert("Failed to delete. Please try again.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">History</h1>
        <span className="text-sm text-slate-400">
          {analyses.length} {analyses.length === 1 ? "analysis" : "analyses"}
        </span>
      </div>

      {/* Bulk action bar */}
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={toggleAll}
            className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
          />
          <span className="text-sm text-slate-600">
            {selected.size > 0 ? `${selected.size} selected` : "Select all"}
          </span>
        </label>

        {selected.size > 0 && (
          <button
            onClick={handleBulkDelete}
            disabled={deleting}
            className="ml-auto flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 disabled:opacity-50 transition-colors"
          >
            {deleting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
            Delete {selected.size} {selected.size === 1 ? "analysis" : "analyses"}
          </button>
        )}
      </div>

      <div className="space-y-3">
        {analyses.map((analysis) => (
          <div
            key={analysis.id}
            className={`flex items-center gap-3 bg-white rounded-2xl border shadow-sm p-5 transition-all ${
              selected.has(analysis.id)
                ? "border-indigo-300 bg-indigo-50/30"
                : "border-slate-200 hover:border-indigo-300 hover:shadow-md"
            }`}
          >
            <input
              type="checkbox"
              checked={selected.has(analysis.id)}
              onChange={() => toggleOne(analysis.id)}
              className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer shrink-0"
            />

            <Link
              href={`/transcripts/${analysis.id}`}
              className="flex items-start justify-between gap-4 flex-1 min-w-0 group"
            >
              <div className="space-y-2 flex-1 min-w-0">
                <p className="text-sm text-slate-800 line-clamp-2 leading-relaxed">
                  {analysis.summary}
                </p>
                <div className="flex items-center gap-4 text-xs text-slate-600">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(analysis.created_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {analysis.action_items.length}{" "}
                    {analysis.action_items.length === 1 ? "action item" : "action items"}
                  </span>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-500 transition-colors shrink-0 mt-1" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
