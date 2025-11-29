-- SQLite schema cho chatbot an ninh mạng (tấn công & phòng thủ)
-- DB này sẽ thay thế db chính cũ.

-- ==================================================================================
-- CORE APP TABLES (Users, Posts, Exams) - Migrated from schema.sql
-- ==================================================================================

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'student' CHECK(role IN ('student', 'teacher', 'admin')),
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Subjects/Topics table
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES subjects(id)
);

-- Posts Table
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    date TEXT NOT NULL,
    subject TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    views INTEGER DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    class TEXT,
    specialized TEXT,
    file_url TEXT,
    user_id INTEGER,
    teacher_id INTEGER, -- Ownership
    subject_id INTEGER, -- Categorization
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- Exams Table
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT,
    duration_min INTEGER,
    file_url TEXT,
    answer_file_url TEXT,
    created_by INTEGER,
    teacher_id INTEGER, -- Ownership
    subject_id INTEGER, -- Categorization
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- Password Reset Tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Questions Table
CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    question_text TEXT NOT NULL,
    question_type TEXT CHECK(question_type IN ('multiple_choice','true_false','short_answer')) NOT NULL,
    points REAL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id)
);

-- Question Options (for MCQ)
CREATE TABLE IF NOT EXISTS question_options (
    option_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

-- Question Answers (for TF/Short Answer, or MCQ official key)
CREATE TABLE IF NOT EXISTS question_answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    correct_answer TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

-- Exam Questions ordering and reuse
CREATE TABLE IF NOT EXISTS exam_questions (
    exam_id INTEGER,
    question_id INTEGER,
    order_index INTEGER,
    PRIMARY KEY (exam_id, question_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id),
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

-- Indexes for Core App
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_posts_subject ON posts(subject);
CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_teacher_id ON posts(teacher_id);
CREATE INDEX IF NOT EXISTS idx_posts_subject_id ON posts(subject_id);
CREATE INDEX IF NOT EXISTS idx_exams_subject ON exams(subject);
CREATE INDEX IF NOT EXISTS idx_exams_teacher_id ON exams(teacher_id);
CREATE INDEX IF NOT EXISTS idx_exams_subject_id ON exams(subject_id);
CREATE INDEX IF NOT EXISTS idx_reset_tokens ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_question_options_qid ON question_options(question_id);
CREATE INDEX IF NOT EXISTS idx_question_answers_qid ON question_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_exam_questions_order ON exam_questions(exam_id, order_index);


-- ==================================================================================
-- CYBER SECURITY CHAT TABLES
-- ==================================================================================

-- Bảng chủ đề an ninh mạng (attack / defense)
CREATE TABLE IF NOT EXISTS cyber_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    -- 'attack', 'defense', 'both', 'other'
    topic_type TEXT NOT NULL DEFAULT 'other',
    -- ví dụ: Web, Network, Malware, Blue Team...
    domain TEXT,
    level TEXT, -- beginner / intermediate / advanced
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cyber_topics_slug ON cyber_topics(slug);
CREATE INDEX IF NOT EXISTS idx_cyber_topics_type ON cyber_topics(topic_type);

-- Bảng tài liệu / resource (sách, bài viết, lab, tool...)
CREATE TABLE IF NOT EXISTS cyber_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    resource_type TEXT CHECK(resource_type IN ('book', 'article', 'lab', 'tool', 'note')) NOT NULL,
    source TEXT,
    file_url TEXT,
    is_offensive BOOLEAN DEFAULT 0,
    is_defensive BOOLEAN DEFAULT 0,
    difficulty TEXT CHECK(difficulty IN ('beginner', 'intermediate', 'advanced')),
    tags TEXT,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES cyber_topics(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_cyber_resources_topic ON cyber_resources(topic_id);
CREATE INDEX IF NOT EXISTS idx_cyber_resources_off_def ON cyber_resources(is_offensive, is_defensive);

-- Phiên chat của người dùng với chatbot
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,                 -- có thể null nếu ẩn danh
    title TEXT,
    topic_id INTEGER,                -- gắn với cyber_topics nếu có
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES cyber_topics(id)
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_topic ON chat_sessions(topic_id);

-- Tin nhắn trong phiên chat
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,              -- user / assistant / system
    content TEXT NOT NULL,
    -- metadata JSON (như: used_docs, model, latency, score...)
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);

-- Insert default subjects if not exists
INSERT OR IGNORE INTO subjects (name, description) VALUES 
('Toán học', 'Các bài học và tài liệu về Toán học'),
('Vật lý', 'Các bài học và tài liệu về Vật lý'),
('Hóa học', 'Các bài học và tài liệu về Hóa học'),
('Sinh học', 'Các bài học và tài liệu về Sinh học'),
('Ngữ văn', 'Các bài học và tài liệu về Ngữ văn'),
('Tiếng Anh', 'Các bài học và tài liệu về Tiếng Anh'),
('Lịch sử', 'Các bài học và tài liệu về Lịch sử'),
('Địa lý', 'Các bài học và tài liệu về Địa lý'),
('Tin học', 'Các bài học và tài liệu về Tin học');
