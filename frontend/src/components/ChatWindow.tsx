import React, { useRef, useEffect, useState } from 'react';
import type { Message, Character, LLMProfile } from '../types/api';

interface ChatWindowProps {
  messages: Message[];
  characters: Record<string, Character>;
  llmProfiles: LLMProfile[];
  sessionCharacterProfiles: Record<string, string>;
  onRedraw: (characterId: string, profileId?: string) => void;
  onSetCharacterProfile: (characterId: string, profileId: string | null) => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ 
  messages, 
  characters, 
  llmProfiles, 
  sessionCharacterProfiles,
  onRedraw,
  onSetCharacterProfile 
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showProfileSelector, setShowProfileSelector] = useState<number | null>(null);
  const [showCharacterProfileEditor, setShowCharacterProfileEditor] = useState<string | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getCharacterInfo = (senderId: string) => {
    const character = characters[senderId];
    return character || { name: senderId, type: 'unknown', control: 'unknown' };
  };

  const getProfileInfo = (profileId?: string) => {
    if (!profileId) return null;
    return llmProfiles.find(p => p.id === profileId);
  };

  const handleRedrawClick = (messageIndex: number, senderId: string) => {
    if (llmProfiles.length > 0) {
      // Show profile selector if profiles are available
      setShowProfileSelector(messageIndex);
    } else {
      // Redraw with default profile
      onRedraw(senderId);
    }
  };

  const handleProfileSelect = (senderId: string, profileId?: string) => {
    setShowProfileSelector(null);
    onRedraw(senderId, profileId);
  };

  const handleSetDefaultProfile = (characterId: string, profileId: string) => {
    setShowCharacterProfileEditor(null);
    onSetCharacterProfile(characterId, profileId || null);
  };

  // Get unique AI characters from messages for showing session profile settings
  const aiCharactersInSession = Array.from(new Set(
    messages
      .filter(msg => {
        const charInfo = getCharacterInfo(msg.sender_id);
        return charInfo.control === 'ai' || msg.is_ai;
      })
      .map(msg => msg.sender_id)
  ));

  return (
    <div className="chat-window">
      {/* Session Character Profile Settings */}
      {aiCharactersInSession.length > 0 && llmProfiles.length > 0 && (
        <div className="session-profile-settings">
          <div className="session-profile-header">
            <strong>Session Profile Defaults:</strong>
            <span className="session-profile-hint">(overrides game preset defaults for this session)</span>
          </div>
          <div className="session-profile-list">
            {aiCharactersInSession.map(charId => {
              const charInfo = getCharacterInfo(charId);
              const currentProfile = sessionCharacterProfiles[charId];
              const profileInfo = getProfileInfo(currentProfile);
              
              return (
                <div key={charId} className="session-profile-item">
                  <span className="session-profile-char">{charInfo.name}:</span>
                  {showCharacterProfileEditor === charId ? (
                    <div className="profile-selector inline">
                      <select
                        onChange={(e) => handleSetDefaultProfile(charId, e.target.value)}
                        value={currentProfile || ''}
                        className="profile-select-small"
                        autoFocus
                      >
                        <option value="">Game Preset Default</option>
                        {llmProfiles.map(profile => (
                          <option key={profile.id} value={profile.id}>
                            {profile.id} ({profile.model})
                          </option>
                        ))}
                      </select>
                      <button
                        className="btn btn-small"
                        onClick={() => setShowCharacterProfileEditor(null)}
                        title="Cancel"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <button
                      className="btn btn-small profile-btn"
                      onClick={() => setShowCharacterProfileEditor(charId)}
                      title="Change default profile for this session"
                    >
                      {profileInfo ? `${profileInfo.id} (${profileInfo.model})` : 'Default'}
                      {' '}✏️
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      <div className="messages">
        {messages.map((msg, idx) => {
          const charInfo = getCharacterInfo(msg.sender_id);
          const isAI = charInfo.control === 'ai' || msg.is_ai;
          const usedProfile = msg.metadata?.used_profile_id;
          const profileInfo = getProfileInfo(usedProfile);
          
          return (
            <div key={idx} className={`message message-${charInfo.type}`}>
              <div className="message-header">
                <span className="character-name">{charInfo.name}</span>
                <span className="character-type">[{charInfo.type.toUpperCase()}]</span>
                {isAI && <span className="ai-badge">AI</span>}
                {profileInfo && (
                  <span className="profile-badge" title={`Provider: ${profileInfo.provider_type}`}>
                    📦 {profileInfo.model}
                  </span>
                )}
                {msg.timestamp && (
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
              <div className="message-content">{msg.content}</div>
              {isAI && (
                <div className="message-actions">
                  {showProfileSelector === idx ? (
                    <div className="profile-selector">
                      <select
                        onChange={(e) => handleProfileSelect(msg.sender_id, e.target.value || undefined)}
                        defaultValue={usedProfile || ''}
                        className="profile-select-small"
                        autoFocus
                      >
                        <option value="">Default Profile</option>
                        {llmProfiles.map(profile => (
                          <option key={profile.id} value={profile.id}>
                            {profile.id} ({profile.model})
                          </option>
                        ))}
                      </select>
                      <button
                        className="btn btn-small"
                        onClick={() => setShowProfileSelector(null)}
                        title="Cancel"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <button
                      className="btn btn-small"
                      onClick={() => handleRedrawClick(idx, msg.sender_id)}
                      title="Redraw with different profile"
                    >
                      🔄 Redraw
                    </button>
                  )}
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
