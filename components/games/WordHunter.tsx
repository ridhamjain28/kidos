import React, { useState, useEffect } from 'react';
import { useGameSound } from '../../hooks/useGameSound';

const WORD_LEVELS = [
    { grid: [['C','A','T'],['D','O','G'],['B','I','R']], words: ['CAT', 'DOG'] },
    { grid: [['F','I','S','H'],['B','I','R','D'],['F','R','O','G'],['L','I','O','N']], words: ['FISH', 'BIRD', 'FROG'] },
];

export const WordHunter: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const playSound = useGameSound();
    const [level, setLevel] = useState(0);
    const [foundWords, setFoundWords] = useState<string[]>([]);
    const [selectedCells, setSelectedCells] = useState<{r:number, c:number}[]>([]); 

    const currentLevel = WORD_LEVELS[level % WORD_LEVELS.length];

    const handleCellClick = (r: number, c: number) => {
        playSound('click');
        const exists = selectedCells.find(cell => cell.r === r && cell.c === c);
        let newSelection = exists 
            ? selectedCells.filter(cell => cell.r !== r || cell.c !== c)
            : [...selectedCells, {r, c}];
        
        // Check word
        const word = newSelection.map(cell => currentLevel.grid[cell.r][cell.c]).join('');
        if (currentLevel.words.includes(word) && !foundWords.includes(word)) {
            playSound('success');
            setFoundWords([...foundWords, word]);
            newSelection = [];
            if (foundWords.length + 1 === currentLevel.words.length) {
                setTimeout(() => {
                   playSound('magic');
                   setLevel(l => l + 1);
                   setFoundWords([]);
                }, 1000);
            }
        }
        setSelectedCells(newSelection);
    };

    return (
        <div className="flex-1 bg-yellow-100 p-8 flex flex-col items-center justify-center animate-in fade-in h-full relative">
            <div className="absolute top-4 left-4">
                <button onClick={onBack} className="px-4 py-2 bg-white rounded-full font-bold shadow-md hover:scale-105 transition-transform text-slate-700">← Back</button>
            </div>
            <h2 className="text-3xl font-black text-yellow-600 mb-8 bg-white px-8 py-2 rounded-full shadow-sm">Level {level + 1}</h2>

            <div className="bg-white p-8 rounded-3xl shadow-xl border-4 border-yellow-300">
                <div 
                  className="grid gap-2" 
                  style={{ gridTemplateColumns: `repeat(${currentLevel.grid[0].length}, minmax(0, 1fr))` }}
                >
                    {currentLevel.grid.map((row, r) => row.map((char, c) => (
                        <button 
                            key={`${r}-${c}`}
                            onClick={() => handleCellClick(r, c)}
                            className={`w-16 h-16 rounded-xl text-3xl font-bold transition-all shadow-sm
                                ${selectedCells.find(cell => cell.r === r && cell.c === c) ? 'bg-yellow-400 text-white scale-110 rotate-3' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}
                            `}
                        >
                            {char}
                        </button>
                    )))}
                </div>
            </div>

            <div className="mt-8 flex gap-4 flex-wrap justify-center">
                {currentLevel.words.map(w => (
                    <div key={w} className={`px-6 py-3 rounded-full font-bold text-lg shadow-sm transition-all ${foundWords.includes(w) ? 'bg-green-500 text-white line-through opacity-50' : 'bg-white text-slate-700'}`}>
                        {w}
                    </div>
                ))}
            </div>
        </div>
    );
};
