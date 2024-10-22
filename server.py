from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid, json
import random, string
from datetime import datetime as date_time
from flask_cors import CORS
# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebasesdk.json")  # Replace with your Firebase admin SDK JSON file path
firebase_admin.initialize_app(cred, {
    'storageBucket': 'http://testing-sit-ed0c2.appspot.com'  # Replace with your storage bucket name
})

db = firestore.client()
bucket = storage.bucket()

@app.route('/')
def hello():
    return "HELLO BARATH"


@app.route('/api/events', methods = ["POST","GET","PUT",'DELETE'])
def events():
    if request.method == "POST":
        # Adding a event
        form_data = request.form
        form_dict = form_data.to_dict()
        event_name = request.form.get('event_name')
        event_id = event_name[:3] + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        event_poster = request.files.get('event_poster')

        if event_poster:
            # Generate a unique file name for the poster
            poster_filename = f"{uuid.uuid4()}_{event_poster.filename}"
            blob = bucket.blob(poster_filename)
            blob.upload_from_file(event_poster, content_type=event_poster.content_type)
            blob.make_public()
            event_poster_url = blob.public_url
            form_dict.update({ 'event_poster_url': event_poster_url})
        form_dict.update({"event_id": event_id, 'created_at': date_time.now()})
        db.collection('events').document(event_id).set(form_dict)
        return jsonify({'success': True, 'message': 'Event added successfully!'}), 201
        

    elif request.method == "GET":
        # Retrieve all events
        all_events_ref = db.collection('events').order_by('created_at', direction=firestore.Query.ASCENDING)
        all_events = [doc.to_dict() for doc in all_events_ref.stream()]
        
        # Return the list of events as a JSON response
        return jsonify({'events': all_events}), 200



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

# Retrieving event details
@app.route('/api/teams/<event_id>', methods = ["POST","GET"])
def teams(event_id):

    if request.method=="GET":
        # Retrieve all teams
        all_teams_ref = db.collection(event_id)
        all_teams = [teams.to_dict() for teams in all_teams_ref.stream()]
        
        # Return the list of events as a JSON response
        return jsonify({'teams': all_teams}), 200

    elif request.method == "POST":
        event_data = request.form
        event_dict = event_data.to_dict()
        team_name = request.form.get('team_name')
        team_id = team_name[:3] + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        ppt = request.files.get('ppt')
              
        # Check if an event poster is uploaded as a file    
        if ppt:
            # Generate a unique file name for the poster
            ppt_filename = f"{uuid.uuid4()}_{ppt.filename}"
            blob = bucket.blob(ppt_filename)
            blob.upload_from_file(ppt, content_type=ppt.content_type)
            blob.make_public()
            ppt_url = blob.public_url
            event_dict.update({ 'event_poster_url': ppt_url})
        event_dict.update({"team_id": team_id})
        db.collection(event_id).document(team_id).set(event_dict)
        return jsonify({'success': True, 'message': 'Team added successfully!'}), 201



@app.route("/api/event/<event_id>", methods=['GET'])
def individual_event(event_id):
    if request.method == "GET":
        ind_event_ref = db.collection('events').document(event_id)
        ind_event = ind_event_ref.get()

        if ind_event.exists:
            event_data = ind_event.to_dict()
            return jsonify({event_id: event_data}), 200
        else:
            return jsonify({"error": "Event not found"}), 404



@app.route("/api/event/<event_id>/<team_id>", methods=['GET','PUT'])
def ind_team(event_id, team_id):


    if request.method == "GET":
    
        ind_team_ref = db.collection(event_id).document(team_id)
        ind_team = ind_team_ref.get()

        if ind_team.exists:
            team_data = ind_team.to_dict()
            return jsonify({team_id: team_data}), 200
        else:
            return jsonify({"error": "Team not found"}), 404
        
    elif request.method == "PUT":
        team_data = request.form
        team_dict = team_data.to_dict()

        status = request.form.get('status')
        status_hod = request.form.get('status_hod')
        status_principal = request.form.get('status_principal')
        if status_hod:
            team_dict.update({'status_hod':status_hod})
        if status_principal: 
            team_dict.update({'status_principal':status_principal})

        feedback = request.form.get('feedback')
        geotag = request.files.get('geotag')

        if geotag:
            # Generate a unique file name for the geotag
            geotag_filename = f"{uuid.uuid4()}_{geotag.filename}"
            blob_geotag = bucket.blob(geotag_filename)
            blob_geotag.upload_from_file(geotag, content_type=geotag.content_type)
            blob_geotag.make_public()
            geotag_url = blob_geotag.public_url
            team_dict.update({ 'geotag_url': geotag_url})

        team_dict.update({ "status": status, 'feedback':feedback})

        db.collection(event_id).document(team_id).set(team_dict)
        return jsonify({'success': True, 'message': 'Team updated successfully!'}), 200

@app.route('/api/custom_events', methods = ["POST","GET","PUT",'DELETE'])
def custom_events():
    if request.method == "POST":
        # Adding a event
        form_data1 = request.form
        form_dict1 = form_data1.to_dict()
        event_name1 = request.form.get('event_name')
        event_id1 = event_name1[:3] + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        event_poster1 = request.files.get('event_poster')
        print(form_dict1)
            
        # Check if an event poster is uploaded as a file
        if event_poster1:
            # Generate a unique file name for the poster
            poster_filename1 = f"{uuid.uuid4()}_{event_poster1.filename}"
            blob1 = bucket.blob(poster_filename1)
            blob1.upload_from_file(event_poster1, content_type=event_poster1.content_type)
            blob1.make_public()
            event_poster_url1 = blob1.public_url
            form_dict1.update({ 'event_poster_url': event_poster_url1})
        form_dict1.update({"event_id": event_id1})
        db.collection('custom_events').document(event_id1).set(form_dict1)
        return jsonify({'success': True, 'message': 'Custom Event added successfully!'}), 201
        

    elif request.method == "GET":
        # Retrieve all events
        all_custom_events_ref = db.collection('custom_events')
        all_custom_events = [doc.to_dict() for doc in all_custom_events_ref.stream()]
        
        # Return the list of events as a JSON response
        return jsonify({'events': all_custom_events}), 200

@app.route("/api/od/<event_id>/<team_id>", methods=['GET', 'PUT'])
def get_od(event_id, team_id):
    if request.method == "GET":
        # Reference to the specific team document in the event collection
        ind_team_ref = db.collection(event_id).document(team_id)
        ind_team = ind_team_ref.get()

        # Check if the document exists
        if ind_team.exists:
            # Convert the document to a dictionary
            team_data = ind_team.to_dict()

            # Filter and print all fields that contain 'department' in their keys
            department_fields = {key: value for key, value in team_data.items() if 'department' in key.lower()}
            year_fields = {key: value for key, value in team_data.items() if (('1st' in key.lower()) or ('I' in key.lower()))}
            department_fields.update(year_fields)
            # Print the fields with 'department' in their keys
            print("Department-related fields and values:", department_fields)
            
            return department_fields  # Return the filtered data as a response
        else:
            return {"error": "Team not found"}, 404




if __name__ == '__main__':
    app.run(port=5001, debug=True, host="0.0.0.0")
