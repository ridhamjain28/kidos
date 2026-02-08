

import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { Feed } from './components/Feed';
import { CreativeStudio } from './components/CreativeStudio';
import { ChatBuddy } from './components/ChatBuddy';
import { ParentZone } from './components/ParentZone';
import { LearnTV } from './components/LearnTV';
import { WelcomeAnimation } from './components/WelcomeAnimation';
import { FloatingBuddy } from './components/FloatingBuddy';
import { DebugHUD } from './components/DebugHUD';
import { View } from './types';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>(View.FEED);
  const [welcomeComplete, setWelcomeComplete] = useState(false);

  const handleWelcomeComplete = () => {
      setWelcomeComplete(true);
  };

  const renderView = () => {
    switch (currentView) {
      case View.FEED:
        return <Feed />;
      case View.TV:
        return <LearnTV />;
      case View.GAMES:
        return <CreativeStudio />;
      case View.CHAT:
        return <ChatBuddy />;
      case View.PARENTS:
        return <ParentZone />;
      default:
        return <Feed />;
    }
  };

  return (
    <>
        {!welcomeComplete && <WelcomeAnimation onComplete={handleWelcomeComplete} />}
        <DebugHUD />
        {/* Global Background for High-End Feel */}
        <div className="fixed inset-0 bg-[#F0FDFA] -z-10 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-teal-50 via-teal-50/50 to-transparent"></div>
        
        <Layout currentView={currentView} onNavigate={setCurrentView}>
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
             {renderView()}
          </div>
        </Layout>
        {welcomeComplete && <FloatingBuddy currentView={currentView} />}
    </>
  );
};

export default App;
