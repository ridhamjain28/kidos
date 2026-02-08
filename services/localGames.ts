
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

export const getLocalChessMove = (board: string[][], color: 'white' | 'black'): {from: {r:number, c:number}, to: {r:number, c:number}} | null => {
    const moves: {from: {r:number, c:number}, to: {r:number, c:number}}[] = [];
    
    // Helper to check bounds and capture
    const isValid = (r: number, c: number) => r >= 0 && r < 8 && c >= 0 && c < 8 && !isColor(board[r][c], color);
    
    for(let r=0; r<8; r++) {
        for(let c=0; c<8; c++) {
            if(isColor(board[r][c], color)) {
                // Generate simple moves based on piece type
                const p = board[r][c];
                const directions = [];
                
                if(p === '♟' || p === '♙') {
                    const dir = color === 'white' ? -1 : 1;
                    if(isValid(r+dir, c) && board[r+dir][c] === '') directions.push({r:r+dir, c:c}); // Move
                    if(isValid(r+dir, c-1) && board[r+dir][c-1] !== '') directions.push({r:r+dir, c:c-1}); // Capture L
                    if(isValid(r+dir, c+1) && board[r+dir][c+1] !== '') directions.push({r:r+dir, c:c+1}); // Capture R
                } else {
                    // For other pieces, just try random 1-step moves for now (Simplified for "KidOS")
                    // Real chess logic is too heavy, making them "Magical Teleporting Pieces" or simple shufflers
                    // Let's do King-like moves for everyone to keep it playable but simple
                    const steps = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]];
                    steps.forEach(([dr, dc]) => {
                       if(isValid(r+dr, c+dc)) directions.push({r:r+dr, c:c+dc});
                    });
                }
                
                directions.forEach(d => moves.push({from: {r, c}, to: d}));
            }
        }
    }
    
    if(moves.length === 0) return null;
    // Prefer captures
    const captures = moves.filter(m => board[m.to.r][m.to.c] !== '');
    if(captures.length > 0) return captures[Math.floor(Math.random() * captures.length)];
    
    return moves[Math.floor(Math.random() * moves.length)];
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
