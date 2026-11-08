import { HealthStatus, StudySession, Message } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

export const api = {
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed with status: ${res.status}`);
    }
    return res.json();
  },

  async listSessions(studentId = 'default_student'): Promise<StudySession[]> {
    const res = await fetch(`${API_BASE_URL}/sessions?student_id=${encodeURIComponent(studentId)}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch sessions: ${res.status}`);
    }
    return res.json();
  },

  async getSession(sessionId: string): Promise<StudySession> {
    const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch session: ${res.status}`);
    }
    return res.json();
  },

  async createSession(data: { title: string; subject: string; student_id?: string }): Promise<StudySession> {
    const res = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error(`Failed to create session: ${res.status}`);
    }
    return res.json();
  },

  async addMessage(sessionId: string, message: {
    sender_role: 'user' | 'assistant' | 'system';
    content: string;
    content_type?: string;
    metadata_json?: string;
  }): Promise<Message> {
    const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message),
    });
    if (!res.ok) {
      throw new Error(`Failed to post message: ${res.status}`);
    }
    return res.json();
  },

  async deleteSession(sessionId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!res.ok && res.status !== 204) {
      throw new Error(`Failed to delete session: ${res.status}`);
    }
  }
};
