import { useState, useEffect } from 'react';
import TopNav from './components/TopNav';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import StatePanel from './components/StatePanel';
import StateDiffsPanel from './components/StateDiffsPanel';
import DebugPanel from './components/DebugPanel';
import ProfileManager from './components/ProfileManager';
import GamePresetLoader from './components/GamePresetLoader';
import DiceRoller from './components/DiceRoller';
import { apiService } from './services/api';
import type { GameState, StateDiff, Event, LLMProfile, GameConfig, DiceRollResult } from './types/api';
import './App.css';

// Default configuration for new sessions (using simple_game.json as reference)
const DEFAULT_CONFIG: GameConfig = {
  name: 'Demo Adventure',
  rule_system: 'generic',
  description: 'A demo adventure for testing the frontend',
  characters: {
    player1: {
      id: 'player1',
      name: 'Hero',
      type: 'player',
      control: 'human',
      description: 'A brave adventurer',
      attributes: {
        strength: 15,
        intelligence: 12,
        dexterity: 14,
      },
      state: {
        hp: 20,
        level: 1,
      },
    },
    gm: {
      id: 'gm',
      name: 'Game Master',
      type: 'gm',
      control: 'ai',
      description: 'Controls the game world',
      ai_config: {
        model: 'gpt-3.5-turbo',
        temperature: 0.7,
      },
    },
  },
  llm_config: {
    default_model: 'gpt-3.5-turbo',
    temperature: 0.7,
    prompts: {
      gm_system: 'You are a Game Master creating an engaging adventure.',
    },
  },
  workflow: {
    turn_order: ['gm', 'player1'],
  },
  tools: [
    {
      name: 'roll_dice',
      description: 'Roll dice',
      parameters: {
        notation: {
          type: 'string',
          description: "Dice notation (e.g., '1d20')",
        },
      },
    },
  ],
  initial_state: {
    location: 'Village Square',
    quest_active: false,
  },
};

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [recentDiffs, setRecentDiffs] = useState<StateDiff[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Global profiles (instance-level configuration)
  const [globalProfiles, setGlobalProfiles] = useState<LLMProfile[]>([]);
  
  // Per-session character profile overrides
  const [sessionCharacterProfiles, setSessionCharacterProfiles] = useState<Record<string, string>>({});

  // Modal states
  const [showProfileManager, setShowProfileManager] = useState(false);
  const [showPresetLoader, setShowPresetLoader] = useState(false);

  // Dice roll state
  const [lastDiceResult, setLastDiceResult] = useState<DiceRollResult | null>(null);

  // Fetch global profiles on mount
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const response = await apiService.getProfiles();
        setGlobalProfiles(response.profiles);
      } catch {
        // Profiles may not be configured yet, that's ok
      }
    };
    fetchProfiles();
  }, []);

  // Fetch session character profiles when session changes
  useEffect(() => {
    if (!sessionId) {
      setSessionCharacterProfiles({});
      return;
    }
    
    const fetchCharacterProfiles = async () => {
      try {
        const response = await apiService.getSessionCharacterProfiles(sessionId);
        setSessionCharacterProfiles(response.character_profiles);
      } catch {
        // May not have any overrides yet
      }
    };
    fetchCharacterProfiles();
  }, [sessionId]);

  const showNotification = (message: string) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  };

  const handleNewSession = async () => {
    setLoading(true);
    try {
      const response = await apiService.createSession(DEFAULT_CONFIG);
      setSessionId(response.session_id);
      setGameState(response.state);
      setRecentDiffs([]);
      setEvents([]);
      setSessionCharacterProfiles({});
      setLastDiceResult(null);
      showNotification('Session created successfully!');
    } catch (err) {
      showNotification('Failed to create session: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async () => {
    if (!sessionId) return;
    
    if (!window.confirm('Are you sure you want to delete this session?')) {
      return;
    }

    setLoading(true);
    try {
      await apiService.deleteSession(sessionId);
      setSessionId(null);
      setGameState(null);
      setRecentDiffs([]);
      setEvents([]);
      setSessionCharacterProfiles({});
      setLastDiceResult(null);
      showNotification('Session deleted successfully!');
    } catch (err) {
      showNotification('Failed to delete session: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadPreset = async (config: GameConfig) => {
    setLoading(true);
    try {
      const response = await apiService.createSessionWithConfig(config);
      setSessionId(response.session_id);
      setGameState(response.state);
      setRecentDiffs([]);
      setEvents([]);
      setSessionCharacterProfiles({});
      setLastDiceResult(null);
      setShowPresetLoader(false);
      showNotification(`Session created with preset: ${config.name}`);
    } catch (err) {
      showNotification('Failed to create session with preset: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Profile management handlers
  const handleLoadProfiles = async (profiles: LLMProfile[]) => {
    setLoading(true);
    try {
      await apiService.setProfiles(profiles);
      setGlobalProfiles(profiles);
      showNotification(`Loaded ${profiles.length} profiles successfully!`);
    } catch (err) {
      showNotification('Failed to load profiles: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProfile = async (profile: LLMProfile) => {
    setLoading(true);
    try {
      await apiService.addProfile(profile);
      setGlobalProfiles(prev => [...prev, profile]);
      showNotification(`Profile '${profile.id}' added successfully!`);
    } catch (err) {
      showNotification('Failed to add profile: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProfile = async (profileId: string) => {
    setLoading(true);
    try {
      await apiService.deleteProfile(profileId);
      setGlobalProfiles(prev => prev.filter(p => p.id !== profileId));
      showNotification(`Profile '${profileId}' deleted successfully!`);
    } catch (err) {
      showNotification('Failed to delete profile: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSetCharacterProfile = async (characterId: string, profileId: string | null) => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      if (profileId) {
        await apiService.setCharacterProfile(sessionId, characterId, profileId);
        setSessionCharacterProfiles(prev => ({ ...prev, [characterId]: profileId }));
        showNotification(`Character '${characterId}' profile set to '${profileId}'`);
      } else {
        await apiService.resetCharacterProfile(sessionId, characterId);
        setSessionCharacterProfiles(prev => {
          const newProfiles = { ...prev };
          delete newProfiles[characterId];
          return newProfiles;
        });
        showNotification(`Character '${characterId}' profile reset to default`);
      }
    } catch (err) {
      showNotification('Failed to update character profile: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (roleId: string, message: string, profileId?: string) => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const response = await apiService.chat(sessionId, {
        role_id: roleId,
        message,
        llm_profile_id: profileId,
      });

      if (response.error) {
        showNotification('Chat error: ' + response.error);
      }

      // Update state with response
      setGameState(response.current_state);
      setRecentDiffs(response.state_diffs);
    } catch (err) {
      showNotification('Failed to send message: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRedraw = async (characterId: string, profileId?: string) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await apiService.redrawMessage(sessionId, {
        character_id: characterId,
        llm_profile_id: profileId,
      });

      if (response.error) {
        showNotification('Redraw error: ' + response.error);
      }

      // Update state with response
      setGameState(response.current_state);
      setRecentDiffs(response.state_diffs);
    } catch (err) {
      showNotification('Failed to redraw message: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRollDice = async (
    notation: string,
    characterId?: string,
    reason?: string,
    modifier?: number
  ) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await apiService.rollDice(sessionId, {
        notation,
        character_id: characterId,
        reason,
        modifier,
      });

      setGameState(response.state);
      setLastDiceResult(response.result);
      showNotification(`Rolled ${notation}: ${response.result.final_result}`);
    } catch (err) {
      showNotification('Failed to roll dice: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshEvents = async () => {
    if (!sessionId) return;

    try {
      const response = await apiService.getHistory(sessionId);
      setEvents(response.events);
    } catch (err) {
      showNotification('Failed to fetch events: ' + (err as Error).message);
    }
  };

  const handleEditEvent = async (eventId: string, newData: Record<string, unknown>) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await apiService.editEvent(sessionId, eventId, {
        event_id: eventId,
        new_data: newData,
      });

      // Update state with response
      setGameState(response.current_state);
      
      // Refresh events
      await handleRefreshEvents();
      
      showNotification('Event edited successfully!');
    } catch (err) {
      showNotification('Failed to edit event: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRollbackToEvent = async (eventId: string) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await apiService.rollback(sessionId, { event_id: eventId });
      setGameState(response.state);
      
      // Refresh events
      await handleRefreshEvents();
      
      showNotification('Rollback successful!');
    } catch (err) {
      showNotification('Failed to rollback: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <TopNav 
        sessionId={sessionId} 
        onNewSession={handleNewSession}
        onOpenProfileManager={() => setShowProfileManager(true)}
        onOpenPresetLoader={() => setShowPresetLoader(true)}
        onDeleteSession={handleDeleteSession}
      />
      
      {error && (
        <div className="error-toast">
          {error}
        </div>
      )}

      <div className="main-content">
        <div className="left-panel">
          <ChatWindow
            messages={gameState?.messages || []}
            characters={gameState?.characters || {}}
            llmProfiles={globalProfiles}
            sessionCharacterProfiles={sessionCharacterProfiles}
            onRedraw={handleRedraw}
            onSetCharacterProfile={handleSetCharacterProfile}
          />
          <ChatInput
            characters={gameState?.characters || {}}
            llmProfiles={globalProfiles}
            sessionCharacterProfiles={sessionCharacterProfiles}
            onSend={handleSendMessage}
            disabled={loading || !sessionId}
          />
        </div>

        <div className="right-panel">
          <StatePanel gameState={gameState} />
          <DiceRoller
            characters={gameState?.characters || {}}
            sessionId={sessionId}
            onRollDice={handleRollDice}
            lastResult={lastDiceResult}
            disabled={loading}
          />
          <StateDiffsPanel diffs={recentDiffs} />
          <DebugPanel
            sessionId={sessionId}
            events={events}
            onRefreshEvents={handleRefreshEvents}
            onEditEvent={handleEditEvent}
            onRollbackToEvent={handleRollbackToEvent}
          />
        </div>
      </div>

      {/* Modals */}
      {showProfileManager && (
        <ProfileManager
          profiles={globalProfiles}
          onLoadProfiles={handleLoadProfiles}
          onAddProfile={handleAddProfile}
          onDeleteProfile={handleDeleteProfile}
          onClose={() => setShowProfileManager(false)}
        />
      )}

      {showPresetLoader && (
        <GamePresetLoader
          onLoadPreset={handleLoadPreset}
          onClose={() => setShowPresetLoader(false)}
        />
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner">Loading...</div>
        </div>
      )}
    </div>
  );
}

export default App;
