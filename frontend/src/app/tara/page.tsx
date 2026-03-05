"use client";

import { useState } from "react";
import { scanTopics } from "@/lib/api";

interface Topic {
  title: string;
  summary: string;
  category: string;
  engagement_score: number;
  media_urls: string[];
}

export default function TaraPage() {
  const [timeRange, setTimeRange] = useState("24h");
  const [category, setCategory] = useState("all");
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = (await scanTopics(timeRange, category)) as {
        topics: Topic[];
      };
      setTopics(result.topics);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Tarama hatasi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold gradient-text">AI Gundem Tara</h2>

      {/* Controls */}
      <div className="glass-card flex flex-wrap gap-4 items-end">
        <div>
          <label className="text-xs text-[var(--text-secondary)] block mb-1">
            Zaman Araligi
          </label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm"
          >
            <option value="1h">Son 1 saat</option>
            <option value="6h">Son 6 saat</option>
            <option value="24h">Son 24 saat</option>
            <option value="7d">Son 7 gun</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-[var(--text-secondary)] block mb-1">
            Kategori
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm"
          >
            <option value="all">Tumu</option>
            <option value="llm">LLM / Model</option>
            <option value="product">Urun / Lansman</option>
            <option value="research">Arastirma</option>
            <option value="funding">Yatirim</option>
          </select>
        </div>

        <button
          onClick={handleScan}
          disabled={loading}
          className="btn-primary"
        >
          {loading ? "Taraniyor..." : "Tara"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="glass-card border-[var(--accent-red)]/50">
          <p className="text-sm text-[var(--accent-red)]">{error}</p>
        </div>
      )}

      {/* Results */}
      {topics.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm text-[var(--text-secondary)]">
            {topics.length} konu bulundu
          </p>
          {topics.map((topic, i) => (
            <div key={i} className="glass-card">
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-[var(--text-primary)]">
                    {topic.title}
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)] mt-2">
                    {topic.summary}
                  </p>
                  <div className="flex gap-2 mt-3">
                    <span className="text-xs bg-[var(--accent-blue)]/20 text-[var(--accent-blue)] px-2 py-1 rounded">
                      {topic.category}
                    </span>
                    <span className="text-xs bg-[var(--accent-green)]/20 text-[var(--accent-green)] px-2 py-1 rounded">
                      Score: {topic.engagement_score.toFixed(0)}
                    </span>
                    {topic.media_urls.length > 0 && (
                      <span className="text-xs bg-[var(--accent-cyan)]/20 text-[var(--accent-cyan)] px-2 py-1 rounded">
                        {topic.media_urls.length} medya
                      </span>
                    )}
                  </div>
                </div>
                <a
                  href={`/yaz?topic=${encodeURIComponent(topic.title)}`}
                  className="btn-primary text-sm whitespace-nowrap"
                >
                  Tweet Yaz
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && topics.length === 0 && !error && (
        <div className="glass-card text-center py-16">
          <div className="text-5xl mb-4">🔍</div>
          <p className="text-[var(--text-secondary)]">
            Zaman araligi secip &quot;Tara&quot; butonuna basin
          </p>
        </div>
      )}
    </div>
  );
}
