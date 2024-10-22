from flask import Flask, request, jsonify, send_file
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid, json
import random, string
from datetime import datetime as date_time
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Initialize Firebase Admin SDK
"""To download this ..  1. go to "Project Settings"  2. click "Service Accounts" tab  3. click "Generate new private key"""
cred = credentials.Certificate("firebasesdk.json")  

# Uploading files to storagebucket
firebase_admin.initialize_app(cred, {
    'storageBucket': 'http://testing-sit-ed0c2.appspot.com'  # Replace with your storage bucket name
})


db = firestore.client() # Database
bucket = storage.bucket() # For storing files

""" API endpoint for events
--> POST: Create a new event
--> GET: Retrieves all events
--> PUT: Updates an existing event
--> DELETE: Deletes an event
"""
@app.route('/api/events', methods = ["POST","GET","PUT",'DELETE'])
def events():
    if request.method == "POST":
        #to create a new event
        form_data = request.form
        form_dict = form_data.to_dict()
        event_name = request.form.get('event_name')
        # Generating a random event_Id with first 3 characters of event_name to debug
        if len(event_name) > 2:
            prefix = event_name[:3]
        else: # if the event)name is less then length 3
            prefix = event_name

        # Generating unique event_id 
        for i in range(5):
            event_id = prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            existing_event = db.collection('events').document(event_id).get()
            if not existing_event.exists:
                break
            if i==4:
                return jsonify({'success': False, 'message': 'Unable to generate a unique event ID after several attempts'}), 500
            
        event_poster = request.files.get('event_poster')

        if event_poster:
            # Upload the poster, if a file is received
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
        # to retrieve all events
        all_events_ref = db.collection('events').order_by('created_at', direction=firestore.Query.ASCENDING)
        all_events = [doc.to_dict() for doc in all_events_ref.stream()]
        
        # Return the list of events as a JSON response
        return jsonify({'events': all_events}), 200



    elif request.method == "PUT" :
        # to update a event
        form_data_edit = request.form
        form_json_edit = form_data_edit.to_dict()
        event_id = request.form.get("event_id")
        event_poster_edit = request.files.get("event_poster")
        # Check if an event poster is uploaded as a file , otherwise only uploads the text data
        if event_poster_edit:
            # Generate a unique file name for the poster
            poster_filename_edit = f"{uuid.uuid4()}_{event_poster_edit.filename}"
            blob_edit = bucket.blob(poster_filename_edit)
            blob_edit.upload_from_file(event_poster_edit, content_type=event_poster_edit.content_type)
            blob_edit.make_public()
            event_poster_url_edit = blob_edit.public_url
            form_json_edit.update({ 'event_poster_url': event_poster_url_edit})
        
        # Using update instead of set to only add new fields and update the specified one
        db.collection('events').document(event_id).update(form_json_edit)
        return jsonify({'success': True, 'message': 'Event updated successfully!'}), 201


    elif request.method == "DELETE":
        # Removing an event
        # event_id is read from request (VERY VERY IMPORTANT)
        event_id = request.form.get('event_id')
        event_ref = db.collection('events').document(event_id)
        if event_ref.get().exists:
            event_ref.delete()
            return jsonify({"message": "Event deleted successfully"}), 200
        else:
            return jsonify({"error": "Event not found"}), 404

