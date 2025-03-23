from flask import Flask, render_template, request, redirect, url_for, flash
from firebase_admin import credentials, initialize_app, storage, firestore, db as admin_db
import os
from datetime import datetime
from dotenv import load_dotenv
import uuid
from werkzeug.utils import secure_filename
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Firebase Admin SDK initialization
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin = initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
    })
    print("Firebase Admin SDK başarıyla başlatıldı")
except Exception as e:
    print(f"Firebase Admin SDK başlatma hatası: {str(e)}")

# Firebase configuration for client-side
firebase_config = {
    "apiKey": os.getenv('FIREBASE_API_KEY'),
    "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
    "projectId": os.getenv('FIREBASE_PROJECT_ID'),
    "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    "appId": os.getenv('FIREBASE_APP_ID'),
    "measurementId": os.getenv('FIREBASE_MEASUREMENT_ID'),
    "databaseURL": os.getenv('FIREBASE_DATABASE_URL')
}

db = firestore.client()
rtdb = admin_db.reference()
bucket = storage.bucket()

@app.route('/')
def home():
    return render_template('index.html', firebase_config=firebase_config)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_phone(phone):
    phone = re.sub(r'[\s-]', '', phone)
    if phone.startswith('+90'):
        phone = phone[3:]
    if phone.startswith('0'):
        phone = phone[1:]
    if re.match(r'^5[0-9]{9}$', phone):
        return f"0{phone[:3]}-{phone[3:6]}-{phone[6:8]}-{phone[8:]}"
    return None

@app.route('/randevu', methods=['GET', 'POST'])
def randevu():
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            date = request.form['date']
            time = request.form['time']
            reason = request.form['reason']
            
            print(f"Form verileri alındı: {name}, {email}, {phone}, {date}, {time}, {reason}")
            
            # Telefon numarasını doğrula
            formatted_phone = validate_phone(phone)
            if not formatted_phone:
                flash('Geçersiz telefon numarası formatı. Lütfen geçerli bir telefon numarası girin.', 'error')
                return redirect(url_for('randevu'))
            
            # Benzersiz randevu ID'si oluştur
            appointment_id = str(uuid.uuid4())
            print(f"Oluşturulan randevu ID: {appointment_id}")
            
            # Randevu verilerini hazırla
            appointment_data = {
                'id': appointment_id,
                'userName': name,
                'userEmail': email,
                'userPhone': formatted_phone,
                'appointmentDate': date,
                'appointmentTime': time,
                'description': reason,
                'status': 'pending',
                'createdAt': int(datetime.now().timestamp()),
                'type': 'web',
                'notificationSent': False,
                'doctorId': 'default_doctor',
                'doctorName': 'Dr. Yağmur Aslan',
                'photoUrl': None
            }
            
            print(f"Hazırlanan randevu verisi: {appointment_data}")
            
            # Fotoğraf yükleme
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    unique_filename = f"{appointment_id}_{filename}"
                    
                    try:
                        # Firebase Storage'a yükle
                        blob = bucket.blob(f"patient_photos/{unique_filename}")
                        blob.upload_from_string(
                            photo.read(),
                            content_type=photo.content_type
                        )
                        
                        # Public URL al
                        blob.make_public()
                        appointment_data['photoUrl'] = blob.public_url
                        print(f"Fotoğraf yüklendi: {appointment_data['photoUrl']}")
                    except Exception as e:
                        print(f"Fotoğraf yükleme hatası: {str(e)}")
            
            try:
                # Firestore'a kaydet
                db.collection('appointments').document(appointment_id).set(appointment_data)
                print("Firestore'a kaydedildi")
                
                # Realtime Database için veriyi düzenle
                rtdb_appointment_data = {
                    'id': appointment_id,
                    'patient': {
                        'name': name,
                        'email': email,
                        'phone': formatted_phone
                    },
                    'appointment': {
                        'date': date,
                        'time': time,
                        'description': reason,
                        'status': 'pending',
                        'type': 'web'
                    },
                    'photos': {
                        'urls': [appointment_data['photoUrl']] if appointment_data['photoUrl'] else []
                    },
                    'metadata': {
                        'createdAt': int(datetime.now().timestamp()),
                        'notificationSent': False,
                        'doctorId': 'default_doctor',
                        'doctorName': 'Dr. Yağmur Aslan'
                    }
                }
                
                # Realtime Database'e kaydet
                rtdb.child('appointments').child(appointment_id).set(rtdb_appointment_data)
                print("Realtime Database'e kaydedildi")
                
                # Doktorun randevu listesine ekle
                rtdb.child('doctorAppointments').child('default_doctor').child(appointment_id).set({
                    'appointmentId': appointment_id,
                    'patientName': name,
                    'date': date,
                    'time': time,
                    'status': 'pending',
                    'hasPhotos': bool(appointment_data['photoUrl'])
                })
                print("Doktor randevu listesine eklendi")
                
                # Hastanın randevu listesine ekle
                sanitized_email = email.replace('.', '_').replace('@', '_at_')
                rtdb.child('patientAppointments').child(sanitized_email).child(appointment_id).set({
                    'appointmentId': appointment_id,
                    'date': date,
                    'time': time,
                    'status': 'pending',
                    'hasPhotos': bool(appointment_data['photoUrl'])
                })
                print("Hasta randevu listesine eklendi")
                
                # Randevuları kontrol et
                try:
                    appointments_ref = rtdb.child('appointments').get()
                    print("Mevcut randevular:", appointments_ref)
                except Exception as e:
                    print(f"Randevuları kontrol etme hatası: {str(e)}")
                
                flash('Randevunuz başarıyla oluşturuldu. En kısa sürede sizinle iletişime geçeceğiz.', 'success')
                return redirect(url_for('randevu'))
                
            except Exception as e:
                print(f"Firebase kaydetme hatası: {str(e)}")
                flash('Randevu kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.', 'error')
                return redirect(url_for('randevu'))
            
        except Exception as e:
            print(f"Genel hata: {str(e)}")
            flash('Randevu oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return redirect(url_for('randevu'))
    
    return render_template('randevu.html', firebase_config=firebase_config)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 