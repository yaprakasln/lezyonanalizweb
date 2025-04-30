// Firebase yapılandırması
const firebaseConfig = {
    // Firebase yapılandırma bilgilerinizi buraya ekleyin
};

// Global değişkenler
const dateInput = document.querySelector('input[type="date"]');
const timeSelect = document.querySelector('select[name="time"]');

// Firebase'i başlat
firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// Mobile Menu Toggle
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const navMenu = document.querySelector('.nav-menu');

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        const spans = mobileMenuBtn.querySelectorAll('span');
        spans[0].classList.toggle('rotate-45');
        spans[1].classList.toggle('opacity-0');
        spans[2].classList.toggle('rotate-negative-45');
    });
}

// Scroll Animation
const fadeElements = document.querySelectorAll('.fade-in');

const fadeInOnScroll = () => {
    fadeElements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (elementTop < windowHeight - 100) {
            element.classList.add('visible');
        }
    });
};

window.addEventListener('scroll', fadeInOnScroll);
window.addEventListener('load', fadeInOnScroll);

// Form Submission
const appointmentForm = document.querySelector('.appointment-form');

if (appointmentForm) {
    appointmentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(appointmentForm);
        const formObject = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch('/api/appointment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formObject)
            });
            
            if (response.ok) {
                showNotification('Randevunuz başarıyla oluşturuldu!', 'success');
                appointmentForm.reset();
            } else {
                throw new Error('Randevu oluşturulurken bir hata oluştu.');
            }
        } catch (error) {
            showNotification(error.message, 'error');
        }
    });
}

// Notification System
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            
            // Close mobile menu if open
            if (navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
            }
        }
    });
});

// Time Slot Management
if (timeInput) {
    const workingHours = {
        start: 9, // 09:00
        end: 17   // 17:00
    };
    
    const interval = 30; // 30 dakikalık aralıklarla randevu
    let currentHour = workingHours.start;
    
    while (currentHour < workingHours.end) {
        const hour = Math.floor(currentHour);
        const minute = (currentHour % 1) * 60;
        
        const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        const option = document.createElement('option');
        option.value = timeString;
        option.textContent = timeString;
        
        timeInput.appendChild(option);
        
        currentHour += interval / 60;
    }
}

// Form Validation
const validateForm = (form) => {
    const inputs = form.querySelectorAll('input, select, textarea');
    let isValid = true;
    
    inputs.forEach(input => {
        if (input.hasAttribute('required') && !input.value.trim()) {
            isValid = false;
            input.classList.add('error');
        } else {
            input.classList.remove('error');
        }
        
        if (input.type === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                isValid = false;
                input.classList.add('error');
            }
        }
        
        if (input.type === 'tel') {
            const phoneRegex = /^[0-9]{10}$/;
            if (!phoneRegex.test(input.value.replace(/\D/g, ''))) {
                isValid = false;
                input.classList.add('error');
            }
        }
    });
    
    return isValid;
};

if (appointmentForm) {
    appointmentForm.addEventListener('submit', (e) => {
        if (!validateForm(appointmentForm)) {
            e.preventDefault();
            showNotification('Lütfen tüm alanları doğru şekilde doldurun.', 'error');
        }
    });
}

// Google Maps Integration
function initMap() {
    const mapElement = document.getElementById('map');
    if (mapElement) {
        const location = { lat: YOUR_LATITUDE, lng: YOUR_LONGITUDE };
        const map = new google.maps.Map(mapElement, {
            zoom: 15,
            center: location,
            styles: [
                {
                    "featureType": "all",
                    "elementType": "geometry",
                    "stylers": [{"color": "#f5f5f5"}]
                },
                {
                    "featureType": "all",
                    "elementType": "labels.text.fill",
                    "stylers": [{"color": "#616161"}]
                },
                {
                    "featureType": "all",
                    "elementType": "labels.text.stroke",
                    "stylers": [{"color": "#f5f5f5"}]
                }
            ]
        });
        
        const marker = new google.maps.Marker({
            position: location,
            map: map,
            title: 'Dr. Ayşe Yılmaz Dermatoloji Kliniği'
        });
    }
}

// Lazy Loading Images
document.addEventListener('DOMContentLoaded', () => {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// Çalışma saatleri kontrolü
function isClinicOpen() {
    const now = new Date();
    const day = now.getDay(); // 0 = Pazar, 1 = Pazartesi, ...
    const hour = now.getHours();

    // Hafta içi kontrol (Pazartesi-Cuma)
    if (day >= 1 && day <= 5) {
        return hour >= 9 && hour < 18;
    }
    // Cumartesi kontrol
    else if (day === 6) {
        return hour >= 9 && hour < 13;
    }
    // Pazar günü kapalı
    return false;
}

// Randevu saatlerini güncelle
function updateAvailableHours(selectedDate) {
    if (!dateInput || !timeSelect || !selectedDate) return;
    
    // Mevcut seçenekleri temizle
    while (timeSelect.firstChild) {
        timeSelect.removeChild(timeSelect.firstChild);
    }
    
    // Seçilen tarihe göre müsait saatleri Firebase'den çek
    const dateRef = database.ref('appointments/' + selectedDate);
    dateRef.once('value').then((snapshot) => {
        const appointments = snapshot.val() || {};
        
        // Çalışma saatlerini ayarla
        const workingHours = {
            start: 9,  // 09:00
            end: 17    // 17:00
        };
        
        const interval = 30; // 30 dakikalık aralıklar
        let currentHour = workingHours.start;
        
        while (currentHour < workingHours.end) {
            const hour = Math.floor(currentHour);
            const minute = (currentHour % 1) * 60;
            const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            
            // Bu saat dolu mu kontrol et
            if (!appointments[timeString]) {
                const option = document.createElement('option');
                option.value = timeString;
                option.textContent = timeString;
                timeSelect.appendChild(option);
            }
            
            currentHour += interval / 60;
        }
    });
}

// Event listener'ları ekle
if (dateInput) {
    dateInput.addEventListener('change', (e) => {
        const selectedDate = e.target.value;
        updateAvailableHours(selectedDate);
    });
    
    // Minimum ve maksimum tarihleri ayarla
    const today = new Date();
    const maxDate = new Date();
    maxDate.setMonth(maxDate.getMonth() + 3);
    
    dateInput.min = today.toISOString().split('T')[0];
    dateInput.max = maxDate.toISOString().split('T')[0];
} 