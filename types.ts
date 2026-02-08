
export enum View {
  FEED = 'FEED',
  GAMES = 'GAMES',
  CHAT = 'CHAT',
  PARENTS = 'PARENTS',
  TV = 'TV'
}

export enum ImageSize {
  S_1K = '1K',
  S_2K = '2K',
  S_4K = '4K'
}

export type WelcomeState = 'HIDDEN' | 'GREETING' | 'FLYING' | 'DONE';

export interface ParentSettings {
  pin: string;
  childName: string;
  childAge: number;
  focusTopics: string[]; // Topics parent wants to encourage
  avatarName?: string;
  hasSeenTutorial?: boolean;
}

export interface ActivityLog {
  id: string;
  type: 'video' | 'chat' | 'fact' | 'create';
  details: string;
  timestamp: number;
  category: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  text: string;
  imageUrl?: string;
  isThinking?: boolean;
}

export interface GroundingChunk {
  web?: {
    uri?: string;
    title?: string;
  };
}

export interface FeedItem {
  id: string;
  title: string;
  fact: string;
  imageUrl: string;
  topic: string;
}

export interface Book {
    id: string;
    title: string;
    emoji: string;
    color: string;
    description: string;
    coverImage?: string;
}

export interface Story {
    title: string;
    coverPrompt: string;
    pages: { text: string; imagePrompt?: string | null }[];
}

// --- IBLM (Individual Behavior Learning Model) ---
export type CuriosityType = 'VISUAL' | 'LOGICAL';
export type EnergyLevel = 'CALM' | 'ENGAGED' | 'FRUSTRATED' | 'TIRED';

/** Content mode driven by IBLM adaptation logic (spec §3.2) */
export type ContentMode = 'NORMAL' | 'CALMING_ESCAPE' | 'SHORT_BURST';

export interface IBLMMetrics {
  /** Duration (ms) between content interactions; rolling average */
  attentionSpan: number;
  /** 1–10; from rapid-tapping, failed attempts, or voice tone */
  frustrationLevel: number;
  curiosityType: CuriosityType;
  energyLevel: EnergyLevel;
  /** Session duration in ms */
  sessionDuration: number;
  /** Increases on success, influences difficulty */
  masteryScore: number;
}

export interface LearnVideo {
  id: string;
  title: string;
  description: string;
  thumbnailUrl?: string;
  category: string;
  script?: string;
  visualPrompts?: string[];
  slideImages?: string[]; // Array of generated image URLs for the slideshow
  /** IBLM pipeline: pre-generated brief for Veo/script */
  videoUri?: string;
  /** COLD = not started, WARM = thumb+brief, HOT = full video ready */
  hydrationStatus?: 'COLD' | 'WARM' | 'HOT';
}

export interface GeneratedVideo {
  uri: string;
  mimeType: string;
}
