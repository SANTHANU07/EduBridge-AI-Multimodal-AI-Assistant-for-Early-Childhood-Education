Pinecone
This project requires Pinecone for vector storage and retrieval.

You need:

A valid Pinecone account
An existing Pinecone index
PINECONE_API_KEY
PINECONE_INDEX
Without Pinecone configuration, the retrieval pipeline will not initialize successfully.

Ollama
Install Ollama locally and pull a supported model.

Example:

ollama pull llama3.1
Make sure the Ollama server is available before using the AI assistant.

Google Calendar
Google Calendar sync is optional.

To enable it:

Create a Google Cloud project
Enable the Google Calendar API
Create a service account
Download the JSON key file
Save it locally and point GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE to it
Share the target Google Calendar with the service account email
If Google Calendar is not configured, events will still be saved locally.

Running the Application
Run with Streamlit
streamlit run app.py
Or use the included PowerShell helper
.\run_app.ps1
Then open:

http://localhost:8501
Supported Inputs
AI Assistant Upload Types
PDF
PNG
JPG
JPEG
WAV
MP3
M4A
MP4
MOV
AVI
MKV
WEBM
Sample Data
The app auto-seeds sample data including:

Students
Teacher account
Parent accounts
Homework
Marks
Attendance
Notices
Default school events
This makes the project usable immediately for demos and academic presentations.

Current Modules
Teacher Modules
Homework management
Marks management
Attendance entry
Bulk attendance
Notices management
File uploads
School event management
AI assistant
Parent Modules
Student dashboard
Homework viewing
Marks viewing
Attendance viewing
Events viewing
Charts and analytics
AI-style summaries
AI assistant
Dashboard Modules
Manual performance data entry
CSV/Excel upload
Trend analysis
Subject comparison
Attendance insights
Downloadable reports
Strengths of the Project
Combines school ERP-style features with AI support
Supports multimodal file understanding
Includes multilingual assistance
Uses role-based UX for clarity
Works well for demos and prototype showcases
Stores core academic data locally with SQLite
Includes optional cloud integration for calendar events
Limitations
Authentication is basic and not production-grade
Password handling uses simple hashing without a full auth framework
Pinecone is required for retrieval features
AI quality depends on the local Ollama setup and model availability
Whisper and OCR can be resource-intensive on smaller machines
No deployment pipeline is included yet
Some integrations are prototype-level and may need hardening for production use
Future Improvements
Add secure production authentication
Add admin role and permission management
Add teacher-specific class mapping
Add notification delivery via email or WhatsApp
Add richer multilingual support beyond current language handling
Add cloud deployment support
Add automated tests
Add document history and knowledge base management
Improve vector storage fallback when Pinecone is unavailable
Add better analytics for longitudinal student growth
Use Cases
EduBridge AI can be used for:

School project demonstrations
AI in education hackathons
Early childhood education analytics prototypes
Parent communication tools
Smart classroom assistant concepts
Multimodal educational support systems
Why This Project Matters
EduBridge AI is more than a dashboard. It is a practical demonstration of how AI can make school systems more inclusive, responsive, and accessible. By combining teacher workflows, parent visibility, academic records, and multimodal AI support, the project shows how educational technology can reduce communication gaps and support better student outcomes.

Screens You Can Highlight in a Demo
Login screen with teacher and parent roles
Teacher portal dashboard
Homework and marks management
Parent/student dashboard
Charts and analytics tab
AI assistant with uploaded school files
Event creation with Google Calendar sync
Performance dashboard with CSV upload
Author
Santhanu

GitHub: SANTHANU07

Repository
Project link:
https://github.com/SANTHANU07/EduBridge-AI-Multimodal-AI-Assistant-for-Early-Childhood-Education
