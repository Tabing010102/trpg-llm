// API service for TRPG-LLM backend

import type {
  CreateSessionResponse,
  ChatRequest,
  ChatResponse,
  RedrawMessageRequest,
  EditEventRequest,
  EditEventResponse,
  SessionHistoryResponse,
  GameState,
  LLMProfile,
  CharacterProfilesResponse,
  ProfilesResponse,
  DiceRollRequest,
  DiceRollResponse,
  RollbackRequest,
  RollbackResponse,
  GameConfig,
} from '../types/api';

const API_BASE = '';  // Using proxy, no need for full URL

class ApiService {
  private async request<T>(
    url: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // ===== Global Profile Management =====
  
  async getProfiles(): Promise<ProfilesResponse> {
    return this.request<ProfilesResponse>(`${API_BASE}/api/v1/profiles`);
  }

  async setProfiles(profiles: LLMProfile[]): Promise<{ message: string; count: number }> {
    return this.request<{ message: string; count: number }>(`${API_BASE}/api/v1/profiles`, {
      method: 'POST',
      body: JSON.stringify(profiles),
    });
  }

  async addProfile(profile: LLMProfile): Promise<{ message: string }> {
    return this.request<{ message: string }>(`${API_BASE}/api/v1/profiles/add`, {
      method: 'POST',
      body: JSON.stringify(profile),
    });
  }

  async deleteProfile(profileId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`${API_BASE}/api/v1/profiles/${profileId}`, {
      method: 'DELETE',
    });
  }

  // ===== Session Character Profiles =====

  async getSessionCharacterProfiles(sessionId: string): Promise<CharacterProfilesResponse> {
    return this.request<CharacterProfilesResponse>(
      `${API_BASE}/sessions/${sessionId}/character-profiles`
    );
  }

  async setCharacterProfile(
    sessionId: string,
    characterId: string,
    profileId: string
  ): Promise<{ message: string; session_id: string; character_id: string; profile_id: string }> {
    return this.request<{ message: string; session_id: string; character_id: string; profile_id: string }>(
      `${API_BASE}/sessions/${sessionId}/character-profiles/${characterId}`,
      {
        method: 'PUT',
        body: JSON.stringify({ profile_id: profileId }),
      }
    );
  }

  async resetCharacterProfile(sessionId: string, characterId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(
      `${API_BASE}/sessions/${sessionId}/character-profiles/${characterId}`,
      {
        method: 'DELETE',
      }
    );
  }

  // ===== Session Management =====

  async createSession(config: Record<string, any>): Promise<CreateSessionResponse> {
    return this.request<CreateSessionResponse>(`${API_BASE}/sessions`, {
      method: 'POST',
      body: JSON.stringify({ config }),
    });
  }

  async getSession(sessionId: string): Promise<{ session_id: string; state: GameState }> {
    return this.request<{ session_id: string; state: GameState }>(
      `${API_BASE}/sessions/${sessionId}`
    );
  }

  async getHistory(sessionId: string): Promise<SessionHistoryResponse> {
    return this.request<SessionHistoryResponse>(
      `${API_BASE}/sessions/${sessionId}/history`
    );
  }

  async chat(sessionId: string, request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>(
      `${API_BASE}/api/v1/sessions/${sessionId}/chat`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  async redrawMessage(sessionId: string, request: RedrawMessageRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>(
      `${API_BASE}/sessions/${sessionId}/redraw`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  async editEvent(
    sessionId: string,
    eventId: string,
    request: EditEventRequest
  ): Promise<EditEventResponse> {
    return this.request<EditEventResponse>(
      `${API_BASE}/sessions/${sessionId}/events/${eventId}/edit`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  async deleteSession(sessionId: string): Promise<{ message: string; session_id: string }> {
    return this.request<{ message: string; session_id: string }>(
      `${API_BASE}/sessions/${sessionId}`,
      {
        method: 'DELETE',
      }
    );
  }

  // ===== Dice Roll =====

  async rollDice(sessionId: string, request: DiceRollRequest): Promise<DiceRollResponse> {
    return this.request<DiceRollResponse>(
      `${API_BASE}/sessions/${sessionId}/dice`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  // ===== Rollback =====

  async rollback(sessionId: string, request: RollbackRequest): Promise<RollbackResponse> {
    return this.request<RollbackResponse>(
      `${API_BASE}/sessions/${sessionId}/rollback`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  // ===== Game Configuration =====

  // Note: This creates a session with a provided config (for loading presets)
  async createSessionWithConfig(config: GameConfig): Promise<CreateSessionResponse> {
    return this.request<CreateSessionResponse>(`${API_BASE}/sessions`, {
      method: 'POST',
      body: JSON.stringify({ config }),
    });
  }
}

export const apiService = new ApiService();
