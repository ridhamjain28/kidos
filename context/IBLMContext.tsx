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
  isChallenge: boolean;
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
  endInteraction: (success: boolean, topic?: string) => void;
  decideNextContent: (topic?: string) => ContentRecommendation;
  reportFrustration: (val: number) => void;
  reportCuriosityPreference: (type: IBLMMetrics['curiosityType']) => void;
  updateMastery: (topic: string, score: number) => void;
  /** Debug HUD: simulate low attention to trigger SHORT_BURST mode */
  simulateLowAttention: () => void;
  resetMetrics: () => void;
}

const IBLMContext = createContext<IBLMContextType | undefined>(undefined);

export const IBLMProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [metrics, setMetrics] = useState<IBLMMetrics>(() => {
    const saved = localStorage.getItem('iblm_mastery');
    const initialVectors = saved ? JSON.parse(saved) : { shortTerm: [], longTerm: [] };
    
    return {
      attentionSpan: 5000,
      frustrationLevel: 0,
      curiosityType: 'VISUAL',
      energyLevel: 'CALM',
      sessionDuration: 0,
      masteryScore: 10,
      vectors: initialVectors
    };
  });

  const [contentBuffer, setBuffer] = useState<FeedItem[]>([]);
  const [tvBuffer, setTvBuffer] = useState<LearnVideo[]>([]);
  const interactionStart = useRef<number>(0);
  const engineInitialized = useRef(false);
  const lastActivity = useRef<number>(Date.now());
  const [isDormant, setIsDormant] = useState(false);
  const itemsServedCount = useRef<number>(0);

  /** Spec §4.1: Dormant Session Filter (Noise Control) */
  useEffect(() => {
    const activityHandler = () => {
      lastActivity.current = Date.now();
      if (isDormant) setIsDormant(false);
    };

    window.addEventListener('mousedown', activityHandler);
    window.addEventListener('touchstart', activityHandler);
    window.addEventListener('keydown', activityHandler);

    const interval = setInterval(() => {
      const idleTime = Date.now() - lastActivity.current;
      if (idleTime > 60000) {
          setIsDormant(true);
          setBuffer([]); // Flush predictive buffer (Spec §4.1)
          setTvBuffer([]);
      } else if (idleTime > 30000) {
          setIsDormant(true);
      }
    }, 5000);

    return () => {
      window.removeEventListener('mousedown', activityHandler);
      window.removeEventListener('touchstart', activityHandler);
      window.removeEventListener('keydown', activityHandler);
      clearInterval(interval);
    };
  }, [isDormant]);

  /** Spec §4.2: STV Decay (50% drop every 24h) */
  useEffect(() => {
    const decayVectors = () => {
      setMetrics(prev => {
        const now = Date.now();
        const updatedSTV = prev.vectors.shortTerm.map(interest => {
          const hoursSince = (now - interest.lastInteraction) / (1000 * 60 * 60);
          const daysSince = hoursSince / 24;
          // 50% decay per day
          const newWeight = interest.weight * Math.pow(0.5, daysSince);
          return { ...interest, weight: newWeight };
        }).filter(i => i.weight > 0.05); // Cleanup small weights

        return {
          ...prev,
          vectors: { ...prev.vectors, shortTerm: updatedSTV }
        };
      });
    };
    decayVectors();
  }, []);

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

  const endInteraction = (success: boolean, topic?: string) => {
    if (isDormant) return; // Ignore noisy signals (Spec §4.1)
    
    const duration = Date.now() - interactionStart.current;
    if (duration < 3000) return; // Ignore accidental taps

    setMetrics((prev) => {
      let newVectors = { ...prev.vectors };

      if (topic) {
        // Update STV (Curiosity Spike)
        const existingIdx = newVectors.shortTerm.findIndex(t => t.topic === topic);
        if (existingIdx >= 0) {
          newVectors.shortTerm[existingIdx] = {
            ...newVectors.shortTerm[existingIdx],
            weight: Math.min(1, newVectors.shortTerm[existingIdx].weight + 0.1),
            lastInteraction: Date.now()
          };
        } else {
          newVectors.shortTerm.push({ topic, weight: 0.3, lastInteraction: Date.now() });
        }

        // Update LMV (Mastery)
        if (success) {
          const masteryIdx = newVectors.longTerm.findIndex(t => t.topic === topic);
          if (masteryIdx >= 0) {
             const record = newVectors.longTerm[masteryIdx];
             newVectors.longTerm[masteryIdx] = {
               ...record,
               successCount: record.successCount + 1,
               level: record.successCount > 5 ? Math.min(3, record.level + 1) as 1|2|3 : record.level
             };
          } else {
             newVectors.longTerm.push({ topic, level: 1, successCount: 1, lastQuizScore: 0 });
          }
        }
      }

      // Persist LMV
      localStorage.setItem('iblm_mastery', JSON.stringify(newVectors));

      return {
        ...prev,
        attentionSpan: Math.round((prev.attentionSpan + duration) / 2),
        frustrationLevel: !success
          ? Math.min(10, prev.frustrationLevel + 1)
          : Math.max(0, prev.frustrationLevel - 1),
        masteryScore: success ? prev.masteryScore + 1 : prev.masteryScore,
        vectors: newVectors
      };
    });
  };

  /** Spec §4.3: Anti-Echo Chamber Growth Injection (3:1 Rule) */
  const decideNextContent = (topic?: string): ContentRecommendation => {
    itemsServedCount.current++;
    
    // Find current mastery for topic
    const mastery = metrics.vectors.longTerm.find(t => t.topic === topic)?.level || 1;
    
    // Growth Constraint: Every 4th item is a "Challenge" (Mastery + 1)
    const isChallenge = itemsServedCount.current % 4 === 0;
    const difficultyLevel = isChallenge ? Math.min(3, mastery + 1) : mastery;

    const difficultyLabel = difficultyLevel === 1 ? 'Basic' : difficultyLevel === 2 ? 'Intermediate' : 'Advanced';

    const topicCategory = metrics.curiosityType === 'VISUAL' ? 'General' : 'Logical';
    const reason = isChallenge 
      ? 'Growth constraint: introducing a structured challenge'
      : contentMode === 'CALMING_ESCAPE'
        ? 'Calming activity to reduce frustration'
        : 'Curiosity-driven discovery';

    return {
      reason,
      difficulty: difficultyLabel,
      topicCategory,
      contentMode,
      isChallenge
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

  const updateMastery = (topic: string, score: number) => {
    setMetrics(prev => {
        const newVectors = { ...prev.vectors };
        const idx = newVectors.longTerm.findIndex(t => t.topic === topic);
        
        if (idx >= 0) {
            const record = newVectors.longTerm[idx];
            // Increase level if score is high (Spec §4.4)
            const newLevel = score >= 80 ? Math.min(3, record.level + 1) : 
                             score < 40 ? Math.max(1, record.level - 1) : record.level;
            
            newVectors.longTerm[idx] = {
                ...record,
                level: newLevel as 1|2|3,
                lastQuizScore: score,
                successCount: record.successCount + 1
            };
        } else {
            newVectors.longTerm.push({ topic, level: score >= 80 ? 2 : 1, successCount: 1, lastQuizScore: score });
        }

        localStorage.setItem('iblm_mastery', JSON.stringify(newVectors));
        return { ...prev, vectors: newVectors };
    });
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
        updateMastery
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
