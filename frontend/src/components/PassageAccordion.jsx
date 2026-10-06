import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Sparkles } from 'lucide-react';

export default function PassageAccordion({ passages }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!passages || passages.length === 0) return null;

  return (
    <div className="mt-3 border border-slate-700/60 rounded-lg overflow-hidden bg-slate-900/60">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-800/40 hover:bg-slate-800/80 transition-colors text-xs font-medium text-slate-300"
      >
        <div className="flex items-center space-x-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Retrieved Context Passages ({passages.length})</span>
        </div>
        {isOpen ? (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400" />
        )}
      </button>

      {isOpen && (
        <div className="p-3 space-y-2.5 max-h-72 overflow-y-auto">
          {passages.map((p, idx) => {
            const similarityPct = Math.round(p.similarity * 100);
            const badgeColor =
              similarityPct >= 75
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : similarityPct >= 50
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                : 'bg-slate-700/50 text-slate-400 border-slate-600';

            return (
              <div
                key={p.chunk_id || idx}
                className="p-3 rounded-md bg-slate-950/70 border border-slate-800 text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between font-mono text-[11px] text-slate-400 border-b border-slate-800/80 pb-1">
                  <div className="flex items-center space-x-1.5 truncate max-w-[70%]">
                    <FileText className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                    <span className="truncate text-slate-200" title={p.document_name}>
                      {p.document_name}
                    </span>
                    <span className="text-slate-500">· Page {p.page_number}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold ${badgeColor}`}>
                    Similarity: {similarityPct}%
                  </span>
                </div>
                <p className="text-slate-300 leading-relaxed font-sans text-xs whitespace-pre-wrap">
                  {p.content}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
