-- Poornima University Management System Database Schema
-- MySQL Database Creation Script

CREATE DATABASE IF NOT EXISTS university_db;
USE university_db;

-- Users Table (Core Authentication)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','hod','teacher','student') NOT NULL,
    status ENUM('pending','approved','suspended') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_status (status)
);


-- Departments Table
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    hod_id INT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Students Table
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    dob DATE,
    gender VARCHAR(20),
    enrollment_number VARCHAR(20) UNIQUE NOT NULL,
    program VARCHAR(50),
    department VARCHAR(100),
    semester INT,
    current_cgpa DECIMAL(4, 2) DEFAULT 0.0,
    status ENUM('pending', 'approved', 'suspended', 'graduated') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_enrollment (enrollment_number),
    INDEX idx_department (department),
    INDEX idx_status (status)
);

-- Teachers Table
CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(100) NOT NULL,
    qualification VARCHAR(100),
    specialization VARCHAR(100),
    experience INT,
    status ENUM('pending', 'approved', 'inactive') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department) REFERENCES departments(name),
    INDEX idx_user_id (user_id),
    INDEX idx_employee_id (employee_id),
    INDEX idx_department (department),
    INDEX idx_status (status)
);

-- HODs Table
CREATE TABLE hods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(100) NOT NULL,
    office_location VARCHAR(100),
    qualification VARCHAR(100),
    experience INT,
    status ENUM('pending', 'approved', 'inactive') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department) REFERENCES departments(name),
    INDEX idx_user_id (user_id),
    INDEX idx_employee_id (employee_id),
    INDEX idx_department (department),
    INDEX idx_status (status)
);

-- Admins Table
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    admin_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    access_level VARCHAR(50),
    security_pin VARCHAR(255),
    status ENUM('approved', 'inactive') DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_admin_id (admin_id),
    INDEX idx_status (status)
);

-- Attendance Table (new feature)
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    `date` DATE NOT NULL,
    status ENUM('present','absent') NOT NULL,
    marked_by INT NOT NULL,
    role ENUM('teacher','hod','admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE INDEX idx_attendance_date ON attendance(`date`);

-- Subjects Table
CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(20) UNIQUE NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    credits INT,
    department VARCHAR(100),
    teacher_id INT,
    semester INT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    FOREIGN KEY (department) REFERENCES departments(name),
    INDEX idx_code (subject_code),
    INDEX idx_department (department)
);

-- Enrollments Table (Student-Subject mapping)
CREATE TABLE enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    UNIQUE KEY unique_enrollment (student_id, subject_id),
    INDEX idx_student (student_id)
);

-- Attendance Table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    date DATE NOT NULL,
    status ENUM('present', 'absent', 'leave') DEFAULT 'absent',
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    INDEX idx_student (student_id),
    INDEX idx_date (date)
);

-- Marks Table
CREATE TABLE marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    internal DECIMAL(5, 2) DEFAULT 0,
    midterm DECIMAL(5, 2) DEFAULT 0,
    final DECIMAL(5, 2) DEFAULT 0,
    total DECIMAL(5, 2) DEFAULT 0,
    grade VARCHAR(2),
    mark_type VARCHAR(50),
    uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    INDEX idx_student (student_id),
    INDEX idx_subject (subject_id)
);

-- Assignments Table
CREATE TABLE assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description LONGTEXT,
    due_date DATE,
    max_marks INT DEFAULT 100,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    INDEX idx_subject (subject_id)
);

-- Assignment Submissions Table
CREATE TABLE submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    student_id INT NOT NULL,
    submission_text LONGTEXT,
    submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assignment_status ENUM('submitted', 'graded', 'late') DEFAULT 'submitted',
    marks INT,
    feedback LONGTEXT,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    INDEX idx_assignment (assignment_id),
    INDEX idx_student (student_id)
);

-- Notices Table
CREATE TABLE notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content LONGTEXT NOT NULL,
    posted_by INT,
    posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visibility ENUM('all', 'students', 'teachers', 'hods', 'admins') DEFAULT 'all',
    INDEX idx_posted_date (posted_date),
    INDEX idx_visibility (visibility)
);

-- Exam Schedule Table
CREATE TABLE exam_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    student_id INT,
    exam_type ENUM('midterm', 'final', 'practical', 'viva') DEFAULT 'final',
    exam_date DATE NOT NULL,
    exam_time TIME NOT NULL,
    room_no VARCHAR(20),
    duration_minutes INT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    INDEX idx_date (exam_date)
);

-- Analytics Table (for storing analytics cache)
CREATE TABLE analytics_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value LONGTEXT,
    department VARCHAR(100),
    semester INT,
    calculated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric (metric_name),
    INDEX idx_department (department)
);

-- AI Predictions Table
CREATE TABLE ai_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    prediction_type ENUM('performance', 'dropout', 'attendance') NOT NULL,
    prediction_score DECIMAL(5, 2),
    prediction_label VARCHAR(50),
    confidence DECIMAL(5, 2),
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    INDEX idx_student (student_id),
    INDEX idx_type (prediction_type)
);

-- System Logs Table
CREATE TABLE system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id INT,
    details LONGTEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_user (user_id)
);

-- Create Indexes for common queries
CREATE INDEX idx_department_hod ON departments(hod_id);
CREATE INDEX idx_teacher_dept ON teachers(department);
CREATE INDEX idx_hod_dept ON hods(department);
CREATE INDEX idx_subject_teacher ON subjects(teacher_id);
CREATE INDEX idx_attendance_composite ON attendance(student_id, subject_id, date);
CREATE INDEX idx_marks_composite ON marks(student_id, subject_id);
CREATE INDEX idx_submission_composite ON submissions(student_id, assignment_id);

-- Set foreign key constraints
ALTER TABLE departments ADD CONSTRAINT fk_hod FOREIGN KEY (hod_id) REFERENCES hods(id);

-- Insert Initial Departments
INSERT IGNORE INTO departments (id, name) VALUES
(1, 'engineering'),
(2, 'science'),
(3, 'commerce'),
(4, 'humanities'),
(5, 'law');
