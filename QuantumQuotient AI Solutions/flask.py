from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB = "support_ai.db"

def db_conn():
  conn = sqlite3.connect(DB)
  conn.row_factory = sqlite3.Row
  return conn

# --- AI stub ---
def generate_ai_reply(ticket_subject, last_message):
  # Here you would call OpenAI / any LLM
  # For demo, return static-ish text
  return f"Hi, thanks for reaching out about '{ticket_subject}'. " \
         f"We're reviewing your issue and will get back shortly. " \
         f"Based on what you wrote: \"{last_message[:100]}\" ..."

# --- Helpers ---
def row_to_dict(row):
  return {k: row[k] for k in row.keys()}

# --- List tickets ---
@app.route("/api/tickets", methods=["GET"])
def list_tickets():
  conn = db_conn()
  rows = conn.execute("""
    SELECT t.*, u.name as user_name
    FROM tickets t
    JOIN users u ON u.id = t.user_id
    ORDER BY t.updated_at DESC
  """).fetchall()
  conn.close()
  return jsonify([row_to_dict(r) for r in rows])

# --- Create ticket with first message ---
@app.route("/api/tickets", methods=["POST"])
def create_ticket():
  data = request.json
  subject = data["subject"]
  content = data["content"]
  user_id = data.get("user_id", 1)  # demo user

  conn = db_conn()
  cur = conn.cursor()
  cur.execute("""
    INSERT INTO tickets (user_id, subject, status, priority)
    VALUES (?, ?, 'open', 'normal')
  """, (user_id, subject))
  ticket_id = cur.lastrowid

  cur.execute("""
    INSERT INTO messages (ticket_id, sender_type, content)
    VALUES (?, 'user', ?)
  """, (ticket_id, content))
  conn.commit()
  conn.close()

  return jsonify({"ticket_id": ticket_id}), 201

# --- Get ticket + messages ---
@app.route("/api/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
  conn = db_conn()
  ticket = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
  msgs = conn.execute("""
    SELECT * FROM messages WHERE ticket_id=? ORDER BY created_at ASC
  """, (ticket_id,)).fetchall()
  conn.close()
  return jsonify({
    "ticket": row_to_dict(ticket),
    "messages": [row_to_dict(m) for m in msgs]
  })

# --- Agent reply (approve / edit AI suggestion) ---
@app.route("/api/tickets/<int:ticket_id>/reply", methods=["POST"])
def reply_ticket(ticket_id):
  data = request.json
  content = data["content"]
  conn = db_conn()
  cur = conn.cursor()
  cur.execute("""
    INSERT INTO messages (ticket_id, sender_type, content)
    VALUES (?, 'agent', ?)
  """, (ticket_id, content))
  cur.execute("""
    UPDATE tickets SET status='pending', updated_at=? WHERE id=?
  """, (datetime.utcnow(), ticket_id))
  conn.commit()
  conn.close()
  return jsonify({"ok": True})
