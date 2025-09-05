CREATE TABLE colleges (college_id INTEGER PRIMARY KEY AUTOINCREMENT, college_name TEXT NOT NULL);
CREATE TABLE students (student_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE, college_id INTEGER);
CREATE TABLE events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, event_name TEXT NOT NULL, event_type TEXT, date TEXT, college_id INTEGER);
CREATE TABLE registrations (reg_id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, event_id INTEGER, status TEXT DEFAULT 'registered', feedback INTEGER);
