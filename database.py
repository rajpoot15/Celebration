import sqlite3

def init_db():
    conn = sqlite3.connect('wishes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS wishes 
                 (id TEXT PRIMARY KEY, category TEXT, groom TEXT, bride TEXT, main_date TEXT, 
                  events_json TEXT, message TEXT, secret_msg TEXT, sender TEXT, phone TEXT, music TEXT)''')
    conn.commit()
    conn.close()

def save_invitation(wish_id, category, groom, bride, main_date, events_json, message, cover_b64, sender, phone, music):
    conn = sqlite3.connect('wishes.db')
    c = conn.cursor()
    c.execute("INSERT INTO wishes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (wish_id, category, groom, bride, main_date, events_json, message, cover_b64, sender, phone, music))
    conn.commit()
    conn.close()

def get_invitation(wish_id):
    conn = sqlite3.connect('wishes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM wishes WHERE id=?", (wish_id,))
    row = c.fetchone()
    conn.close()
    return row
  
