import React, { useState } from 'react';
import { useGameSound } from '../../hooks/useGameSound';
import { gameService } from '../../services/gameService';
import { LightBulbIcon, SparklesIcon } from '../Icons';
import { useIBLM } from '../../context/IBLMContext';

const INITIAL_BOARD = [
    ['♜', '♞', '♝', '♛', '♚', '♝', '♞', '♜'],
    ['♟', '♟', '♟', '♟', '♟', '♟', '♟', '♟'],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['♙', '♙', '♙', '♙', '♙', '♙', '♙', '♙'],
    ['♖', '♘', '♗', '♕', '♔', '♗', '♘', '♖'],
];

export const ChessGame: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const playSound = useGameSound();
    const { startInteraction, endInteraction } = useIBLM();
    const [board, setBoard] = useState(INITIAL_BOARD);
    const [selectedPos, setSelectedPos] = useState<{r: number, c: number} | null>(null);
    const [turn, setTurn] = useState<'white' | 'black'>('white');
    const [chessAdvice, setChessAdvice] = useState<string>('');
    const [adviceLoading, setAdviceLoading] = useState(false);

    const handleChessClick = (r: number, c: number) => {
        const piece = board[r][c];
        const isWhitePiece = '♙♖♘♗♕♔'.includes(piece);
        
        // Select logic
        if (selectedPos === null) { 
            if (piece && isWhitePiece && turn === 'white') { 
                setSelectedPos({r, c}); 
                playSound('click'); 
                startInteraction('chess', 'game');
            } 
            return; 
        }
        
        // Change selection
        if (isWhitePiece) { setSelectedPos({r, c}); playSound('click'); return; }
        
        // Move logic
        const prevPiece = board[selectedPos.r][selectedPos.c];
        playSound('click');
        const newBoard = [...board.map(row => [...row])];
        newBoard[r][c] = prevPiece; 
        newBoard[selectedPos.r][selectedPos.c] = '';
        
        setBoard(newBoard); 
        setSelectedPos(null); 
        setTurn('black'); 
        setChessAdvice('');
        
        // CPU Move (Black)
        setTimeout(() => {
            // Import dynamic move
            import('../../services/localGames').then(({ getLocalChessMove }) => {
               const move = getLocalChessMove(newBoard, 'black');
               if (move) {
                   const cpuBoard = [...newBoard.map(row => [...row])];
                   cpuBoard[move.to.r][move.to.c] = cpuBoard[move.from.r][move.from.c];
                   cpuBoard[move.from.r][move.from.c] = '';
                   setBoard(cpuBoard);
                   playSound('click');
               }
               setTurn('white');
            });
        }, 1000);
    };

    const getHint = async () => { 
        playSound('click'); 
        setAdviceLoading(true); 
        const advice = await gameService.getChessHint(board, turn); 
        setChessAdvice(advice); 
        setAdviceLoading(false); 
    };

    return (
        <div className="flex-1 bg-slate-200 p-4 flex flex-col md:flex-row gap-8 items-center justify-center animate-in fade-in h-full">
            <div className="absolute top-4 left-4">
                <button onClick={() => { endInteraction(true, 'Chess', 'chess'); onBack(); }} className="px-4 py-2 bg-white rounded-full font-bold shadow-md hover:scale-105 transition-transform text-slate-700">← Back</button>
            </div>

            <div className="bg-[#b58863] p-4 rounded-lg shadow-2xl">
                <div className="grid grid-cols-8 gap-0 border-4 border-[#5d4037]">
                    {board.map((row, r) => row.map((piece, c) => {
                        const isBlack = (r + c) % 2 === 1;
                        const isSelected = selectedPos?.r === r && selectedPos?.c === c;
                        return (
                            <div 
                              key={`${r}-${c}`} 
                              onClick={() => handleChessClick(r, c)}
                              className={`w-10 h-10 md:w-16 md:h-16 flex items-center justify-center text-3xl md:text-5xl cursor-pointer
                                  ${isBlack ? 'bg-[#8b4513]' : 'bg-[#f0d9b5]'}
                                  ${isSelected ? 'ring-4 ring-yellow-400 z-10' : ''}
                              `}
                            >
                                <span className={['♟','♜','♞','♝','♛','♚'].includes(piece) ? 'text-black drop-shadow-sm' : 'text-white drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]'}>
                                    {piece}
                                </span>
                            </div>
                        );
                    }))}
                </div>
            </div>
            <div className="flex flex-col gap-4 w-full md:w-64">
                <div className="bg-white p-6 rounded-2xl shadow-lg">
                    <h3 className="font-black text-slate-800 text-lg mb-2">Chess Coach 🦉</h3>
                    <div className="min-h-[80px] text-slate-600 text-sm italic bg-slate-50 p-4 rounded-xl border border-slate-100">
                        {chessAdvice || "Click 'Hint' and I'll help you find a great move!"}
                    </div>
                    <button onClick={getHint} disabled={adviceLoading} className="w-full mt-4 py-3 bg-yellow-400 hover:bg-yellow-500 text-black font-bold rounded-xl shadow-md active:translate-y-1 transition-all flex items-center justify-center gap-2">
                        {adviceLoading ? <SparklesIcon className="animate-spin"/> : <LightBulbIcon />} 
                        {adviceLoading ? 'Analyzing...' : 'Give me a Hint!'}
                    </button>
                </div>
            </div>
        </div>
    );
};
