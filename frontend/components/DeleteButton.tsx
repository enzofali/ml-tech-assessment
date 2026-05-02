"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { deleteAnalysis } from "@/lib/api";
import { Trash2, Loader2 } from "lucide-react";

export default function DeleteButton({ id }: { id: string }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleDelete() {
    if (!confirm("Delete this analysis? This cannot be undone.")) return;
    setLoading(true);
    try {
      await deleteAnalysis(id);
      router.push("/history");
      router.refresh();
    } catch {
      alert("Failed to delete. Please try again.");
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleDelete}
      disabled={loading}
      className="flex items-center gap-1.5 text-sm text-red-400 hover:text-red-600 disabled:opacity-50 transition-colors"
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
      Delete
    </button>
  );
}
