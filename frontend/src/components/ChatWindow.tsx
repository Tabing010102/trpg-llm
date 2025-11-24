import React, { useRef, useEffect } from 'react';
import type { Message, Character } from '../types/api';

interface ChatWindowProps {
  messages: Message[];
  characters: Record<string, Character>;
  onRedraw: (characterId: string) => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages, characters, onRedraw }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getCharacterInfo = (senderId: string) => {
    const character = characters[senderId];
    return character || { name: senderId, type: 'unknown', control: 'unknown' };
  };

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map((msg, idx) => {
          const charInfo = getCharacterInfo(msg.sender_id);
          const isAI = charInfo.control === 'ai' || msg.is_ai;
          
          return (
            <div key={idx} className={`message message-${charInfo.type}`}>
              <div className="message-header">
                <span className="character-name">{charInfo.name}</span>
                <span className="character-type">[{charInfo.type.toUpperCase()}]</span>
                {isAI && <span className="ai-badge">AI</span>}
                {msg.timestamp && (
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
              <div className="message-content">{msg.content}</div>
              {isAI && (
                <div className="message-actions">
                  <button
                    className="btn btn-small"
                    onClick={() => onRedraw(msg.sender_id)}
                    title="Redraw last AI message"
                  >
                    🔄 Redraw
                  </button>
                </div>
              )}
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;
