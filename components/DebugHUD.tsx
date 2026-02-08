import React, { useState } from 'react';
import { useIBLM } from '../context/IBLMContext';

/** Spec §7: Stress-test IBLM mood change via Debug HUD */
export const DebugHUD: React.FC = () => {
  const [open, setOpen] = useState(false);
  const { metrics, contentMode, reportFrustration, simulateLowAttention, resetMetrics } = useIBLM();

  // Show HUD when ?iblm=1 or in dev
  const show = typeof window !== 'undefined' && (
    new URLSearchParams(window.location.search).get('iblm') === '1' ||
    import.meta.env?.DEV
  );

  if (!show) return null;

  return (
    <div className="fixed top-2 right-2 z-[9999] font-mono text-xs">
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="px-2 py-1 bg-slate-800/90 text-white rounded-lg border border-slate-600 shadow-lg"
          aria-label="Open IBLM Debug"
        >
          IBLM
        </button>
      ) : (
        <div className="bg-slate-900/95 text-white rounded-xl border border-slate-600 shadow-xl p-3 max-w-[240px] space-y-2">
          <div className="flex justify-between items-center">
            <span className="font-bold text-amber-400">IBLM Debug</span>
            <button type="button" onClick={() => setOpen(false)} className="text-slate-400 hover:text-white">×</button>
          </div>
          <div className="grid grid-cols-2 gap-1 text-slate-300">
            <span>Mode</span>
            <span className={contentMode === 'CALMING_ESCAPE' ? 'text-rose-400' : contentMode === 'SHORT_BURST' ? 'text-amber-400' : 'text-emerald-400'}>
              {contentMode}
            </span>
            <span>Frustration</span>
            <span>{metrics.frustrationLevel}/10</span>
            <span>Attention (s)</span>
            <span>{(metrics.attentionSpan / 1000).toFixed(1)}</span>
            <span>Curiosity</span>
            <span>{metrics.curiosityType}</span>
            <span>Energy</span>
            <span>{metrics.energyLevel}</span>
          </div>
          <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-700">
            <button
              type="button"
              onClick={() => reportFrustration(3)}
              className="px-2 py-0.5 bg-rose-600 hover:bg-rose-500 rounded text-white"
              title="Trigger CALMING_ESCAPE (frustration ≥6)"
            >
              +Frustration
            </button>
            <button
              type="button"
              onClick={() => simulateLowAttention()}
              className="px-2 py-0.5 bg-amber-600 hover:bg-amber-500 rounded text-white"
              title="Trigger SHORT_BURST (low attention)"
            >
              Low Attention
            </button>
            <button
              type="button"
              onClick={() => resetMetrics()}
              className="px-2 py-0.5 bg-slate-600 hover:bg-slate-500 rounded text-white"
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
