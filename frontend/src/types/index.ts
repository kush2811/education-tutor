export interface User {
  id: string;
  email: string;
  full_name: string;
  grade_level: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface MessageCitation {
  source_name: string;
  chapter: string;
  page_number?: number;
  excerpt?: string;
}

export interface Message {
  id: string;
  session_id: string;
  sender_role: 'user' | 'assistant' | 'system';
  content_type: 'text' | 'image' | 'audio' | 'multimodal';
  content: string;
  metadata_json?: string | null;
  citations?: MessageCitation[];
  audio_url?: string;
  created_at: string;
}

export interface StudySession {
  id: string;
  user_id?: string;
  student_id: string;
  title: string;
  subject: string;
  status: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
  database_status: string;
  timestamp: string;
}

export interface UploadedFileResponse {
  asset_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  status: string;
  message: string;
}

export interface RecentSessionItem {
  id: string;
  title: string;
  subject: string;
  status: string;
  message_count: number;
  updated_at: string;
}

export interface DashboardStats {
  user_id: string;
  full_name: string;
  grade_level: string;
  total_sessions: number;
  total_messages: number;
  total_uploads: number;
  active_streak_days: number;
  recent_sessions: RecentSessionItem[];
  recommended_topics: string[];
}
