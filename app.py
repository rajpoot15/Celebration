import sqlite3
import json
import uuid
import io
import base64
from PIL import Image
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Database Setup
def init_db():
    conn = sqlite3.connect('wishes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS wishes 
                 (id TEXT PRIMARY KEY, category TEXT, groom TEXT, bride TEXT, main_date TEXT, 
                  events_json TEXT, message TEXT, secret_msg TEXT, sender TEXT, phone TEXT, music TEXT)''')
    conn.commit()
    conn.close()

init_db()

DEFAULT_MUSIC_WEDDING = "https://cdn.pixabay.com/download/audio/2022/10/05/audio_606bbecf21.mp3?filename=shehnai-wedding-theme-121980.mp3"

def process_image(file_storage):
    try:
        if not file_storage or file_storage.filename == '':
            return ""
        img = Image.open(file_storage.stream)
        img.thumbnail((800, 800))
        buffered = io.BytesIO()
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(buffered, format="JPEG", quality=75)
        encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return ""

# 1. LANDING PAGE
PORTAL_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Celebration Portal</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Poppins:wght@300;400;600&display=swap');
        * { box-sizing: border-box; font-family: 'Poppins', sans-serif; margin: 0; padding: 0; }
        body { background: radial-gradient(circle, #2d0a12, #0f0204); min-height: 100vh; display: flex; justify-content: center; align-items: center; color: #fff; padding: 20px; }
        .portal-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 24px; padding: 35px 25px; width: 100%; max-width: 420px; text-align: center; }
        h1 { font-family: 'Cinzel', serif; color: #f3c677; font-size: 24px; margin-bottom: 8px; }
        .subtitle { color: #d4af37; font-size: 13px; margin-bottom: 30px; }
        .category-card { background: linear-gradient(135deg, rgba(128, 14, 19, 0.8), rgba(74, 3, 6, 0.9)); border: 1px solid #d4af37; border-radius: 16px; padding: 18px; text-decoration: none; color: #fff; display: flex; align-items: center; gap: 15px; text-align: left; }
        .icon-box { font-size: 28px; background: rgba(212, 175, 55, 0.15); width: 50px; height: 50px; border-radius: 12px; display: flex; justify-content: center; align-items: center; border: 1px solid #d4af37; }
        .card-info h3 { font-family: 'Cinzel', serif; color: #f3c677; font-size: 16px; }
        .card-info p { font-size: 11px; color: #e2d1c3; }
    </style>
</head>
<body>
<div class="portal-card">
    <h1>Create Web Invite</h1>
    <p class="subtitle">Select a category to start designing</p>
    <a href="/create/wedding" class="category-card">
        <div class="icon-box">💍</div>
        <div class="card-info">
            <h3>Shadi Invitation</h3>
            <p>Haldi, Mehndi, Phere & RSVP Details</p>
        </div>
    </a>
</div>
</body>
</html>
'''

# 2. WEDDING FORM PAGE
FORM_WEDDING_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Wedding Invitation</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body { background: #1a0508; min-height: 100vh; margin: 0; padding: 15px; color: #fff; }
        .form-card { background: #2d0a12; border: 1px solid #d4af37; border-radius: 16px; padding: 25px; max-width: 500px; margin: auto; }
        h2 { text-align: center; color: #f3c677; font-family: 'Georgia', serif; }
        label { font-size: 13px; margin-top: 14px; display: block; color: #e2d1c3; }
        input, textarea { width: 100%; padding: 11px; margin-top: 5px; background: rgba(0,0,0,0.4); border: 1px solid #800e13; border-radius: 8px; color: #fff; }
        .event-box { background: rgba(255, 255, 255, 0.04); border: 1px dashed #d4af37; border-radius: 12px; padding: 15px; margin-top: 15px; }
        .add-btn { background: transparent; border: 1px solid #d4af37; color: #f3c677; padding: 12px; border-radius: 8px; width: 100%; cursor: pointer; margin-top: 15px; }
        .btn-submit { background: linear-gradient(135deg, #d4af37, #aa7c11); color: #1a0508; padding: 15px; border-radius: 10px; border: none; font-weight: bold; width: 100%; margin-top: 25px; cursor: pointer; }
    </style>
</head>
<body>
<div class="form-card">
    <h2>Royal Wedding Details</h2>
    <form action="/save_wish" method="POST" enctype="multipart/form-data">
        <input type="hidden" name="category" value="wedding">
        <label>Bride's Name:</label><input type="text" name="bride" placeholder="e.g. Meenal" required>
        <label>Groom's Name:</label><input type="text" name="groom" placeholder="e.g. Avinash" required>
        <label>Main Wedding Date (e.g. Jul 01, 2026):</label><input type="text" name="main_date" placeholder="July 01, 2026" required>
        <label>Main Couple Cover Photo:</label><input type="file" name="cover_photo" accept="image/*" required>
        
        <div id="eventsContainer">
            <div class="event-box">
                <h4 style="color:#f3c677;">Function 1 Details</h4>
                <label>Event Name:</label><input type="text" name="ev_name[]" placeholder="e.g. Haldi / Mehndi" required>
                <label>Date & Time:</label><input type="text" name="ev_time[]" placeholder="e.g. June 30, 2026 - 11:00 AM" required>
                <label>Venue Name & Address:</label><input type="text" name="ev_venue[]" placeholder="Venue location" required>
                <label>Google Map Link:</label><input type="text" name="ev_map[]" placeholder="https://maps.google.com/...">
                <label>Event Photo:</label><input type="file" name="ev_photo_0" accept="image/*">
            </div>
        </div>
        <button type="button" class="add-btn" onclick="addEventField()">+ Add Another Function</button>
        
        <label>Custom Audio MP3 Link (Optional):</label>
        <input type="text" name="music" placeholder="Paste direct MP3 URL here (Keep empty for default Shehnai music)">

        <label>Message / Quote:</label><textarea name="message" rows="2"></textarea>
        <label>Host Name:</label><input type="text" name="sender" placeholder="e.g. Mrs & Mr Sharma" required>
        <label>WhatsApp Contact Number:</label><input type="tel" name="phone" placeholder="+91 9973234977" required>
        <button type="submit" class="btn-submit">Generate Web Invitation Link</button>
    </form>
</div>
<script>
    let eventCount = 1;
    function addEventField() {
        const container = document.getElementById('eventsContainer');
        const div = document.createElement('div');
        div.className = 'event-box';
        div.innerHTML = `
            <h4 style="color:#f3c677;">Function ${eventCount + 1} Details</h4>
            <label>Event Name:</label><input type="text" name="ev_name[]" placeholder="e.g. Phere / Reception" required>
            <label>Date & Time:</label><input type="text" name="ev_time[]" placeholder="Date and time" required>
            <label>Venue Name & Address:</label><input type="text" name="ev_venue[]" placeholder="Venue Address" required>
            <label>Google Map Link:</label><input type="text" name="ev_map[]" placeholder="https://maps.google.com/...">
            <label>Event Photo:</label><input type="file" name="ev_photo_${eventCount}" accept="image/*">
        `;
        container.appendChild(div);
        eventCount++;
    }
</script>
</body>
</html>
'''

# 3. DISPLAY WEDDING PAGE (ALL FEATURES INTEGRATED)
DISPLAY_WEDDING_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Royal Celebration Invitation</title>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Great+Vibes&family=Poppins:wght@300;400;600&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body { 
            background: #0d0103; 
            font-family: 'Poppins', sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh;
        }

        .mobile-container { 
            width: 100%; 
            max-width: 440px; 
            background: radial-gradient(circle, #2a0409 0%, #120104 100%); 
            min-height: 100vh; 
            position: relative; 
            padding-bottom: 70px; 
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.2);
            border-left: 2px solid #d4af37;
            border-right: 2px solid #d4af37;
            overflow: hidden;
            color: #fff;
        }

        .bg-pattern {
            position: absolute;
            inset: 0;
            background-image: radial-gradient(rgba(212, 175, 55, 0.15) 1px, transparent 0);
            background-size: 24px 24px;
            pointer-events: none;
        }

        .envelope-overlay { 
            position: fixed; 
            inset: 0; 
            max-width: 440px; 
            margin: auto; 
            background: linear-gradient(135deg, #4a0307, #1a0103); 
            z-index: 100; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            color: #f3c677; 
            transition: transform 0.8s ease-in-out;
            border: 3px solid #d4af37;
        }

        .seal-btn { 
            width: 90px; 
            height: 90px; 
            background: radial-gradient(circle, #f3c677, #aa7c11); 
            border-radius: 50%; 
            border: 4px solid #fff; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            font-family: 'Cinzel', serif; 
            font-weight: bold; 
            font-size: 16px; 
            color: #2a0409; 
            cursor: pointer; 
            margin-top: 25px; 
            box-shadow: 0 0 20px rgba(243, 198, 119, 0.6);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.98); box-shadow: 0 0 0 0 rgba(243, 198, 119, 0.7); }
            70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(243, 198, 119, 0); }
            100% { transform: scale(0.98); box-shadow: 0 0 0 0 rgba(243, 198, 119, 0); }
        }

        .header-section { text-align: center; padding: 40px 20px 10px 20px; position: relative; }
        .mantra { color: #d4af37; font-size: 13px; letter-spacing: 1px; margin-bottom: 10px; }
        
        .couple-title { 
            font-family: 'Great Vibes', cursive; 
            font-size: 52px; 
            color: #f3c677; 
            text-shadow: 0 0 10px rgba(243, 198, 119, 0.4);
        }

        .ampersand { font-family: 'Cinzel', serif; color: #d4af37; font-size: 24px; margin: 5px 0; }

        .save-date-card { 
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(128, 14, 19, 0.5)); 
            color: #f3c677; 
            margin: 20px; 
            padding: 15px; 
            border-radius: 12px; 
            text-align: center; 
            border: 1px solid #d4af37;
            backdrop-filter: blur(5px);
        }

        .cover-photo-box { 
            margin: 20px; 
            border: 2px solid #d4af37; 
            padding: 6px; 
            border-radius: 16px; 
            background: rgba(0,0,0,0.3);
        }
        .cover-photo-box img { width: 100%; border-radius: 10px; height: 280px; object-fit: cover; display: block; }

        .event-card { 
            background: rgba(42, 4, 9, 0.7); 
            border: 1px solid rgba(212, 175, 55, 0.4); 
            border-radius: 16px; 
            margin: 20px; 
            overflow: hidden; 
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }
        .event-card img { width: 100%; height: 180px; object-fit: cover; }
        .event-details { padding: 18px; text-align: center; }
        .event-details h3 { color: #f3c677; font-family: 'Cinzel', serif; font-size: 20px; margin-bottom: 8px; }
        .event-info { color: #e2d1c3; font-size: 13px; margin-bottom: 5px; }

        .map-btn { 
            display: inline-block; 
            margin-top: 12px; 
            background: linear-gradient(135deg, #d4af37, #aa7c11); 
            color: #120104; 
            text-decoration: none; 
            padding: 8px 20px; 
            border-radius: 20px; 
            font-size: 12px; 
            font-weight: bold;
        }

        .wa-share-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #25D366;
            color: #fff;
            padding: 12px 20px;
            border-radius: 30px;
            font-weight: bold;
            font-size: 13px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            z-index: 90;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .music-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(212, 175, 55, 0.2);
            border: 1px solid #d4af37;
            color: #f3c677;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 18px;
            cursor: pointer;
            z-index: 90;
        }

        .footer-msg { text-align: center; padding: 20px; color: #d4af37; font-style: italic; font-size: 13px; }
    </style>
</head>
<body>
<div class="mobile-container">
    <div class="bg-pattern"></div>
    
    <div class="music-toggle" onclick="toggleMusic()" id="musicBtn">🎵</div>

    <div class="envelope-overlay" id="envelope">
        <h2 style="font-family:'Cinzel', serif; letter-spacing: 2px;">ROYAL INVITATION</h2>
        <p style="font-size: 12px; margin-top: 5px; color: #e2d1c3;">Tap to open celebration</p>
        <div class="seal-btn" onclick="openEnvelope()">OPEN</div>
    </div>

    <div class="header-section">
        <div class="mantra">|| Shree Ganeshay Namah ||</div>
        <div class="couple-title">{{ wish.bride }}</div>
        <div class="ampersand">&</div>
        <div class="couple-title">{{ wish.groom }}</div>
        <div style="margin-top: 15px; font-size: 12px; color: #e2d1c3;">Warmly Invited By: <b style="color:#f3c677;">{{ wish.sender }}</b></div>
    </div>

    <div class="save-date-card">
        <div style="font-size: 10px; letter-spacing: 2px; color: #fff;">CELEBRATION COUNTDOWN</div>
        <div id="countdown" style="font-size: 18px; font-weight: bold; margin-top: 5px; color: #f3c677;">Loading...</div>
    </div>

    {% if wish.cover_photo %}
    <div class="cover-photo-box">
        <img src="{{ wish.cover_photo }}">
    </div>
    {% endif %}

    {% for event in wish.events %}
    <div class="event-card">
        {% if event.photo %}<img src="{{ event.photo }}">{% endif %}
        <div class="event-details">
            <h3>{{ event.name }}</h3>
            <div class="event-info">📅 {{ event.time }}</div>
            <div class="event-info">📍 {{ event.venue }}</div>
            {% if event.map %}<a href="{{ event.map }}" target="_blank" class="map-btn">GET LOCATION</a>{% endif %}
        </div>
    </div>
    {% endfor %}

    {% if wish.message %}
    <div class="footer-msg">"{{ wish.message }}"</div>
    {% endif %}

    <a href="https://api.whatsapp.com/send?text=You%20are%20cordially%20invited%20to%20our%20wedding!%20Check%20the%20invitation%20here:%20" 
       target="_blank" class="wa-share-btn">
       💬 Share Invite
    </a>
</div>

<audio id="bgMusic" src="{{ wish.music }}" loop></audio>

<script>
    function openEnvelope() {
        document.getElementById('envelope').style.transform = 'translateY(-100%)';
        var music = document.getElementById('bgMusic');
        if(music) { music.play().catch(function(e){ console.log(e); }); }
        
        // Flower / Celebration Shower
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }

    var isPlaying = true;
    function toggleMusic() {
        var music = document.getElementById('bgMusic');
        var btn = document.getElementById('musicBtn');
        if (isPlaying) {
            music.pause();
            btn.innerHTML = '🔇';
        } else {
            music.play();
            btn.innerHTML = '🎵';
        }
        isPlaying = !isPlaying;
    }

    // Dynamic Countdown Timer Setup
    var eventDate = new Date("{{ wish.main_date }}").getTime();
    var x = setInterval(function() {
        var now = new Date().getTime();
        var distance = eventDate - now;
        if (isNaN(distance) || distance < 0) {
            document.getElementById("countdown").innerHTML = "{{ wish.main_date }}";
            clearInterval(x);
            return;
        }
        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        document.getElementById("countdown").innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s ";
    }, 1000);
</script>
</body>
</html>
'''

# ROUTES
@app.route('/')
def portal():
    return render_template_string(PORTAL_HTML)

@app.route('/create/wedding')
def create_wedding():
    return render_template_string(FORM_WEDDING_HTML)

@app.route('/save_wish', methods=['POST'])
def save_wish():
    category = request.form.get('category')
    groom = request.form.get('groom')
    bride = request.form.get('bride', '')
    main_date = request.form.get('main_date', '')
    message = request.form.get('message', '')
    sender = request.form.get('sender')
    phone = request.form.get('phone')
    user_music = request.form.get('music', '').strip()

    music_url = user_music if user_music else DEFAULT_MUSIC_WEDDING

    cover_file = request.files.get('cover_photo')
    cover_b64 = process_image(cover_file) if cover_file else ""

    names = request.form.getlist('ev_name[]')
    times = request.form.getlist('ev_time[]')
    venues = request.form.getlist('ev_venue[]')
    maps = request.form.getlist('ev_map[]')

    events_list = []
    for idx, name in enumerate(names):
        photo_file = request.files.get(f'ev_photo_{idx}')
        photo_b64 = process_image(photo_file) if photo_file else ""
        events_list.append({
            'name': name,
            'time': times[idx] if idx < len(times) else '',
            'venue': venues[idx] if idx < len(venues) else '',
            'map': maps[idx] if idx < len(maps) else '',
            'photo': photo_b64
        })

    wish_id = str(uuid.uuid4())[:6]
    
    conn = sqlite3.connect('wishes.db')
    c = conn.cursor()
    c.execute("INSERT INTO wishes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (wish_id, category, groom, bride, main_date, json.dumps(events_list), message, cover_b64, sender, phone, music_url))
    conn.commit()
    conn.close()

    link = f"http://127.0.0.1:8080/w/{wish_id}"
    return f'''
    <div style="background:#1a0508; color:#f3c677; text-align:center; padding:50px 20px; font-family:sans-serif; 
