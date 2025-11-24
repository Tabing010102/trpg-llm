import React, { useState } from 'react';
import type { Character } from '../types/api';

interface ChatInputProps {
  characters: Record<string, Character>;
  onSend: (roleId: string, message: string) => void;
  disabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ characters, onSend, disabled }) => {
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (!selectedRole || !message.trim()) return;
    onSend(selectedRole, message);
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
              {char.name} ({char.type})
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
    </div>
  );
};

export default ChatInput;
