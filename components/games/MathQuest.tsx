import React, { useState, useEffect } from 'react';
import { useGameSound } from '../../hooks/useGameSound';

export const MathQuest: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const playSound = useGameSound();
    const [problem, setProblem] = useState({ q: '2 + 2', a: 4, options: [3, 4, 5] });
    const [score, setScore] = useState(0);
    const [streak, setStreak] = useState(0);

    const generateProblem = () => {
        const operations = ['+', '-', '*'];
        const op = operations[Math.floor(Math.random() * (streak > 5 ? 3 : 2))]; 
        let a = Math.floor(Math.random() * 10) + 1;
        let b = Math.floor(Math.random() * 10) + 1;
        if (op === '-') { if (a < b) [a, b] = [b, a]; } 
        if (op === '*') { a = Math.floor(Math.random() * 5) + 1; b = Math.floor(Math.random() * 5) + 1; }
        
        const ans = eval(`${a} ${op} ${b}`);
        const opts = new Set([ans]);
        while(opts.size < 3) {
            opts.add(ans + Math.floor(Math.random() * 5) - 2);
        }
        setProblem({ q: `${a} ${op} ${b}`, a: ans, options: Array.from(opts).sort(() => Math.random() - 0.5) });
    };

    useEffect(() => { generateProblem(); }, []);

    const handleAnswer = (val: number) => {
        if (val === problem.a) {
            playSound('success'); setScore(s => s + 10 + streak * 2); setStreak(s => s + 1);
            generateProblem();
        } else {
            playSound('error'); setStreak(0);
        }
    };

    return (
        <div className="flex-1 bg-gradient-to-br from-green-400 to-cyan-500 p-8 flex flex-col items-center justify-center animate-in fade-in h-full relative">
            <div className="absolute top-4 left-4">
                <button onClick={onBack} className="px-4 py-2 bg-white rounded-full font-bold shadow-md hover:scale-105 transition-transform text-slate-700">← Back</button>
            </div>
            <div className="absolute top-4 right-4 bg-white px-6 py-2 rounded-full font-black text-xl shadow-lg text-green-600">
                Score: {score} 🔥 {streak}
            </div>

            <div className="bg-white p-12 rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.3)] text-center w-full max-w-lg">
                <h2 className="text-6xl font-black text-slate-800 mb-8 font-display">{problem.q} = ?</h2>
                <div className="grid grid-cols-3 gap-4">
                    {problem.options.map((opt, i) => (
                        <button 
                            key={i} 
                            onClick={() => handleAnswer(opt)}
                            className="bg-green-100 hover:bg-green-200 text-green-700 font-bold text-4xl py-6 rounded-2xl shadow-sm active:scale-95 transition-all text-center"
                        >
                            {opt}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};
