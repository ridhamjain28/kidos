import { useRef, useCallback } from 'react';

export const useGameSound = () => {
    const audioCtxRef = useRef<AudioContext | null>(null);

    const playSound = useCallback((type: 'click' | 'success' | 'draw' | 'error' | 'magic' | 'pop') => {
        if (!audioCtxRef.current) {
            audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
        const ctx = audioCtxRef.current;
        if (ctx.state === 'suspended') ctx.resume();

        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        const now = ctx.currentTime;
        
        switch (type) {
            case 'click': 
                osc.frequency.setValueAtTime(600, now); 
                osc.frequency.exponentialRampToValueAtTime(300, now + 0.1); 
                gain.gain.setValueAtTime(0.1, now); 
                gain.gain.linearRampToValueAtTime(0, now + 0.1); 
                osc.start(now); osc.stop(now + 0.1); 
                break;
            case 'draw': 
                osc.type = 'triangle'; 
                osc.frequency.setValueAtTime(200, now); 
                osc.frequency.linearRampToValueAtTime(400, now + 0.1); 
                gain.gain.setValueAtTime(0.05, now); 
                gain.gain.linearRampToValueAtTime(0, now + 0.1); 
                osc.start(now); osc.stop(now + 0.1); 
                break;
            case 'magic': 
                osc.type = 'sine'; 
                osc.frequency.setValueAtTime(400, now); 
                osc.frequency.linearRampToValueAtTime(800, now + 0.3); 
                gain.gain.setValueAtTime(0.1, now); 
                gain.gain.linearRampToValueAtTime(0, now + 0.5); 
                osc.start(now); osc.stop(now + 0.5); 
                break;
            case 'pop': 
                osc.frequency.setValueAtTime(800, now); 
                osc.frequency.exponentialRampToValueAtTime(100, now + 0.1); 
                gain.gain.setValueAtTime(0.1, now); 
                gain.gain.linearRampToValueAtTime(0, now + 0.1); 
                osc.start(now); osc.stop(now + 0.1); 
                break;
            case 'success': 
                osc.type = 'square'; 
                osc.frequency.setValueAtTime(440, now); 
                osc.frequency.setValueAtTime(554, now + 0.1); 
                osc.frequency.setValueAtTime(659, now + 0.2); 
                gain.gain.setValueAtTime(0.1, now); 
                gain.gain.linearRampToValueAtTime(0, now + 0.4); 
                osc.start(now); osc.stop(now + 0.4); 
                break;
            case 'error': 
                osc.type = 'sawtooth'; 
                osc.frequency.setValueAtTime(150, now); 
                osc.frequency.linearRampToValueAtTime(100, now + 0.2); 
                gain.gain.setValueAtTime(0.1, now); 
                gain.gain.linearRampToValueAtTime(0, now + 0.2); 
                osc.start(now); osc.stop(now + 0.2); 
                break;
        }
    }, []);

    return playSound;
};
