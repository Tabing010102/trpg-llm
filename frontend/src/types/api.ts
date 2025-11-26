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
    model?: string;
    temperature?: number;
    profile_id?: string;
  };
}

export interface LLMProfile {
  id: string;
  provider_type: string;
  model: string;
  temperature: number;
  base_url?: string;
  api_key_ref?: string;
  top_p?: number;
  max_tokens?: number;
  context_window?: number;
  extra_params?: Record<string, any>;
}

export interface GameState {
  session_id: string;
  config: {
    name: string;
    rule_system: string;
    description?: string;
    characters: Record<string, Character>;
    llm_config?: Record<string, any>;
    llm_profiles?: LLMProfile[];
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
  llm_profile_id?: string;
}

export interface ChatResponse {
  content?: string;
  state_diffs: StateDiff[];
  current_state: GameState;
  tool_calls: any[];
  role_id: string;
  is_ai: boolean;
  error?: string;
  used_profile_id?: string;
}

export interface RedrawMessageRequest {
  character_id: string;
  template?: string;
  llm_profile_id?: string;
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

export interface SetCharacterProfileRequest {
  profile_id: string;
}

export interface CharacterProfilesResponse {
  session_id: string;
  character_profiles: Record<string, string>;
}

export interface ProfilesResponse {
  profiles: LLMProfile[];
}

// Dice roll types
export interface DiceRollRequest {
  notation: string;
  reason?: string;
  character_id?: string;
  modifier?: number;
  difficulty?: string;
  target_value?: number;
}

export interface DiceRollResponse {
  session_id: string;
  result: DiceRollResult;
  state: GameState;
}

export interface DiceRollResult {
  notation: string;
  rolls: number[];
  modifier: number;
  total: number;
  final_result: number;
  success?: boolean | null;
  success_level?: string | null;
  critical_success?: boolean | null;
  critical_failure?: boolean | null;
  reason?: string | null;
  character_id?: string | null;
}

// Rollback types
export interface RollbackRequest {
  event_id?: string;
  timestamp?: string;
}

export interface RollbackResponse {
  session_id: string;
  state: GameState;
}

// Game config type for loading presets
export interface GameConfig {
  name: string;
  rule_system: string;
  description?: string;
  characters: Record<string, Character>;
  llm_config?: LLMConfig;
  llm_profiles?: LLMProfile[];
  workflow?: WorkflowConfig;
  tools?: ToolConfig[];
  initial_state?: Record<string, unknown>;
}

export interface LLMConfig {
  default_model?: string;
  temperature?: number;
  max_tokens?: number;
  prompts?: Record<string, string>;
}

export interface WorkflowConfig {
  turn_order?: string[];
  phases?: string[];
}

export interface ToolConfig {
  name: string;
  description: string;
  parameters: Record<string, ToolParameter>;
}

export interface ToolParameter {
  type: string;
  description?: string;
  enum?: string[];
  default?: string | number | boolean;
}
