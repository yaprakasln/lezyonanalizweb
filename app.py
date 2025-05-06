from flask import Flask, render_template, request, redirect, url_for, flash, session
from firebase_admin import credentials, initialize_app, firestore, db as admin_db
import os
from datetime import datetime
from dotenv import load_dotenv
import uuid
import base64
from werkzeug.utils import secure_filename
import re
import json

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

# Load language files
with open('translations/tr.json', 'r', encoding='utf-8') as f:
    tr_translations = json.load(f)
with open('translations/en.json', 'r', encoding='utf-8') as f:
    en_translations = json.load(f)

def get_translations(lang):
    return en_translations if lang == 'en' else tr_translations

@app.before_request
def before_request():
    # URL'den dil parametresini al
    lang = request.args.get('lang', None)
    if lang in ['en', 'tr']:
        session['lang'] = lang
    elif 'lang' not in session:
        session['lang'] = 'tr'  # Varsayılan dil

@app.route('/')
def home():
    translations = get_translations(session.get('lang', 'tr'))
    return render_template('index.html', lang=session.get('lang', 'tr'), t=translations)

@app.route('/hakkimizda')
def about():
    return render_template('hakkimizda.html')

@app.route('/iletisim')
def contact():
    return render_template('iletisim.html')

@app.route('/blog')
def blog():
    translations = get_translations(session.get('lang', 'tr'))
    return render_template('blog.html', t=translations)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_phone(phone):
    # Telefon numarası formatını kontrol et
    phone = re.sub(r'\D', '', phone)  # Sadece rakamları al
    if len(phone) == 10 and phone.startswith(('5')):
        return f"0{phone}"
    elif len(phone) == 11 and phone.startswith('05'):
        return phone
    return None

@app.route('/randevu', methods=['GET', 'POST'])
def randevu():
    translations = get_translations(session.get('lang', 'tr'))
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
                flash(translations.get('invalid_phone', 'Geçersiz telefon numarası formatı.'), 'error')
                return redirect(url_for('randevu'))
            
            # Benzersiz randevu ID'si oluştur
            appointment_id = str(uuid.uuid4())
            
            # Fotoğraf işleme
            photo_base64 = None
            has_photos = False
            
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo.filename != '':
                    # Dosya boyutu kontrolü (5MB)
                    if len(photo.read()) > 5 * 1024 * 1024:
                        flash(translations.get('file_too_large', 'Dosya boyutu çok büyük. Maksimum 5MB boyutunda dosya yükleyebilirsiniz.'), 'error')
                        return redirect(url_for('randevu'))
                    photo.seek(0)
                    
                    # Dosya formatı kontrolü
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if '.' in photo.filename and photo.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        photo_base64 = base64.b64encode(photo.read()).decode('utf-8')
                        has_photos = True
                    else:
                        flash(translations.get('invalid_file_format', 'Desteklenmeyen dosya formatı. Lütfen PNG, JPG, JPEG veya GIF formatında bir dosya yükleyin.'), 'error')
                        return redirect(url_for('randevu'))
                    
            current_timestamp = datetime.now().timestamp()
            
            appointment_data = {
                'id': appointment_id,
                'appointmentDate': date,
                'appointmentTime': time,
                'hasPhotos': has_photos,
                'status': 0,
                'photos': [photo_base64] if has_photos else [],
                'notes': reason,
                'userName': name,
                'userEmail': email,
                'userPhone': formatted_phone,
                'timestamp': -current_timestamp,
                'createdAt': -current_timestamp,
                'doctorId': 'default_doctor',
                'doctorName': 'Dr. Yağmur Aslan',
                'type': 'web',
                'photoUrl': photo_base64 if has_photos else ""
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
                
                flash(translations.get('appointment_success', 'Randevunuz başarıyla oluşturuldu.'), 'success')
                return redirect(url_for('randevu'))
                
            except Exception as db_error:
                print(f"Veritabanı hatası: {str(db_error)}")
                flash(translations.get('db_error', 'Randevu kaydedilirken bir hata oluştu.'), 'error')
                return redirect(url_for('randevu'))
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            flash(translations.get('general_error', 'Randevu oluşturulurken bir hata oluştu.'), 'error')
            return redirect(url_for('randevu'))
    
    return render_template('randevu.html', lang=session.get('lang', 'tr'), t=translations)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 