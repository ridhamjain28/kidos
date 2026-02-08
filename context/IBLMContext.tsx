import React, { createContext, useContext, useState, useEffect, useRef, useMemo } from 'react';
import { IBLMMetrics, FeedItem, LearnVideo, ParentSettings, ContentMode, ImageSize } from '../types';
import { generateLearnTopics, generateImage, generateVideoBrief } from '../services/gemini';

/** Thresholds for adaptation (spec §3.2) */
const FRUSTRATION_CALMING_THRESHOLD = 6;
const ATTENTION_SHORT_BURST_THRESHOLD_MS = 3500;
const SESSION_START = Date.now();

export interface ContentRecommendation {
  reason: string;
  difficulty: string;
  topicCategory: string;
  /** NORMAL | CALMING_ESCAPE | SHORT_BURST for UI to switch mode */
  contentMode: ContentMode;
}

interface IBLMContextType {
  metrics: IBLMMetrics;
  /** Derived from metrics: which mode the UI should adapt to */
  contentMode: ContentMode;
  contentBuffer: FeedItem[];
  tvBuffer: LearnVideo[];
  setBuffer: React.Dispatch<React.SetStateAction<FeedItem[]>>;
  setTvBuffer: React.Dispatch<React.SetStateAction<LearnVideo[]>>;
  startInteraction: (id: string, type: string) => void;
  endInteraction: (success: boolean) => void;
  decideNextContent: () => ContentRecommendation;
  reportFrustration: (val: number) => void;
  reportCuriosityPreference: (type: IBLMMetrics['curiosityType']) => void;
  /** Debug HUD: simulate low attention to trigger SHORT_BURST mode */
  simulateLowAttention: () => void;
  resetMetrics: () => void;
}

const IBLMContext = createContext<IBLMContextType | undefined>(undefined);

