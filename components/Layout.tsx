

import React from 'react';
import { View } from '../types';
import { HomeIcon, GamepadIcon, BrainIcon, ShieldIcon, TvIcon } from './Icons';

interface LayoutProps {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ currentView, onNavigate, children }) => {
  const NavItem = ({ view, icon, label, activeColor }: { view: View; icon: React.ReactNode; label: string; activeColor: string }) => {
    const isActive = currentView === view;
    return (
      <button
        type="button"
        onClick={() => onNavigate(view)}
        className={`relative flex flex-col items-center justify-center flex-1 h-full py-1 transition-all duration-300 ${
          isActive ? 'translate-y-[-8px]' : 'hover:bg-slate-50'
        }`}
        aria-label={label}
        aria-current={isActive ? 'page' : undefined}
      >
        <div 
          className={`
            w-12 h-12 sm:w-14 sm:h-14 rounded-2xl flex items-center justify-center mb-1 transition-all duration-300
            ${isActive 
              ? `${activeColor} shadow-clay text-white scale-110` 
              : 'bg-slate-100 text-slate-400 shadow-inner'
            }
          `}
        >
          {icon}
        </div>
        <span 
          className={`
            text-[10px] sm:text-xs font-bold tracking-wide transition-colors duration-300
            ${isActive ? 'text-slate-800 opacity-100' : 'text-slate-400 opacity-0 hidden sm:block sm:opacity-70'}
          `}
        >
          {label}
        </span>
        
        {/* Active Indicator Dot (Mobile) */}
        {isActive && (
           <div className="absolute bottom-1 w-1 h-1 rounded-full bg-slate-800 sm:hidden"></div>
        )}
      </button>
    );
  };

  return (
    <div className="min-h-[100dvh] w-full flex flex-col bg-transparent font-sans">
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col w-full mx-auto pb-[100px] sm:pb-[120px]">
         {children}
      </main>

      {/* Floating Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 z-50 pointer-events-none flex justify-center pb-[max(env(safe-area-inset-bottom),16px)] px-4">
        <nav
          className="pointer-events-auto w-full max-w-lg md:max-w-3xl lg:max-w-4xl bg-white/90 backdrop-blur-xl border border-white/50 shadow-clay-sm rounded-3xl flex items-center justify-between px-2 sm:px-8 h-[72px] sm:h-[88px]"
        >
          <NavItem 
            view={View.FEED} 
            icon={<HomeIcon className="w-6 h-6 sm:w-7 sm:h-7" />} 
            label="Home" 
            activeColor="bg-primary" 
          />
          <NavItem 
            view={View.TV} 
            icon={<TvIcon className="w-6 h-6 sm:w-7 sm:h-7" />} 
            label="TV" 
            activeColor="bg-cta" 
          />
          <NavItem 
            view={View.GAMES} 
            icon={<GamepadIcon className="w-6 h-6 sm:w-7 sm:h-7" />} 
            label="Games" 
            activeColor="bg-pink-500" 
          />
          <NavItem 
            view={View.CHAT} 
            icon={<BrainIcon className="w-6 h-6 sm:w-7 sm:h-7" />} 
            label="Hoot" 
            activeColor="bg-indigo-500" 
          />
          <NavItem 
            view={View.PARENTS} 
            icon={<ShieldIcon className="w-6 h-6 sm:w-7 sm:h-7" />} 
            label="Parents" 
            activeColor="bg-slate-700" 
          />
        </nav>
      </div>
    </div>
  );
};
