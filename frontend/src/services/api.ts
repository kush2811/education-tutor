import { HealthStatus, StudySession, Message, User, TokenResponse, UploadedFileResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

// Token storage key
const TOKEN_KEY = 'ai_tutor_auth_token';

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const getHeaders = (isFormData = false): HeadersInit => {
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  const token = tokenStorage.get();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const api = {
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed with status: ${res.status}`);
    }
    return res.json();
  },

  // --- Auth & User ---
  async register(data: { email: string; password: string; full_name?: string; grade_level?: string }): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  async login(data: { email: string; password: string }): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Invalid email or password');
    }
    const tokenData: TokenResponse = await res.json();
    tokenStorage.set(tokenData.access_token);
    return tokenData;
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      throw new Error('Not authenticated');
    }
    return res.json();
  },

  async updateProfile(data: { full_name?: string; grade_level?: string }): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/users/profile`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error('Failed to update profile');
    }
    return res.json();
  },

  async getDashboardStats(): Promise<import('../types').DashboardStats> {
    const res = await fetch(`${API_BASE_URL}/users/dashboard`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      throw new Error('Failed to load dashboard statistics');
    }
    return res.json();
  },

  // --- Sessions & Messages ---
  async listSessions(studentId = 'default_student'): Promise<StudySession[]> {
    const res = await fetch(`${API_BASE_URL}/sessions?student_id=${encodeURIComponent(studentId)}`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch sessions: ${res.status}`);
    }
    return res.json();
  },

  async getSession(sessionId: string): Promise<StudySession> {
    const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch session: ${res.status}`);
    }
    return res.json();
  },

  async createSession(data: { title: string; subject: string; student_id?: string }): Promise<StudySession> {
    const res = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'POST',
      headers: getHeaders(),
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
      headers: getHeaders(),
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
      headers: getHeaders(),
    });
    if (!res.ok && res.status !== 204) {
      throw new Error(`Failed to delete session: ${res.status}`);
    }
  },

  // --- File Uploads ---
  async uploadFile(file: File, sessionId?: string): Promise<UploadedFileResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    const res = await fetch(`${API_BASE_URL}/ingest/upload`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'File upload failed');
    }
    return res.json();
  }
};
