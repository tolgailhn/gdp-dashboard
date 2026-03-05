"use client";

import { useState } from "react";
import { analyzeAccount } from "@/lib/api";

interface StyleDNA {
  avg_length: number;
  emoji_usage: number;
  hashtag_usage: number;
  top_topics: string[];
  tone: string;
  sample_patterns: string[];
}

interface AnalysisResult {
  username: string;
  tweets_analyzed: number;
  style_dna: StyleDNA;
  engagement_avg: number;
}

export default function AnalizPage() {
  const [username, setUsername] = useState("");
  const [tweetCount, setTweetCount] = useState(50);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = (await analyzeAccount(
        username.replace("@", ""),
        tweetCount
      )) as AnalysisResult;
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analiz hatasi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold gradient-text">Tweet Analizi</h2>

      {/* Input */}
      <div className="glass-card flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-[var(--text-secondary)] block mb-1">
            Kullanici Adi
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="@kullanici"
            className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm focus:border-[var(--accent-blue)] focus:outline-none"
          />
        </div>
        <div>
          <label className="text-xs text-[var(--text-secondary)] block mb-1">
            Tweet Sayisi
          </label>
          <select
            value={tweetCount}
            onChange={(e) => setTweetCount(Number(e.target.value))}
            className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm"
          >
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading || !username.trim()}
          className="btn-primary"
        >
          {loading ? "Analiz ediliyor..." : "Analiz Et"}
        </button>
      </div>

      {error && (
        <div className="glass-card border-[var(--accent-red)]/50">
          <p className="text-sm text-[var(--accent-red)]">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="glass-card">
            <h3 className="font-semibold mb-4">
              @{result.username} — Stil DNA
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--accent-blue)]">
                  {result.tweets_analyzed}
                </div>
                <div className="text-xs text-[var(--text-secondary)]">
                  Tweet Analiz
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--accent-cyan)]">
                  {result.style_dna.avg_length.toFixed(0)}
                </div>
                <div className="text-xs text-[var(--text-secondary)]">
                  Ort. Uzunluk
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--accent-green)]">
                  {result.engagement_avg.toFixed(1)}
                </div>
                <div className="text-xs text-[var(--text-secondary)]">
                  Ort. Engagement
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--accent-amber)]">
                  {result.style_dna.tone}
                </div>
                <div className="text-xs text-[var(--text-secondary)]">Ton</div>
              </div>
            </div>
          </div>

          {result.style_dna.top_topics.length > 0 && (
            <div className="glass-card">
              <h4 className="text-sm font-semibold mb-2">En Cok Konular</h4>
              <div className="flex flex-wrap gap-2">
                {result.style_dna.top_topics.map((t, i) => (
                  <span
                    key={i}
                    className="text-xs bg-[var(--accent-blue)]/20 text-[var(--accent-blue)] px-3 py-1 rounded-full"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
