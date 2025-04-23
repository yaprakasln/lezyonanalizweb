from flask import Flask, render_template, request, redirect, url_for, flash
from firebase_admin import credentials, initialize_app, firestore, db as admin_db
import os
from datetime import datetime
from dotenv import load_dotenv
import uuid
import base64
from werkzeug.utils import secure_filename
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Firebase initialization
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_app = initialize_app(cred, {
        'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
    })
    db = firestore.client()
    rtdb = admin_db.reference()
    print("Firebase bağlantısı başarılı")
except Exception as e:
    print(f"Firebase bağlantı hatası: {str(e)}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/hakkimizda')
def about():
    return render_template('hakkimizda.html')

@app.route('/iletisim')
def contact():
    return render_template('iletisim.html')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_phone(phone):
    # Telefon numarası formatını düzenle
    phone = re.sub(r'\D', '', phone)  # Sadece rakamları al
    if len(phone) == 10:  # 5XX XXX XXXX formatı
        return phone
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
            
            # Telefon numarasını formatla
            formatted_phone = validate_phone(phone)
            if not formatted_phone:
                flash('Geçersiz telefon numarası formatı.', 'error')
                return redirect(url_for('randevu'))
            
            # Benzersiz randevu ID'si oluştur
            appointment_id = str(uuid.uuid4())
            
            # Fotoğraf işleme
            photo_base64 = None
            has_photos = False
            
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                if not allowed_file(photo.filename):
                    flash('Desteklenmeyen dosya formatı. Lütfen PNG, JPG, JPEG veya GIF formatında bir dosya yükleyin.', 'error')
                    return redirect(url_for('randevu'))
                
                try:
                    # Dosya içeriğini oku ve Base64'e çevir
                    photo_content = photo.read()
                    if len(photo_content) > 5 * 1024 * 1024:  # 5MB limit
                        flash('Dosya boyutu çok büyük. Maksimum 5MB boyutunda dosya yükleyebilirsiniz.', 'error')
                        return redirect(url_for('randevu'))
                    
                    photo_base64 = base64.b64encode(photo_content).decode('utf-8')
                    has_photos = True
                    print("Fotoğraf başarıyla Base64'e çevrildi")
                    
                except Exception as e:
                    print(f"Fotoğraf işleme hatası: {str(e)}")
                    flash('Fotoğraf işlenirken bir hata oluştu. Lütfen tekrar deneyin.', 'error')
                    return redirect(url_for('randevu'))
            
            # Randevu verisi
            current_timestamp = int(datetime.now().timestamp() * 1000)
            appointment_data = {
                'id': appointment_id,
                'appointmentDate': date,
                'appointmentTime': time,
                'hasPhotos': has_photos,
                'status': 0,
                'photos': [photo_base64] if has_photos else [],  # Store raw base64 without prefix
                'notes': reason,
                'userName': name,
                'userEmail': email,
                'userPhone': formatted_phone,
                'timestamp': -current_timestamp,
                'createdAt': -current_timestamp,
                'doctorId': 'default_doctor',
                'doctorName': 'Dr. Yağmur Aslan',
                'type': 'web',
                'photoUrl': photo_base64 if has_photos else ""  # Store raw base64 without prefix
            }
            
            try:
                # Realtime Database'e kaydet
                rtdb.child('appointments').child(appointment_id).set(appointment_data)
                
                # patientAppointments altına kaydet
                patient_email_key = email.replace('@', '_').replace('.', '_')
                rtdb.child('patientAppointments').child(patient_email_key).child(appointment_id).set(appointment_data)
                
                # userAppointments altına kaydet
                rtdb.child('userAppointments').child('default_doctor').child(appointment_id).set(appointment_data)
                
                print(f"Randevu başarıyla kaydedildi: {appointment_id}")
                print(f"Fotoğraf durumu: hasPhotos={has_photos}")
                
                flash('Randevunuz başarıyla oluşturuldu.', 'success')
                return redirect(url_for('randevu'))
                
            except Exception as db_error:
                print(f"Veritabanı hatası: {str(db_error)}")
                flash('Randevu kaydedilirken bir hata oluştu.', 'error')
                return redirect(url_for('randevu'))
            
        except Exception as e:
            print(f"Genel hata: {str(e)}")
            flash('Randevu oluşturulurken bir hata oluştu.', 'error')
            return redirect(url_for('randevu'))
    
    return render_template('randevu.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001) 