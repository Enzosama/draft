-- Add role field to users table
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student' CHECK(role IN ('student', 'teacher', 'admin'));

-- Add teacher_id field to posts for ownership
ALTER TABLE posts ADD COLUMN teacher_id INTEGER;
ALTER TABLE posts ADD FOREIGN KEY (teacher_id) REFERENCES users(id);

-- Add teacher_id field to exams for ownership
ALTER TABLE exams ADD COLUMN teacher_id INTEGER;
ALTER TABLE exams ADD FOREIGN KEY (teacher_id) REFERENCES users(id);

-- Classrooms table
CREATE TABLE IF NOT EXISTS classrooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    subject TEXT,
    teacher_id INTEGER NOT NULL,
    code TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

-- Classroom students relationship
CREATE TABLE IF NOT EXISTS classroom_students (
    classroom_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (classroom_id, student_id),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Classroom posts (teacher can assign posts to specific classrooms)
CREATE TABLE IF NOT EXISTS classroom_posts (
    classroom_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (classroom_id, post_id),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Classroom exams (teacher can assign exams to specific classrooms)
CREATE TABLE IF NOT EXISTS classroom_exams (
    classroom_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME,
    PRIMARY KEY (classroom_id, exam_id),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classroom_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    is_announcement BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Student notification read status
CREATE TABLE IF NOT EXISTS notification_reads (
    notification_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (notification_id, student_id),
    FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Subjects/Topics table for better organization
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES subjects(id)
);

-- Add subject_id to posts for better categorization
ALTER TABLE posts ADD COLUMN subject_id INTEGER;
ALTER TABLE posts ADD FOREIGN KEY (subject_id) REFERENCES subjects(id);

-- Add subject_id to exams for better categorization
ALTER TABLE exams ADD COLUMN subject_id INTEGER;
ALTER TABLE exams ADD FOREIGN KEY (subject_id) REFERENCES subjects(id);

-- Add classroom_id to posts for classroom-specific content
ALTER TABLE posts ADD COLUMN classroom_id INTEGER;
ALTER TABLE posts ADD FOREIGN KEY (classroom_id) REFERENCES classrooms(id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_posts_teacher_id ON posts(teacher_id);
CREATE INDEX IF NOT EXISTS idx_posts_subject_id ON posts(subject_id);
CREATE INDEX IF NOT EXISTS idx_posts_classroom_id ON posts(classroom_id);
CREATE INDEX IF NOT EXISTS idx_exams_teacher_id ON exams(teacher_id);
CREATE INDEX IF NOT EXISTS idx_exams_subject_id ON exams(subject_id);
CREATE INDEX IF NOT EXISTS idx_classrooms_teacher_id ON classrooms(teacher_id);
CREATE INDEX IF NOT EXISTS idx_classrooms_code ON classrooms(code);
CREATE INDEX IF NOT EXISTS idx_classroom_students_classroom_id ON classroom_students(classroom_id);
CREATE INDEX IF NOT EXISTS idx_classroom_students_student_id ON classroom_students(student_id);
CREATE INDEX IF NOT EXISTS idx_notifications_classroom_id ON notifications(classroom_id);
CREATE INDEX IF NOT EXISTS idx_notification_reads_notification_id ON notification_reads(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_reads_student_id ON notification_reads(student_id);

-- Insert default subjects
INSERT INTO subjects (name, description) VALUES 
('Toán học', 'Các bài học và tài liệu về Toán học'),
('Vật lý', 'Các bài học và tài liệu về Vật lý'),
('Hóa học', 'Các bài học và tài liệu về Hóa học'),
('Sinh học', 'Các bài học và tài liệu về Sinh học'),
('Ngữ văn', 'Các bài học và tài liệu về Ngữ văn'),
('Tiếng Anh', 'Các bài học và tài liệu về Tiếng Anh'),
('Lịch sử', 'Các bài học và tài liệu về Lịch sử'),
('Địa lý', 'Các bài học và tài liệu về Địa lý'),
('Tin học', 'Các bài học và tài liệu về Tin học');