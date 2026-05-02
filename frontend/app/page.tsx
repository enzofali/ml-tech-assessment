"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { analyzeTranscript, analyzeTranscripts, type Analysis } from "@/lib/api";
import { Loader2, Upload, Sparkles, CheckCircle2, ArrowRight, X, Files } from "lucide-react";

interface BatchFile {
  name: string;
  content: string;
}

export default function AnalyzePage() {
  const [transcript, setTranscript] = useState("");
  const [batchFiles, setBatchFiles] = useState<BatchFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Analysis | null>(null);
  const [batchResults, setBatchResults] = useState<Analysis[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isBatch = batchFiles.length > 0;

  function readFileAsText(file: File): Promise<string> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (ev) => resolve(ev.target?.result as string);
      reader.readAsText(file);
    });
  }

  async function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    if (files.length === 1) {
      const content = await readFileAsText(files[0]);
      setTranscript(content);
      setBatchFiles([]);
    } else {
      const loaded = await Promise.all(files.map(async (f) => ({ name: f.name, content: await readFileAsText(f) })));
      setBatchFiles(loaded);
      setTranscript("");
    }
    e.target.value = "";
  }

  async function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (!files.length) return;
    if (files.length === 1) {
      const content = await readFileAsText(files[0]);
      setTranscript(content);
      setBatchFiles([]);
    } else {
      const loaded = await Promise.all(files.map(async (f) => ({ name: f.name, content: await readFileAsText(f) })));
      setBatchFiles(loaded);
      setTranscript("");
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragging(false);
  }

  function removeFile(index: number) {
    const next = batchFiles.filter((_, i) => i !== index);
    if (next.length === 0) setBatchFiles([]);
    else setBatchFiles(next);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setBatchResults(null);
    try {
      if (isBatch) {
        const results = await analyzeTranscripts(batchFiles.map((f) => f.content));
        setBatchResults(results);
      } else {
        const analysis = await analyzeTranscript(transcript);
        setResult(analysis);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = isBatch ? batchFiles.length > 0 : transcript.trim().length > 0;

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="text-center space-y-3 pt-2">
        <h1 className="text-4xl font-bold text-slate-900 tracking-tight">
          Analyze a Coaching Transcript
        </h1>
        <p className="text-slate-500 max-w-lg mx-auto leading-relaxed">
          Paste or upload a session transcript to extract a structured summary
          and actionable next steps.
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4"
      >
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-slate-700">
              {isBatch ? (
                <span className="flex items-center gap-1.5">
                  <Files className="w-4 h-4 text-indigo-500" />
                  {batchFiles.length} files queued for batch analysis
                </span>
              ) : (
                "Transcript"
              )}
            </label>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              <Upload className="w-3 h-3" />
              Upload file{" "}
              <span className="text-slate-400">(.txt, .vtt, .srt — select multiple for batch)</span>
            </button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.vtt,.srt"
            multiple
            className="hidden"
            onChange={handleFileInput}
          />

          {isBatch ? (
            /* Batch file list */
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`rounded-xl border transition-colors space-y-2 p-3 ${
                dragging ? "bg-indigo-50 border-2 border-dashed border-indigo-400" : "border-slate-300"
              }`}
            >
              {batchFiles.map((f, i) => (
                <div key={i} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2">
                  <span className="text-sm text-slate-700 truncate">{f.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(i)}
                    className="ml-3 text-slate-400 hover:text-red-500 transition-colors shrink-0"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <p className="text-xs text-slate-400 px-1">Drop more files to add them to the batch</p>
            </div>
          ) : (
            /* Single drop zone */
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`relative rounded-xl transition-colors ${
                dragging
                  ? "bg-indigo-50 border-2 border-dashed border-indigo-400"
                  : "border border-slate-300"
              }`}
            >
              {dragging && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-xl pointer-events-none">
                  <Upload className="w-6 h-6 text-indigo-500" />
                  <span className="text-sm font-medium text-indigo-600">
                    Drop 1 file to load · Drop multiple for batch
                  </span>
                </div>
              )}
              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder={"Alice | Coach: How have you been since our last session?\n\nBob: Much better. I finished the project report.\n\nAlice | Coach: What helped?\n\nBob: Breaking it into daily tasks."}
                rows={10}
                disabled={loading}
                className={`w-full px-3.5 py-3 text-sm bg-transparent rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-400 disabled:bg-slate-50 disabled:cursor-not-allowed transition ${
                  dragging ? "opacity-20 pointer-events-none" : ""
                }`}
              />
            </div>
          )}
          <p className="text-xs text-slate-400">
            Accepts plain text, WebVTT, SRT, or timestamped formats — drag & drop one file or multiple for batch.
          </p>
        </div>

        {error && (
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!canSubmit || loading}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-2.5 px-4 rounded-xl font-medium text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {isBatch ? `Analyzing ${batchFiles.length} transcripts…` : "Analyzing…"}
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              {isBatch ? `Analyze ${batchFiles.length} Transcripts` : "Analyze Transcript"}
            </>
          )}
        </button>
      </form>

      {/* Single result */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Analysis</h2>
            <Link
              href={`/transcripts/${result.id}`}
              className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              View full analysis <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
              <Sparkles className="w-4 h-4 text-indigo-500" />
              Summary
            </div>
            <p className="text-slate-800 leading-relaxed text-sm">{result.summary}</p>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
              <CheckCircle2 className="w-4 h-4 text-indigo-500" />
              Action Items
              <span className="ml-auto bg-indigo-50 text-indigo-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                {result.action_items.length}
              </span>
            </div>
            <ul className="space-y-2.5">
              {result.action_items.map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-slate-700">
                  <span className="mt-0.5 w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 text-xs font-semibold flex items-center justify-center shrink-0">
                    {i + 1}
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Batch results */}
      {batchResults && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Batch Results</h2>
            <span className="text-sm text-slate-400">{batchResults.length} analyses</span>
          </div>
          {batchResults.map((analysis, i) => (
            <div key={analysis.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
                  {batchFiles[i]?.name ?? `Transcript ${i + 1}`}
                </span>
                <Link
                  href={`/transcripts/${analysis.id}`}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-indigo-600 transition-colors"
                >
                  View full <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  Summary
                </div>
                <p className="text-sm text-slate-800 leading-relaxed">{analysis.summary}</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
                  Action Items
                  <span className="ml-auto bg-indigo-50 text-indigo-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                    {analysis.action_items.length}
                  </span>
                </div>
                <ul className="space-y-1.5">
                  {analysis.action_items.map((item, j) => (
                    <li key={j} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <span className="mt-0.5 w-4 h-4 rounded-full bg-indigo-50 text-indigo-600 text-xs font-semibold flex items-center justify-center shrink-0">
                        {j + 1}
                      </span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
