import Link from "next/link";
import { listAnalyses } from "@/lib/api";
import { ArrowRight, Clock, CheckCircle2, FileText } from "lucide-react";

export default async function HistoryPage() {
  let analyses;
  try {
    analyses = await listAnalyses();
  } catch {
    return (
      <div className="text-center py-20 text-slate-500 text-sm">
        Could not connect to the API. Make sure the backend is running.
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">History</h1>
        <span className="text-sm text-slate-400">
          {analyses.length} {analyses.length === 1 ? "analysis" : "analyses"}
        </span>
      </div>

      <div className="space-y-3">
        {analyses.map((analysis) => (
          <Link
            key={analysis.id}
            href={`/transcripts/${analysis.id}`}
            className="flex items-start justify-between gap-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-5 hover:border-indigo-300 hover:shadow-md transition-all group"
          >
            <div className="space-y-2 flex-1 min-w-0">
              <p className="text-sm text-slate-800 line-clamp-2 leading-relaxed">
                {analysis.summary}
              </p>
              <div className="flex items-center gap-4 text-xs text-slate-400">
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
        ))}
      </div>
    </div>
  );
}
