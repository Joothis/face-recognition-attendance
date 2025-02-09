import cv2
import numpy as np
import os
import face_recognition
import pandas as pd
import streamlit as st
from datetime import datetime
import csv
from pathlib import Path
from PIL import Image
import io

class AttendanceSystem:
    def __init__(self):
        self.initialize_system()
        self.load_known_faces()
        
    def initialize_system(self):
        """Initialize necessary directories and files"""
        Path("dataset").mkdir(exist_ok=True)
        Path("encodings").mkdir(exist_ok=True)
        Path("attendance_records").mkdir(exist_ok=True)
        
        if not Path("students.csv").exists():
            with open("students.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID", "Name"])
                
        if not Path("encodings/face_encodings.csv").exists():
            with open("encodings/face_encodings.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID", "Encoding"])

    def load_known_faces(self):
        """Load all known face encodings"""
        self.known_faces_encoding = []
        self.known_faces_names = []
        
        if Path("encodings/face_encodings.csv").exists():
            df = pd.read_csv("encodings/face_encodings.csv")
            for _, row in df.iterrows():
                encoding = np.fromstring(row['Encoding'][1:-1], sep=' ')
                self.known_faces_encoding.append(encoding)
                self.known_faces_names.append(row['Student ID'])

    def register_student(self, student_id, name, image):
        """Register a new student with face encoding"""
        try:
            # Convert the image to RGB format
            rgb_image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
            
            # Detect faces in the image
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                st.error("No face detected in the image. Please try again.")
                return False
            
            # Generate face encoding
            encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
            
            # Save the image
            image.save(f"dataset/{student_id}.jpg")
            
            # Save student info
            with open("students.csv", "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([student_id, name])
            
            # Save face encoding
            with open("encodings/face_encodings.csv", "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([student_id, ' '.join(map(str, encoding))])
            
            # Reload known faces
            self.load_known_faces()
            return True
            
        except Exception as e:
            st.error(f"Error registering student: {str(e)}")
            return False

    def process_frame(self, frame):
        """Process a single frame for face recognition"""
        # Convert frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces in frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_students = []
        
        # Process each detected face
        for encoding, location in zip(face_encodings, face_locations):
            # Compare with known faces
            if self.known_faces_encoding:
                distances = face_recognition.face_distance(self.known_faces_encoding, encoding)
                min_distance_idx = np.argmin(distances)
                
                if distances[min_distance_idx] < 0.6:  # Threshold for face matching
                    student_id = self.known_faces_names[min_distance_idx]
                    recognized_students.append(student_id)
                    
                    # Draw rectangle and name
                    top, right, bottom, left = location
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, f"ID: {student_id}", 
                              (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                              0.5, (0, 255, 0), 2)
                else:
                    # Unknown face
                    top, right, bottom, left = location
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown", 
                              (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                              0.5, (0, 0, 255), 2)
        
        return frame, recognized_students

    def mark_attendance(self, recognized_students):
        """Mark attendance for recognized students"""
        date = datetime.now().strftime("%Y-%m-%d")
        attendance_file = f"attendance_records/attendance_{date}.csv"
        
        if not Path(attendance_file).exists():
            with open(attendance_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID", "Time"])
        
        current_time = datetime.now().strftime("%H:%M:%S")
        marked_students = set()
        
        # Read existing attendance
        if Path(attendance_file).exists():
            df = pd.read_csv(attendance_file)
            marked_students.update(df["Student ID"].tolist())
        
        # Mark new attendances
        newly_marked = []
        with open(attendance_file, "a", newline='') as f:
            writer = csv.writer(f)
            for student_id in recognized_students:
                if student_id not in marked_students:
                    writer.writerow([student_id, current_time])
                    marked_students.add(student_id)
                    newly_marked.append(student_id)
        
        return newly_marked

    def view_attendance(self, date=None):
        """View attendance for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        attendance_file = f"attendance_records/attendance_{date}.csv"
        
        if not Path(attendance_file).exists():
            return pd.DataFrame()
        
        attendance_df = pd.read_csv(attendance_file)
        students_df = pd.read_csv("students.csv")
        
        merged_df = pd.merge(attendance_df, students_df, on="Student ID")
        return merged_df

def main():
    st.title("Face Recognition Attendance System")
    
    # Initialize attendance system
    if 'attendance_system' not in st.session_state:
        st.session_state.attendance_system = AttendanceSystem()
        st.session_state.attendance_active = False
        st.session_state.marked_today = set()
    
    # Sidebar menu
    menu = st.sidebar.selectbox(
        "Select Option",
        ["Register Student", "Mark Attendance", "View Attendance"]
    )
    
    if menu == "Register Student":
        st.header("Register New Student")
        student_id = st.text_input("Student ID")
        name = st.text_input("Name")
        
        # Camera input
        image = st.camera_input("Take a photo")
        
        if image is not None and student_id and name:
            if st.button("Register Student"):
                # Convert the image to PIL format
                img = Image.open(image)
                if st.session_state.attendance_system.register_student(student_id, name, img):
                    st.success("Student registered successfully!")
    
    elif menu == "Mark Attendance":
        st.header("Mark Attendance")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Start/Stop Attendance"):
                st.session_state.attendance_active = not st.session_state.attendance_active
        
        with col2:
            if st.button("Clear Today's Records"):
                st.session_state.marked_today = set()
        
        if st.session_state.attendance_active:
            # Create a placeholder for the camera feed
            camera_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # Initialize camera
            cap = cv2.VideoCapture(0)
            
            try:
                while st.session_state.attendance_active:
                    ret, frame = cap.read()
                    if not ret:
                        st.error("Failed to access camera")
                        break
                    
                    # Process frame and get recognized students
                    processed_frame, recognized_students = st.session_state.attendance_system.process_frame(frame)
                    
                    # Mark attendance for recognized students
                    newly_marked = st.session_state.attendance_system.mark_attendance(recognized_students)
                    st.session_state.marked_today.update(newly_marked)
                    
                    # Display the frame
                    camera_placeholder.image(processed_frame, channels="BGR", use_column_width=True)
                    status_placeholder.write(f"Students marked today: {len(st.session_state.marked_today)}")
                    
            finally:
                cap.release()
    
    elif menu == "View Attendance":
        st.header("View Attendance")
        date = st.date_input("Select Date")
        attendance_df = st.session_state.attendance_system.view_attendance(date.strftime("%Y-%m-%d"))
        
        if not attendance_df.empty:
            st.dataframe(attendance_df)
        else:
            st.info("No attendance records found for selected date")

if __name__ == "__main__":
    main()