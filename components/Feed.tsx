import React, { useState, useEffect } from 'react';
import { generateFunFact, generateLibrary, generateStory, generateImage, promptForKey } from '../services/gemini';
import { FeedItem, ParentSettings, Book, Story, ImageSize } from '../types';
import { useIBLM } from '../context/IBLMContext';
import { SparklesIcon, BookIcon, XIcon, PlayIcon } from './Icons';
import { QuizOverlay } from './QuizOverlay';

const DEFAULT_TOPICS = ['Dinosaurs', 'Space', 'Ocean', 'Insects', 'Robots', 'Castles', 'Jungle'];

const SEED_FACTS: FeedItem[] = [
    {
        id: 'seed-1',
        title: 'Space',
        topic: 'Space',
        fact: "Did you know? One million Earths could fit inside the Sun! It's like a giant beach ball compared to a tiny grain of sand.",
        imageUrl: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80'
    },
    {
        id: 'seed-2',
        title: 'Dinosaurs',
        topic: 'Dinosaurs',
        fact: "The T-Rex had teeth the size of bananas! But don't worry, they are all gone now.",
        imageUrl: 'https://images.unsplash.com/photo-1583144573429-4c54cb432072?auto=format&fit=crop&w=800&q=80'
    },
    {
        id: 'seed-3',
        title: 'Ocean',
        topic: 'Ocean',
        fact: "Octopuses have three hearts! Two pump blood to the gills, and one pumps it to the rest of the body.",
        imageUrl: 'https://images.unsplash.com/photo-1582967788606-a171f1080ca8?auto=format&fit=crop&w=800&q=80'
    }
];

const SEED_BOOKS: Book[] = [
    {
        id: 'seed-b-1',
        title: 'The Magical Forest',
        emoji: '🌲',
        description: 'Discover the hidden secrets of the whispering woods.',
        color: 'bg-green-500',
        coverImage: 'https://images.unsplash.com/photo-1448375240586-dfd8d395ea6c?auto=format&fit=crop&w=800&q=80'
    },
    {
        id: 'seed-b-2',
        title: 'Space Explorer',
        emoji: '🚀',
        description: 'Blast off on a journey to the stars and beyond!',
        color: 'bg-indigo-500',
        coverImage: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=800&q=80'
    },
    {
        id: 'seed-b-3',
        title: 'Rusty the Robot',
        emoji: '🤖',
        description: 'A friendly robot learns what it means to have a heart.',
        color: 'bg-blue-500',
        coverImage: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=800&q=80'
    }
];

