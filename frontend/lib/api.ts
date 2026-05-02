const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export interface Analysis {
  id: string;
  summary: string;
  action_items: string[];
  created_at: string;
}

export async function analyzeTranscript(transcript: string): Promise<Analysis> {
  const res = await fetch(`${API_URL}/transcripts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function analyzeTranscripts(transcripts: string[]): Promise<Analysis[]> {
  const res = await fetch(`${API_URL}/transcripts/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcripts }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function listAnalyses(): Promise<Analysis[]> {
  const res = await fetch(`${API_URL}/transcripts`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch analyses");
  return res.json();
}

export async function getAnalysis(id: string): Promise<Analysis> {
  const res = await fetch(`${API_URL}/transcripts/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Analysis not found");
  return res.json();
}

export async function deleteAnalysis(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/transcripts/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 404) throw new Error("Failed to delete");
}
