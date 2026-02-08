import React, { useState, useEffect } from 'react';
import { useGameSound } from '../../hooks/useGameSound';

const ZOO_EMOJIS = ['🦁', '🐯', '🐻', '🐨', '🐼', '🦊', '🐸', '🐵'];

export const MemoryZoo: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const playSound = useGameSound();
    const [cards, setCards] = useState<{id: number, emoji: string, flipped: boolean, matched: boolean}[]>([]);
    const [selected, setSelected] = useState<number[]>([]);

    useEffect(() => {
        const deck = [...ZOO_EMOJIS, ...ZOO_EMOJIS]
            .sort(() => Math.random() - 0.5)
            .map((emoji, i) => ({ id: i, emoji, flipped: false, matched: false }));
        setCards(deck);
    }, []);

    const handleCardClick = (id: number) => {
        if (selected.length >= 2 || cards[id].flipped || cards[id].matched) return;
        playSound('click');
        
        const newCards = [...cards];
        newCards[id].flipped = true;
        setCards(newCards);
        
        const newSelected = [...selected, id];
        setSelected(newSelected);
        
        if (newSelected.length === 2) {
            const [first, second] = newSelected;
            if (cards[first].emoji === cards[second].emoji) {
                playSound('success');
                setTimeout(() => {
                    setCards(prev => prev.map((c, i) => (i === first || i === second) ? { ...c, matched: true } : c));
                    setSelected([]);
                }, 500);
            } else {
                playSound('error');
                setTimeout(() => {
                    setCards(prev => prev.map((c, i) => (i === first || i === second) ? { ...c, flipped: false } : c));
                    setSelected([]);
                }, 1000);
            }
        }
    };

    return (
        <div className="flex-1 bg-gradient-to-br from-orange-100 to-rose-200 p-8 flex flex-col items-center justify-center animate-in fade-in h-full relative">
            <div className="absolute top-4 left-4">
                <button onClick={onBack} className="px-4 py-2 bg-white rounded-full font-bold shadow-md hover:scale-105 transition-transform text-slate-700">← Back</button>
            </div>
            
            <div className="grid grid-cols-4 gap-4 max-w-2xl w-full">
                {cards.map((card, i) => (
                    <button 
                        key={i} 
                        onClick={() => handleCardClick(i)}
                        className={`aspect-square rounded-2xl shadow-md text-6xl flex items-center justify-center transition-all duration-500 transform
                            ${card.flipped || card.matched ? 'bg-white rotate-y-180 scale-100' : 'bg-orange-400 rotate-y-0 scale-95 hover:scale-100'}
                        `}
                    >
                        {(card.flipped || card.matched) ? card.emoji : '🐾'}
                    </button>
                ))}
            </div>
            {cards.every(c => c.matched) && cards.length > 0 && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center backdrop-blur-sm z-20">
                    <div className="bg-white p-8 rounded-3xl animate-bounce text-center">
                        <h2 className="text-4xl font-black mb-4">You Did It! 🎉</h2>
                        <button onClick={() => window.location.reload()} className="px-8 py-3 bg-orange-500 text-white rounded-full font-bold text-xl">Play Again</button>
                    </div>
                </div>
            )}
        </div>
    );
};
