-- AI-Based Personalised Study Planner — Database Schema (MySQL/MariaDB)

CREATE DATABASE IF NOT EXISTS study_planner;
USE study_planner;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    daily_study_hours FLOAT NOT NULL DEFAULT 2.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE modules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    priority ENUM('low','medium','high') NOT NULL DEFAULT 'medium',
    difficulty INT NOT NULL DEFAULT 3,          -- 1 (easy) to 5 (very hard)
    estimated_hours FLOAT NOT NULL,
    hours_completed FLOAT NOT NULL DEFAULT 0,
    is_struggling BOOLEAN NOT NULL DEFAULT FALSE,
    status ENUM('not_started','in_progress','completed') NOT NULL DEFAULT 'not_started',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    CHECK (difficulty BETWEEN 1 AND 5)
);

CREATE TABLE study_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    scheduled_date DATE NOT NULL,
    allocated_hours FLOAT NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    started_at DATETIME NULL,   -- set when a live Start/Stop Session timer begins
    ended_at DATETIME NULL,     -- set when it's stopped; allocated_hours is computed from the two
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NULL,
    user_id INT NOT NULL,
    content TEXT,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_tasks_module ON tasks(module_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_sessions_user_date ON study_sessions(user_id, scheduled_date);
