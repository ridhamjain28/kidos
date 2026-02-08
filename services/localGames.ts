
// Local Game Logic - No API Required

// --- CHESS LOGIC ---

// Simple board evaluation to find a decent move (Capture > Center > Random)
export const getLocalChessHint = (board: string[][], turn: 'white' | 'black'): string => {
    // 1. Check for captures
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const piece = board[r][c];
            if (isColor(piece, turn)) {
                // Check all possible moves for this piece (Simplified pseudo-logic)
                // In a real engine we'd generate all moves. Here we just look for diagonal pawn captures or obvious threats.
                if (piece === '♙' && turn === 'white') {
                    // Check captures
                    if (r > 0 && c > 0 && isColor(board[r-1][c-1], 'black')) return "Your pawn can capture that piece on the left!";
                    if (r > 0 && c < 7 && isColor(board[r-1][c+1], 'black')) return "Look! Your pawn can capture on the right!";
                }
            }
        }
    }

    // 2. Control Center
    if (turn === 'white') {
        if (board[6][3] === '♙') return "Try moving your Queen's pawn forward to control the center.";
        if (board[6][4] === '♙') return "Moving your King's pawn forward is a great way to start!";
        if (board[7][1] === '♘' && board[5][2] === '') return "Knights love to jump! Try moving your Knight to the center.";
    }

    // 3. General Advice
    const tips = [
        "Protect your King!",
        "Try to control the middle of the board.",
        "Don't leave your pieces undefended!",
        "Think: 'If I move here, can they capture me?'",
        "Knights are tricky—use them to jump over pieces!",
        "Bishops like open diagonals. Clear the path!"
    ];
    return tips[Math.floor(Math.random() * tips.length)];
};

const isColor = (piece: string, color: 'white' | 'black') => {
    if (!piece) return false;
    const white = '♙♖♘♗♕♔';
    const black = '♟♜♞♝♛♚';
    return color === 'white' ? white.includes(piece) : black.includes(piece);
};


// --- LANGUAGE LOGIC ---

interface LessonCard {
    phrase: string;
    translation: string;
    pronunciation: string;
    imagePrompt: string; // Keyword for unsplash/loremflickr
    voiceInstruction: string;
}

const DICTIONARY: Record<string, LessonCard[]> = {
    'Spanish': [
        { phrase: 'Hola', translation: 'Hello', pronunciation: 'OH-lah', imagePrompt: 'waving', voiceInstruction: "Can you say 'Hola'?" },
        { phrase: 'Gato', translation: 'Cat', pronunciation: 'GAH-toh', imagePrompt: 'cat', voiceInstruction: "Say 'Gato'!" },
        { phrase: 'Perro', translation: 'Dog', pronunciation: 'PEH-rroh', imagePrompt: 'dog', voiceInstruction: "Let's say 'Perro'!" },
        { phrase: 'Gracias', translation: 'Thank you', pronunciation: 'GRAH-see-ahs', imagePrompt: 'happy', voiceInstruction: "Say 'Gracias'!" },
        { phrase: 'Amigo', translation: 'Friend', pronunciation: 'ah-MEE-goh', imagePrompt: 'friends', voiceInstruction: "Who is your Amigo?" }
    ],
    'French': [
        { phrase: 'Bonjour', translation: 'Hello', pronunciation: 'bon-ZHOOR', imagePrompt: 'eiffel tower', voiceInstruction: "Can you say 'Bonjour'?" },
        { phrase: 'Chat', translation: 'Cat', pronunciation: 'SHAH', imagePrompt: 'cat', voiceInstruction: "Say 'Chat'!" },
        { phrase: 'Chien', translation: 'Dog', pronunciation: 'SHYEN', imagePrompt: 'dog', voiceInstruction: "Let's say 'Chien'!" },
        { phrase: 'Merci', translation: 'Thank you', pronunciation: 'mehr-SEE', imagePrompt: 'smile', voiceInstruction: "Say 'Merci'!" },
        { phrase: 'Ami', translation: 'Friend', pronunciation: 'ah-MEE', imagePrompt: 'high five', voiceInstruction: "Say 'Ami'!" }
    ],
    'German': [
        { phrase: 'Hallo', translation: 'Hello', pronunciation: 'HAH-loh', imagePrompt: 'waving', voiceInstruction: "Can you say 'Hallo'?" },
        { phrase: 'Katze', translation: 'Cat', pronunciation: 'KAT-seh', imagePrompt: 'cat', voiceInstruction: "Say 'Katze'!" },
        { phrase: 'Hund', translation: 'Dog', pronunciation: 'HOONT', imagePrompt: 'dog', voiceInstruction: "Let's say 'Hund'!" },
        { phrase: 'Danke', translation: 'Thank you', pronunciation: 'DAN-keh', imagePrompt: 'gift', voiceInstruction: "Say 'Danke'!" },
        { phrase: 'Freund', translation: 'Friend', pronunciation: 'FROYND', imagePrompt: 'friends', voiceInstruction: "Say 'Freund'!" }
    ]
};

export const getLocalLanguageLesson = (language: string): LessonCard => {
    const pool = DICTIONARY[language] || DICTIONARY['Spanish'];
    return pool[Math.floor(Math.random() * pool.length)];
};

export const checkLocalPronunciation = (target: string, spoken: string) => {
    const t = target.toLowerCase().trim();
    const s = spoken.toLowerCase().trim();
    
    // Simple fuzzy match check
    if (s.includes(t) || t.includes(s) || levenshteinDistance(s, t) <= 2) {
        return { correct: true, feedback: "Excellent! You said it perfectly! 🎉" };
    }
    return { correct: false, feedback: "Close! Try saying it one more time. 👂" };
};

// Simple Edit Distance for fuzzy matching
function levenshteinDistance(a: string, b: string): number {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    const matrix = [];
    for (let i = 0; i <= b.length; i++) matrix[i] = [i];
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) matrix[i][j] = matrix[i - 1][j - 1];
            else matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j] + 1);
        }
    }
    return matrix[b.length][a.length];
}

// --- DRAWING LOGIC ---

const INSPIRATION_PROMPTS = [
    "Draw a happy dinosaur!",
    "Can you draw a spaceship?",
    "Draw your favorite food!",
    "Paint a magical castle!",
    "Draw a robot with 3 arms!",
    "Draw a cat wearing a hat!",
    "Paint a beautiful rainbow!",
    "Draw an underwater adventure!"
];

export const getLocalDrawingPrompt = (): string => {
    return INSPIRATION_PROMPTS[Math.floor(Math.random() * INSPIRATION_PROMPTS.length)];
};
