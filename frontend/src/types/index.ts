export interface User {
  id: string;
  email: string;
  full_name: string;
  grade_level: string;
  is_active: boolean;
  preferred_explanation_level?: string;
  preferred_voice?: string;
  preferred_playback_speed?: number;
  preferred_language?: string;
  preferred_subjects?: string;
  created_at: string;
}

export interface StudentPreferences {
  preferred_explanation_level: 'beginner' | 'intermediate' | 'advanced';
  preferred_voice: string;
  preferred_playback_speed: number;
  preferred_language: string;
  preferred_subjects: string[];
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
  created_at: string;
  updated_at: string;
}

export interface WordSegment {
  word: string;
  start_time: number;
  end_time: number;
}

export interface SentenceSegment {
  sentence_index: number;
  display_text: string;
  spoken_text: string;
  start_time: number;
  end_time: number;
  words: WordSegment[];
}

export interface TTSVoiceResponse {
  complete_answer_text: string;
  spoken_text: string;
  audio_url: string | null;
  duration_seconds: number;
  sentence_segments: SentenceSegment[];
  voice_used: string;
  alignment_method: string;
  audio_format: string;
  error?: string;
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

export interface PipelineResponse {
  session_id?: string;
  input_type: string;
  extracted_question: string;
  detected_math: string[];
  query_intent: string;
  subject: string;
  retrieved_chunks_count: number;
  citations: MessageCitation[];
  sympy_verified: boolean;
  sympy_result?: string;
  formatted_markdown: string;
  validation: Record<string, any>;
  voice?: TTSVoiceResponse;
  performance_metrics: {
    input_processing_time_ms: number;
    query_classification_time_ms: number;
    retrieval_time_ms: number;
    answer_generation_time_ms: number;
    validation_time_ms: number;
    tts_generation_time_ms: number;
    total_response_time_ms: number;
  };
}