export const Feed: React.FC = () => {
  const { contentMode, startInteraction, endInteraction, decideNextContent } = useIBLM();
  const [activeTab, setActiveTab] = useState<'FACTS' | 'LIBRARY'>('FACTS');
  const [showQuizFor, setShowQuizFor] = useState<string | null>(null);
  const [activeChallenge, setActiveChallenge] = useState<Record<string, boolean>>({});
  
  // Facts State
  const [items, setItems] = useState<FeedItem[]>(SEED_FACTS);
  const [loadingFacts, setLoadingFacts] = useState(false);
  
  // Library State
  const [books, setBooks] = useState<Book[]>(SEED_BOOKS);
  const [loadingLibrary, setLoadingLibrary] = useState(false);
  
  // Reader State
  const [activeBook, setActiveBook] = useState<Book | null>(null);
  const [currentStory, setCurrentStory] = useState<Story | null>(null);
  const [storyLoading, setStoryLoading] = useState(false);
  
  // Page -1 is Cover, 0+ are story pages
  const [currentPage, setCurrentPage] = useState(-1);
  const [pageImages, setPageImages] = useState<Record<number, string>>({});
  const [coverImage, setCoverImage] = useState<string | null>(null);

  const [settings, setSettings] = useState<ParentSettings | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem('parent_settings');
    const parsed = JSON.parse(saved || 'null');
    setSettings(parsed);
    // Don't auto-load on mount if we have seeds, user can load more.
    // Actually, let's load more in background to append, but keep seeds visual immediately.
  }, []);

  // --- Facts Logic ---
  const loadFeed = async (currentSettings: ParentSettings | null) => {
    setLoadingFacts(true);
    const newItems: FeedItem[] = [];
    
    let topicPool = DEFAULT_TOPICS;
    if (currentSettings && currentSettings.focusTopics.length > 0) {
        topicPool = [...DEFAULT_TOPICS, ...currentSettings.focusTopics, ...currentSettings.focusTopics];
    }
    
    for (let i = 0; i < 3; i++) {
      const topic = topicPool[Math.floor(Math.random() * topicPool.length)];
      const id = Date.now() + i;
      // Use LoremFlickr for topic-relevant images instead of random picsum
      const imageUrl = `https://loremflickr.com/800/600/${topic.toLowerCase().replace(' ', ',')}?random=${id}`;
      
      const fact = await generateFunFact(topic, currentSettings || undefined);
      
      newItems.push({
        id: id.toString(),
        title: topic,
        fact: fact,
        imageUrl,
        topic
      });
    }
    setItems(prev => [...newItems, ...prev]); // Add new items to top
    setLoadingFacts(false);
  };

  // --- Library Logic ---
  const loadLibrary = async (currentSettings: ParentSettings | null) => {
      setLoadingLibrary(true);
      try {
          const library = await generateLibrary(currentSettings || undefined);
          // Assign random seed image to generated books if they lack one
          const libraryWithImages = library.map((b, i) => ({
             ...b,
             coverImage: `https://loremflickr.com/800/600/${b.title.split(' ')[0]}?random=${Date.now()+i}`
          }));
          setBooks(prev => [...prev, ...libraryWithImages]);
      } catch (e) {
          console.error("Library error", e);
      }
      setLoadingLibrary(false);
  }

  const openBook = async (book: Book) => {
      setActiveBook(book);
      setStoryLoading(true);
      setCurrentStory(null);
      setCurrentPage(-1); // Start at cover
      setPageImages({});
      setCoverImage(null);
      
      try {
          const story = await generateStory(book.title);
          setCurrentStory(story);
          
          // Generate Cover Image using Nano Banana (Flash Image)
          generateImage(story.coverPrompt || `${book.title} book cover cute`, ImageSize.S_1K, 'gemini-2.5-flash-image')
            .then(img => setCoverImage(img))
            .catch(e => console.warn("Cover gen failed", e));
            
          // Pre-generate Page 0 image if needed
          if (story.pages.length > 0 && story.pages[0].imagePrompt) {
              generatePageImage(0, story.pages[0].imagePrompt);
          }
      } catch (e: any) {
          if (e.toString().includes('403') || e.toString().includes('permission')) {
              if (window.confirm("To read this magical story, please connect your account.")) {
                  await promptForKey();
              }
          } else {
            alert("Could not open book. Try another one!");
          }
          setActiveBook(null);
      }
      setStoryLoading(false);
  }

  const generatePageImage = async (pageIndex: number, prompt: string) => {
      if (pageImages[pageIndex]) return; // Already exists
      try {
          const img = await generateImage(prompt, ImageSize.S_1K, 'gemini-2.5-flash-image');
          if (img) {
              setPageImages(prev => ({ ...prev, [pageIndex]: img }));
          }
      } catch (e) { console.warn("Image gen failed", e); }
  }

  const handleNextPage = () => {
      if (!currentStory) return;
      if (currentPage < currentStory.pages.length - 1) {
          const next = currentPage + 1;
          setCurrentPage(next);
          // Trigger image gen for next page if needed
          if (currentStory.pages[next]?.imagePrompt) {
              generatePageImage(next, currentStory.pages[next].imagePrompt!);
          }
      } else {
          // Close book at end
          setActiveBook(null);
      }
  }

  const handlePrevPage = () => {
      if (currentPage > -1) setCurrentPage(currentPage - 1);
  }

  return (
    <div className="flex flex-col font-sans w-full min-h-full">
      {/* IBLM mood banner (spec §3.2 adaptation) */}
      {contentMode === 'CALMING_ESCAPE' && (
        <div className="bg-gradient-to-r from-violet-100 to-indigo-100 border-b border-violet-200 px-4 py-2 flex items-center gap-2 shrink-0">
          <span className="text-2xl">🫧</span>
          <span className="text-sm font-bold text-violet-800 font-display">Calm mode — take a breath.</span>
        </div>
      )}
      {contentMode === 'SHORT_BURST' && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center gap-2 shrink-0">
          <span className="text-2xl">⚡</span>
          <span className="text-sm font-bold text-amber-800 font-display">Quick facts mode!</span>
        </div>
      )}
      
      {/* Tab Switcher – Claymorphism */}
      <div className="p-3 sm:p-4 z-20 shrink-0 sticky top-0 bg-background/95 backdrop-blur-sm">
        <div className="bg-white/50 p-1.5 rounded-3xl shadow-clay-inset flex items-center gap-2 max-w-md mx-auto">
           <button
             type="button"
             onClick={() => setActiveTab('FACTS')}
             className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl font-bold font-display text-base transition-all duration-300 ${
                activeTab === 'FACTS' 
                ? 'bg-primary text-white shadow-clay scale-[1.02]' 
                : 'text-slate-400 hover:text-slate-600 hover:bg-white/40'
             }`}
           >
               <SparklesIcon className="w-5 h-5 shrink-0" />
               <span className="truncate">Daily Facts</span>
           </button>
           <button
             type="button"
             onClick={() => setActiveTab('LIBRARY')}
             className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl font-bold font-display text-base transition-all duration-300 ${
                activeTab === 'LIBRARY' 
                ? 'bg-cta text-white shadow-clay scale-[1.02]' 
                : 'text-slate-400 hover:text-slate-600 hover:bg-white/40'
             }`}
           >
               <BookIcon className="w-5 h-5 shrink-0" />
               <span className="truncate">Library</span>
           </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 w-full relative pb-8">
        
        {activeTab === 'FACTS' && (
            <div className="px-4 pb-24 w-full">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 max-w-[1600px] mx-auto">
                    {items.map((item) => (
                        <div 
                            key={item.id} 
                            onMouseEnter={() => {
                                const rec = decideNextContent(item.topic, item.id);
                                if (rec.isChallenge) {
                                    setActiveChallenge(prev => ({ ...prev, [item.id]: true }));
                                }
                                startInteraction(item.id, 'fact');
                            }}
                            onMouseLeave={() => {
                                endInteraction(true, item.topic, item.id);
                                if (activeChallenge[item.id]) {
                                    setShowQuizFor(item.topic);
                                    setActiveChallenge(prev => {
                                        const next = { ...prev };
                                        delete next[item.id];
                                        return next;
                                    });
                                }
                            }}
                            className="w-full bg-white rounded-[32px] overflow-hidden shadow-clay transform transition hover:scale-[1.02] hover:shadow-xl flex flex-col"
                        >
                            <div className="relative aspect-[4/5] w-full">
                                <img 
                                    src={item.imageUrl} 
                                    alt={item.topic} 
                                    className="absolute inset-0 w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>
                                <div className="absolute bottom-0 left-0 right-0 p-6">
                                    <span className="inline-block px-4 py-1.5 bg-secondary text-white font-black font-display rounded-full text-xs uppercase tracking-wider mb-2 shadow-sm border-2 border-white/20">
                                        {item.topic}
                                    </span>
                                    <p className="text-white text-2xl font-black font-display leading-tight drop-shadow-md line-clamp-4">
                                        {item.fact}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                
                <div className="flex justify-center py-12">
                    {loadingFacts ? (
                        <div className="animate-bounce flex flex-col items-center gap-2 text-primary">
                            <SparklesIcon className="w-10 h-10" />
                            <span className="font-bold font-display text-lg">Finding cool facts...</span>
                        </div>
                    ) : (
                        <button
                            type="button"
                            onClick={() => loadFeed(settings)}
                            className="px-8 py-4 bg-white text-primary rounded-full font-black font-display text-lg shadow-clay hover:scale-105 active:scale-95 transition-all border-2 border-primary/10"
                        >
                            Load More Facts!
                        </button>
                    )}
                </div>
            </div>
        )}

        {activeTab === 'LIBRARY' && (
            <div className="px-4 pb-24">
                <div className="mb-6 text-center sm:text-left max-w-6xl mx-auto">
                    <h2 className="text-3xl font-black text-text mb-2 font-display">Reading Time! 📚</h2>
                    <p className="text-slate-500 font-medium">Pick a book to start a magical adventure.</p>
                </div>

                {loadingLibrary && books.length === 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-6xl mx-auto">
                        {[1,2,3,4,5,6].map(i => (
                            <div key={i} className="aspect-[3/4] bg-white rounded-3xl animate-pulse shadow-clay-sm" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6 max-w-6xl mx-auto">
                        {books.map((book) => (
                            <button
                                type="button"
                                key={book.id}
                                onClick={() => openBook(book)}
                                className={`aspect-[3/4] rounded-3xl p-5 flex flex-col justify-between shadow-clay hover:shadow-xl transform hover:-translate-y-1 active:scale-[0.98] transition-all text-left ${book.color} text-white relative overflow-hidden group`}
                            >
                                <div className="absolute top-0 right-0 w-32 h-32 bg-white/20 rounded-full -mr-12 -mt-12 blur-2xl"></div>
                                
                                {book.coverImage && (
                                    <img src={book.coverImage} className="absolute inset-0 w-full h-full object-cover opacity-50 mix-blend-overlay" alt="" />
                                )}

                                <div className="relative z-10 w-full">
                                    <div className="text-6xl mb-4 transform group-hover:scale-110 transition-transform filter drop-shadow-lg">{book.emoji}</div>
                                    <h3 className="font-black text-2xl leading-none mb-2 font-display drop-shadow-md">{book.title}</h3>
                                    <p className="text-sm font-bold opacity-90 line-clamp-2 leading-snug">{book.description}</p>
                                </div>
                                <div className="flex justify-end mt-2">
                                    <div className="w-10 h-10 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center font-bold text-white shadow-sm group-hover:bg-white group-hover:text-primary transition-colors">
                                        <PlayIcon className="w-5 h-5 ml-0.5" />
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>
        )}
      </div>

      {/* --- IMMERSIVE BOOK READER --- */}
      {activeBook && (
          <div className="fixed inset-0 z-[100] bg-[#2d1b0e] flex items-center justify-center p-0 md:p-8 overflow-hidden animate-in fade-in duration-300">
              {/* Background Wood Texture/Table */}
              <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/wood-pattern.png')] opacity-20 pointer-events-none"></div>

              {/* Close Button – safe area and min touch target */}
              <button
                type="button"
                onClick={() => setActiveBook(null)}
                className="absolute z-50 w-14 h-14 bg-black/40 hover:bg-black/60 text-white rounded-full flex items-center justify-center transition-colors backdrop-blur-md active:scale-95 right-4 top-4"
                style={{ top: 'max(1rem, env(safe-area-inset-top))' }}
              >
                  <XIcon className="w-8 h-8" />
              </button>

              <div className="relative w-full h-[100dvh] md:h-[85vh] md:aspect-[1.5/1] max-w-6xl md:rounded-[40px] shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex transition-all duration-500 perspective-1000 bg-[#fdfbf7] overflow-hidden">
                  
                  {/* --- LOADING STATE --- */}
                  {storyLoading && (
                      <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-[#fdfbf7] text-center p-8">
                          <div className="text-9xl animate-bounce mb-8">{activeBook.emoji}</div>
                          <h2 className="text-4xl font-display font-black text-slate-800 mb-2">Printing "{activeBook.title}"...</h2>
                          <div className="w-64 h-4 bg-slate-100 rounded-full overflow-hidden mt-8 shadow-inner">
                              <div className="h-full bg-cta animate-progress rounded-full"></div>
                          </div>
                      </div>
                  )}

                  {/* --- BOOK CONTENT --- */}
                  {!storyLoading && currentStory && (
                      <>
                        {/* Cover View */}
                        {currentPage === -1 ? (
                             <div className="w-full h-full flex flex-col md:flex-row bg-orange-900 relative">
                                  {/* Front Cover Art */}
                                  <div className="flex-1 relative overflow-hidden">
                                      {coverImage ? (
                                          <img src={coverImage} className="w-full h-full object-cover opacity-90" alt="Cover" />
                                      ) : (
                                          <div className="w-full h-full bg-orange-800 flex items-center justify-center text-white/20"><SparklesIcon className="w-32 h-32" /></div>
                                      )}
                                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
                                      <div className="absolute bottom-12 left-8 right-8 text-white">
                                          <h1 className="text-5xl md:text-7xl font-display font-black leading-[0.9] mb-4 drop-shadow-xl text-yellow-100">{currentStory.title}</h1>
                                          <p className="text-2xl font-handwriting opacity-90 text-orange-100">A magical story for you</p>
                                      </div>
                                  </div>
                                  
                                  {/* Cover Actions */}
                                  <div className="h-32 md:h-full md:w-96 bg-[#fdfbf7] md:border-l-4 md:border-orange-950/20 flex md:flex-col items-center justify-center p-6 shrink-0 z-10 shadow-2xl relative">
                                       {/* Paper texture on sidebar */}
                                       <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cream-paper.png')] opacity-50 pointer-events-none"></div>
                                       
                                       <div className="hidden md:block text-center mb-12 relative z-10">
                                           <div className="text-8xl mb-6 filter drop-shadow-md">{activeBook.emoji}</div>
                                           <p className="font-display font-bold text-slate-400 uppercase tracking-widest text-sm">WonderFeed Library</p>
                                       </div>
                                       
                                       <button
                                          type="button"
                                          onClick={handleNextPage}
                                          className="w-full md:w-auto min-h-[64px] px-10 py-4 bg-cta hover:bg-orange-600 text-white font-black rounded-3xl shadow-clay text-xl flex items-center justify-center gap-3 transition-transform hover:scale-105 active:scale-95 relative z-10"
                                       >
                                           <BookIcon className="w-7 h-7" /> Open Book
                                       </button>
                                  </div>
                             </div>
                        ) : (
                            // --- OPEN BOOK VIEW ---
                            <div className="w-full h-full flex flex-col md:flex-row bg-[#fdfbf7] relative">
                                
                                {/* Center Spine (Desktop Only) */}
                                <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-12 -ml-6 z-20 bg-gradient-to-r from-stone-900/5 via-stone-900/10 to-stone-900/5 rounded-md pointer-events-none blur-sm"></div>

                                {/* LEFT PAGE: Visuals */}
                                <div className="flex-1 h-[45%] md:h-full relative overflow-hidden bg-slate-100 md:rounded-l-[40px]">
                                     {currentStory.pages[currentPage].imagePrompt ? (
                                         <div className="w-full h-full relative group">
                                             {pageImages[currentPage] ? (
                                                <img src={pageImages[currentPage]} className="w-full h-full object-cover" alt="Illustration" />
                                             ) : (
                                                 <div className="w-full h-full flex flex-col items-center justify-center bg-orange-50 text-orange-300 gap-4">
                                                     <SparklesIcon className="w-16 h-16 animate-spin" />
                                                     <p className="text-sm font-bold uppercase tracking-widest opacity-50">Painting Scene...</p>
                                                 </div>
                                             )}
                                             {/* Paper Texture Overlay */}
                                             <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/canvas-orange.png')] opacity-20 mix-blend-multiply pointer-events-none"></div>
                                             {/* Inner Shadow */}
                                             <div className="absolute inset-0 shadow-[inset_0_0_60px_rgba(0,0,0,0.1)] pointer-events-none"></div>
                                         </div>
                                     ) : (
                                         <div className="w-full h-full flex items-center justify-center bg-[#fdfbf7] p-8">
                                             <div className="text-9xl opacity-5">{activeBook.emoji}</div>
                                         </div>
                                     )}
                                </div>

                                {/* RIGHT PAGE: Text */}
                                <div className="flex-1 h-[55%] md:h-full flex flex-col relative md:rounded-r-[40px] bg-[#fdfbf7]">
                                     {/* Paper Texture */}
                                     <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cream-paper.png')] opacity-60 pointer-events-none"></div>
                                     
                                     {/* Content */}
                                     <div className="flex-1 p-8 md:p-16 lg:p-20 overflow-y-auto flex flex-col justify-center text-center md:text-left relative z-10">
                                         <p className="text-2xl md:text-4xl lg:text-5xl font-display font-medium text-slate-800 leading-relaxed drop-shadow-sm whitespace-pre-wrap">
                                             {currentStory.pages[currentPage].text}
                                         </p>
                                     </div>

                                     {/* Page Number */}
                                     <div className="absolute bottom-8 left-0 right-0 text-center text-slate-400 font-display font-bold text-sm">
                                         Page {currentPage + 1}
                                     </div>

                                     {/* Navigation Controls – mobile-friendly touch targets */}
                                     <div className="h-24 min-h-[88px] shrink-0 flex items-center justify-between px-6 md:px-12 z-20 relative pb-[max(env(safe-area-inset-bottom),20px)]">
                                          <button
                                            type="button"
                                            onClick={handlePrevPage}
                                            className="w-14 h-14 rounded-full border-2 border-slate-200 flex items-center justify-center text-slate-400 hover:text-slate-800 hover:border-slate-800 transition-all hover:bg-slate-100 active:scale-95"
                                          >
                                              <span className="text-2xl">←</span>
                                          </button>
                                          {/* Fixed: Use currentStory.pages.length to check for last page */}
                                          <button
                                            type="button"
                                            onClick={handleNextPage}
                                            className="px-8 py-4 bg-secondary hover:bg-teal-400 text-white font-black rounded-2xl shadow-clay hover:shadow-lg hover:-translate-y-1 active:scale-95 transition-all text-xl flex items-center gap-2"
                                          >
                                              {currentPage === currentStory.pages.length - 1 ? 'Finish' : 'Next'} <span className="text-2xl">→</span>
                                          </button>
                                     </div>
                                </div>
                            </div>
                        )}

      {showQuizFor && (
          <QuizOverlay 
              topic={showQuizFor} 
              onClose={() => setShowQuizFor(null)} 
          />
      )}
                      </>
                  )}
              </div>
          </div>
      )}

    </div>
  );
};
