# Face Recognition Attendance System

A Streamlit-based attendance system that uses facial recognition to automate student attendance tracking. The system provides an intuitive web interface for registering students, marking attendance, and viewing attendance records.

## Features

- **Student Registration**: Register students with their photo taken directly through the web interface
- **Face Recognition**: Real-time face detection and recognition
- **Attendance Tracking**: Automatic attendance marking with timestamp
- **Attendance Records**: View and manage attendance records by date
- **Embedded Camera Interface**: Camera controls integrated directly into the Streamlit UI

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/joothis/face-recognition-attendance.git
    cd face-recognition-attendance
    ```

2. Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use: venv\Scripts\activate
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Directory Structure

The system will automatically create the following directories:
```
face-recognition-attendance/
├── dataset/            # Stores student photos
├── encodings/          # Stores face encoding data
├── attendance_records/ # Stores daily attendance CSV files
├── students.csv        # Student information database
└── app.py              # Main application file
```

## Usage

1. Start the application:
    ```bash
    streamlit run app.py
    ```

2. Access the web interface through your browser (typically http://localhost:8501)

3. Use the sidebar menu to:
   - Register new students
   - Mark attendance
   - View attendance records

### Student Registration
1. Select "Register Student" from the sidebar
2. Enter student ID and name
3. Take a photo using the embedded camera
4. Click "Register Student" to save

### Mark Attendance
1. Select "Mark Attendance" from the sidebar
2. Click "Start/Stop Attendance" to begin
3. The system will automatically recognize faces and mark attendance
4. Click "Start/Stop Attendance" again to stop

### View Attendance
1. Select "View Attendance" from the sidebar
2. Choose a date to view records
3. View attendance data in tabular format

## Screenshots

### Dashboard
![Dashboard Screenshot](screenshots/dashboard.png)

### Register Student
![Register Student Screenshot](screenshots/register_student.png)

### Mark Attendance
![Mark Attendance Screenshot](screenshots/mark_attendance.png)

### View Attendance
![View Attendance Screenshot](screenshots/view_attendance.png)

## Dependencies

Major dependencies include:
- Streamlit
- OpenCV
- face_recognition
- NumPy
- Pandas

For a complete list, see `requirements.txt`

## System Requirements

- Python 3.7 or higher
- Webcam for face registration and attendance
- Sufficient RAM for face recognition processing (minimum 4GB recommended)
- CPU with good processing power (for real-time face recognition)

## Limitations

- Works best with good lighting conditions
- Face recognition accuracy may vary based on image quality
- Requires stable internet connection for web interface

## Troubleshooting

1. If camera doesn't work:
   - Check camera permissions in your browser
   - Ensure no other application is using the camera

2. If face recognition is slow:
   - Reduce the number of registered faces
   - Ensure good lighting conditions
   - Check CPU usage and available memory

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
