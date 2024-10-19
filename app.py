from flask import Flask, request, jsonify, render_template, redirect
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid
import os,json
import requests

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebasesdk.json")  # Replace with your Firebase admin SDK JSON file path
firebase_admin.initialize_app(cred, {
    'storageBucket': 'msec-test-62a61.appspot.com'  # Replace with your storage bucket name
})

db = firestore.client()
bucket = storage.bucket()

@app.route('/')
def home():
    return render_template('add_event.html')

@app.route('/register_event')
def register_event():
    return render_template('register_event.html')

# Route to handle form submission via POST request
@app.route('/add-event', methods=['POST'])
def add_event():
    try:

        
        form_data = request.form
        form_dict = form_data.to_dict()
        form_json = json.dumps(form_dict)
        # return form_json

        # # Collect form data and files
        event_name = request.form.get('event_name')
        # event_description = request.form.get('event_description')
        # event_registration_link = request.form.get('event_registration_link')
        # event_deadline = request.form.get('event_deadline')
        event_poster = request.files['event_poster']

        # Check if an event poster is uploaded as a file
        if event_poster:
            # Generate a unique file name for the poster
            poster_filename = f"{uuid.uuid4()}_{event_poster.filename}"
            blob = bucket.blob(poster_filename)
            blob.upload_from_file(event_poster, content_type=event_poster.content_type)
            blob.make_public()
            event_poster_url = blob.public_url
            form_json.update({ 'event_poster_url': event_poster_url})

        else:
            return jsonify({'error': 'Event poster is missing'}), 400
        
        
        # # Store event details in Firestore
        # event_data = {
        #     'event_name': event_name,
        #     'event_description': event_description,
        #     'event_poster_url': event_poster_url,
        #     'event_registration_link': event_registration_link,
        #     'event_deadline': event_deadline
        # }
        db.collection('events').document(event_name).set(form_json)

        return jsonify({'success': True, 'message': 'Event added successfully!'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to handle registration via POST request
@app.route('/register_event', methods=['POST'])
def register_team():
    try:
        print(request.form)
        # Collect form data and files
        event_name = request.form.get('event_name')  # hidden input
        team_name = request.form.get('team_name')
        lead_name = request.form.get('lead_name')
        idea_title = request.form.get('idea_title')
        idea_description = request.form.get('idea_description')
        idea_ppt = request.files['idea_ppt']  # This is the PDF file
        lead_department = request.form.get('lead_department')
        lead_registerno = request.form.get('lead_registerno')
        lead_mailid = request.form.get('lead_mailid')
        lead_phoneno = request.form.get('lead_phoneno')

        # Member 1 details
        member1_name = request.form.get('member1_name')
        member1_department = request.form.get('member1_department')
        member1_registerno = request.form.get('member1_registerno')
        member1_mailid = request.form.get('member1_mailid')
        member1_phoneno = request.form.get('member1_phoneno')

        # Member 2 details
        member2_name = request.form.get('member2_name')
        member2_department = request.form.get('member2_department')
        member2_registerno = request.form.get('member2_registerno')
        member2_mailid = request.form.get('member2_mailid')
        member2_phoneno = request.form.get('member2_phoneno')

        # Member 3 details
        member3_name = request.form.get('member3_name')
        member3_department = request.form.get('member3_department')
        member3_registerno = request.form.get('member3_registerno')
        member3_mailid = request.form.get('member3_mailid')
        member3_phoneno = request.form.get('member3_phoneno')

        # Mentor details
        mentor_name = request.form.get('mentor_name')

        # Check if the idea PPT is uploaded as a file
        if idea_ppt:
            # Generate a unique file name for the PPT
            ppt_filename = f"{uuid.uuid4()}_{idea_ppt.filename}"

            # Upload the PPT to Firebase Storage
            blob = bucket.blob(ppt_filename)
            blob.upload_from_file(idea_ppt, content_type=idea_ppt.content_type)

            # Get the publicly accessible URL for the uploaded PPT
            blob.make_public()
            idea_ppt_url = blob.public_url
        else:
            return jsonify({'error': 'Idea PPT is missing'}), 400

        # Store team registration details in Firestore
        team_data = {
            'team_name': team_name,
            'lead_name': lead_name,
            'idea_title': idea_title,
            'idea_description': idea_description,
            'idea_ppt_url': idea_ppt_url,
            'lead_department': lead_department,
            'lead_registerno': lead_registerno,
            'lead_mailid': lead_mailid,
            'lead_phoneno': lead_phoneno,
            'member1': {
                'name': member1_name,
                'department': member1_department,
                'registerno': member1_registerno,
                'mailid': member1_mailid,
                'phoneno': member1_phoneno
            },
            'member2': {
                'name': member2_name,
                'department': member2_department,
                'registerno': member2_registerno,
                'mailid': member2_mailid,
                'phoneno': member2_phoneno
            },
            'member3': {
                'name': member3_name,
                'department': member3_department,
                'registerno': member3_registerno,
                'mailid': member3_mailid,
                'phoneno': member3_phoneno
            },
            'mentor_name': mentor_name
        }

        # Store the registration details under the event collection
        db.collection(event_name).document(team_name).set(team_data)

        return jsonify({'success': True, 'message': 'Team registered successfully!'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


# Route to display registered teams
@app.route('/teams/<event_name>')
def display_teams(event_name):
    try:
        # Fetch all teams registered under the given event
        response = requests.post(f'http://localhost:5001/api-teams/{event_name}')
        teams = response.json()
        # teams_ref = db.collection(event_name)
        # teams = [doc.to_dict() for doc in teams_ref.stream()]

        # Pass the teams and event_name to the HTML template
        return render_template('display_teams.html', teams=teams, event_name=event_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Route to handle approve/reject actions
@app.route('/teams/<event_name>/<team_name>/update_status', methods=['POST','GET'])
def update_status(event_name, team_name):
    try:
        action = request.form.get('action')  # "approve" or "reject"

        # Update the team's status in Firestore
        status = 'Approved' if action == 'approve' else 'Rejected'
        db.collection(event_name).document(team_name).update({'status': status})

        return redirect(url_for('display_teams', event_name=event_name))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to view details of a team
@app.route('/teams/<event_name>/<team_name>')
def view_team_details(event_name, team_name):

    ,
    try:
        # Fetch the team details from Firestore
        team_ref = db.collection(event_name).document(team_name)
        team = team_ref.get().to_dict()

        return render_template('team_details.html', team=team, event_name=event_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
