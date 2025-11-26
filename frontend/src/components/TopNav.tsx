import React from 'react';

interface TopNavProps {
  sessionId: string | null;
  onNewSession: () => void;
  onOpenProfileManager: () => void;
  onOpenPresetLoader: () => void;
  onDeleteSession: () => void;
}

const TopNav: React.FC<TopNavProps> = ({ 
  sessionId, 
  onNewSession,
  onOpenProfileManager,
  onOpenPresetLoader,
  onDeleteSession,
}) => {
  return (
    <div className="top-nav">
      <div className="top-nav-content">
        <h1>TRPG-LLM</h1>
        <div className="nav-actions">
          <button 
            className="btn btn-small" 
            onClick={onOpenProfileManager}
            title="Manage LLM Profiles"
          >
            ⚙️ Profiles
          </button>
          <button 
            className="btn btn-small" 
            onClick={onOpenPresetLoader}
            title="Load Game Preset"
          >
            📂 Load Preset
          </button>
          <button className="btn btn-primary" onClick={onNewSession}>
            + New Session
          </button>
        </div>
        <div className="session-info">
          <span className="session-label">Session ID:</span>
          <code className="session-id">{sessionId || 'None'}</code>
          {sessionId && (
            <button 
              className="btn btn-small btn-danger" 
              onClick={onDeleteSession}
              title="Delete current session"
            >
              🗑️
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TopNav;
