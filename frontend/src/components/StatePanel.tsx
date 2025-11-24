import React from 'react';
import type { GameState, Character } from '../types/api';

interface StatePanelProps {
  gameState: GameState | null;
}

const StatePanel: React.FC<StatePanelProps> = ({ gameState }) => {
  if (!gameState) {
    return (
      <div className="state-panel">
        <div className="panel-section">
          <h3>State Panel</h3>
          <p className="text-muted">No session active</p>
        </div>
      </div>
    );
  }

  const extractCharacterStats = (character: Character) => {
    const stats: Record<string, any> = {};
    if (character.state) {
      Object.entries(character.state).forEach(([key, value]) => {
        if (typeof value === 'number' || typeof value === 'string') {
          stats[key] = value;
        }
      });
    }
    return stats;
  };

  return (
    <div className="state-panel">
      <div className="panel-section">
        <h3>Game Flow</h3>
        <div className="state-item">
          <span className="state-key">Turn:</span>
          <span className="state-value">{gameState.current_turn}</span>
        </div>
        {gameState.current_phase && (
          <div className="state-item">
            <span className="state-key">Phase:</span>
            <span className="state-value">{gameState.current_phase}</span>
          </div>
        )}
        {gameState.current_actor && (
          <div className="state-item">
            <span className="state-key">Current Actor:</span>
            <span className="state-value">{gameState.current_actor}</span>
          </div>
        )}
      </div>

      <div className="panel-section">
        <h3>Global State</h3>
        <div className="state-json">
          {Object.entries(gameState.state).length > 0 ? (
            Object.entries(gameState.state).map(([key, value]) => (
              <div key={key} className="state-item">
                <span className="state-key">{key}:</span>
                <span className="state-value">
                  {typeof value === 'object' 
                    ? JSON.stringify(value, null, 2) 
                    : String(value)
                  }
                </span>
              </div>
            ))
          ) : (
            <p className="text-muted">No global state</p>
          )}
        </div>
      </div>

      <div className="panel-section">
        <h3>Characters</h3>
        {Object.values(gameState.characters).map((character) => {
          const stats = extractCharacterStats(character);
          return (
            <div key={character.id} className="character-card">
              <div className="character-header">
                <span className="character-name">{character.name}</span>
                <span className="character-type-badge">{character.type}</span>
              </div>
              {Object.keys(stats).length > 0 && (
                <div className="character-stats">
                  {Object.entries(stats).map(([key, value]) => (
                    <div key={key} className="stat-item">
                      <span className="stat-key">{key}:</span>
                      <span className="stat-value">{String(value)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StatePanel;
