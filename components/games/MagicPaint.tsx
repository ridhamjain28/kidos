import React, { useState, useRef, useEffect } from 'react';
import { useGameSound } from '../../hooks/useGameSound';
import { gameService } from '../../services/gameService';
import { PencilIcon, EraserIcon, TrashIcon, DownloadIcon, CircleIcon, SquareIcon, FillIcon, LightBulbIcon, XIcon } from '../Icons';

type Tool = 'BRUSH' | 'ERASER' | 'FILL' | 'CIRCLE' | 'SQUARE';

interface Particle {
    x: number; y: number; vx: number; vy: number; life: number; color: string; size: number;
}
const COLORS = ['#EF4444', '#F97316', '#EAB308', '#22C55E', '#3B82F6', '#A855F7', '#EC4899', '#000000'];

export const MagicPaint: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const playSound = useGameSound();
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const particlesCanvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const snapshotRef = useRef<ImageData | null>(null);
    const startPosRef = useRef<{x: number, y: number} | null>(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [color, setColor] = useState('#EC4899');
    const [tool, setTool] = useState<Tool>('BRUSH');
    const [brushSize, setBrushSize] = useState(5);
    const particles = useRef<Particle[]>([]);
    const animationFrameId = useRef<number>(0);
    const [drawingGuess, setDrawingGuess] = useState<string>('');
    const [guessing, setGuessing] = useState(false);

    const handleInspiration = async () => {
        playSound('magic');
        setGuessing(true);
        // Hybrid check: If AI available, user might want to Guess (Identify), OR we stick to inspiration.
        // User asked for "Inspiration" in local, "Identify" was the original.
        // Let's offer Inspiration primarily, but if we had a "Guess my Drawing" button we could use identifyDrawing.
        // For now, let's keep it simple: Inspiration works everywhere. 
        const prompt = gameService.getInspiration();
        setDrawingGuess(prompt); 
        setGuessing(false);
    };

    const handleGuess = async () => {
        if (!canvasRef.current || !gameService.hasKey) return;
        setGuessing(true);
        const base64 = canvasRef.current.toDataURL('image/png');
        try {
            const guess = await gameService.identifyDrawing(base64);
            setDrawingGuess(guess);
        } catch(e) { console.error(e); }
        setGuessing(false);
    }

    // --- Canvas Logic ---
    useEffect(() => {
        if (containerRef.current) {
            const { width, height } = containerRef.current.getBoundingClientRect();
            if (canvasRef.current && particlesCanvasRef.current) {
                if (canvasRef.current.width !== width) { 
                   const tempCanvas = document.createElement('canvas');
                   tempCanvas.width = canvasRef.current.width;
                   tempCanvas.height = canvasRef.current.height;
                   tempCanvas.getContext('2d')?.drawImage(canvasRef.current, 0, 0);
                   canvasRef.current.width = width; canvasRef.current.height = height;
                   particlesCanvasRef.current.width = width; particlesCanvasRef.current.height = height;
                   const ctx = canvasRef.current.getContext('2d');
                   if (ctx) { ctx.fillStyle = '#FFFFFF'; ctx.fillRect(0, 0, width, height); ctx.lineCap='round'; ctx.drawImage(tempCanvas, 0, 0); }
                }
            }
        }
    }, []);

    useEffect(() => {
        const animate = () => {
            if (particlesCanvasRef.current) {
                const ctx = particlesCanvasRef.current.getContext('2d');
                if (ctx) {
                    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                    for (let i = particles.current.length - 1; i >= 0; i--) {
                        const p = particles.current[i];
                        p.x += p.vx; p.y += p.vy; p.life -= 0.02; p.size *= 0.95;
                        if (p.life <= 0) { particles.current.splice(i, 1); continue; }
                        ctx.globalAlpha = p.life; ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2); ctx.fill();
                    }
                }
            }
            animationFrameId.current = requestAnimationFrame(animate);
        };
        animate();
        return () => cancelAnimationFrame(animationFrameId.current);
    }, []);

    // Drawing Handlers
    const getCoordinates = (e: any) => {
        if (!canvasRef.current) return { x: 0, y: 0 };
        const rect = canvasRef.current.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return { x: clientX - rect.left, y: clientY - rect.top };
    };
    const startDrawing = (e: any) => {
        if (!canvasRef.current) return;
        playSound('draw');
        const { x, y } = getCoordinates(e);
        if (tool === 'FILL') return; 
        setIsDrawing(true); startPosRef.current = { x, y };
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) { ctx.beginPath(); ctx.moveTo(x, y); if (['CIRCLE', 'SQUARE'].includes(tool)) snapshotRef.current = ctx.getImageData(0, 0, canvasRef.current.width, canvasRef.current.height); }
        if (tool === 'BRUSH') draw(e);
    };
    const draw = (e: any) => {
        if (!isDrawing || !canvasRef.current) return;
        const ctx = canvasRef.current.getContext('2d');
        if (!ctx) return;
        const { x, y } = getCoordinates(e);
        if (['CIRCLE', 'SQUARE'].includes(tool) && snapshotRef.current) {
            ctx.putImageData(snapshotRef.current, 0, 0);
            ctx.lineWidth = brushSize; ctx.strokeStyle = color;
            const sx = startPosRef.current!.x; const sy = startPosRef.current!.y;
            ctx.beginPath();
            if (tool === 'SQUARE') ctx.rect(sx, sy, x - sx, y - sy);
            else ctx.arc(sx, sy, Math.sqrt(Math.pow(x-sx,2) + Math.pow(y-sy,2)), 0, 2 * Math.PI);
            ctx.stroke(); return;
        }
        ctx.lineWidth = brushSize; ctx.strokeStyle = tool === 'ERASER' ? '#FFFFFF' : color;
        ctx.lineTo(x, y); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x, y);
        if (tool === 'BRUSH') for(let i=0;i<2;i++) particles.current.push({x, y, vx:(Math.random()-.5)*5, vy:(Math.random()-.5)*5, life:1, color, size: Math.random()*5+2});
    };
    const stopDrawing = () => { if(isDrawing) playSound('click'); setIsDrawing(false); snapshotRef.current = null; startPosRef.current = null; canvasRef.current?.getContext('2d')?.beginPath(); };
    const clearCanvas = () => { const ctx = canvasRef.current?.getContext('2d'); if(ctx) { ctx.fillStyle = '#FFFFFF'; ctx.fillRect(0,0,ctx.canvas.width,ctx.canvas.height); } setDrawingGuess(''); playSound('click'); };

    return (
        <div className="flex-1 flex flex-col h-full bg-white relative animate-in fade-in">
             <div className="absolute top-4 left-4 z-50">
                <button onClick={onBack} className="px-4 py-2 bg-slate-100 rounded-full font-bold shadow-md hover:scale-105 transition-transform text-slate-700">← Back</button>
            </div>

            {drawingGuess && (
                <div className="absolute top-4 left-16 right-4 lg:left-32 bg-purple-600 text-white p-4 rounded-xl shadow-lg z-40 animate-in slide-in-from-top fade-in flex items-center justify-between">
                    <div className="flex items-center gap-3"><LightBulbIcon className="w-6 h-6 text-yellow-300" /><p className="font-bold">{drawingGuess}</p></div>
                    <button onClick={() => setDrawingGuess('')}><XIcon className="w-5 h-5 opacity-50" /></button>
                </div>
            )}
            <div ref={containerRef} className="flex-1 relative cursor-crosshair bg-white">
                <canvas ref={canvasRef} onMouseDown={startDrawing} onMouseMove={draw} onMouseUp={stopDrawing} onMouseLeave={stopDrawing} onTouchStart={startDrawing} onTouchMove={draw} onTouchEnd={stopDrawing} className="absolute inset-0 z-10" />
                <canvas ref={particlesCanvasRef} className="absolute inset-0 z-20 pointer-events-none" />
            </div>
            <div className="bg-purple-50 p-4 border-t-2 border-purple-100 flex flex-col gap-4 z-30">
                <div className="flex justify-between items-center">
                     <div className="flex gap-2">
                         {['BRUSH', 'FILL', 'CIRCLE', 'SQUARE', 'ERASER'].map(t => (
                             <button key={t} onClick={() => { setTool(t as Tool); playSound('click'); }} className={`p-3 rounded-xl transition-all ${tool === t ? 'bg-purple-500 text-white scale-110 shadow-lg' : 'bg-white text-purple-400'}`}>
                                 {t === 'BRUSH' && <PencilIcon className="w-6 h-6" />}
                                 {t === 'FILL' && <FillIcon className="w-6 h-6" />}
                                 {t === 'CIRCLE' && <CircleIcon className="w-6 h-6" />}
                                 {t === 'SQUARE' && <SquareIcon className="w-6 h-6" />}
                                 {t === 'ERASER' && <EraserIcon className="w-6 h-6" />}
                             </button>
                         ))}
                     </div>
                     <div className="flex gap-2">
                        <button onClick={handleInspiration} disabled={guessing} className="p-3 bg-yellow-400 text-black rounded-xl font-bold flex gap-2">{guessing ? '...' : <><LightBulbIcon className="w-6 h-6"/> Inspire Me</>}</button>
                        {/* Option: Check gameService.hasKey to show "Guess" button? For simplicity, hiding it unless user explicitly requested. User requested "when api key available use it". So let's add it if available. */}
                        {gameService.hasKey && (
                            <button onClick={handleGuess} disabled={guessing} className="p-3 bg-indigo-500 text-white rounded-xl font-bold flex gap-2">{guessing ? '...' : 'Guess?'}</button>
                        )}
                        <button onClick={clearCanvas} className="p-3 bg-red-100 text-red-500 rounded-xl"><TrashIcon className="w-6 h-6"/></button>
                        <button onClick={() => {if(canvasRef.current){const l=document.createElement('a');l.download='art.png';l.href=canvasRef.current.toDataURL();l.click();}}} className="p-3 bg-green-100 text-green-600 rounded-xl"><DownloadIcon className="w-6 h-6"/></button>
                     </div>
                </div>
                <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
                    {COLORS.map(c => <button key={c} onClick={() => { setColor(c); playSound('click'); }} className={`w-10 h-10 rounded-full border-4 ${color === c ? 'border-purple-500 scale-110' : 'border-transparent'}`} style={{ backgroundColor: c }} />)}
                </div>
            </div>
        </div>
    );
};
