import React, { useState } from 'react';
import type { Character, DiceRollResult } from '../types/api';

interface DiceRollerProps {
  characters: Record<string, Character>;
  sessionId: string | null;
  onRollDice: (
    notation: string,
    characterId?: string,
    reason?: string,
    modifier?: number
  ) => void;
  lastResult: DiceRollResult | null;
  disabled: boolean;
}

const DiceRoller: React.FC<DiceRollerProps> = ({
  characters,
  sessionId,
  onRollDice,
  lastResult,
  disabled,
}) => {
  const [notation, setNotation] = useState('1d20');
  const [characterId, setCharacterId] = useState('');
  const [reason, setReason] = useState('');
  const [modifier, setModifier] = useState(0);

  const handleRoll = () => {
    if (!notation.trim()) return;
    onRollDice(
      notation,
      characterId || undefined,
      reason || undefined,
      modifier || undefined
    );
  };

  const commonDice = ['1d4', '1d6', '1d8', '1d10', '1d12', '1d20', '1d100', '2d6', '3d6'];

  return (
    <div className="dice-roller">
      <h3>🎲 Dice Roller</h3>
      
      <div className="dice-quick-buttons">
        {commonDice.map(dice => (
          <button
            key={dice}
            className={`btn btn-small ${notation === dice ? 'btn-primary' : ''}`}
            onClick={() => setNotation(dice)}
            disabled={disabled || !sessionId}
          >
            {dice}
          </button>
        ))}
      </div>

      <div className="dice-input-row">
        <div className="dice-input-group">
          <label htmlFor="notation">Notation:</label>
          <input
            id="notation"
            type="text"
            value={notation}
            onChange={(e) => setNotation(e.target.value)}
            placeholder="e.g., 2d6+3"
            disabled={disabled || !sessionId}
            className="dice-notation-input"
          />
        </div>

        <div className="dice-input-group">
          <label htmlFor="modifier">Modifier:</label>
          <input
            id="modifier"
            type="number"
            value={modifier}
            onChange={(e) => setModifier(parseInt(e.target.value) || 0)}
            disabled={disabled || !sessionId}
            className="dice-modifier-input"
          />
        </div>
      </div>

      <div className="dice-input-row">
        <div className="dice-input-group">
          <label htmlFor="character">Character:</label>
          <select
            id="character"
            value={characterId}
            onChange={(e) => setCharacterId(e.target.value)}
            disabled={disabled || !sessionId}
            className="dice-character-select"
          >
            <option value="">No character</option>
            {Object.values(characters).map(char => (
              <option key={char.id} value={char.id}>
                {char.name}
              </option>
            ))}
          </select>
        </div>

        <div className="dice-input-group">
          <label htmlFor="reason">Reason:</label>
          <input
            id="reason"
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Optional reason"
            disabled={disabled || !sessionId}
            className="dice-reason-input"
          />
        </div>
      </div>

      <button
        className="btn btn-primary dice-roll-btn"
        onClick={handleRoll}
        disabled={disabled || !sessionId || !notation.trim()}
      >
        🎲 Roll {notation}
      </button>

      {lastResult && (
        <div className="dice-result">
          <div className="dice-result-header">
            <span className="dice-result-notation">{lastResult.notation}</span>
            <span className="dice-result-total">{lastResult.final_result}</span>
          </div>
          <div className="dice-result-details">
            <span className="dice-rolls">
              [{lastResult.rolls.join(', ')}]
              {lastResult.modifier !== 0 && (
                <span className="dice-modifier-display">
                  {lastResult.modifier >= 0 ? ' + ' : ' - '}
                  {Math.abs(lastResult.modifier)}
                </span>
              )}
            </span>
          </div>
          {lastResult.success !== undefined && lastResult.success !== null && (
            <div className={`dice-success-info ${lastResult.success ? 'success' : 'failure'}`}>
              {lastResult.success ? '✓ Success' : '✗ Failure'}
              {lastResult.success_level && ` (${lastResult.success_level})`}
              {lastResult.critical_success && ' - CRITICAL!'}
              {lastResult.critical_failure && ' - FUMBLE!'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DiceRoller;
