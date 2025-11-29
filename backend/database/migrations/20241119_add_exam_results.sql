-- Exam Results table to store student exam submissions
CREATE TABLE IF NOT EXISTS exam_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    score REAL DEFAULT 0,
    total_points REAL DEFAULT 0,
    percentage REAL DEFAULT 0,
    time_spent_seconds INTEGER DEFAULT 0,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Student Answers table to store individual answers
CREATE TABLE IF NOT EXISTS student_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_result_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer_text TEXT,
    option_id INTEGER,
    is_correct BOOLEAN DEFAULT 0,
    points_earned REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_result_id) REFERENCES exam_results(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES question_options(option_id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_exam_results_exam_id ON exam_results(exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_results_student_id ON exam_results(student_id);
CREATE INDEX IF NOT EXISTS idx_exam_results_submitted_at ON exam_results(submitted_at);
CREATE INDEX IF NOT EXISTS idx_student_answers_result_id ON student_answers(exam_result_id);
CREATE INDEX IF NOT EXISTS idx_student_answers_question_id ON student_answers(question_id);

