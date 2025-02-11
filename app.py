import cv2
import numpy as np
import face_recognition
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import csv
from pathlib import Path
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

class EnhancedAttendanceSystem:
    def __init__(self):
        self.initialize_system()
        self.load_known_faces()
        
    def initialize_system(self):
        """Initialize necessary directories and files"""
        # Create required directories
        for directory in ["dataset", "attendance_records"]:
            Path(directory).mkdir(exist_ok=True)
        
        # Initialize students.csv if it doesn't exist
        if not Path("students.csv").exists():
            with open("students.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID", "Name", "Email", "Phone", "RFID"])
                
        # Initialize settings.csv if it doesn't exist
        if not Path("settings.csv").exists():
            with open("settings.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Setting", "Value"])
                writer.writerow(["late_threshold", "09:00"])
                writer.writerow(["enable_email", "True"])
                writer.writerow(["enable_whatsapp", "True"])

    def load_known_faces(self):
        """Load known faces and their encodings from the dataset"""
        self.known_face_encodings = []
        self.known_face_ids = []
        
        for image_path in Path("dataset").glob("*.jpg"):
            try:
                image = face_recognition.load_image_file(str(image_path))
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_ids.append(image_path.stem)
            except Exception as e:
                print(f"Error loading {image_path}: {e}")

    def recognize_face(self, frame):
        """Recognize faces in the frame"""
        # Convert frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find all faces in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_students = []
        
        for face_encoding in face_encodings:
            if len(self.known_face_encodings) > 0:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                if True in matches:
                    first_match_index = matches.index(True)
                    student_id = self.known_face_ids[first_match_index]
                    recognized_students.append(student_id)
        
        return recognized_students, face_locations

    def mark_attendance(self, student_id):
        """Mark attendance for a student"""
        today = datetime.now().date()
        attendance_file = f"attendance_records/attendance_{today}.csv"
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Create attendance file for today if it doesn't exist
        if not Path(attendance_file).exists():
            with open(attendance_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID", "Time"])
        
        # Check if student already marked attendance today
        df = pd.read_csv(attendance_file)
        if student_id not in df['Student ID'].values:
            with open(attendance_file, "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([student_id, current_time])
            return True
        return False

    def get_attendance_records(self, start_date, end_date):
        """Get attendance records between two dates"""
        records = []
        current_date = start_date
        
        while current_date <= end_date:
            attendance_file = f"attendance_records/attendance_{current_date}.csv"
            if Path(attendance_file).exists():
                df = pd.read_csv(attendance_file)
                df['Date'] = current_date
                records.append(df)
            current_date += timedelta(days=1)
            
        if records:
            combined_records = pd.concat(records, ignore_index=True)
            students_df = pd.read_csv("students.csv")
            return combined_records.merge(students_df, on="Student ID", how="left")
        return pd.DataFrame()

    def register_student(self, student_id, name, image_data, email, phone, rfid=None):
        """Register a new student"""
        try:
            # Save student info
            with open("students.csv", "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([student_id, name, email, phone, rfid])
            
            # Save student image
            img_path = f"dataset/{student_id}.jpg"
            image_data.save(img_path)
            
            # Reload known faces
            self.load_known_faces()
            return True
        except Exception as e:
            print(f"Error registering student: {e}")
            return False

    def get_dashboard_metrics(self):
        """Get metrics for dashboard"""
        total_students = len(pd.read_csv("students.csv"))
        
        today = datetime.now().date()
        attendance_file = f"attendance_records/attendance_{today}.csv"
        
        if Path(attendance_file).exists():
            present_students = len(pd.read_csv(attendance_file))
        else:
            present_students = 0
            
        absent_students = total_students - present_students
        attendance_rate = (present_students / total_students * 100) if total_students > 0 else 0
        
        return {
            "total_students": total_students,
            "present_today": present_students,
            "absent_today": absent_students,
            "attendance_rate": attendance_rate
        }

    def get_weekly_trend(self):
        """Get weekly attendance trend data"""
        dates = [(datetime.now() - timedelta(days=x)).date() for x in range(6, -1, -1)]
        attendance_counts = []
        
        for date in dates:
            attendance_file = f"attendance_records/attendance_{date}.csv"
            if Path(attendance_file).exists():
                count = len(pd.read_csv(attendance_file))
            else:
                count = 0
            attendance_counts.append(count)
            
        return dates, attendance_counts

def create_ui():
    """Create the main UI"""
    st.set_page_config(page_title="Smart Attendance System", layout="wide", page_icon="📊")
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 0rem 1rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #4CAF50;
            color: white;
        }
        .css-1d391kg {
            padding: 1rem;
        }
        .metric-card {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize system
    if 'attendance_system' not in st.session_state:
        st.session_state.attendance_system = EnhancedAttendanceSystem()
        st.session_state.camera_active = False
        st.session_state.marked_today = set()
    
    # Sidebar navigation
    with st.sidebar:
        if Path("images/logo.jpeg").exists():
            st.image("images/logo.jpeg", width=100)
        else:
            st.warning("Logo image not found.")
        nav_selection = st.selectbox(
            "Navigation",
            ["Dashboard", "Mark Attendance", "Register Student", "View Records", "Settings"]
        )
    
    # Page routing
    if nav_selection == "Dashboard":
        show_dashboard()
    elif nav_selection == "Mark Attendance":
        show_attendance_page()
    elif nav_selection == "Register Student":
        show_registration_page()
    elif nav_selection == "View Records":
        show_records_page()
    elif nav_selection == "Settings":
        show_settings_page()
    
    # Footer

    st.markdown("<div style='text-align: center; margin-top: 2rem;'>© 2025 Smart Attendance System <br>Developed by Joothiswaran Palanisamy</div>", unsafe_allow_html=True)

def show_dashboard():
    """Display dashboard page"""
    st.title("📊 Attendance Dashboard")
    
    # Get metrics
    metrics = st.session_state.attendance_system.get_dashboard_metrics()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", metrics["total_students"])
    with col2:
        st.metric("Present Today", metrics["present_today"])
    with col3:
        st.metric("Absent Today", metrics["absent_today"])
    with col4:
        st.metric("Attendance Rate", f"{metrics['attendance_rate']:.1f}%")
    
    # Weekly trend
    dates, counts = st.session_state.attendance_system.get_weekly_trend()
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=[d.strftime("%Y-%m-%d") for d in dates],
            y=counts,
            mode='lines+markers',
            name='Attendance'
        ))
        fig_trend.update_layout(
            title="Weekly Attendance Trend",
            xaxis_title="Date",
            yaxis_title="Students Present",
            template="plotly_dark"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Present', 'Absent'],
            values=[metrics["present_today"], metrics["absent_today"]],
            hole=.3
        )])
        fig_pie.update_layout(
            title="Today's Attendance Distribution",
            template="plotly_dark"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

def show_attendance_page():
    """Display attendance marking page"""
    st.title("📸 Mark Attendance")
    
    method = st.radio("Select Attendance Method", ["Face Recognition", "RFID Card"])
    
    if method == "Face Recognition":
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("Start Camera" if not st.session_state.camera_active else "Stop Camera"):
                st.session_state.camera_active = not st.session_state.camera_active
            
            if st.session_state.camera_active:
                stframe = st.empty()
                cap = cv2.VideoCapture(0)
                
                while st.session_state.camera_active:
                    ret, frame = cap.read()
                    if not ret:
                        st.error("Failed to access camera")
                        break
                    
                    # Recognize faces
                    recognized_students, face_locations = st.session_state.attendance_system.recognize_face(frame)
                    
                    # Draw rectangles around faces
                    for (top, right, bottom, left), student_id in zip(face_locations, recognized_students):
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, student_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                    # Mark attendance for recognized students
                    for student_id in recognized_students:
                        if student_id not in st.session_state.marked_today:
                            if st.session_state.attendance_system.mark_attendance(student_id):
                                st.session_state.marked_today.add(student_id)
                                st.success(f"Attendance marked for Student {student_id}")
                    
                    stframe.image(frame, channels="BGR")
                
                cap.release()
        
        with col2:
            st.subheader("Recently Marked")
            for student_id in list(st.session_state.marked_today)[-5:]:
                st.write(f"✅ {student_id}")
    
    elif method == "RFID Card":
        st.info("Please scan RFID card to mark attendance")
        if st.button("Mark Attendance"):
            # Placeholder for RFID card scanning
            pass

def show_registration_page():
    """Display student registration page"""
    st.title("👤 Register New Student")
    
    col1, col2 = st.columns(2)
    
    with col1:
        student_id = st.text_input("Student ID")
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        rfid = st.text_input("RFID Card Number (Optional)")
    
    with col2:
        st.write("Take Photo")
        photo = st.camera_input("Capture")
    
    if st.button("Register Student"):
        if student_id and name and photo:
            if st.session_state.attendance_system.register_student(
                student_id, name, Image.open(photo), email, phone, rfid
            ):
                st.success("Student registered successfully!")
                st.balloons()
        else:
            st.error("Please fill all required fields (Student ID, Name, and Photo)")

def show_records_page():
    """Display attendance records page"""
    st.title("📋 Attendance Records")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", datetime.now().date())
    with col2:
        end_date = st.date_input("End Date", datetime.now().date())
    
    if start_date and end_date:
        if start_date <= end_date:
            records = st.session_state.attendance_system.get_attendance_records(start_date, end_date)
            
            if not records.empty:
                st.download_button(
                    "Download Records",
                    records.to_csv(index=False),
                    "attendance_records.csv",
                    "text/csv"
                )
                st.dataframe(records, use_container_width=True)
            else:
                st.info("No records found for selected date range")
        else:
            st.error("End date must be after start date")

def show_settings_page():
    """Display settings page"""
    st.title("⚙️ Settings")
    
    
    settings_df = pd.DataFrame(columns=["Setting", "Value"])

    # Check if settings.csv file exists
    try:
        settings_df = pd.read_csv("settings.csv", index_col="Setting")
    except FileNotFoundError:
        pass

    st.subheader("Attendance Settings")
    late_threshold = st.time_input(
        "Late Attendance Threshold",
        datetime.strptime(settings_df.loc["late_threshold", "Value"], "%H:%M").time() if "late_threshold" in settings_df.index else datetime.strptime("09:00", "%H:%M").time()
    )

    st.subheader("Alert Settings")
    enable_email = st.checkbox(
        "Enable Email Alerts",
        bool(settings_df.loc["enable_email", "Value"] == "True") if "enable_email" in settings_df.index else False
    )
    enable_whatsapp = st.checkbox(
        "Enable WhatsApp Alerts",
        bool(settings_df.loc["enable_whatsapp", "Value"] == "True") if "enable_whatsapp" in settings_df.index else False
    )

    if enable_email:
        email_address = st.text_input("Email Address", value=settings_df.loc["email_address", "Value"] if "email_address" in settings_df.index else "")
    else:
        email_address = ""

    if enable_whatsapp:
        whatsapp_number = st.text_input("WhatsApp Number", value=settings_df.loc["whatsapp_number", "Value"] if "whatsapp_number" in settings_df.index else "")
    else:
        whatsapp_number = ""

    if st.button("Save Settings"):
        settings_df.loc["late_threshold", "Value"] = late_threshold.strftime("%H:%M")
        settings_df.loc["enable_email", "Value"] = str(enable_email)
        settings_df.loc["enable_whatsapp", "Value"] = str(enable_whatsapp)
        settings_df.loc["email_address", "Value"] = email_address
        settings_df.loc["whatsapp_number", "Value"] = whatsapp_number

        settings_df.to_csv("settings.csv")

        st.success("Settings saved successfully!")


if __name__ == "__main__":
    create_ui()
    st.stop()
