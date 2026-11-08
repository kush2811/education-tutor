export interface Message {
  id: string;
  session_id: string;
  sender_role: 'user' | 'assistant' | 'system';
  content_type: 'text' | 'image' | 'audio' | 'multimodal';
  content: string;
  metadata_json?: string | null;
  created_at: string;
}

export interface StudySession {
  id: string;
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
