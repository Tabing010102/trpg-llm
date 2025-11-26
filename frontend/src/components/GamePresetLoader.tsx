import React, { useState, useRef } from 'react';
import type { GameConfig } from '../types/api';

// Simple YAML parser for basic game configs
// Note: This is a simplified parser that handles common YAML structures
function parseYAML(text: string): Record<string, unknown> {
  const lines = text.split('\n');
  const result: Record<string, unknown> = {};
  const stack: { obj: Record<string, unknown>; indent: number }[] = [{ obj: result, indent: -1 }];
  let currentKey = '';
  let inMultilineString = false;
  let multilineValue = '';
  let multilineKey = '';
  let multilineIndent = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trimEnd();
    
    // Handle multiline strings (|)
    if (inMultilineString) {
      const indent = line.search(/\S/);
      if (indent === -1 || indent > multilineIndent) {
        multilineValue += (multilineValue ? '\n' : '') + line.slice(multilineIndent + 2);
        continue;
      } else {
        // End of multiline string
        const parent = stack[stack.length - 1].obj;
        parent[multilineKey] = multilineValue.trim();
        inMultilineString = false;
        multilineValue = '';
      }
    }

    // Skip empty lines and comments
    if (trimmedLine === '' || trimmedLine.startsWith('#')) continue;

    const indent = line.search(/\S/);
    
    // Pop stack until we find the right parent
    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }

    const parent = stack[stack.length - 1].obj;

    // Handle list items
    if (trimmedLine.startsWith('- ')) {
      const listItem = trimmedLine.slice(2).trim();
      if (!Array.isArray(parent[currentKey])) {
        parent[currentKey] = [];
      }
      
      // Check if it's a simple value or an object
      if (listItem.includes(':')) {
        const obj: Record<string, unknown> = {};
        const [key, ...rest] = listItem.split(':');
        const value = rest.join(':').trim();
        obj[key.trim()] = parseValue(value);
        (parent[currentKey] as unknown[]).push(obj);
        stack.push({ obj: obj, indent: indent + 2 });
      } else {
        (parent[currentKey] as unknown[]).push(parseValue(listItem));
      }
      continue;
    }

    // Handle key-value pairs
    const colonIndex = trimmedLine.indexOf(':');
    if (colonIndex === -1) continue;

    const key = trimmedLine.slice(0, colonIndex).trim();
    const value = trimmedLine.slice(colonIndex + 1).trim();
    currentKey = key;

    if (value === '|') {
      // Start of multiline string
      inMultilineString = true;
      multilineKey = key;
      multilineIndent = indent;
      continue;
    }

    if (value === '' || value === '{}' || value === '[]') {
      // Nested object or empty
      if (value === '[]') {
        parent[key] = [];
      } else {
        parent[key] = {};
        stack.push({ obj: parent[key] as Record<string, unknown>, indent: indent });
      }
    } else {
      parent[key] = parseValue(value);
    }
  }

  return result;
}

function parseValue(value: string): unknown {
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (value === 'null' || value === '~') return null;
  
  // Remove quotes
  if ((value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }
  
  // Try parsing as number
  const num = Number(value);
  if (!isNaN(num) && value !== '') return num;
  
  // Array shorthand
  if (value.startsWith('[') && value.endsWith(']')) {
    try {
      return JSON.parse(value);
    } catch {
      return value.slice(1, -1).split(',').map(v => parseValue(v.trim()));
    }
  }
  
  return value;
}

interface GamePresetLoaderProps {
  onLoadPreset: (config: GameConfig) => void;
  onClose: () => void;
}

const GamePresetLoader: React.FC<GamePresetLoaderProps> = ({
  onLoadPreset,
  onClose,
}) => {
  const [error, setError] = useState<string | null>(null);
  const [previewConfig, setPreviewConfig] = useState<GameConfig | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      let config: GameConfig;

      if (file.name.endsWith('.json')) {
        config = JSON.parse(text);
      } else if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
        config = parseYAML(text) as unknown as GameConfig;
      } else {
        // Try JSON first, then YAML
        try {
          config = JSON.parse(text);
        } catch {
          config = parseYAML(text) as unknown as GameConfig;
        }
      }

      // Validate required fields
      if (!config.name) {
        throw new Error("Config must have a 'name' field");
      }
      if (!config.rule_system) {
        throw new Error("Config must have a 'rule_system' field");
      }
      if (!config.characters || Object.keys(config.characters).length === 0) {
        throw new Error("Config must have at least one character");
      }

      setPreviewConfig(config);
      setError(null);
    } catch (err) {
      setError('Failed to parse file: ' + (err as Error).message);
      setPreviewConfig(null);
    }
  };

  const handleConfirmLoad = () => {
    if (previewConfig) {
      onLoadPreset(previewConfig);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content preset-loader">
        <div className="modal-header">
          <h2>Load Game Preset</h2>
          <button className="btn btn-small" onClick={onClose}>✕</button>
        </div>

        {error && (
          <div className="error-message">{error}</div>
        )}

        <div className="preset-section">
          <h3>Upload Configuration File</h3>
          <p className="hint">Upload a JSON or YAML game configuration file</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.yaml,.yml"
            onChange={handleFileUpload}
            className="file-input"
          />
        </div>

        {previewConfig && (
          <div className="preset-preview">
            <h3>Preview</h3>
            <div className="preview-details">
              <div className="preview-item">
                <span className="preview-label">Name:</span>
                <span className="preview-value">{previewConfig.name}</span>
              </div>
              <div className="preview-item">
                <span className="preview-label">Rule System:</span>
                <span className="preview-value">{previewConfig.rule_system}</span>
              </div>
              {previewConfig.description && (
                <div className="preview-item">
                  <span className="preview-label">Description:</span>
                  <span className="preview-value">{previewConfig.description}</span>
                </div>
              )}
              <div className="preview-item">
                <span className="preview-label">Characters:</span>
                <span className="preview-value">
                  {Object.values(previewConfig.characters).map(c => c.name).join(', ')}
                </span>
              </div>
              {previewConfig.llm_config?.default_model && (
                <div className="preview-item">
                  <span className="preview-label">Default Model:</span>
                  <span className="preview-value">{previewConfig.llm_config.default_model}</span>
                </div>
              )}
            </div>
            <div className="preview-actions">
              <button
                className="btn btn-primary"
                onClick={handleConfirmLoad}
              >
                Create Session with this Preset
              </button>
            </div>
          </div>
        )}

        <div className="preset-section">
          <h3>Example Configuration Structure</h3>
          <pre className="code-preview">
{`{
  "name": "My Adventure",
  "rule_system": "generic",
  "description": "An exciting adventure",
  "characters": {
    "player1": {
      "id": "player1",
      "name": "Hero",
      "type": "player",
      "control": "human"
    },
    "gm": {
      "id": "gm",
      "name": "Game Master",
      "type": "gm",
      "control": "ai"
    }
  }
}`}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default GamePresetLoader;
