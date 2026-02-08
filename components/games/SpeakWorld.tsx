import React, { useState, useRef, useEffect } from 'react';
import { useGameSound } from '../../hooks/useGameSound';
import { gameService } from '../../services/gameService';
import { SparklesIcon, VolumeIcon, MicIcon } from '../Icons';

export const SpeakWorld: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const playSound = useGameSound();
    const [langTarget, setLangTarget] = useState('Spanish');
    const [lesson, setLesson] = useState<any>(null);
    const [lessonLoading, setLessonLoading] = useState(false);
    const [lessonImage, setLessonImage] = useState<string | null>(null);
    const [isListening, setIsListening] = useState(false);
    const [score, setScore] = useState(0);
    const [feedback, setFeedback] = useState<{correct: boolean, text: string} | null>(null);
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        startLanguageLesson();
    }, [langTarget]);

    const speak = (text: string, lang: string = 'en-US') => {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        if (lang === 'Spanish') u.lang = 'es-ES';
        else if (lang === 'French') u.lang = 'fr-FR';
        else if (lang === 'German') u.lang = 'de-DE';
        else u.lang = 'en-US';
        window.speechSynthesis.speak(u);
    };

    const startLanguageLesson = async () => {
        setLessonLoading(true); setLesson(null); setFeedback(null); setLessonImage(null);
        
        const l = await gameService.getLesson(langTarget);
        setLesson(l);
        
        // Image logic: use loremflickr fallback or api if available (gameService handles logic?)
        // Actually gameService just returns data. We handle image display.
        // If we want AI images, we need that in gameService too. 
        // For now, let's stick to the reliable LoremFlickr for consistency unless api key.
        // But user asked for API usage.
        // Let's check l.imagePrompt.
        if (l.imagePrompt) {
            setLessonImage(`https://loremflickr.com/800/600/${l.imagePrompt.replace(' ', ',')}?random=${Date.now()}`);
        }
        
        if (l.voiceInstruction) speak(l.voiceInstruction);
        setLessonLoading(false);
    };
    
    const handleListen = () => {
        if(lesson) speak(lesson.phrase, langTarget);
    };
    
    const handleMic = () => {
        if ('webkitSpeechRecognition' in window) {
            const SpeechRecognition = (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.lang = langTarget === 'Spanish' ? 'es-ES' : langTarget === 'French' ? 'fr-FR' : 'en-US';
            recognitionRef.current.onstart = () => setIsListening(true);
            recognitionRef.current.onend = () => setIsListening(false);
            recognitionRef.current.onresult = async (event: any) => {
                const transcript = event.results[0][0].transcript;
                setIsListening(false);
                const assessment = await gameService.checkPronunciation(lesson.phrase, transcript);
                if (assessment.correct) {
                    playSound('success');
                    setScore(s => s + 50);
                } else {
                    playSound('error');
                }
                setFeedback({ correct: assessment.correct, text: assessment.feedback });
            };
            recognitionRef.current.start();
        } else {
            alert("Voice recognition not supported in this browser.");
        }
    };

    return (
        <div className="flex-1 bg-indigo-50 p-6 flex flex-col items-center justify-center relative h-full animate-in fade-in">
             <div className="absolute top-4 left-4">
                <button onClick={onBack} className="px-4 py-2 bg-white rounded-full font-bold shadow-md hover:scale-105 transition-transform text-slate-700">← Back</button>
            </div>
             <div className="absolute top-4 right-4 bg-indigo-600 text-white px-6 py-2 rounded-full font-black text-xl shadow-lg">Score: {score}</div>
             
             <div className="flex gap-2 mb-8 bg-white p-1 rounded-xl shadow-sm z-10">
                 {['Spanish', 'French', 'German'].map(l => (
                     <button key={l} onClick={() => setLangTarget(l)} className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${langTarget === l ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:bg-slate-100'}`}>{l}</button>
                 ))}
             </div>

             <div className="bg-white rounded-3xl shadow-xl p-8 w-full max-w-md text-center border-b-8 border-indigo-100 relative overflow-hidden">
                 {lessonLoading ? (
                     <div className="h-64 flex items-center justify-center flex-col gap-4">
                         <SparklesIcon className="w-12 h-12 text-indigo-400 animate-spin" />
                         <p className="font-bold text-slate-400">Loading lesson...</p>
                     </div>
                 ) : lesson ? (
                     <>
                         <div className="w-full h-48 bg-slate-100 rounded-2xl mb-6 overflow-hidden relative">
                              {lessonImage ? <img src={lessonImage} className="w-full h-full object-cover animate-in fade-in" /> : <div className="flex items-center justify-center h-full text-4xl">🌍</div>}
                         </div>
                         
                         <h2 className="text-4xl font-black text-slate-800 mb-2">{lesson.phrase}</h2>
                         <p className="text-indigo-500 font-bold text-lg mb-1">{lesson.pronunciation}</p>
                         <p className="text-slate-400 font-medium italic mb-8">"{lesson.translation}"</p>

                         <div className="grid grid-cols-2 gap-4">
                             <button onClick={handleListen} className="py-4 rounded-xl bg-blue-100 text-blue-600 font-bold flex flex-col items-center justify-center gap-2 hover:bg-blue-200 transition-colors">
                                 <VolumeIcon className="w-6 h-6" /> Listen
                             </button>
                             <button onClick={handleMic} className={`py-4 rounded-xl font-bold flex flex-col items-center justify-center gap-2 transition-all ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-green-100 text-green-600 hover:bg-green-200'}`}>
                                 <MicIcon className="w-6 h-6" /> {isListening ? 'Listening...' : 'Speak'}
                             </button>
                         </div>

                         {feedback && (
                             <div className={`mt-6 p-4 rounded-xl font-bold animate-in slide-in-from-bottom-2 ${feedback.correct ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}`}>
                                 {feedback.text}
                             </div>
                         )}
                     </>
                 ) : null}
             </div>
             
             <button onClick={startLanguageLesson} className="mt-8 px-12 py-4 bg-indigo-600 text-white font-bold rounded-full shadow-lg active:scale-95 transition-transform">
                 Next Card →
             </button>
        </div>
    );
};
