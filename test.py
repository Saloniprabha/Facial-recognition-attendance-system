import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import cv2
import os
import numpy as np
import face_recognition
import sqlite3
from datetime import datetime
import pandas as pd
from PIL import Image, ImageTk
import hashlib
import sys
import traceback
import io

class AttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Facial Recognition Attendance System")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Initialize variables
        self.cap = None
        self.captured_encoding = None
        self.video_frame = None
        self.status_label = None
        self.capture_in_progress = False
        
        # Database connection with error handling
        try:
            self.conn = sqlite3.connect("attendance.db")
            self.create_tables()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
            self.exit_application()
        
        # Load known faces
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()
        
        # Main screen components
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.place(relwidth=1, relheight=1)
        
        # Title
        title_label = tk.Label(self.main_frame, text="Facial Recognition Attendance System", 
                              font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=30)
        
        # Buttons
        student_btn = tk.Button(self.main_frame, text="Student", font=("Arial", 14),
                               width=20, height=2, command=self.open_student_interface)
        student_btn.pack(pady=20)
        
        faculty_btn = tk.Button(self.main_frame, text="Faculty", font=("Arial", 14),
                               width=20, height=2, command=self.open_faculty_login)
        faculty_btn.pack(pady=20)
        
        register_btn = tk.Button(self.main_frame, text="Register New Student", font=("Arial", 14),
                                width=20, height=2, command=self.open_registration)
        register_btn.pack(pady=20)
        
        exit_btn = tk.Button(self.main_frame, text="Exit", font=("Arial", 14),
                           width=20, height=2, command=self.exit_application)
        exit_btn.pack(pady=20)

        # Modify the main menu in __init__ to include student login
        student_login_btn = tk.Button(self.main_frame, text="Student Login", font=("Arial", 14),
                           width=20, height=2, command=self.open_student_login)
        student_login_btn.pack(pady=20)
        
        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Faculty table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
        ''')
        
        # Student table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            face_encoding BLOB
        )
        ''')
        
        # Attendance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
        ''')
        
        # Insert default faculty account if not exists
        cursor.execute("SELECT * FROM faculty WHERE faculty_id = 'admin'")
        if not cursor.fetchone():
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO faculty (faculty_id, name, password_hash) VALUES (?, ?, ?)",
                         ("admin", "Administrator", password_hash))
        
        self.conn.commit()

    def load_known_faces(self):
        try:
            if not self.reconnect_database():
                return
                
            cursor = self.conn.cursor()
            cursor.execute("SELECT student_id, name, face_encoding FROM students WHERE face_encoding IS NOT NULL")
            students = cursor.fetchall()
            
            self.known_face_encodings = []
            self.known_face_names = []
            
            for student in students:
                student_id, name, face_encoding_blob = student
                if face_encoding_blob:  # Check if not None
                    try:
                        face_encoding = np.frombuffer(face_encoding_blob, dtype=np.float64)
                        self.known_face_encodings.append(face_encoding)
                        self.known_face_names.append(f"{name} ({student_id})")
                    except Exception as e:
                        print(f"Error loading face encoding for student {student_id}: {str(e)}")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading face data: {str(e)}")
    
    def open_student_interface(self):
        self.clear_frame()
    
        student_frame = tk.Frame(self.root, bg="#f0f0f0")
        student_frame.place(relwidth=1, relheight=1)
    
        title_label = tk.Label(student_frame, text="Student Attendance", 
                          font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
    
        # Video frame
        self.video_frame = tk.Label(student_frame)
        self.video_frame.pack(pady=10)
    
        # Status label
        self.status_label = tk.Label(student_frame, text="Ready to detect faces...", 
                                font=("Arial", 12), bg="#f0f0f0")
        self.status_label.pack(pady=10)
    
        # Button frame for better layout
        button_frame = tk.Frame(student_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)
    
        # Buttons
        take_attendance_btn = tk.Button(button_frame, text="Mark Attendance", font=("Arial", 14),
                                  width=20, height=2, command=self.take_attendance)
        take_attendance_btn.grid(row=0, column=0, padx=10, pady=10)
    
        back_btn = tk.Button(student_frame, text="Back to Main Menu", font=("Arial", 14),
                        width=20, height=2, command=self.back_to_main)
        back_btn.pack(pady=10)
    
        # Initialize camera
        self.cap = None

    def open_student_login(self):
        self.clear_frame()
    
        login_frame = tk.Frame(self.root, bg="#f0f0f0")
        login_frame.place(relwidth=1, relheight=1)
    
        title_label = tk.Label(login_frame, text="Student Login", 
                      font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=30)
    
    # Student ID
        id_label = tk.Label(login_frame, text="Student ID:", font=("Arial", 14), bg="#f0f0f0")
        id_label.pack(pady=10)
    
        id_entry = tk.Entry(login_frame, font=("Arial", 14), width=20)
        id_entry.pack(pady=10)
    
    # Login button
        login_btn = tk.Button(login_frame, text="Login", font=("Arial", 14),
                    width=10, command=lambda: self.verify_student(id_entry.get()))
        login_btn.pack(pady=20)
    
    # Back button
        back_btn = tk.Button(login_frame, text="Back", font=("Arial", 14),
                    width=10, command=self.back_to_main)
        back_btn.pack(pady=10)

    def verify_student(self, student_id):
        if not student_id:
            messagebox.showerror("Error", "Please enter your Student ID")
            return
    
        try:
            if not self.reconnect_database():
                return
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
            student = cursor.fetchone()
        
            if student:
                self.open_student_dashboard(student_id, student[0])
            else:
                messagebox.showerror("Login Failed", "Student ID not found")
        except Exception as e:
            messagebox.showerror("Error", f"Login error: {str(e)}")

    def open_student_dashboard(self, student_id, student_name):
        self.clear_frame()
    
        student_frame = tk.Frame(self.root, bg="#f0f0f0")
        student_frame.place(relwidth=1, relheight=1)
    
        title_label = tk.Label(student_frame, text=f"Welcome, {student_name}", 
                          font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
    
        id_label = tk.Label(student_frame, text=f"Student ID: {student_id}", 
                      font=("Arial", 14), bg="#f0f0f0")
        id_label.pack(pady=10)
    
    # Get attendance stats
        total_days, present_days, percentage = self.get_student_attendance_stats(student_id)
    
    # Stats frame
        stats_frame = tk.Frame(student_frame, bg="#f0f0f0", relief=tk.RIDGE, bd=2)
        stats_frame.pack(pady=20, padx=20, fill="x")
    
        tk.Label(stats_frame, text=f"Total Working Days: {total_days}", 
            font=("Arial", 12), bg="#f0f0f0", anchor="w").pack(pady=5, padx=10, fill="x")
    
        tk.Label(stats_frame, text=f"Days Present: {present_days}", 
            font=("Arial", 12), bg="#f0f0f0", anchor="w").pack(pady=5, padx=10, fill="x")
    
        tk.Label(stats_frame, text=f"Attendance Percentage: {percentage:.2f}%", 
            font=("Arial", 12, "bold"), bg="#f0f0f0", anchor="w").pack(pady=5, padx=10, fill="x")
    
    # View detailed attendance button
        view_btn = tk.Button(student_frame, text="View Detailed Attendance", font=("Arial", 14),
                       width=20, height=2, command=lambda: self.view_student_attendance(student_id, student_name))
        view_btn.pack(pady=15)
    
    # Logout button
        logout_btn = tk.Button(student_frame, text="Logout", font=("Arial", 14),
                         width=20, height=2, command=self.back_to_main)
        logout_btn.pack(pady=15)

    def get_student_attendance_stats(self, student_id):
        try:
            if not self.reconnect_database():
                return 0, 0, 0
            
            cursor = self.conn.cursor()
        
        # Get total working days (all unique dates in attendance table)
            cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
            total_days = cursor.fetchone()[0]
        
        # Get days present for this student
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id = ?", (student_id,))
            present_days = cursor.fetchone()[0]
        
        # Calculate percentage
            percentage = (present_days / total_days) * 100 if total_days > 0 else 0
        
            return total_days, present_days, percentage
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error getting attendance stats: {str(e)}")
            return 0, 0, 0

    def view_student_attendance(self, student_id, student_name):
        try:
            if not self.reconnect_database():
                return
            
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT a.date, a.time, a.status, s.course
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.student_id = ?
            ORDER BY a.date DESC, a.time DESC
            ''', (student_id,))
        
            attendance_data = cursor.fetchall()
            self.display_student_attendance(student_id, student_name, attendance_data)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error retrieving attendance data: {str(e)}")

    def display_student_attendance(self, student_id, student_name, data):
        self.clear_frame()
    
        data_frame = tk.Frame(self.root, bg="#f0f0f0")
        data_frame.place(relwidth=1, relheight=1)
    
        title_label = tk.Label(data_frame, text=f"Attendance Records for {student_name}", 
                          font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
    
        if not data:
            no_data_label = tk.Label(data_frame, text="No attendance records found", 
                               font=("Arial", 14), bg="#f0f0f0")
            no_data_label.pack(pady=20)
        else:
        # Create a frame for the table with scrollbar
            table_frame = tk.Frame(data_frame)
            table_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Add scrollbar
            scrollbar_y = tk.Scrollbar(table_frame)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas for scrolling
            canvas = tk.Canvas(table_frame, yscrollcommand=scrollbar_y.set)
            canvas.pack(side=tk.LEFT, fill="both", expand=True)
        
            scrollbar_y.config(command=canvas.yview)
        
        # Create a frame inside the canvas to hold the table
            inner_frame = tk.Frame(canvas)
            canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        # Create headers
            headers = ["Date", "Time", "Status", "Course"]
            for col, header in enumerate(headers):
                tk.Label(inner_frame, text=header, font=("Arial", 12, "bold"), 
                    width=12, relief="ridge", padx=5, pady=5).grid(row=0, column=col, sticky="nsew")
        
        # Add data rows
            for row, record in enumerate(data, start=1):
                for col, value in enumerate(record):
                    tk.Label(inner_frame, text=str(value), font=("Arial", 12),
                        width=12, relief="ridge", padx=5, pady=5).grid(row=row, column=col, sticky="nsew")
        
        # Update the canvas scroll region
            inner_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))
    
    # Back button
        back_btn = tk.Button(data_frame, text="Back", font=("Arial", 12),
                       width=10, command=lambda: self.open_student_dashboard(student_id, student_name))
        back_btn.pack(pady=10)

    def turn_off_camera(self):
        """Method to turn off the camera and clear the video frame"""
        self.release_camera()
        if hasattr(self, 'video_frame') and self.video_frame:
           self.video_frame.config(image='')
        if hasattr(self, 'status_label') and self.status_label:
           self.status_label.config(text="Camera turned off")
    
    def take_attendance(self):
        if self.cap is None:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    messagebox.showerror("Camera Error", "Could not open camera. Please check your camera connection.")
                    self.cap = None
                    return
                self.status_label.config(text="Camera active - Looking for faces")
                self.process_frame()
            except Exception as e:
                messagebox.showerror("Camera Error", f"Error initializing camera: {str(e)}")
                if self.cap:
                    self.cap.release()
                self.cap = None
        else:
            self.release_camera()
            self.status_label.config(text="Camera stopped")
    
    def release_camera(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self.capture_in_progress = False
        if hasattr(self, 'video_frame') and self.video_frame:
            self.video_frame.config(image='')
    
    def process_frame(self):
        if not self.cap or not self.cap.isOpened():
            self.status_label.config(text="Camera not available")
            return
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.status_label.config(text="Failed to capture frame. Check camera connection.")
                self.release_camera()
                return
                
            # Find faces in the frame
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            face_names = []
            for face_encoding in face_encodings:
                # Compare with known faces
                if len(self.known_face_encodings) > 0:  # Check if we have any known faces
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                    name = "Unknown"
                    
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_face_names[first_match_index]
                        
                        # Mark attendance in database
                        student_id = name.split("(")[1].split(")")[0]
                        student_name = name.split(" (")[0]
                        self.mark_attendance(student_id)
                        self.status_label.config(text=f"Attendance marked for {student_name}")
                else:
                    name = "No registered students"
                
                face_names.append(name)
            
            # Display results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
            
            # Convert to PhotoImage
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_frame.imgtk = imgtk
            self.video_frame.config(image=imgtk)
            
            # Process next frame if camera is still open
            if self.cap and self.cap.isOpened():
                self.video_frame.after(10, self.process_frame)
            else:
                self.status_label.config(text="Camera disconnected")
        
        except Exception as e:
            self.status_label.config(text=f"Error processing frame: {str(e)}")
            print("Error in process_frame:", traceback.format_exc())
            self.release_camera()
    
    def mark_attendance(self, student_id):
        try:
            if not self.reconnect_database():
                return
                
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            cursor = self.conn.cursor()
            
            # Using a transaction to avoid race conditions
            self.conn.execute("BEGIN TRANSACTION")
            
            # Check if attendance already marked today
            cursor.execute("SELECT * FROM attendance WHERE student_id = ? AND date = ?", 
                         (student_id, date_str))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
                             (student_id, date_str, time_str, "Present"))
                self.status_label.config(text=f"Marked attendance for student {student_id}")
            else:
                self.status_label.config(text=f"Attendance already marked for {student_id} today")
            
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Error marking attendance: {str(e)}")
    
    def open_faculty_login(self):
       self.clear_frame()
    
       login_frame = tk.Frame(self.root, bg="#f0f0f0")
       login_frame.place(relwidth=1, relheight=1)
    
       title_label = tk.Label(login_frame, text="Faculty Login", 
                          font=("Arial", 20, "bold"), bg="#f0f0f0")
       title_label.pack(pady=30)
    
       # Faculty ID
       id_label = tk.Label(login_frame, text="Faculty ID:", font=("Arial", 14), bg="#f0f0f0")
       id_label.pack(pady=10)
    
       id_entry = tk.Entry(login_frame, font=("Arial", 14), width=20)
       id_entry.pack(pady=10)
       id_entry.insert(0, "admin")  # Default value for testing
    
      # Password
       pw_label = tk.Label(login_frame, text="Password:", font=("Arial", 14), bg="#f0f0f0")
       pw_label.pack(pady=10)
    
       pw_entry = tk.Entry(login_frame, font=("Arial", 14), width=20, show="*")
       pw_entry.pack(pady=10)
       pw_entry.insert(0, "admin123")  # Default value for testing
    
       # Login button
       login_btn = tk.Button(login_frame, text="Login", font=("Arial", 14),
                        width=10, command=lambda: self.verify_faculty(id_entry.get(), pw_entry.get()))
       login_btn.pack(pady=20)
    
       # Back button
       back_btn = tk.Button(login_frame, text="Back", font=("Arial", 14),
                        width=10, command=self.back_to_main)
       back_btn.pack(pady=10)
    
    def verify_faculty(self, faculty_id, password):
        if not faculty_id or not password:
            messagebox.showerror("Error", "Please enter both ID and password")
            return
        
        try:
            if not self.reconnect_database():
                return
                
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM faculty WHERE faculty_id = ? AND password_hash = ?", 
                         (faculty_id, password_hash))
            
            if cursor.fetchone():
                self.open_faculty_dashboard(faculty_id)
            else:
                messagebox.showerror("Login Failed", "Invalid ID or password")
        except Exception as e:
            messagebox.showerror("Error", f"Login error: {str(e)}")
    
    def open_faculty_dashboard(self, faculty_id):
        self.clear_frame()
        
        faculty_frame = tk.Frame(self.root, bg="#f0f0f0")
        faculty_frame.place(relwidth=1, relheight=1)
        
        title_label = tk.Label(faculty_frame, text=f"Faculty Dashboard - {faculty_id}", 
                              font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # View all attendance button
        view_all_btn = tk.Button(faculty_frame, text="View All Attendance", font=("Arial", 14),
                               width=20, height=2, command=self.view_all_attendance)
        view_all_btn.pack(pady=15)
        
        # View by date button
        by_date_btn = tk.Button(faculty_frame, text="View Attendance by Date", font=("Arial", 14),
                              width=20, height=2, command=self.view_by_date)
        by_date_btn.pack(pady=15)
        
        # View by student button
        by_student_btn = tk.Button(faculty_frame, text="View Attendance by Student", font=("Arial", 14),
                                 width=20, height=2, command=self.view_by_student)
        by_student_btn.pack(pady=15)
        
        # Export to CSV button
        export_btn = tk.Button(faculty_frame, text="Export to CSV", font=("Arial", 14),
                             width=20, height=2, command=self.export_to_csv)
        export_btn.pack(pady=15)
        
        # Back button
        back_btn = tk.Button(faculty_frame, text="Logout", font=("Arial", 14),
                           width=20, height=2, command=self.back_to_main)
        back_btn.pack(pady=15)
    
    def view_all_attendance(self):
        try:
            if not self.reconnect_database():
                return
                
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT a.id, s.student_id, s.name, a.date, a.time, a.status 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            ORDER BY a.date DESC, a.time DESC
            ''')
            
            attendance_data = cursor.fetchall()
            self.display_attendance_data("All Attendance Records", attendance_data)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error retrieving attendance data: {str(e)}")
    
    def view_by_date(self):
        date_str = simpledialog.askstring("Date Input", "Enter date (YYYY-MM-DD):",
                                        parent=self.root)
        if not date_str:
            return
        
        # Validate date format
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
            return
        
        try:
            if not self.reconnect_database():
                return
                
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT a.id, s.student_id, s.name, a.date, a.time, a.status 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.date = ?
            ORDER BY a.time
            ''', (date_str,))
            
            attendance_data = cursor.fetchall()
            self.display_attendance_data(f"Attendance Records for {date_str}", attendance_data)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error retrieving attendance data: {str(e)}")
    
    def view_by_student(self):
        student_id = simpledialog.askstring("Student ID", "Enter student ID:",
                                          parent=self.root)
        if not student_id:
            return
        
        try:
            if not self.reconnect_database():
                return
                
            cursor = self.conn.cursor()
            
            # First verify if student exists
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
            student = cursor.fetchone()
            
            if not student:
                messagebox.showerror("Error", f"Student ID {student_id} not found")
                return
                
            cursor.execute('''
            SELECT a.id, s.student_id, s.name, a.date, a.time, a.status 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.student_id = ?
            ORDER BY a.date DESC, a.time DESC
            ''', (student_id,))
            
            attendance_data = cursor.fetchall()
            self.display_attendance_data(f"Attendance Records for Student {student_id}", attendance_data)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error retrieving attendance data: {str(e)}")
    
    def display_attendance_data(self, title, data):
        self.clear_frame()
        
        data_frame = tk.Frame(self.root, bg="#f0f0f0")
        data_frame.place(relwidth=1, relheight=1)
        
        title_label = tk.Label(data_frame, text=title, 
                              font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        if not data:
            no_data_label = tk.Label(data_frame, text="No records found", 
                                   font=("Arial", 14), bg="#f0f0f0")
            no_data_label.pack(pady=20)
        else:
            # Create a frame for the table with scrollbar
            table_frame = tk.Frame(data_frame)
            table_frame.pack(pady=10, padx=10, fill="both", expand=True)
            
            # Add scrollbar
            scrollbar_y = tk.Scrollbar(table_frame)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create canvas for scrolling
            canvas = tk.Canvas(table_frame, yscrollcommand=scrollbar_y.set)
            canvas.pack(side=tk.LEFT, fill="both", expand=True)
            
            scrollbar_y.config(command=canvas.yview)
            
            # Create a frame inside the canvas to hold the table
            inner_frame = tk.Frame(canvas)
            canvas.create_window((0, 0), window=inner_frame, anchor="nw")
            
            # Create headers
            headers = ["ID", "Student ID", "Name", "Date", "Time", "Status"]
            for col, header in enumerate(headers):
                tk.Label(inner_frame, text=header, font=("Arial", 12, "bold"), 
                        width=12, relief="ridge", padx=5, pady=5).grid(row=0, column=col, sticky="nsew")
            
            # Add data rows
            for row, record in enumerate(data, start=1):
                for col, value in enumerate(record):
                    tk.Label(inner_frame, text=str(value), font=("Arial", 12),
                            width=12, relief="ridge", padx=5, pady=5).grid(row=row, column=col, sticky="nsew")
            
            # Update the canvas scroll region
            inner_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))
        
        # Back button
        back_btn = tk.Button(data_frame, text="Back", font=("Arial", 12),
                           width=10, command=lambda: self.open_faculty_dashboard("admin"))
        back_btn.pack(pady=10)
    
    def export_to_csv(self):
        try:
            if not self.reconnect_database():
                return
                
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT s.student_id, s.name, s.course, a.date, a.time, a.status 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            ORDER BY a.date DESC, a.time DESC
            ''')
            
            data = cursor.fetchall()
            if not data:
                messagebox.showinfo("Export", "No attendance data to export")
                return
            
            df = pd.DataFrame(data, columns=["Student ID", "Name", "Course", "Date", "Time", "Status"])
            
            try:
                file_path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                        filetypes=[("CSV files", "*.csv")],
                                                        title="Save Attendance Report")
                if file_path:
                    df.to_csv(file_path, index=False)
                    messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Error exporting data: {str(e)}")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error retrieving data for export: {str(e)}")
    
    def open_registration(self):
        self.clear_frame()
        
        register_frame = tk.Frame(self.root, bg="#f0f0f0")
        register_frame.place(relwidth=1, relheight=1)
        
        title_label = tk.Label(register_frame, text="Register New Student", 
                              font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Student ID
        id_label = tk.Label(register_frame, text="Student ID:", font=("Arial", 12), bg="#f0f0f0")
        id_label.pack(pady=5)
        
        id_entry = tk.Entry(register_frame, font=("Arial", 12), width=20)
        id_entry.pack(pady=5)
        
        # Student Name
        name_label = tk.Label(register_frame, text="Full Name:", font=("Arial", 12), bg="#f0f0f0")
        name_label.pack(pady=5)
        
        name_entry = tk.Entry(register_frame, font=("Arial", 12), width=20)
        name_entry.pack(pady=5)
        
        # Course
        course_label = tk.Label(register_frame, text="Course:", font=("Arial", 12), bg="#f0f0f0")
        course_label.pack(pady=5)
        
        course_entry = tk.Entry(register_frame, font=("Arial", 12), width=20)
        course_entry.pack(pady=5)
        
        # Video frame for capturing
        self.video_frame = tk.Label(register_frame)
        self.video_frame.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(register_frame, text="Choose capture method below", 
                                    font=("Arial", 12), bg="#f0f0f0")
        self.status_label.pack(pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(register_frame, bg="#f0f0f0")
        buttons_frame.pack(pady=10)
        
        # First row of buttons
        camera_btn = tk.Button(buttons_frame, text="Start Camera", font=("Arial", 12),
                           width=15, command=lambda: self.start_camera_registration())
        camera_btn.grid(row=0, column=0, padx=10, pady=5)
        
        capture_btn = tk.Button(buttons_frame, text="Capture Face", font=("Arial", 12),
                              width=15, command=lambda: self.capture_face(id_entry.get(), name_entry.get(), course_entry.get()))
        capture_btn.grid(row=0, column=1, padx=10, pady=5)
        
        # Second row of buttons
        upload_btn = tk.Button(buttons_frame, text="Upload Image", font=("Arial", 12),
                             width=15, command=lambda: self.upload_image(id_entry.get(), name_entry.get(), course_entry.get()))
        upload_btn.grid(row=1, column=0, padx=10, pady=5)
        
        back_btn = tk.Button(buttons_frame, text="Back", font=("Arial", 12),
                           width=15, command=self.back_to_main)
        back_btn.grid(row=1, column=1, padx=10, pady=5)
        
        # Initialize variables
        self.cap = None
        self.captured_encoding = None
        self.capture_in_progress = False
    
    def start_camera_registration(self):
        """Start the camera for registration"""
        if self.cap is None:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    messagebox.showerror("Camera Error", "Could not open camera. Please check your camera connection.")
                    self.cap = None
                    return
                    
                self.capture_in_progress = True
                self.status_label.config(text="Camera started. Position face in frame and click 'Capture Face'")
                self.capture_frames_registration()
            except Exception as e:
                messagebox.showerror("Camera Error", f"Error initializing camera: {str(e)}")
                if self.cap:
                    self.cap.release()
                self.cap = None
        else:
            # If camera is already running, stop it
            self.release_camera()
            self.status_label.config(text="Camera stopped")
    
    def upload_image(self, student_id, name, course):
       """Upload an image file for face registration"""
       if not student_id or not name or not course:
        messagebox.showerror("Error", "Please fill all fields")
        return
        
       try:
        # Check if student_id already exists
        if not self.reconnect_database():
            return
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        if cursor.fetchone():
            messagebox.showerror("Error", f"Student ID {student_id} already exists")
            return
        
        # Open file dialog to select image
        file_path = filedialog.askopenfilename(
            title="Select Student Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if not file_path:
            return  # User canceled
            
        # Load and process the image
        image = face_recognition.load_image_file(file_path)
        face_locations = face_recognition.face_locations(image)
        
        if not face_locations:
            messagebox.showerror("Error", "No face detected in the uploaded image")
            return
            
        # Take the first face found
        face_encoding = face_recognition.face_encodings(image, [face_locations[0]])[0]
        
        # Store in database
        face_encoding_bytes = face_encoding.tobytes()
        cursor.execute(
            "INSERT INTO students (student_id, name, course, face_encoding) VALUES (?, ?, ?, ?)",
            (student_id, name, course, face_encoding_bytes)
        )
        self.conn.commit()
        
        # Show success message
        messagebox.showinfo("Success", f"Student {name} registered successfully")
        
        # Reload known faces
        self.load_known_faces()
        
        # Clear the form
        self.clear_registration_form()
        
       except Exception as e:
        messagebox.showerror("Error", f"Failed to process image: {str(e)}")
        print("Error in upload_image:", traceback.format_exc())

    def capture_frames_registration(self):
      """Continuously capture frames for the registration process"""
      if not self.cap or not self.cap.isOpened() or not self.capture_in_progress:
        return
        
      try:
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.config(text="Failed to capture frame. Check camera connection.")
            self.release_camera()
            return
            
        # Detect faces in the frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Draw rectangles around detected faces
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Convert to PhotoImage
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_frame.imgtk = imgtk
        self.video_frame.config(image=imgtk)
        
        # Process next frame if still capturing
        if self.capture_in_progress:
            self.video_frame.after(10, self.capture_frames_registration)
    
      except Exception as e:
        self.status_label.config(text=f"Error processing frame: {str(e)}")
        print("Error in capture_frames_registration:", traceback.format_exc())
        self.release_camera()

    def capture_face(self, student_id, name, course):
       """Capture and save the student's face encoding"""
       if not student_id or not name or not course:
        messagebox.showerror("Error", "Please fill all fields")
        return
        
       if not self.cap or not self.cap.isOpened():
        messagebox.showerror("Error", "Camera is not started. Please start the camera first.")
        return
        
       try:
        # Check if student_id already exists
        if not self.reconnect_database():
            return
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        if cursor.fetchone():
            messagebox.showerror("Error", f"Student ID {student_id} already exists")
            return
            
        # Capture a frame
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture frame")
            return
            
        # Find face in the frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            messagebox.showerror("Error", "No face detected. Please position face properly.")
            return
            
        # Get encoding of the first face found
        face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
        
        # Save the student record with face encoding
        face_encoding_bytes = face_encoding.tobytes()
        cursor.execute(
            "INSERT INTO students (student_id, name, course, face_encoding) VALUES (?, ?, ?, ?)",
            (student_id, name, course, face_encoding_bytes)
        )
        self.conn.commit()
        
        # Display success message
        self.status_label.config(text=f"Student {name} registered successfully")
        messagebox.showinfo("Success", f"Student {name} registered successfully")
        
        # Release camera
        self.release_camera()
        
        # Reload known faces
        self.load_known_faces()
        
        # Clear the form
        self.clear_registration_form()
        
       except Exception as e:
        messagebox.showerror("Error", f"Error during face capture: {str(e)}")
        print("Error in capture_face:", traceback.format_exc())

    def clear_registration_form(self):
        """Clear the registration form fields"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                   if isinstance(child, tk.Entry):
                        child.delete(0, tk.END)

    def reconnect_database(self):
        """Ensure database connection is active, reconnect if needed"""
        try:
            # Test if connection is alive
            self.conn.execute("SELECT 1")
            return True
        except (sqlite3.Error, AttributeError):
            # Try to reconnect
            try:
                self.conn = sqlite3.connect("attendance.db")
                return True
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
                return False

    def clear_frame(self):
        """Clear all widgets from the root window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
        if self.cap:
           self.release_camera()

    def back_to_main(self):
        """Return to the main menu"""
        if self.cap:
           self.release_camera()
    
    # Recreate the main interface
        self.clear_frame()
        self.__init__(self.root)

    def exit_application(self):
        """Clean up resources and exit the application"""
        if self.cap:
           self.release_camera()
    
        if hasattr(self, 'conn') and self.conn:
           self.conn.close()
    
        self.root.destroy()
        sys.exit()

    # Add error handling functionality
    def setup_exception_logging(self):
        """Set up logging for unhandled exceptions"""
        # Redirect stderr to capture unhandled exceptions
        sys.stderr = io.StringIO()
    
        # Set up a custom exception hook
        def custom_excepthook(exc_type, exc_value, exc_traceback):
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            messagebox.showerror("Unhandled Error", f"An unexpected error occurred:\n\n{error_msg}")
            print(error_msg)
    
        sys.excepthook = custom_excepthook

# Main function to run the application
if __name__ == "__main__":
    try:
        # Check for required libraries
        required_modules = ["cv2", "face_recognition", "numpy", "pandas", "PIL"]
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"Missing required modules: {', '.join(missing_modules)}")
            messagebox.showerror("Missing Dependencies", 
                                f"The following modules are required but not installed:\n{', '.join(missing_modules)}\n\n"
                                "Please install them using pip before running this application.")
            sys.exit(1)
        
        # Start the application
        root = tk.Tk()
        app = AttendanceSystem(root)
        root.mainloop()
        
    except Exception as e:
        # Handle any startup errors
        error_msg = traceback.format_exc()
        print(f"Error starting application: {error_msg}")
        
        # Show error in GUI if possible
        try:
            messagebox.showerror("Startup Error", 
                               f"Failed to start application:\n\n{str(e)}\n\nSee console for details.")
        except:
            # If GUI fails, just print to console
            print("Could not display error dialog. Application failed to start.")
        
        sys.exit(1)