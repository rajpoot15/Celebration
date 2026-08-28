import json
import uuid
import io
import base64
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for
from database import init_db, save_invitation, get_invitation

app = Flask(__name__)
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

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/create/wedding')
def create_wedding():
    return render_template('form_wedding.html')

@app.route('/save_wish', methods=['POST'])
def save_wish():
    category = request.form.get('category')
    groom = request.form.get('groom')
    bride = request.form.get('bride', '')
    main_date = request.form.get('main_date', '')
    message = request.form.get('message', '')
    sender = request.form.get('sender')
    phone = request.form.get('phone')

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
    save_invitation(wish_id, category, groom, bride, main_date, json.dumps(events_list), message, cover_b64, sender, phone, DEFAULT_MUSIC_WEDDING)

    link = f"http://127.0.0.1:8080/w/{wish_id}"
    return f'''
    <div style="background:#1a0508; color:#f3c677; text-align:center; padding:50px 20px; font-family:sans-serif; min-height:100vh;">
        <h2>Royal Invitation Link Ready!</h2>
        <p style="color:#fff;">Share this link:</p>
        <input type="text" value="{link}" style="width:90%; max-width:400px; padding:12px; text-align:center;" readonly>
        <br><br>
        <a href="{link}" style="color:#d4af37; font-weight:bold;">Preview Invitation</a>
    </div>
    '''

@app.route('/w/<wish_id>')
def view_wish(wish_id):
    row = get_invitation(wish_id)
    if not row:
        return "Invitation Not Found", 404

    wish_data = {
        'category': row[1], 'groom': row[2], 'bride': row[3], 'main_date': row[4],
        'events': json.loads(row[5]), 'message': row[6], 'cover_photo': row[7], 'sender': row[8], 'music': row[10]
    }
    return render_template('display_wedding.html', wish=wish_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
  
