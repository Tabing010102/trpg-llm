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
}

export const apiService = new ApiService();
