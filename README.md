# 🎓 Facial Recognition Attendance System

A Python-based desktop application that automates attendance management using facial recognition technology. The system identifies registered students through a webcam and marks attendance automatically, reducing manual effort and minimizing proxy attendance.

---

## 📌 Features

- 👤 Student Registration with Face Capture
- 📸 Face Recognition using Webcam
- ✅ Automatic Attendance Marking
- 🔐 Faculty Login System
- 🎓 Student Login & Attendance Dashboard
- 📊 View Attendance Records
- 📅 Search Attendance by Student or Date
- 📁 Export Attendance Reports to CSV
- 💾 SQLite Database for Data Storage
- ⚠️ Error Handling and Database Reconnection

---

## 🛠️ Tech Stack

- **Language:** Python
- **GUI:** Tkinter
- **Computer Vision:** OpenCV
- **Face Recognition:** face_recognition (dlib)
- **Database:** SQLite
- **Data Processing:** Pandas, NumPy
- **Image Handling:** Pillow (PIL)

---

## 🚀 How It Works

1. Register a student by entering:
   - Student ID
   - Student Name
   - Course
   - Capture or Upload Student Photo

2. The system extracts the student's facial encoding and stores it securely in the SQLite database.

3. During attendance:
   - Webcam captures the student's face.
   - Facial encoding is generated.
   - The encoding is compared with registered students.
   - If matched, attendance is marked automatically.

4. Faculty members can:
   - View attendance records
   - Search by student or date
   - Export attendance reports as CSV files

---

## 📂 Project Structure

```
Facial-Recognition-Attendance-System/
│
├── main.py
├── attendance.db
├── README.md
└── requirements.txt
```

---

## 💻 Installation

### Clone the repository

```bash
git clone https://github.com/your-username/facial-recognition-attendance-system.git
```

### Navigate to the project

```bash
cd facial-recognition-attendance-system
```

### Install dependencies

```bash
pip install opencv-python numpy pandas pillow face_recognition
```

### Run the application

```bash
python "main.py"
```

---

## 🔑 Default Faculty Login

| Field | Value |
|-------|-------|
| Faculty ID | admin |
| Password | admin123 |

---

## 📷 Screenshots

Add screenshots here after running the application.

- Main Menu
- Student Registration
- Attendance Detection
- Faculty Dashboard
- Attendance Report

---

## 📊 Database

The project uses **SQLite** with three tables:

- Faculty
- Students
- Attendance

Attendance records include:

- Student ID
- Date
- Time
- Status

---

## 🎯 Future Enhancements

- Web-based version using React + Flask
- Cloud Database Integration
- Email Attendance Reports
- Face Mask Detection
- Multi-Face Attendance Support
- Attendance Analytics Dashboard
- QR Code Backup Attendance
- Secure Authentication

---

## 📖 Learning Outcomes

This project demonstrates:

- Computer Vision
- Face Recognition
- Desktop GUI Development
- Database Management
- Python Programming
- CRUD Operations
- Error Handling
- CSV Report Generation

---

## ⚠️ Limitations

- Performance depends on camera quality.
- Recognition accuracy may decrease in poor lighting.
- Desktop application only.
- SQLite is suitable for small-scale deployments.

---

## 👩‍💻 Author

**Saloni Prabha**

- GitHub: https://github.com/Saloniprabha

---

## ⭐ If you found this project useful, don't forget to star the repository!
