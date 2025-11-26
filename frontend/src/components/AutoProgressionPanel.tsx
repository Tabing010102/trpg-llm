import React, { useState, useEffect, useCallback } from 'react';
import type {
  Character,
  AutoProgressionConfig,
  AutoProgressionStatus,
  ChatResponse,
} from '../types/api';

interface AutoProgressionPanelProps {
  sessionId: string | null;
  characters: Record<string, Character>;
  config: AutoProgressionConfig | null;
  status: AutoProgressionStatus | null;
  onConfigChange: (config: Partial<AutoProgressionConfig>) => void;
  onRunProgression: (fromCharacterId?: string) => void;
  onRetry: () => void;
  onSkip: () => void;
  onPause: () => void;
  onResume: () => void;
  onMessagesGenerated: (messages: ChatResponse[]) => void;
  disabled: boolean;
}

const AutoProgressionPanel: React.FC<AutoProgressionPanelProps> = ({
  sessionId,
  characters,
  config,
  status,
  onConfigChange,
  onRunProgression,
  onRetry,
  onSkip,
  onPause,
  onResume,
  disabled,
}) => {
  const [editingTurnOrder, setEditingTurnOrder] = useState(false);
  const [tempTurnOrder, setTempTurnOrder] = useState<string[]>([]);

  // Initialize temp turn order when config changes
  useEffect(() => {
    if (config?.turn_order) {
      setTempTurnOrder([...config.turn_order]);
    }
  }, [config?.turn_order]);

  const handleToggleEnabled = useCallback(() => {
    if (config) {
      onConfigChange({ enabled: !config.enabled });
    }
  }, [config, onConfigChange]);

  const handleSaveTurnOrder = useCallback(() => {
    onConfigChange({ turn_order: tempTurnOrder });
    setEditingTurnOrder(false);
  }, [tempTurnOrder, onConfigChange]);

  const handleCancelTurnOrder = useCallback(() => {
    if (config?.turn_order) {
      setTempTurnOrder([...config.turn_order]);
    }
    setEditingTurnOrder(false);
  }, [config?.turn_order]);

  const moveCharacterUp = (index: number) => {
    if (index > 0) {
      const newOrder = [...tempTurnOrder];
      [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
      setTempTurnOrder(newOrder);
    }
  };

  const moveCharacterDown = (index: number) => {
    if (index < tempTurnOrder.length - 1) {
      const newOrder = [...tempTurnOrder];
      [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
      setTempTurnOrder(newOrder);
    }
  };

  const addCharacterToOrder = (characterId: string) => {
    if (!tempTurnOrder.includes(characterId)) {
      setTempTurnOrder([...tempTurnOrder, characterId]);
    }
  };

  const removeCharacterFromOrder = (index: number) => {
    const newOrder = [...tempTurnOrder];
    newOrder.splice(index, 1);
    setTempTurnOrder(newOrder);
  };

  const getCharacterName = (charId: string): string => {
    return characters[charId]?.name || charId;
  };

  const getCharacterControl = (charId: string): string => {
    return characters[charId]?.control || 'unknown';
  };

  const getStatusColor = (state: string): string => {
    switch (state) {
      case 'idle':
        return '#6c757d';
      case 'progressing':
        return '#28a745';
      case 'waiting_for_user':
        return '#17a2b8';
      case 'error':
        return '#dc3545';
      case 'paused':
        return '#ffc107';
      default:
        return '#6c757d';
    }
  };

  const getStatusLabel = (state: string): string => {
    switch (state) {
      case 'idle':
        return 'Idle';
      case 'progressing':
        return 'Processing...';
      case 'waiting_for_user':
        return 'Waiting for Human';
      case 'error':
        return 'Error';
      case 'paused':
        return 'Paused';
      default:
        return state;
    }
  };

  if (!sessionId) {
    return (
      <div className="auto-progression-panel">
        <h3>Auto-Progression</h3>
        <p className="no-session">Create a session to enable auto-progression</p>
      </div>
    );
  }

  const charactersNotInOrder = Object.keys(characters).filter(
    (charId) => !tempTurnOrder.includes(charId)
  );

  return (
    <div className="auto-progression-panel">
      <h3>Auto-Progression</h3>

      {/* Enable/Disable Toggle */}
      <div className="config-row">
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={config?.enabled || false}
            onChange={handleToggleEnabled}
            disabled={disabled}
          />
          <span>Enable Auto-Progression</span>
        </label>
      </div>

      {/* Status Display */}
      {status && (
        <div className="status-section">
          <div className="status-indicator">
            <span
              className="status-dot"
              style={{ backgroundColor: getStatusColor(status.state) }}
            />
            <span className="status-text">{getStatusLabel(status.state)}</span>
          </div>

          {status.queue.length > 0 && (
            <div className="queue-info">
              <strong>Queue:</strong>{' '}
              {status.queue.map((charId) => getCharacterName(charId)).join(' → ')}
            </div>
          )}

          {status.completed.length > 0 && (
            <div className="completed-info">
              <strong>Completed:</strong>{' '}
              {status.completed.map((charId) => getCharacterName(charId)).join(', ')}
            </div>
          )}

          {status.error && (
            <div className="error-info">
              <strong>Error:</strong> {status.error.error_message}
              <br />
              <small>Character: {getCharacterName(status.error.character_id)}</small>
            </div>
          )}
        </div>
      )}

      {/* Control Buttons */}
      <div className="control-buttons">
        {status?.state === 'error' && (
          <>
            <button
              className="btn btn-warning"
              onClick={onRetry}
              disabled={disabled}
              title="Retry from error"
            >
              🔄 Retry
            </button>
            <button
              className="btn btn-secondary"
              onClick={onSkip}
              disabled={disabled}
              title="Skip failed character"
            >
              ⏭️ Skip
            </button>
          </>
        )}

        {status?.state === 'paused' && (
          <button
            className="btn btn-primary"
            onClick={onResume}
            disabled={disabled}
            title="Resume auto-progression"
          >
            ▶️ Resume
          </button>
        )}

        {status?.state === 'progressing' && (
          <button
            className="btn btn-warning"
            onClick={onPause}
            disabled={disabled}
            title="Pause auto-progression"
          >
            ⏸️ Pause
          </button>
        )}

        {(status?.state === 'idle' || status?.state === 'waiting_for_user') && config?.enabled && (
          <button
            className="btn btn-primary"
            onClick={() => onRunProgression()}
            disabled={disabled}
            title="Start auto-progression"
          >
            ▶️ Run Progression
          </button>
        )}
      </div>

      {/* Turn Order Configuration */}
      <div className="turn-order-section">
        <div className="section-header">
          <strong>Turn Order</strong>
          {!editingTurnOrder ? (
            <button
              className="btn btn-small"
              onClick={() => setEditingTurnOrder(true)}
              disabled={disabled}
            >
              ✏️ Edit
            </button>
          ) : (
            <div className="edit-buttons">
              <button
                className="btn btn-small btn-primary"
                onClick={handleSaveTurnOrder}
                disabled={disabled}
              >
                💾 Save
              </button>
              <button
                className="btn btn-small"
                onClick={handleCancelTurnOrder}
                disabled={disabled}
              >
                ✕ Cancel
              </button>
            </div>
          )}
        </div>

        {editingTurnOrder ? (
          <div className="turn-order-editor">
            <ul className="turn-order-list">
              {tempTurnOrder.map((charId, index) => (
                <li key={charId} className="turn-order-item">
                  <span className="order-number">{index + 1}.</span>
                  <span className="character-name">
                    {getCharacterName(charId)}
                    <span className={`control-badge ${getCharacterControl(charId)}`}>
                      {getCharacterControl(charId) === 'ai' ? '🤖' : '👤'}
                    </span>
                  </span>
                  <div className="item-controls">
                    <button
                      className="btn btn-tiny"
                      onClick={() => moveCharacterUp(index)}
                      disabled={index === 0}
                      title="Move up"
                    >
                      ↑
                    </button>
                    <button
                      className="btn btn-tiny"
                      onClick={() => moveCharacterDown(index)}
                      disabled={index === tempTurnOrder.length - 1}
                      title="Move down"
                    >
                      ↓
                    </button>
                    <button
                      className="btn btn-tiny btn-danger"
                      onClick={() => removeCharacterFromOrder(index)}
                      title="Remove"
                    >
                      ✕
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            {charactersNotInOrder.length > 0 && (
              <div className="add-character">
                <label>Add character:</label>
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      addCharacterToOrder(e.target.value);
                      e.target.value = '';
                    }
                  }}
                  defaultValue=""
                >
                  <option value="">Select...</option>
                  {charactersNotInOrder.map((charId) => (
                    <option key={charId} value={charId}>
                      {getCharacterName(charId)} ({getCharacterControl(charId)})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        ) : (
          <div className="turn-order-display">
            {config?.turn_order && config.turn_order.length > 0 ? (
              <ol className="turn-order-list readonly">
                {config.turn_order.map((charId) => (
                  <li key={charId}>
                    {getCharacterName(charId)}
                    <span className={`control-badge ${getCharacterControl(charId)}`}>
                      {getCharacterControl(charId) === 'ai' ? '🤖' : '👤'}
                    </span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="no-order">No turn order configured</p>
            )}
          </div>
        )}
      </div>

      {/* Additional Settings */}
      <div className="settings-section">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config?.stop_before_human ?? true}
            onChange={(e) => onConfigChange({ stop_before_human: e.target.checked })}
            disabled={disabled}
          />
          <span>Stop before human characters</span>
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config?.continue_after_human ?? true}
            onChange={(e) => onConfigChange({ continue_after_human: e.target.checked })}
            disabled={disabled}
          />
          <span>Continue after human speaks</span>
        </label>
      </div>
    </div>
  );
};

export default AutoProgressionPanel;
