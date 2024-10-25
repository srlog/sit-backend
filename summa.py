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
    'storageBucket': 'testing-sit-ed0c2.appspot.com'  # Replace with your storage bucket name
})


db = firestore.client() # Database
bucket = storage.bucket() # For storing files\

data = db.collection('KRSGGxdBgR0Z8').document('SecvJtfUTTPAV').get().to_dict()
final = data
print(final)
db.collection('KRSGGxdBgR0Z8').document('test2').set(final)
db.collection('KRSGGxdBgR0Z8').document('test4').set(final)
# db.collection('KRSGGxdBgR0Z8').document('test4').set(data)
