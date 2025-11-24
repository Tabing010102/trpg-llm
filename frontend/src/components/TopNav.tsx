import React from 'react';

interface TopNavProps {
  sessionId: string | null;
  onNewSession: () => void;
}

const TopNav: React.FC<TopNavProps> = ({ sessionId, onNewSession }) => {
  return (
    <div className="top-nav">
      <div className="top-nav-content">
        <h1>TRPG-LLM</h1>
        <div className="session-info">
          <span className="session-label">Session ID:</span>
          <code className="session-id">{sessionId || 'None'}</code>
          <button className="btn btn-primary" onClick={onNewSession}>
            New Session
          </button>
        </div>
      </div>
    </div>
  );
};

export default TopNav;
