# automation_worker.py
import sqlite3, json
from datetime import datetime
from main import DB, generate_ai_reply  # reuse

def db_conn():
  conn = sqlite3.connect(DB)
  conn.row_factory = sqlite3.Row
  return conn

def apply_rules_to_ticket(cur, ticket, rules):
  for rule in rules:
    cond = json.loads(rule["condition_json"])
    action = json.loads(rule["action_json"])
    txt = (ticket["subject"] or "") + " " + (ticket.get("last_message") or "")
    if any(word.lower() in txt.lower() for word in cond.get("contains", [])):
      if "set_priority" in action:
        cur.execute(
          "UPDATE tickets SET priority=?, updated_at=? WHERE id=?",
          (action["set_priority"], datetime.utcnow(), ticket["id"])
        )

def run():
  conn = db_conn()
  cur = conn.cursor()

  # 1. get rules
  rules = cur.execute("SELECT * FROM automation_rules").fetchall()

  # 2. find tickets without AI reply yet
  tickets = cur.execute("""
    SELECT t.*, 
      (SELECT content FROM messages 
       WHERE ticket_id=t.id ORDER BY created_at DESC LIMIT 1) as last_message
    FROM tickets t
    WHERE t.status='open'
  """).fetchall()

  for t in tickets:
    # apply text-based rules
    apply_rules_to_ticket(cur, t, rules)

    # generate AI suggestion if not exists
    ai_count = cur.execute("""
      SELECT COUNT(*) as c FROM messages 
      WHERE ticket_id=? AND sender_type='ai'
    """, (t["id"],)).fetchone()["c"]

    if ai_count == 0 and t["last_message"]:
      suggestion = generate_ai_reply(t["subject"], t["last_message"])
      cur.execute("""
        INSERT INTO messages (ticket_id, sender_type, content)
        VALUES (?, 'ai', ?)
      """, (t["id"], suggestion))
      cur.execute(
        "UPDATE tickets SET updated_at=? WHERE id=?",
        (datetime.utcnow(), t["id"])
      )

  conn.commit()
  conn.close()

if __name__ == "__main__":
  run()