export const IBLMProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [metrics, setMetrics] = useState<IBLMMetrics>({
    attentionSpan: 5000,
    frustrationLevel: 0,
    curiosityType: 'VISUAL',
    energyLevel: 'CALM',
    sessionDuration: 0,
    masteryScore: 10,
  });

  const [contentBuffer, setBuffer] = useState<FeedItem[]>([]);
  const [tvBuffer, setTvBuffer] = useState<LearnVideo[]>([]);
  const interactionStart = useRef<number>(0);
  const engineInitialized = useRef(false);

  /** Spec §3.2: High Frustration → Calming Escape; Low Attention → Short Burst */
  const contentMode: ContentMode = useMemo(() => {
    if (metrics.frustrationLevel >= FRUSTRATION_CALMING_THRESHOLD) return 'CALMING_ESCAPE';
    if (metrics.attentionSpan > 0 && metrics.attentionSpan < ATTENTION_SHORT_BURST_THRESHOLD_MS) return 'SHORT_BURST';
    return 'NORMAL';
  }, [metrics.frustrationLevel, metrics.attentionSpan]);

  /** Session duration tick (for energy level and analytics) */
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics((prev) => ({
        ...prev,
        sessionDuration: Date.now() - SESSION_START,
        energyLevel:
          prev.frustrationLevel >= FRUSTRATION_CALMING_THRESHOLD
            ? 'FRUSTRATED'
            : prev.attentionSpan > 0 && prev.attentionSpan < 2000
              ? 'TIRED'
              : prev.attentionSpan > 6000
                ? 'ENGAGED'
                : 'CALM',
      }));
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  // --- Automated production pipeline (Discovery / WonderTV pre-hydration) ---
  useEffect(() => {
    const startFactory = async () => {
      if (engineInitialized.current) return;
      engineInitialized.current = true;

      const saved = localStorage.getItem('parent_settings');
      const settings: ParentSettings = saved ? JSON.parse(saved) : { childAge: 5, focusTopics: ['Nature'], pin: '', childName: 'Kiddo' };

      try {
        const topics = await generateLearnTopics(settings);
        setTvBuffer(
          topics.map((t) => ({ ...t, hydrationStatus: 'COLD' as const }))
        );

        // Parallel: thumbnails + briefs (predictive hydration; spec §4.1)
        const productionTasks = topics.map(async (video, idx) => {
          const [thumb, brief] = await Promise.all([
            generateImage(`${video.title} - cute 3D render`, ImageSize.S_1K, 'gemini-2.5-flash-image'),
            generateVideoBrief(video.title, settings, metrics),
          ]);

          setTvBuffer((prev) =>
            prev.map((v, i) =>
              i === idx
                ? {
                    ...v,
                    thumbnailUrl: thumb || v.thumbnailUrl || '',
                    script: brief,
                    hydrationStatus: 'WARM' as const,
                  }
                : v
            )
          );
          return { idx, brief };
        });

        await Promise.all(productionTasks);
        // Veo rendering is heavy and async; LearnTV can do on-demand script + images + TTS for <4s (spec §7).
        // Optional: run generateVeoVideo + pollForVideo in background and set videoUri + hydrationStatus 'HOT'.
      } catch (e) {
        console.error('IBLM factory error:', e);
      }
    };

    startFactory();
  }, []);

  const startInteraction = (id: string, type: string) => {
    interactionStart.current = Date.now();
  };

  const endInteraction = (success: boolean) => {
    const duration = Date.now() - interactionStart.current;
    setMetrics((prev) => ({
      ...prev,
      attentionSpan: Math.round((prev.attentionSpan + duration) / 2),
      frustrationLevel: !success
        ? Math.min(10, prev.frustrationLevel + 1)
        : Math.max(0, prev.frustrationLevel - 1),
      masteryScore: success ? prev.masteryScore + 1 : prev.masteryScore,
    }));
  };

  /** Spec §3.2 + §4: Decide next content from metrics (curiosity, mastery, adaptation mode). */
  const decideNextContent = (): ContentRecommendation => {
    const difficulty = metrics.masteryScore > 15 ? 'Intermediate' : 'Basic';
    const topicCategory = metrics.curiosityType === 'VISUAL' ? 'General' : 'Logical';
    const reason =
      contentMode === 'CALMING_ESCAPE'
        ? 'Calming activity to reduce frustration'
        : contentMode === 'SHORT_BURST'
          ? 'Short burst to match attention span'
          : 'Curiosity-driven discovery';
    return {
      reason,
      difficulty,
      topicCategory,
      contentMode,
    };
  };

  const reportFrustration = (val: number) => {
    setMetrics((prev) => ({
      ...prev,
      frustrationLevel: Math.min(10, prev.frustrationLevel + val),
    }));
  };

  const reportCuriosityPreference = (type: IBLMMetrics['curiosityType']) => {
    setMetrics((prev) => ({ ...prev, curiosityType: type }));
  };

  const simulateLowAttention = () => {
    setMetrics((prev) => ({ ...prev, attentionSpan: 2000 }));
  };

  const resetMetrics = () => {
    setMetrics({
      attentionSpan: 5000,
      frustrationLevel: 0,
      curiosityType: 'VISUAL',
      energyLevel: 'CALM',
      sessionDuration: 0,
      masteryScore: 10,
    });
  };

  return (
    <IBLMContext.Provider
      value={{
        metrics,
        contentMode,
        contentBuffer,
        tvBuffer,
        setBuffer,
        setTvBuffer,
        startInteraction,
        endInteraction,
        decideNextContent,
        reportFrustration,
        reportCuriosityPreference,
        simulateLowAttention,
        resetMetrics,
      }}
    >
      {children}
    </IBLMContext.Provider>
  );
};

export const useIBLM = (): IBLMContextType => {
  const context = useContext(IBLMContext);
  if (!context) throw new Error('useIBLM must be used within an IBLMProvider');
  return context;
};
