from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid, json
import random, string

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebasesdk.json")  # Replace with your Firebase admin SDK JSON file path
firebase_admin.initialize_app(cred, {
    'storageBucket': 'http://testing-sit-ed0c2.appspot.com'  # Replace with your storage bucket name
})

db = firestore.client()
bucket = storage.bucket()


@app.route('/api/events', methods = ["POST","GET","PUT",'DELETE'])
def events():
    if request.method == "POST":
        # Adding a event
        form_data = request.form
        form_dict = form_data.to_dict()
        event_name = request.form.get('event_name')
        event_id = event_name[:3] + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        event_poster = request.files.get('event_poster')
        print(form_dict)
              
        # Check if an event poster is uploaded as a file
        if event_poster:
            # Generate a unique file name for the poster
            poster_filename = f"{uuid.uuid4()}_{event_poster.filename}"
            blob = bucket.blob(poster_filename)
            blob.upload_from_file(event_poster, content_type=event_poster.content_type)
            blob.make_public()
            event_poster_url = blob.public_url
            form_dict.update({ 'event_poster_url': event_poster_url})
        form_dict.update({"event_id": event_id})
        db.collection('events').document(event_id).set(form_dict)
        return jsonify({'success': True, 'message': 'Event added successfully!'}), 201
        

    elif request.method == "GET":
        # Retrieve all events
        all_events_ref = db.collection('events')
        all_events = [doc.to_dict() for doc in all_events_ref.stream()]
        
        # Return the list of events as a JSON response
        return jsonify({'events': all_events}), 200

        pass


    elif request.method == "PUT" :
        # updating the event
        form_data_edit = request.form
        form_json_edit = form_data_edit.to_dict()
        event_id = request.form.get("event_id")
        event_poster_edit = request.files.get("event_poster")

        # Check if an event poster is uploaded as a file
        if event_poster_edit:
            # Generate a unique file name for the poster
            poster_filename_edit = f"{uuid.uuid4()}_{event_poster_edit.filename}"
            blob_edit = bucket.blob(poster_filename_edit)
            blob_edit.upload_from_file(event_poster_edit, content_type=event_poster_edit.content_type)
            blob_edit.make_public()
            event_poster_url_edit = blob_edit.public_url
            form_json_edit.update({ 'event_poster_url': event_poster_url_edit})
        
        db.collection('events').document(event_id).set(form_json_edit)
        return jsonify({'success': True, 'message': 'Event updated successfully!'}), 201


    elif request.method == "DELETE":
        # Removing an event
        # event_id read from request
        event_id = request.form.get('event_id')
        event_ref = db.collection('events').document(event_id)
        if event_ref.get().exists:
            # Delete the document
            event_ref.delete()
            return jsonify({"message": "Event deleted successfully"}), 200
        else:
            return jsonify({"error": "Event not found"}), 404


        pass


    
















# API route to handle adding an event
@app.route('/add-event', methods=['POST'])
def add_event():
    try:
        form_data = request.form
        event_name = form_data.get('event_name')
        event_description = form_data.get('event_description')
        event_registration_link = form_data.get('event_registration_link')
        event_deadline = form_data.get('event_deadline')
        event_poster = request.files['event_poster']

        # Check if event poster is uploaded as a file
        if event_poster:
            # Generate a unique file name for the poster
            poster_filename = f"{uuid.uuid4()}_{event_poster.filename}"

            # Upload poster to Firebase Storage
            blob = bucket.blob(poster_filename)
            blob.upload_from_file(event_poster, content_type=event_poster.content_type)
            blob.make_public()
            event_poster_url = blob.public_url
        else:
            return jsonify({'error': 'Event poster is missing'}), 400

        # Store event details in Firestore
        event_data = {
            'event_name': event_name,
            'event_description': event_description,
            'event_poster_url': event_poster_url,
            'event_registration_link': event_registration_link,
            'event_deadline': event_deadline
        }
        db.collection('events').document(event_name).set(event_data)

        return jsonify({'success': True, 'message': 'Event added successfully!'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# API route to display registered teams
@app.route('/api-teams/<event_name>', methods=['GET','POST'])
def display_teams(event_name):
    try:
        # Fetch all teams registered under the given event
        teams_ref = db.collection(event_name)
        teams = [doc.to_dict() for doc in teams_ref.stream()]
        
        # Debugging: Log the fetched data
        print(f"Fetched teams: {teams}")
        
        # Check if teams data is empty
        if not teams:
            return jsonify({'error': 'No teams found for the event'}), 404
        
        return jsonify({'teams': teams})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


# API route to handle approve/reject actions
@app.route('/teams/<event_name>/<team_name>/update_status', methods=['POST'])
def update_status(event_name, team_name):
    try:
        action = request.form.get('action')  # "approve" or "reject"
        status = 'Approved' if action == 'approve' else 'Rejected'

        # Update the team's status in Firestore
        db.collection(event_name).document(team_name).update({'status': status})

        return jsonify({'success': True, 'message': f'Team {status.lower()} successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API route to view details of a team
@app.route('/teams/<event_name>/<team_name>', methods=['GET'])
def view_team_details(event_name, team_name):
    try:
        # Fetch the team details from Firestore
        team_ref = db.collection(event_name).document(team_name)
        team = team_ref.get().to_dict()

        return jsonify({'team': team}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
