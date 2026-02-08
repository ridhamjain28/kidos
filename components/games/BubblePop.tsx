import React, { useState, useEffect, useRef } from 'react';
import { useGameSound } from '../../hooks/useGameSound';

export const BubblePop: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const playSound = useGameSound();
    const [bubbles, setBubbles] = useState<{id: number, x: number, y: number, size: number, color: string, speed: number}[]>([]);
    const [score, setScore] = useState(0);
    const frameRef = useRef<number>(0);

    const addBubble = () => {
        const id = Date.now();
        const size = Math.random() * 60 + 40;
        const color = `hsl(${Math.random() * 360}, 70%, 60%)`;
        setBubbles(prev => [...prev, { id, x: Math.random() * 80 + 10, y: 110, size, color, speed: Math.random() * 0.5 + 0.2 }]);
    };

    useEffect(() => {
        const interval = setInterval(addBubble, 1000);
        const animate = () => {
             setBubbles(prev => prev.map(b => ({ ...b, y: b.y - b.speed })).filter(b => b.y > -20));
             frameRef.current = requestAnimationFrame(animate);
        };
        animate();
        return () => { clearInterval(interval); cancelAnimationFrame(frameRef.current); };
    }, []);

    const popBubble = (id: number) => {
        playSound('pop');
        setScore(s => s + 10);
        setBubbles(prev => prev.filter(b => b.id !== id));
    };

    return (
        <div className="flex-1 bg-gradient-to-b from-blue-300 to-blue-500 overflow-hidden relative h-full">
            <div className="absolute top-4 left-4 z-50">
                <button onClick={onBack} className="px-4 py-2 bg-white rounded-full font-bold shadow-md hover:scale-105 transition-transform text-slate-700">← Back</button>
            </div>
            <div className="absolute top-4 right-4 z-50 bg-white/20 backdrop-blur-md text-white px-6 py-2 rounded-full font-black text-2xl shadow-lg border-2 border-white/30">
                {score}
            </div>

            {bubbles.map(b => (
                <div 
                    key={b.id}
                    onClick={() => popBubble(b.id)}
                    className="absolute rounded-full cursor-pointer shadow-[inset_-10px_-10px_20px_rgba(0,0,0,0.1),inset_10px_10px_20px_rgba(255,255,255,0.4)] hover:scale-110 active:scale-90 transition-transform flex items-center justify-center before:content-[''] before:absolute before:top-[15%] before:left-[15%] before:w-[20%] before:h-[20%] before:bg-white before:rounded-full before:opacity-60"
                    style={{ left: `${b.x}%`, top: `${b.y}%`, width: b.size, height: b.size, backgroundColor: b.color + '80', backdropFilter: 'blur(2px)', border: `2px solid ${b.color}` }}
                />
            ))}
        </div>
    );
};