""" API endpoint for teams
--> POST: Register a team for this event
--> GET: Retrieves all teams registered for this event
"""
@app.route('/api/teams/<event_id>', methods = ["POST","GET"])
def teams(event_id):

    if request.method=="GET":
        # Retrieve all individual teams
        all_teams_ref = db.collection(event_id)
        all_teams = [teams.to_dict() for teams in all_teams_ref.stream()]
        return jsonify({'teams': all_teams}), 200

    elif request.method == "POST":
        # Registering a team fo the event specified with the event_id
        event_data = request.form
        event_dict = event_data.to_dict()
        # Extracts Departments and adding individual status fields for each HOD
        departments_status = ["status_"+value+"_HOD" for key, value in event_dict.items() if 'department' in key.lower()]
        departments_status.append(firstyear[0])
        for each in departments_status:
            event_dict.update({each: False})
        event_dict.update({"status_admin" : False})
        # same as the event_id
        team_name = request.form.get('team_name')
        if len(team_name) > 2:
            prefix = team_name[:3]
        else: 
            prefix = team_name
        for i in range(5):
            team_id = prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            existing_team = db.collection(event_id).document(team_id).get()
            if not existing_team.exists:
                break
            if i==4:
                return jsonify({'success': False, 'message': 'Unable to generate a unique team ID after several attempts'}), 500
        
        ppt = request.files.get('ppt')  
        if ppt:
            ppt_filename = f"{uuid.uuid4()}_{ppt.filename}"
            blob_team = bucket.blob(ppt_filename)
            blob_team.upload_from_file(ppt, content_type=ppt.content_type)
            blob_team.make_public()
            ppt_url = blob_team.public_url
            event_dict.update({ 'event_poster_url': ppt_url})
        event_dict.update({"team_id": team_id})
        db.collection(event_id).document(team_id).set(event_dict)
        return jsonify({'success': True, 'message': 'Team added successfully!'}), 201


""" API endpoint for retrieving event details
--> GET: Retrieves details about particular event, specified with the event_id on the address
"""
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


""" API endpoint to retrieve individual team details
--> GET: Retrieves all teams from a event
--> PUT: Updates a team
--> DELETE: Deletes a team
"""
@app.route("/api/event/<event_id>/<team_id>", methods=['GET','PUT'])
def ind_team(event_id, team_id):

    if request.method == "GET":
        # each team is a document inside the collection within the event_id collection
        ind_team_ref = db.collection(event_id).document(team_id)
        ind_team = ind_team_ref.get()
        if ind_team.exists:
            team_data = ind_team.to_dict()
            return jsonify({team_id: team_data}), 200
        else:
            return jsonify({"error": "Team not found"}), 404
        
    elif request.method == "DELETE":
        team_ref = db.collection(event_id).document(team_id)
        if team_ref.get().exists:
            team_ref.delete()
            return jsonify({"message": "Team deleted successfully"}), 200
        else:
            return jsonify({"error": "Team not found"}), 404
        
    elif request.method == "PUT":
        team_data = request.form
        team_dict = team_data.to_dict()
        # Check for the updates in all status field
        status = request.form.get("status_admin")
        if status:
            team_dict.update({"status_admin": status})
        # Extracts all the status keys and values
        all_status_hod = [key for key, value in team_dict.items() if 'status' in key and value]
        for each_status in all_status_hod:
            status_cur = team_dict.get(each_status)
            # If the field present in the request, updates on the firestore
            if status_cur:
                team_dict.update({each_status: status_cur})
        # Check whether the requesst contains feedback or not
        feedback = request.form.get('feedback')
        if feedback:
            team_dict.update({'feedback':feedback})

        geotag = request.files.get('geotag')
        if geotag:
            # Generate a unique file name for the geotag
            geotag_filename = f"{uuid.uuid4()}_{geotag.filename}"
            blob_geotag = bucket.blob(geotag_filename)
            blob_geotag.upload_from_file(geotag, content_type=geotag.content_type)
            blob_geotag.make_public()
            geotag_url = blob_geotag.public_url
            team_dict.update({ 'geotag_url': geotag_url})
        db.collection(event_id).document(team_id).set(team_dict)
        return jsonify({'success': True, 'message': 'Team updated successfully!'}), 200

