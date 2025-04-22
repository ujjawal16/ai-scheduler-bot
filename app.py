from datetime import datetime, timedelta
from flask import Flask, jsonify, request, redirect, session, url_for
from flask_session import Session
from nylas import Client
from nylas.models.auth import URLForAuthenticationConfig, CodeExchangeRequest
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize Nylas client
nylas = Client(api_key=os.getenv("NYLAS_API_KEY"))

# Route to begin OAuth flow
@app.route("/nylas/auth")
def auth():
    config = URLForAuthenticationConfig(
        client_id=os.getenv("NYLAS_CLIENT_ID"),
        redirect_uri=os.getenv("NYLAS_REDIRECT_URI"),
        response_type="code",
        #scope="calendar,email,events"
    )
    auth_url = nylas.auth.url_for_oauth2(config)
    return redirect(auth_url)

# OAuth redirect callback
@app.route("/oauth/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Missing authorization code!", 400

    exchange_request = CodeExchangeRequest(
        client_id=os.getenv("NYLAS_CLIENT_ID"),
        client_secret=os.getenv("NYLAS_CLIENT_SECRET"),
        code=code,
        redirect_uri=os.getenv("NYLAS_REDIRECT_URI")
    )

    token_response = nylas.auth.exchange_code_for_token(exchange_request)
    print(token_response)

    session["access_token"] = token_response.access_token
    session["email"] = token_response.email
    session["grant_id"] = token_response.grant_id

    return f"""
        <h3>Authorization Successful!</h3>
        <p>Email: {session['email']}</p>
        <p>Access Token: {session['access_token']}</p>
    """


import requests
from flask import jsonify, session

@app.route("/calendars", methods=["GET"])
def list_calendars():
    if "access_token" not in session:
        return "User not authenticated!", 401

    try:
        # Prepare the headers
        headers = {
            'Authorization': f'Bearer {session["access_token"]}',
            'Accept': 'application/json'
        }

        # Make the GET request to fetch calendars
        response = requests.get('https://api.us.nylas.com/v3/grants/me/calendars', headers=headers)

        # Check if the request was successful
        if response.status_code != 200:
            return f"Error fetching calendars: {response.text}", response.status_code

        # Parse the JSON response
        calendars = response.json()

        if not calendars:
            return "No calendars found for the authenticated user.", 404

        # Return the list of calendars
        return jsonify([
            {
                "id": cal["id"],
                "name": cal["name"],
                "read_only": cal["read_only"]
            } for cal in calendars.get('data', [])
        ])

    except Exception as e:
        # Log detailed error message
        import traceback
        traceback.print_exc()
        print(f"Error fetching calendars: {e}")
        return f"Error fetching calendars: {e}", 500


@app.route('/candidate-availability', methods=['GET', 'POST'])
def candidate_availability():
    if request.method == 'POST':
        # Candidate selects time slot
        selected_time = request.form.get('time')  # Candidate selects a time
        session['candidate_time'] = selected_time
        return redirect(url_for('check_recruiter_availability'))
    
    # Show availability options (this could be done via a form or dynamic UI)
    return '''
        <form method="post">
            <label>Select your available time slot:</label>
            <input type="datetime-local" name="time">
            <input type="submit" value="Submit">
        </form>
    '''


@app.route('/recruiter-availability', methods=['GET'])
def check_recruiter_availability():
    if 'access_token' not in session:
        return "User not authenticated!", 401

    try:
        # Fetch recruiter calendars
        headers = {
            'Authorization': f'Bearer {session["access_token"]}',
            'Accept': 'application/json'
        }

        # Get recruiter’s primary calendar events for the next few days
        response = requests.get('https://api.us.nylas.com/v3/grants/me/calendars', headers=headers)
        calendars = response.json().get('data', [])
        print("calendars--", calendars)

        if len(calendars) == 0:
            return "No calendars found for the recruiter.", 404

        # Check for availability
        calendar_id = calendars[1]['id']  # Assuming the first calendar is the primary calendar
        available_slots = []

        # Get events within the next 3 days for the recruiter
        current_time = datetime.utcnow()
        end_time = current_time + timedelta(days=30)

        # Convert to epoch (in seconds)
        start_epoch = int(current_time.timestamp())
        end_epoch = int(end_time.timestamp())

        session['calendar_id'] = calendar_id

        # Fetch calendar events for the recruiter
        events_url = f'https://api.us.nylas.com/v3/grants/me/events?calendar_id={calendar_id}&start={start_epoch}&end={end_epoch}'
        
        print("events_url--", events_url)
        events_response = requests.get(events_url, headers=headers)

        # Parse the events to find free slots
        events = events_response.json().get('data', [])

        print("events_response--", events_response.text)
        
        # Logic to find available slots (this is a simplified version)
        busy_times = [event['start_time'] for event in events]

        # Find a matching slot (you can use AI here for more complex matching)
        if 'candidate_time' in session:
            candidate_time = session['candidate_time']
            if candidate_time not in busy_times:
                available_slots.append(candidate_time)

        if not available_slots:
            return "No available slots for the recruiter.", 404

        # Proceed to schedule the interview
        return jsonify(available_slots)
    
    except Exception as e:
        return f"Error fetching recruiter availability: {str(e)}", 500


@app.route("/schedule-interview", methods=["GET"])
def schedule_interview():
    if "access_token" not in session or "calendar_id" not in session:
        return jsonify({"error": "User not authenticated or calendar not selected!"}), 401

    try:
        data = request.data
        candidate_time = session['candidate_time']  # e.g. "2025-04-23T09:30:00Z"

        if not candidate_time:
            return jsonify({"error": "start_time is required"}), 400

        # Convert to epoch timestamps
        start_dt = datetime.fromisoformat(candidate_time.replace("Z", "+00:00"))
        end_dt = start_dt + timedelta(hours=1)

        start_epoch = int(start_dt.timestamp())
        end_epoch = int(end_dt.timestamp())

        # Prepare the event data
        event_data = {
            "title": "Interview with Candidate",
            "busy": True,
            "participants": [
                {"email": "uzialways@gmail.com"},       # Candidate
                {"email": "ujjawal.golani@gmail.com"}    # Recruiter
            ],
            "description": "Interview for the open role.",
            "location": "Online Interview",
            "when": {
                "start_time": start_epoch,
                "end_time": end_epoch,
                "start_timezone": "UTC",
                "end_timezone": "UTC"
            }
        }

        # Call the Nylas API
        url = f"https://api.us.nylas.com/v3/grants/me/events?calendar_id={session['calendar_id']}"
        headers = {
            "Authorization": f"Bearer {session['access_token']}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=event_data)
        print("response--", response.text)

        if response.status_code in [200, 201]:
            return jsonify({
                "message": "Interview scheduled successfully!",
                "event": response.json()
            })
        else:
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Root route
@app.route("/")
def index():
    return "Nylas OAuth Integration - Go to /nylas/auth to start."

if __name__ == "__main__":
    app.run(debug=True)

