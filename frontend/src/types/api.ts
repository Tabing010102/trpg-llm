// API types for TRPG-LLM

export interface Character {
  id: string;
  name: string;
  type: 'player' | 'npc' | 'gm';
  control: 'human' | 'ai';
  description?: string;
  attributes?: Record<string, any>;
  state?: Record<string, any>;
  ai_config?: {
    model: string;
    temperature: number;
  };
}

export interface GameState {
  session_id: string;
  config: {
    name: string;
    rule_system: string;
    description?: string;
    characters: Record<string, Character>;
    llm_config?: Record<string, any>;
    workflow?: Record<string, any>;
    tools?: any[];
    initial_state?: Record<string, any>;
  };
  state: Record<string, any>;
  characters: Record<string, Character>;
  current_turn: number;
  current_phase?: string;
  current_actor?: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Message {
  sender_id: string;
  content: string;
  message_type?: string;
  metadata?: Record<string, any>;
  timestamp?: string;
  is_ai?: boolean;
}

export interface StateDiff {
  path: string;
  operation: string;
  value: any;
  previous_value?: any;
}

export interface Event {
  id: string;
  timestamp: string;
  type: string;
  actor_id?: string;
  data: Record<string, any>;
  state_diffs: StateDiff[];
  metadata?: Record<string, any>;
}

export interface CreateSessionRequest {
  config: Record<string, any>;
}

export interface CreateSessionResponse {
  session_id: string;
  state: GameState;
}

export interface ChatRequest {
  role_id: string;
  message?: string;
  template?: string;
  max_tool_iterations?: number;
}

export interface ChatResponse {
  content?: string;
  state_diffs: StateDiff[];
  current_state: GameState;
  tool_calls: any[];
  role_id: string;
  is_ai: boolean;
  error?: string;
}

export interface RedrawMessageRequest {
  character_id: string;
  template?: string;
}

export interface EditEventRequest {
  event_id: string;
  new_data?: Record<string, any>;
  new_state_diffs?: StateDiff[];
}

export interface EditEventResponse {
  session_id: string;
  event_id: string;
  current_state: GameState;
}

export interface SessionHistoryResponse {
  session_id: string;
  events: Event[];
}
