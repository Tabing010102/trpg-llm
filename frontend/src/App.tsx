import { useState } from 'react';
import TopNav from './components/TopNav';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import StatePanel from './components/StatePanel';
import StateDiffsPanel from './components/StateDiffsPanel';
import DebugPanel from './components/DebugPanel';
import { apiService } from './services/api';
import type { GameState, StateDiff, Event } from './types/api';
import './App.css';

// Default configuration for new sessions (using simple_game.json as reference)
const DEFAULT_CONFIG = {
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

  const showError = (message: string) => {
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
      showError('Session created successfully!');
    } catch (err) {
      showError('Failed to create session: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (roleId: string, message: string) => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const response = await apiService.chat(sessionId, {
        role_id: roleId,
        message,
      });

      if (response.error) {
        showError('Chat error: ' + response.error);
      }

      // Update state with response
      setGameState(response.current_state);
      setRecentDiffs(response.state_diffs);
    } catch (err) {
      showError('Failed to send message: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRedraw = async (characterId: string) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await apiService.redrawMessage(sessionId, {
        character_id: characterId,
      });

      if (response.error) {
        showError('Redraw error: ' + response.error);
      }

      // Update state with response
      setGameState(response.current_state);
      setRecentDiffs(response.state_diffs);
    } catch (err) {
      showError('Failed to redraw message: ' + (err as Error).message);
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
      showError('Failed to fetch events: ' + (err as Error).message);
    }
  };

  const handleEditEvent = async (eventId: string, newData: Record<string, any>) => {
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
      
      showError('Event edited successfully!');
    } catch (err) {
      showError('Failed to edit event: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <TopNav sessionId={sessionId} onNewSession={handleNewSession} />
      
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
            onRedraw={handleRedraw}
          />
          <ChatInput
            characters={gameState?.characters || {}}
            onSend={handleSendMessage}
            disabled={loading || !sessionId}
          />
        </div>

        <div className="right-panel">
          <StatePanel gameState={gameState} />
          <StateDiffsPanel diffs={recentDiffs} />
          <DebugPanel
            sessionId={sessionId}
            events={events}
            onRefreshEvents={handleRefreshEvents}
            onEditEvent={handleEditEvent}
          />
        </div>
      </div>

      {loading && (
        <div className="loading-overlay">
          <div className="spinner">Loading...</div>
        </div>
      )}
    </div>
  );
}

export default App;
