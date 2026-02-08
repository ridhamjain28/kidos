

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
      className={`flex flex-col items-center justify-center w-full min-h-[44px] py-2 transition-all duration-300 active:scale-95 ${
        currentView === view ? 'translate-y-[-6px] md:translate-y-[-8px]' : 'opacity-60'
      }`}
      aria-label={label}
    >
      <div className={`p-2.5 md:p-3 rounded-2xl shadow-lg mb-0.5 min-w-[44px] min-h-[44px] flex items-center justify-center ${currentView === view ? color : 'bg-gray-200 text-gray-500'}`}>
        {icon}
      </div>
      <span className={`text-[10px] font-bold leading-tight ${currentView === view ? 'text-gray-800' : 'text-gray-400'}`}>
        {label}
      </span>
    </button>
  );

  return (
    <div className="min-h-screen min-h-[100dvh] w-full max-w-full flex flex-col bg-gray-50 overflow-hidden">
      {/* Main Content Area */}
      <main className="flex-1 relative overflow-hidden min-h-0">
        {children}
      </main>

      {/* Bottom Navigation – safe area for notched devices */}
      <nav
        className="h-20 min-h-[5rem] bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] z-50 shrink-0"
        style={{ paddingBottom: 'max(env(safe-area-inset-bottom, 0), 8px)' }}
      >
        <div className="h-full max-w-lg mx-auto flex justify-between items-center px-1 sm:px-2">
          <NavItem 
            view={View.FEED} 
            icon={<HomeIcon className="w-6 h-6 sm:w-6 sm:h-6 text-white" />} 
            label="Home" 
            color="bg-blue-500" 
          />
          <NavItem 
            view={View.TV} 
            icon={<TvIcon className="w-6 h-6 sm:w-6 sm:h-6 text-white" />} 
            label="LearnTV" 
            color="bg-red-500" 
          />
          <NavItem 
            view={View.GAMES} 
            icon={<GamepadIcon className="w-6 h-6 sm:w-6 sm:h-6 text-white" />} 
            label="Games" 
            color="bg-pink-500" 
          />
          <NavItem 
            view={View.CHAT} 
            icon={<BrainIcon className="w-6 h-6 sm:w-6 sm:h-6 text-white" />} 
            label="Ask Hoot" 
            color="bg-indigo-600" 
          />
          <NavItem 
            view={View.PARENTS} 
            icon={<ShieldIcon className="w-6 h-6 sm:w-6 sm:h-6 text-white" />} 
            label="Parents" 
            color="bg-slate-700" 
          />
        </div>
      </nav>
    </div>
  );
};
