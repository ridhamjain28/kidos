

import React from 'react';
import { View } from '../types';
import { HomeIcon, GamepadIcon, BrainIcon, ShieldIcon, TvIcon } from './Icons';

interface LayoutProps {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ currentView, onNavigate, children }) => {
  const NavItem = ({ view, icon, label, color }: { view: View; icon: React.ReactNode; label: string; color: string }) => (
    <button
      type="button"
      onClick={() => onNavigate(view)}
      className={`flex flex-col items-center justify-center flex-1 min-w-0 min-h-[52px] py-1.5 sm:py-2 transition-all duration-300 active:scale-95 ${
        currentView === view ? 'translate-y-[-4px] sm:translate-y-[-6px] md:translate-y-[-8px]' : 'opacity-60'
      }`}
      aria-label={label}
    >
      <div className={`p-2 sm:p-2.5 md:p-3 rounded-xl sm:rounded-2xl shadow-lg mb-0.5 min-w-[36px] min-h-[36px] sm:min-w-[44px] sm:min-h-[44px] flex items-center justify-center flex-shrink-0 ${currentView === view ? color : 'bg-gray-200 text-gray-500'}`}>
        {icon}
      </div>
      <span className={`text-[9px] sm:text-[10px] font-bold leading-tight truncate max-w-full px-0.5 ${currentView === view ? 'text-gray-800' : 'text-gray-400'}`}>
        {label}
      </span>
    </button>
  );

  return (
    <div className="min-h-screen min-h-[100dvh] w-full max-w-full flex flex-col bg-gray-50 overflow-hidden">
      {/* Main Content Area – constrained on large screens */}
      <main className="flex-1 relative overflow-hidden min-h-0 flex flex-col max-w-7xl mx-auto w-full">
        {children}
      </main>

      {/* Bottom Navigation – always visible, safe area, no overflow */}
      <nav
        className="h-16 sm:h-20 min-h-[64px] sm:min-h-[5rem] bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] z-50 shrink-0 flex-shrink-0"
        style={{ paddingBottom: 'max(env(safe-area-inset-bottom, 0), 6px)' }}
      >
        <div className="h-full w-full max-w-2xl mx-auto flex items-stretch justify-between gap-0 px-0.5 sm:px-2">
          <NavItem 
            view={View.FEED} 
            icon={<HomeIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />} 
            label="Home" 
            color="bg-blue-500" 
          />
          <NavItem 
            view={View.TV} 
            icon={<TvIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />} 
            label="TV" 
            color="bg-red-500" 
          />
          <NavItem 
            view={View.GAMES} 
            icon={<GamepadIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />} 
            label="Games" 
            color="bg-pink-500" 
          />
          <NavItem 
            view={View.CHAT} 
            icon={<BrainIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />} 
            label="Hoot" 
            color="bg-indigo-600" 
          />
          <NavItem 
            view={View.PARENTS} 
            icon={<ShieldIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />} 
            label="Parents" 
            color="bg-slate-700" 
          />
        </div>
      </nav>
    </div>
  );
};
