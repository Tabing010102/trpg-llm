import React, { useState } from 'react';
import type { Character, LLMProfile } from '../types/api';

interface ChatInputProps {
  characters: Record<string, Character>;
  llmProfiles: LLMProfile[];
  onSend: (roleId: string, message: string, profileId?: string) => void;
  disabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ characters, llmProfiles, onSend, disabled }) => {
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [message, setMessage] = useState('');
  const [selectedProfile, setSelectedProfile] = useState<string>('');

  const handleSend = () => {
    if (!selectedRole || !message.trim()) return;
    onSend(selectedRole, message, selectedProfile || undefined);
    setMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Get human-controlled characters for selection
  const humanCharacters = Object.values(characters).filter(
    (char) => char.control === 'human'
  );

  // Auto-select first human character if available and none selected
  React.useEffect(() => {
    if (!selectedRole && humanCharacters.length > 0) {
      setSelectedRole(humanCharacters[0].id);
    }
  }, [humanCharacters, selectedRole]);

  // Check if selected character is AI-controlled
  const selectedChar = characters[selectedRole];
  const isAICharacter = selectedChar?.control === 'ai';

  return (
    <div className="chat-input">
      <div className="input-row">
        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
          disabled={disabled}
          className="role-select"
        >
          <option value="">Select Role</option>
          {Object.values(characters).map((char) => (
            <option key={char.id} value={char.id}>
              {char.name} ({char.type}) {char.control === 'ai' ? '🤖' : ''}
            </option>
          ))}
        </select>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={disabled || !selectedRole}
          rows={2}
          className="message-input"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !selectedRole || !message.trim()}
          className="btn btn-primary"
        >
          Send
        </button>
      </div>
      {isAICharacter && llmProfiles.length > 0 && (
        <div className="profile-selector-row">
          <label htmlFor="profile-select">LLM Profile:</label>
          <select
            id="profile-select"
            value={selectedProfile}
            onChange={(e) => setSelectedProfile(e.target.value)}
            disabled={disabled}
            className="profile-select"
          >
            <option value="">Default (from character config)</option>
            {llmProfiles.map(profile => (
              <option key={profile.id} value={profile.id}>
                {profile.id} - {profile.model} (temp: {profile.temperature})
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};

export default ChatInput;
