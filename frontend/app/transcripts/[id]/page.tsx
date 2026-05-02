import Link from "next/link";
import { notFound } from "next/navigation";
import { getAnalysis } from "@/lib/api";
import { ArrowLeft, CheckCircle2, Sparkles, Clock } from "lucide-react";
import DeleteButton from "@/components/DeleteButton";

export default async function TranscriptPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let analysis;
  try {
    analysis = await getAnalysis(id);
  } catch {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/history"
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to history
        </Link>
        <DeleteButton id={analysis.id} />
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-900">Analysis</h1>
        <div className="flex items-center gap-1.5 text-xs text-slate-600">
          <Clock className="w-3 h-3" />
          {new Date(analysis.created_at).toLocaleDateString("en-US", {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
          <Sparkles className="w-4 h-4 text-indigo-500" />
          Summary
        </div>
        <p className="text-slate-800 leading-relaxed text-sm">{analysis.summary}</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
          <CheckCircle2 className="w-4 h-4 text-indigo-500" />
          Action Items
          <span className="ml-auto bg-indigo-50 text-indigo-700 text-xs font-semibold px-2 py-0.5 rounded-full">
            {analysis.action_items.length}
          </span>
        </div>
        <ul className="space-y-3">
          {analysis.action_items.map((item, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="mt-0.5 w-6 h-6 rounded-full bg-indigo-50 text-indigo-600 text-xs font-semibold flex items-center justify-center shrink-0">
                {i + 1}
              </span>
              <span className="text-sm text-slate-700 leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <p className="text-xs text-slate-500 font-mono">ID: {analysis.id}</p>
    </div>
  );
}
