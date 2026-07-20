"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { CircleCheck, CircleAlert, Send } from "lucide-react";
import { PageHeader } from "@/components/domain/page-header";
import { ErrorState } from "@/components/domain/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { apiPost } from "@/lib/api/client";
import type { AnalystAnswer } from "@/lib/api/types";

const SUGGESTED = [
  "Who are the most undervalued midfielders?",
  "Which nation has the highest supplier concentration?",
  "How is the valuation model evaluated?",
  "Which club supplies the most national teams?",
];

export default function AnalystPage() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<AnalystAnswer[]>([]);

  const ask = useMutation({
    mutationFn: (q: string) =>
      apiPost<AnalystAnswer>("/v1/analyst/ask", { question: q }),
    onSuccess: (result) => {
      setHistory((h) => [result.data, ...h]);
      setQuestion("");
    },
  });

  function submit(q: string) {
    if (q.trim().length > 0 && !ask.isPending) ask.mutate(q.trim());
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Ask the Analyst"
        description="Grounded RAG: every number in an answer is traced to executed SQL; definitional context is retrieved and cited. If a number can't be verified, the answer is flagged."
      />

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
      >
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about players, valuations, talent flow…"
          aria-label="Question for the analyst"
          maxLength={2000}
        />
        <Button type="submit" disabled={ask.isPending || question.trim().length === 0}>
          <Send className="h-4 w-4" aria-hidden="true" />
          Ask
        </Button>
      </form>

      <div className="flex flex-wrap gap-2">
        {SUGGESTED.map((s) => (
          <button
            key={s}
            onClick={() => submit(s)}
            disabled={ask.isPending}
            className="rounded-full border border-edge bg-surface px-3 py-1.5 text-xs text-fg-secondary transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      {ask.isPending ? <Skeleton className="h-48" aria-label="Waiting for answer" /> : null}
      {ask.isError ? <ErrorState error={ask.error} onRetry={() => ask.reset()} /> : null}

      <div aria-live="polite" className="flex flex-col gap-4">
        {history.map((a, i) => (
          <Card key={`${a.question}-${i}`}>
            <CardHeader className="flex-row items-start justify-between gap-3">
              <div>
                <CardTitle>{a.question}</CardTitle>
                <CardDescription>route: {a.route}</CardDescription>
              </div>
              {a.grounded ? (
                <Badge variant="accent">
                  <CircleCheck className="h-3 w-3" aria-hidden="true" /> grounded
                </Badge>
              ) : (
                <Badge variant="signal">
                  <CircleAlert className="h-3 w-3" aria-hidden="true" /> unverified numbers
                </Badge>
              )}
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-fg">
                {a.answer}
              </p>
              {a.facts.length > 0 ? (
                <div>
                  <p className="mb-2 text-xs uppercase tracking-wide text-fg-muted">
                    Facts from executed SQL
                  </p>
                  <ul className="flex flex-wrap gap-2">
                    {a.facts.map((f, j) => (
                      <li
                        key={`${f.label}-${j}`}
                        className="rounded-md border border-edge bg-raised px-3 py-1.5 text-xs"
                        title={`source: ${f.source}`}
                      >
                        <span className="text-fg-muted">{f.label}: </span>
                        <span className="num font-semibold text-fg">{f.value}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {a.citations.length > 0 ? (
                <div>
                  <p className="mb-2 text-xs uppercase tracking-wide text-fg-muted">
                    Citations
                  </p>
                  <ul className="flex flex-col gap-1">
                    {a.citations.map((c, j) => (
                      <li key={`${c.source_path}-${j}`} className="num text-xs text-info">
                        {c.source_path} § {c.section}{" "}
                        <span className="text-fg-muted">({c.score.toFixed(2)})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
