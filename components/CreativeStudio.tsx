import React, { useState } from 'react';
import { 
    SparklesIcon, 
    PuzzleIcon, 
    BrushIcon as PaintBrushIcon, 
    BookIcon as BookOpenIcon, 
    MathIcon as CalculatorIcon, 
    GlobeIcon, 
    AbcBlockIcon as CubeIcon 
} from './Icons';
import { ChessGame } from './games/ChessGame';
import { SpeakWorld } from './games/SpeakWorld';
import { MagicPaint } from './games/MagicPaint';
import { MathQuest } from './games/MathQuest';
import { WordHunter } from './games/WordHunter';
import { MemoryZoo } from './games/MemoryZoo';
import { BubblePop } from './games/BubblePop';

type GameMode = 'MENU' | 'DRAW' | 'CHESS' | 'STORY' | 'MATH' | 'WORD' | 'MEMORY' | 'BUBBLE';

// Helper component for game cards
const GameCard: React.FC<{title: string, icon: React.ReactNode, color: string, onClick: () => void, desc: string}> = ({ title, icon, color, onClick, desc }) => (
    <button onClick={onClick} className={`p-8 rounded-3xl border-4 text-left transition-all hover:scale-105 active:scale-95 shadow-sm hover:shadow-xl group flex flex-col gap-4 ${color}`}>
        <div className="bg-white p-4 rounded-2xl w-fit shadow-sm group-hover:rotate-6 transition-transform">
            {icon}
        </div>
        <div>
            <h3 className="text-2xl font-black text-slate-800 mb-1">{title}</h3>
            <p className="text-slate-500 font-bold text-sm">{desc}</p>
        </div>
    </button>
);

export const CreativeStudio: React.FC = () => {
    const [mode, setMode] = useState<GameMode>('MENU');

    const handleBack = () => setMode('MENU');

    if (mode === 'CHESS') return <ChessGame onBack={handleBack} />;
    if (mode === 'STORY') return <SpeakWorld onBack={handleBack} />;
    if (mode === 'DRAW') return <MagicPaint onBack={handleBack} />;
    if (mode === 'MATH') return <MathQuest onBack={handleBack} />;
    if (mode === 'WORD') return <WordHunter onBack={handleBack} />;
    if (mode === 'MEMORY') return <MemoryZoo onBack={handleBack} />;
    if (mode === 'BUBBLE') return <BubblePop onBack={handleBack} />;

    return (
        <div className="h-full overflow-y-auto p-4 md:p-8 animate-in fade-in">
            <div className="max-w-6xl mx-auto">
                <header className="mb-12 text-center">
                    <h1 className="text-5xl md:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 mb-4 font-display drop-shadow-sm">
                        Creative Studio
                    </h1>
                    <p className="text-xl text-slate-500 font-medium">Create, Play, and Learn with AI!</p>
                </header>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    <GameCard 
                        title="Magic Paint" 
                        icon={<PaintBrushIcon className="w-12 h-12 text-pink-500" />} 
                        color="bg-pink-50 border-pink-200 hover:border-pink-400" 
                        onClick={() => setMode('DRAW')} 
                        desc="Draw with AI inspiration!"
                    />
                    <GameCard 
                        title="Chess Coach" 
                        icon={<PuzzleIcon className="w-12 h-12 text-blue-500" />} 
                        color="bg-blue-50 border-blue-200 hover:border-blue-400" 
                        onClick={() => setMode('CHESS')} 
                        desc="Learn chess from a Grandmaster Owl."
                    />
                    <GameCard 
                        title="Speak World" 
                        icon={<GlobeIcon className="w-12 h-12 text-indigo-500" />} 
                        color="bg-indigo-50 border-indigo-200 hover:border-indigo-400" 
                        onClick={() => setMode('STORY')} 
                        desc="Learn languages with AI feedback."
                    />
                    <GameCard 
                        title="Math Quest" 
                        icon={<CalculatorIcon className="w-12 h-12 text-green-500" />} 
                        color="bg-green-50 border-green-200 hover:border-green-400" 
                        onClick={() => setMode('MATH')} 
                        desc="Solve fun math puzzles!"
                    />
                    <GameCard 
                        title="Word Hunter" 
                        icon={<BookOpenIcon className="w-12 h-12 text-yellow-500" />} 
                        color="bg-yellow-50 border-yellow-200 hover:border-yellow-400" 
                        onClick={() => setMode('WORD')} 
                        desc="Find hidden words!"
                    />
                    <GameCard 
                        title="Memory Zoo" 
                        icon={<CubeIcon className="w-12 h-12 text-orange-500" />} 
                        color="bg-orange-50 border-orange-200 hover:border-orange-400" 
                        onClick={() => setMode('MEMORY')} 
                        desc="Match the animals!"
                    />
                    <GameCard 
                        title="Bubble Pop" 
                        icon={<SparklesIcon className="w-12 h-12 text-cyan-500" />} 
                        color="bg-cyan-50 border-cyan-200 hover:border-cyan-400" 
                        onClick={() => setMode('BUBBLE')} 
                        desc="Pop bubbles for points!"
                    />
                </div>
            </div>
        </div>
    );
};
