"use client";

import { useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

type Source = {
  file_path: string;
  start_line: number;
  end_line: number;
  distance: number;
};

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repoName, setRepoName] = useState("");
  const [repoId, setRepoId] = useState<number | null>(null);

  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);

  const [isIndexing, setIsIndexing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState("");

  async function indexRepository() {
    setError("");
    setAnswer("");
    setSources([]);

    if (!repoUrl.trim()) {
      setError("Enter a GitHub repository URL.");
      return;
    }

    setIsIndexing(true);

    try {
      const createResponse = await fetch(`${API_BASE_URL}/repositories/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: repoUrl,
          name: repoName || "Repository",
          description: "",
        }),
      });

      if (!createResponse.ok) {
        throw new Error("Failed to create repository.");
      }

      const repository = await createResponse.json();
      setRepoId(repository.id);

      const ingestResponse = await fetch(
        `${API_BASE_URL}/repositories/${repository.id}/ingest`,
        {
          method: "POST",
        }
      );

      if (!ingestResponse.ok) {
        const details = await ingestResponse.text();
        throw new Error(details || "Repository ingestion failed.");
      }

      const ingestion = await ingestResponse.json();

      setAnswer(
        `Repository indexed successfully. ${ingestion.files_processed} files were processed, ${ingestion.chunks_created} chunks were created, and ${ingestion.chunks_embedded} embeddings were generated.`
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setIsIndexing(false);
    }
  }

  async function askQuestion() {
    setError("");

    if (!repoId) {
      setError("Index a repository first.");
      return;
    }

    if (!query.trim()) {
      setError("Enter a question about the codebase.");
      return;
    }

    setIsAsking(true);

    try {
      const params = new URLSearchParams({
        q: query,
        limit: "5",
      });

      const response = await fetch(
        `${API_BASE_URL}/repositories/${repoId}/ask?${params.toString()}`
      );

      if (!response.ok) {
        const details = await response.text();
        throw new Error(details || "Failed to get an answer.");
      }

      const data = await response.json();

      setAnswer(data.answer);
      setSources(data.sources);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-10">
          <h1 className="text-4xl font-bold tracking-tight">
            AI Codebase Assistant
          </h1>

          <p className="mt-3 text-slate-400">
            Index a GitHub repository and ask questions about its codebase.
          </p>
        </div>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <h2 className="text-xl font-semibold">Repository</h2>

          <div className="mt-5 space-y-4">
            <div>
              <label className="mb-2 block text-sm text-slate-300">
                GitHub URL
              </label>

              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repository.git"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm text-slate-300">
                Repository name
              </label>

              <input
                type="text"
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                placeholder="My Project"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
              />
            </div>

            <button
              onClick={indexRepository}
              disabled={isIndexing}
              className="rounded-lg bg-blue-600 px-5 py-3 font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isIndexing ? "Indexing Repository..." : "Index Repository"}
            </button>
          </div>
        </section>

        <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <h2 className="text-xl font-semibold">Ask About Your Code</h2>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  askQuestion();
                }
              }}
              placeholder="Where is the filtering logic implemented?"
              className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500"
            />

            <button
              onClick={askQuestion}
              disabled={isAsking || !repoId}
              className="rounded-lg bg-emerald-600 px-6 py-3 font-medium transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isAsking ? "Thinking..." : "Ask"}
            </button>
          </div>
        </section>

        {error && (
          <div className="mt-6 rounded-lg border border-red-800 bg-red-950/40 p-4 text-red-300">
            {error}
          </div>
        )}

        {answer && (
          <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-xl font-semibold">Answer</h2>

            <div className="mt-4 whitespace-pre-wrap leading-7 text-slate-300">
              {answer}
            </div>
          </section>
        )}

        {sources.length > 0 && (
          <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-xl font-semibold">Sources</h2>

            <div className="mt-4 space-y-3">
              {sources.map((source, index) => (
                <div
                  key={`${source.file_path}-${source.start_line}-${index}`}
                  className="rounded-lg border border-slate-800 bg-slate-950 p-4"
                >
                  <div className="font-mono text-sm text-blue-400">
                    {source.file_path}
                  </div>

                  <div className="mt-1 text-sm text-slate-400">
                    Lines {source.start_line}–{source.end_line}
                  </div>

                  <div className="mt-1 text-xs text-slate-500">
                    Similarity distance: {source.distance.toFixed(4)}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}