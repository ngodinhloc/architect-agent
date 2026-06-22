"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle, Loader2 } from "lucide-react";
import { TicketInterface } from "@/types/chat";
import { getTicket } from "@/lib/api";

export default function TicketPage() {
  const { id } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<TicketInterface | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setTicket(await getTicket(id));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center gap-2 text-zinc-500">
        <Loader2 size={18} className="animate-spin" />
        Loading ticket…
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-red-500">{error ?? "Ticket not found"}</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-2xl space-y-6 p-8">
        <div className="flex items-center gap-3">
          <Link href={`/epic/${ticket.epicId}`} className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200">
            <ArrowLeft size={14} />
            Back to epic
          </Link>
        </div>

        <div>
          <p className="mb-1 font-mono text-xs text-zinc-400">{ticket.id}</p>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">{ticket.name}</h1>
          <p className="mt-1 font-mono text-xs text-zinc-400">Epic: {ticket.epicId}</p>
        </div>

        {/* Requirements */}
        {ticket.requirements.length > 0 && (
          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">Requirements</p>
            <ul className="space-y-2">
              {ticket.requirements.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-zinc-700 dark:text-zinc-300">
                  <span className="mt-0.5 shrink-0 text-zinc-400">•</span>
                  {r.requirement}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Acceptance Criteria */}
        {ticket.acceptance_criteria.length > 0 && (
          <div className="rounded-xl border border-green-200 bg-green-50 p-5 dark:border-green-800 dark:bg-green-950/40">
            <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-green-700 dark:text-green-400">Acceptance Criteria</p>
            <ul className="space-y-2">
              {ticket.acceptance_criteria.map((a, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-zinc-700 dark:text-zinc-300">
                  <CheckCircle size={14} className="mt-0.5 shrink-0 text-green-500" />
                  {a.criterion}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
