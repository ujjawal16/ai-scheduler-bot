# 🤖 AI-Powered Scheduling Bot using Flask & Nylas

This project is an **AI-powered scheduling assistant** built using **Flask** and **Nylas**. 
It syncs **candidate availability** with **recruiter calendars** and automatically sends **calendar invites** for interviews.

## 🚀 Features

- 🔐 OAuth2-based authentication with Nylas
- 🗓 List recruiter’s calendars and events
- 🔄 Sync candidate and recruiter availability
- 📬 Automatically schedule and send interview invites
- ⚙️ REST API powered by Flask

---

## 🔧 Tech Stack

- **Backend**: Python (Flask)
- **Calendar API**: [Nylas Calendar & Events API](https://developer.nylas.com/docs/)
- **OAuth**: Nylas OAuth 2.0
- **Environment Management**: `python-dotenv`
- **HTTP Client**: `requests`
- **Session Handling**: Flask Session

---

## 📁 Project Structure

flask_nylas/

├── app.py                
├── requirements.txt     
├── .env                  
├── README.md            


🔑 Environment Variables

Create a .env file in the root directory with the following contents:

NYLAS_CLIENT_ID=your_client_id

NYLAS_CLIENT_SECRET=your_client_secret

NYLAS_API_KEY=your_api_key

NYLAS_API_URI=https://api.us.nylas.com


🧪 Getting Started

1. Clone the Repo

git clone https://github.com/{your-username}/flask_nylas.git

cd flask_nylas

2. Set Up Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

3. Start the Flask Server
python app.py

Visit http://localhost:5000/nylas/auth to start the OAuth authentication flow.

📚 API Endpoints

->GET /nylas/auth
Initiates OAuth login with Nylas.

->GET /oauth/callback
Handles OAuth callback and retrieves access token + grant ID.

->GET /calendars
Returns calendars of the authenticated recruiter.

->POST /schedule-interview
Schedules a new calendar event using candidate time and recruiter availability.

📄 License
2025 Ujjawal Golani

