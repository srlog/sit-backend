from flask import Flask, request, jsonify, render_template, redirect
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid
import os

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
    return render_template('event_form.html')


# Route to handle form submission via POST request
@app.route('/add-event', methods=['POST'])
def add_event():
    try:
        # Collect form data and files
        event_name = request.form.get('event_name')
        event_description = request.form.get('event_description')
        event_registration_link = request.form.get('event_registration_link')
        event_deadline = request.form.get('event_deadline')
        event_poster = request.files['event_poster']

        # Check if an event poster is uploaded as a file
        if event_poster:
            # Generate a unique file name for the poster
            poster_filename = f"{uuid.uuid4()}_{event_poster.filename}"

            # Upload the poster to Firebase Storage
            blob = bucket.blob(poster_filename)
            blob.upload_from_file(event_poster, content_type=event_poster.content_type)

            # Get the publicly accessible URL for the uploaded poster
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


if __name__ == '__main__':
    app.run(debug=True)