""" API endpoint for custom_events
--> POST: Create a new custom event
--> GET: Retrieves all custom events
--> PUT: Event gets approved by admin
--> DELETE: Deletes a custom event
"""
@app.route('/api/custom_events', methods = ["POST","GET","PUT",'DELETE'])
def custom_events():
    if request.method == "POST":
        # Adding a event
        form_data1 = request.form
        form_dict1 = form_data1.to_dict()
        event_name1 = request.form.get('event_name')

        if len(event_name1) > 2:
            prefix = event_name1[:3]
        else: # if the event)name is less then length 3
            prefix = event_name1

        # Generating unique event_id 
        for i in range(5):
            event_id1 = prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            existing_event1 = db.collection('custom_events').document(event_id1).get()
            if not existing_event1.exists:
                break
            if i==4:
                return jsonify({'success': False, 'message': 'Unable to generate a unique event ID after several attempts'}), 500  
        event_poster1 = request.files.get('event_poster')
    
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
        # Retrieve all custom events
        all_custom_events_ref = db.collection('custom_events')
        all_custom_events = [doc.to_dict() for doc in all_custom_events_ref.stream()]
        return jsonify({'events': all_custom_events}), 200
    
    elif request.method == "PUT":
        # Approving a event and adding it to the events collection
        event_id_approve = request.form.get('event_id')
        event_ref_approve = db.collection('custom_events').document(event_id_approve)
        
        if event_ref_approve.get().exists:
            this_data = event_ref_approve.get()
            db.collection('events').document(event_id_approve).set(this_data)
            event_ref_approve.delete()
            return jsonify({"message": "Event deleted successfully"}), 200
        else:
            return jsonify({"error": "Event not found"}), 404
    

    elif request.method == "DELETE":
        # Removing an event
        # event_id is read from request (VERY VERY IMPORTANT here too)
        event_id = request.form.get('event_id')
        event_ref = db.collection('custom_events').document(event_id)
        if event_ref.get().exists:
            event_ref.delete()
            return jsonify({"message": "Custom Event deleted successfully"}), 200
        else:
            return jsonify({"error": "Custom Event not found"}), 404


