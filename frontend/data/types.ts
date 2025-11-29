export enum Category {
  MATERIAL = 'Tài Liệu',
  PRACTICE = 'Luyện tập',
  MOCK_TEST = 'Đề Thi',
}

export interface Post {
  id: number;
  title: string;
  author: string;
  date: string;
  subject: string;
  category: Category;
  description: string;
  views: number;
  downloads: number;
  comments: number;
  fileUrl?: string;
}

export interface User {
  id?: number;
  name: string;
  email: string;
  avatarUrl?: string;
  role?: 'student' | 'teacher' | 'admin';
  phone?: string;
  created_at?: string;
  is_active?: boolean;
}

export interface Classroom {
  id: number;
  name: string;
  description?: string;
  subject?: string;
  code: string;
  is_active: boolean;
  student_count: number;
  created_at: string;
  teacher_id?: number;
}

export interface Notification {
  id: number;
  classroom_id: number;
  title: string;
  content: string;
  is_announcement: boolean;
  created_by: number;
  created_at: string;
  unread_count?: number;
  is_read?: boolean;
  read_at?: string;
}

export interface TeacherPost extends Post {
  teacher_id?: number;
  classroom_id?: number;
}

export interface CyberResource {
  id?: number;
  topic_id?: number;
  title: string;
  resource_type: 'book' | 'article' | 'lab' | 'tool' | 'note';
  source?: string;
  file_url?: string;
  is_offensive: boolean;
  is_defensive: boolean;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  tags?: string;
  summary?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CyberTopic {
  id?: number;
  slug: string;
  name: string;
  topic_type: 'attack' | 'defense' | 'both' | 'other';
  domain?: string;
  level?: 'beginner' | 'intermediate' | 'advanced';
  description?: string;
  created_at?: string;
  resources?: CyberResource[];
}
