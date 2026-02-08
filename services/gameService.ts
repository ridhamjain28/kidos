import { getChessAdvice, generateLanguageLesson, checkPronunciation, identifyDrawing } from './gemini';
import { getLocalChessHint, getLocalLanguageLesson, checkLocalPronunciation, getLocalDrawingPrompt } from './localGames';

// Check if API key is configured (basic length check to avoid placeholder values)
const HAS_KEY = !!import.meta.env.VITE_API_KEY && import.meta.env.VITE_API_KEY.length > 20;

export const gameService = {
  hasKey: HAS_KEY,

  // --- CHESS ---
  getChessHint: async (board: string[][], turn: 'white' | 'black'): Promise<string> => {
    if (HAS_KEY) {
      try {
        // Convert board to simple string representation for AI
        const boardStr = board.map(row => row.map(c => c || '.').join(' ')).join('\n');
        return await getChessAdvice(boardStr);
      } catch (e) {
        console.warn("API Switch: Falling back to local Chess");
        return getLocalChessHint(board, turn);
      }
    }
    return getLocalChessHint(board, turn);
  },

  // --- LANGUAGE ---
  getLesson: async (language: string): Promise<any> => {
    if (HAS_KEY) {
      try {
        return await generateLanguageLesson(language, 'Easy');
      } catch (e) {
        console.warn("API Switch: Falling back to local Language");
        return getLocalLanguageLesson(language);
      }
    }
    return getLocalLanguageLesson(language);
  },

  checkPronunciation: async (target: string, spoken: string): Promise<any> => {
    if (HAS_KEY) {
      try {
        return await checkPronunciation(target, spoken);
      } catch (e) {
        return checkLocalPronunciation(target, spoken);
      }
    }
    return checkLocalPronunciation(target, spoken);
  },

  // --- DRAWING ---
  // API can guess drawing. Local can only provide prompts.
  // We'll expose both capabilities.
  identifyDrawing: async (base64: string): Promise<string> => {
    if (HAS_KEY) {
        return await identifyDrawing(base64);
    }
    throw new Error("AI required");
  },

  getInspiration: (): string => {
      // Local only for now, AI prompt gen is overkill mostly
      return getLocalDrawingPrompt();
  }
};