# FUnction to generate OD for a registered team
def generate_od(team_data):
    # team_data is the document retrieved from the firestore
    # Checking for any of the 7 departments or 1st year students are there..
    department_fields = [value for key, value in team_data.items() if 'department' in key.lower()]
    year_fields = [value for key, value in team_data.items() if '1st year' in value]
    department_fields.extend(year_fields)

    # extracting the members
    members = [value for key, value in team_data.items() if 'name' in key.lower() and 'member' in key.lower()]

    # Initialising the frequently used keys
    lead_name = team_data.get("lead_name")
    team_name = team_data.get("team_name")
    event_name = team_data.get("event_name")
    event_date = team_data.get("event_date")

    # The final output is getting generated with this name
    output_filename = f"{event_name} {team_name} {lead_name}.pdf"
    
    # For selecting the corresponding name and image of the sign
    hashmap_hod = {
        "IT": "IT HOD",
        "CSE": "CSE HOD",
        "ECE": "ECE HOD",
        "EEE": "EEE HOD",
        "AI&DS": "AI&DS HOD",
        "MECH": "MECH HOD",
        "CIVIL": "CIVIL HOD",
        "1st year": "1st year HOD"
    }
    hashmap_hod_sign = {
        "IT": "sample.jpg",
        "CSE": "sample.jpg",
        "ECE": "sample.jpg",
        "EEE": "sample.jpg",
        "AI&DS": "sample.jpg",
        "MECH": "sample.jpg",
        "CIVIL": "sample.jpg",
        "1st year": "sample.jpg"
    }

    doc = SimpleDocTemplate(output_filename, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    heading_style = styles["Heading1"]

    #Header image
    header_image_path = "headermsec.jpg"
    try:
        img = Image(header_image_path, 7 * inch, 1.3 * inch)
        elements.append(img)
    except:
        elements.append(Paragraph("Meenakshi Sundararajan Engineering College", heading_style))

    # Adding event details dynamically
    elements.append(Spacer(1, 12))
    event_details = f"<b>Event Details:</b><br/>{event_name}<br/>{event_date}<br/>"
    elements.append(Paragraph(event_details, normal_style))
    elements.append(Spacer(1, 12))
    
    time_of_duty = f"<b>Time of OD:</b><br/>Start Time: {event_date} 9:00AM<br/>End Time: {event_date} 4:00PM"
    elements.append(Paragraph(time_of_duty, normal_style))
    elements.append(Spacer(1, 12))

    participation_details = f"<b>Team Lead</b><br/>{lead_name} {team_data.get("lead_department")} <br/><b>Team members</b><br/>"
    # Iterating through each team member and displaying it 
    for i in range(1, len(members) + 1):
        member_key = f"member{i}"
        participation_details += f"{team_data.get(member_key+'_name')} {team_data.get(member_key+'_department')} {team_data.get(member_key+'_year')}<br/>"
    elements.append(Paragraph(participation_details, normal_style))
    elements.append(Spacer(1, 12))

    mentor_details = f"<b>Mentor name: {team_data.get('mentor_name')}</b><br/><br/><br/>"
    elements.append(Paragraph(mentor_details, normal_style))

    elements.append(Paragraph("<b>HODs:</b>", normal_style))
    elements.append(Spacer(1, 12))

    # Dynamically adding the HODs sign , if any of their student is on the team
    for dept in department_fields:
        hod_name = hashmap_hod.get(dept, "N/A")
        hod_image_path = hashmap_hod_sign.get(dept, 'default.jpg')
        try:
            img = Image(hod_image_path, 1 * inch, 0.5 * inch)
            hod_table = Table([[Paragraph(hod_name, normal_style), img]], colWidths=[1 * inch, 5 * inch])
            hod_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
            elements.append(hod_table)
        except:
            elements.append(Paragraph("APPROVED", normal_style))
            elements.append(Paragraph(hod_name, normal_style))

        elements.append(Spacer(1, 10))

    elements.append(Spacer(1, 15))

    signatures_data = [['PRINCIPAL']]
    table = Table(signatures_data, colWidths=[2 * inch, 4 * inch, 2 * inch])
    table.setStyle(TableStyle([('LINEABOVE', (0,0), (1, 1), 1, colors.black), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    elements.append(table)

    doc.build(elements)
    return output_filename


""" API endpoint for generating OD
--> GET: Generates OD letter for the registered team, if they got aproved from all HODs and principal
"""
# Admin has a generate OD button on the progress page, when clicked the OD is returned as a file 
# The frontend should write code to save it locally and make it downloadable for the user
@app.route("/api/od/<event_id>/<team_id>", methods=['GET'])
def get_od(event_id, team_id):
    if request.method == "GET":
        # Reference to the specific team document in the event collection
        ind_team_ref = db.collection(event_id).document(team_id)
        ind_team = ind_team_ref.get()
        team_data = ind_team.to_dict()
        print(team_data)
        status = [value for key,value in team_data.items() if ('status') in key]
        # Check if the document exists and all function will make sure all Approval is obtained
        if ind_team.exists and all(status):
            # Convert the document to a dictionary
            od_pdf = generate_od(team_data)
            return send_file(od_pdf,as_attachment=True)
        elif ind_team.exists : 
            return {"error": "OD not approved by all HODS"}, 404

        else:
            return {"error": "Team not found"}, 404
        
        
""" API endpoint for custom_events
--> POST: Create a new user
--> GET: Get password for the username from firestore
--> PUT: Update the password
--> DELETE: Deletes a user
"""
@app.route("/api/admin/users", methods=["POST","GET","PUT","DELETE"])
def admin_users():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db.collection("users").document(username).set({
            "username": username,
            "password": password
        })
        return jsonify({"message": "New User added successfully"}), 200
    
    elif request.method == "GET":
        username = request.form.get("username")
        ref_user = db.collection('users').document(username)
        user_data = ref_user.get()
        return jsonify({"data":{"username": username, "password" : user_data.get('password')}})
    
    elif request.method == "PUT":
        username = request.form.get("username")
        password = request.form.get("password")

        db.collection("users").document(username).update({
            "username": username,
            "password": password
        })
        return jsonify({"message": "User updated successfully"}), 200
    elif request.method == "DELETE":
        username = request.form.get("username")
        password = request.form.get("password")
        ref_user = db.collection('users').document(username)
        data_user = ref_user.get()
        if password == data_user.get("password"):
            if ref_user.get().exists:
                ref_user.delete()
                return jsonify({'message':"User deleted successfully"})
            else: 
                return jsonify({"error": "User not found"}), 404
        else:
            return jsonify({"error": "Enter correct password to delete it"})


if __name__ == '__main__':
    app.run(port=5001, debug=True, host="0.0.0.0")
