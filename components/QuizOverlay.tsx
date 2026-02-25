import React, { useState } from 'react';
import { useIBLM } from '../context/IBLMContext';
import { SparklesIcon, XIcon } from './Icons';

interface QuizOverlayProps {
  topic: string;
  onClose: () => void;
}

const MOCK_QUESTIONS: Record<string, { q: string, a: string[], correct: number }[]> = {
  'Space': [
    { q: "How many Earths fit in the Sun?", a: ["One", "Ten", "One Million"], correct: 2 },
    { q: "Is the Sun a star?", a: ["Yes", "No"], correct: 0 }
  ],
  'Standard': [
    { q: "Did you enjoy learning about this?", a: ["Yes!", "It was okay", "Not really"], correct: 0 },
    { q: "Want to learn more?", a: ["Yes please!", "Maybe later"], correct: 0 }
  ]
};

export const QuizOverlay: React.FC<QuizOverlayProps> = ({ topic, onClose }) => {
  const { updateMastery } = useIBLM();
  const [step, setStep] = useState(0);
  const [score, setScore] = useState(0);
  const [complete, setComplete] = useState(false);

  const questions = MOCK_QUESTIONS[topic] || MOCK_QUESTIONS['Standard'];

  const handleAnswer = (idx: number) => {
    const isCorrect = idx === questions[step].correct;
    const newScore = isCorrect ? score + (100 / questions.length) : score;
    setScore(newScore);

    if (step < questions.length - 1) {
      setStep(step + 1);
    } else {
      setComplete(true);
      updateMastery(topic, Math.round(newScore));
    }
  };

  return (
    <div className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-lg rounded-[40px] shadow-clay p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-2 bg-slate-100">
           <div className="h-full bg-primary transition-all duration-500" style={{ width: `${((step + 1) / questions.length) * 100}%` }}></div>
        </div>

        {!complete ? (
          <div className="pt-4">
            <h3 className="text-slate-400 font-bold uppercase tracking-widest text-xs mb-2">Challenge Quiz: {topic}</h3>
            <h2 className="text-2xl font-black font-display text-slate-800 mb-8">{questions[step].q}</h2>
            <div className="space-y-4">
              {questions[step].a.map((ans, i) => (
                <button
                  key={i}
                  onClick={() => handleAnswer(i)}
                  className="w-full p-6 bg-slate-50 hover:bg-primary hover:text-white rounded-3xl font-bold text-lg text-left transition-all shadow-sm border-2 border-slate-100 hover:border-primary active:scale-95"
                >
                  {ans}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-6xl mb-6">🎉</div>
            <h2 className="text-3xl font-black font-display text-slate-800 mb-2">Great Job!</h2>
            <p className="text-slate-500 font-bold mb-8">You scored {Math.round(score)}% and earned mastery points!</p>
            <button
              onClick={onClose}
              className="px-10 py-4 bg-cta text-white font-black rounded-full text-xl shadow-clay hover:scale-105 active:scale-95 transition-all"
            >
              Back to Feed
            </button>
          </div>
        )}

        <button onClick={onClose} className="absolute top-6 right-6 text-slate-300 hover:text-slate-500 transition-colors">
          <XIcon className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};
