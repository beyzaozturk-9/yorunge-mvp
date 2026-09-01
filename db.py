"""
Yörünge MVP - Veritabanı katmanı
Hastalık-agnostik çekirdek şema + onkolojiye özel alanlar
"""
import sqlite3
from datetime import date, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "yorunge.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            diagnosis TEXT,
            diagnosis_date TEXT,
            treatment_stage TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT
        );

        CREATE TABLE IF NOT EXISTS lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            test_name TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS doctor_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            note_text TEXT,
            prescription TEXT,
            next_appointment TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            status TEXT DEFAULT 'Planlandı',
            requested_by TEXT DEFAULT 'doktor',
            proposed_date TEXT,
            proposed_time TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );

        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            mood TEXT,
            pain_level INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );

        CREATE TABLE IF NOT EXISTS consult_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            requesting_doctor_id INTEGER NOT NULL,
            target_doctor_id INTEGER NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        """
    )
    conn.commit()
    conn.close()


def seed_demo_data():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM patients")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    cur.execute("INSERT INTO doctors (name, specialty) VALUES (?, ?)", ("Dr. Elif Karaca", "Onkoloji"))
    doc1 = cur.lastrowid
    cur.execute("INSERT INTO doctors (name, specialty) VALUES (?, ?)", ("Dr. Burak Sönmez", "Radyoloji"))
    cur.execute("INSERT INTO doctors (name, specialty) VALUES (?, ?)", ("Dr. Selin Aydın", "Genel Cerrahi"))

    cur.execute(
        "INSERT INTO patients (name, age, diagnosis, diagnosis_date, treatment_stage, notes) VALUES (?, ?, ?, ?, ?, ?)",
        ("Ayşe Yılmaz", 54, "Meme Kanseri (Evre 2)", "2026-03-10", "Kemoterapi 3. döngü", ""),
    )
    p1 = cur.lastrowid
    cur.execute(
        "INSERT INTO patients (name, age, diagnosis, diagnosis_date, treatment_stage, notes) VALUES (?, ?, ?, ?, ?, ?)",
        ("Mehmet Demir", 61, "Kolon Kanseri (Evre 1)", "2026-01-15", "Takip döneminde", ""),
    )
    p2 = cur.lastrowid

    today = date.today()
    for d, v in [
        (today - timedelta(days=60), 12.5), (today - timedelta(days=45), 15.1),
        (today - timedelta(days=30), 18.7), (today - timedelta(days=15), 24.3),
        (today, 27.9),
    ]:
        cur.execute(
            "INSERT INTO lab_results (patient_id, date, test_name, value, unit) VALUES (?, ?, ?, ?, ?)",
            (p1, d.isoformat(), "Tümör markırı (CA 15-3)", v, "U/mL"),
        )
    for d, v in [(today - timedelta(days=40), 3.1), (today - timedelta(days=10), 3.2)]:
        cur.execute(
            "INSERT INTO lab_results (patient_id, date, test_name, value, unit) VALUES (?, ?, ?, ?, ?)",
            (p2, d.isoformat(), "Tümör markırı (CEA)", v, "ng/mL"),
        )

    cur.execute(
        """INSERT INTO doctor_notes (patient_id, doctor_id, date, note_text, prescription, next_appointment)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (p1, doc1, (today - timedelta(days=15)).isoformat(),
         "Marker değerinde artış gözlendi, tedavi protokolü gözden geçirilecek.",
         "Tamoksifen 20mg - günde 1 tablet", (today + timedelta(days=10)).isoformat()),
    )
    cur.execute(
        """INSERT INTO doctor_notes (patient_id, doctor_id, date, note_text, prescription, next_appointment)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (p2, doc1, (today - timedelta(days=10)).isoformat(),
         "İyi seyrediyor, mevcut protokole devam.", "", (today + timedelta(days=30)).isoformat()),
    )

    cur.execute(
        "INSERT INTO appointments (patient_id, doctor_id, date, time, status, requested_by) VALUES (?, ?, ?, ?, ?, ?)",
        (p1, doc1, (today + timedelta(days=10)).isoformat(), "10:00", "Onay bekliyor", "hasta"),
    )
    cur.execute(
        "INSERT INTO appointments (patient_id, doctor_id, date, time, status, requested_by) VALUES (?, ?, ?, ?, ?, ?)",
        (p2, doc1, today.isoformat(), "14:00", "Planlandı", "doktor"),
    )

    cur.execute(
        "INSERT INTO checkins (patient_id, date, mood, pain_level) VALUES (?, ?, ?, ?)",
        (p1, (today - timedelta(days=1)).isoformat(), "Orta", 6),
    )
    cur.execute(
        "INSERT INTO checkins (patient_id, date, mood, pain_level) VALUES (?, ?, ?, ?)",
        (p1, (today - timedelta(days=8)).isoformat(), "İyi", 3),
    )

    cur.execute(
        "INSERT INTO messages (patient_id, doctor_id, sender, text, date) VALUES (?, ?, ?, ?, ?)",
        (p2, doc1, "patient", "Ağrı kesici dozunu artırabilir miyim?", (today - timedelta(days=1)).isoformat()),
    )

    conn.commit()
    conn.close()


# ---- Genel yardımcılar ----

def get_patients():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM patients ORDER BY name").fetchall()
    conn.close()
    return rows


def get_patient(patient_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return row


def get_doctors():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM doctors ORDER BY name").fetchall()
    conn.close()
    return rows


def add_patient(name, age, diagnosis, diagnosis_date, treatment_stage="", notes=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO patients (name, age, diagnosis, diagnosis_date, treatment_stage, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (name, age, diagnosis, diagnosis_date, treatment_stage, notes),
    )
    conn.commit()
    conn.close()


# ---- Tahlil ----

def add_lab_result(patient_id, date_str, test_name, value, unit):
    conn = get_connection()
    conn.execute(
        "INSERT INTO lab_results (patient_id, date, test_name, value, unit) VALUES (?, ?, ?, ?, ?)",
        (patient_id, date_str, test_name, value, unit),
    )
    conn.commit()
    conn.close()


def get_lab_results(patient_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM lab_results WHERE patient_id = ? ORDER BY date", (patient_id,)).fetchall()
    conn.close()
    return rows


def compute_risk_flag(lab_rows, rise_threshold_pct=20):
    if len(lab_rows) < 2:
        return "Yeterli veri yok", "gray"
    last, prev = lab_rows[-1]["value"], lab_rows[-2]["value"]
    if prev == 0:
        return "Yeterli veri yok", "gray"
    change_pct = ((last - prev) / prev) * 100
    if change_pct >= rise_threshold_pct:
        return f"Takip Gerekli (+%{change_pct:.1f})", "red"
    elif change_pct <= -rise_threshold_pct:
        return f"İyileşme Trendi (%{change_pct:.1f})", "green"
    else:
        return f"Stabil (%{change_pct:+.1f})", "blue"


# ---- Doktor notu ----

def add_doctor_note(patient_id, doctor_id, date_str, note_text, prescription, next_appointment):
    conn = get_connection()
    conn.execute(
        """INSERT INTO doctor_notes (patient_id, doctor_id, date, note_text, prescription, next_appointment)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (patient_id, doctor_id, date_str, note_text, prescription, next_appointment),
    )
    conn.commit()
    conn.close()


def get_doctor_notes(patient_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT dn.*, d.name as doctor_name FROM doctor_notes dn
           JOIN doctors d ON dn.doctor_id = d.id
           WHERE dn.patient_id = ? ORDER BY dn.date DESC""",
        (patient_id,),
    ).fetchall()
    conn.close()
    return rows


# ---- Check-in (ruh hali / ağrı) ----

def add_checkin(patient_id, date_str, mood, pain_level):
    conn = get_connection()
    conn.execute(
        "INSERT INTO checkins (patient_id, date, mood, pain_level) VALUES (?, ?, ?, ?)",
        (patient_id, date_str, mood, pain_level),
    )
    conn.commit()
    conn.close()


def get_checkins(patient_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM checkins WHERE patient_id = ? ORDER BY date", (patient_id,)).fetchall()
    conn.close()
    return rows


# ---- Randevu / online görüşme talebi ----

def add_appointment(patient_id, doctor_id, date_str, time_str, requested_by):
    conn = get_connection()
    conn.execute(
        "INSERT INTO appointments (patient_id, doctor_id, date, time, status, requested_by) VALUES (?, ?, ?, ?, 'Onay bekliyor', ?)",
        (patient_id, doctor_id, date_str, time_str, requested_by),
    )
    conn.commit()
    conn.close()


def get_appointments(patient_id=None, doctor_id=None):
    conn = get_connection()
    if patient_id:
        rows = conn.execute(
            """SELECT a.*, d.name as doctor_name FROM appointments a
               JOIN doctors d ON a.doctor_id = d.id
               WHERE a.patient_id = ? ORDER BY a.date""", (patient_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT a.*, p.name as patient_name FROM appointments a
               JOIN patients p ON a.patient_id = p.id
               ORDER BY a.date"""
        ).fetchall()
    conn.close()
    return rows


def approve_appointment(appointment_id):
    conn = get_connection()
    conn.execute("UPDATE appointments SET status = 'Onaylandı' WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()


def propose_new_date(appointment_id, new_date, new_time):
    conn = get_connection()
    conn.execute(
        "UPDATE appointments SET status = 'Yeni tarih önerildi', proposed_date = ?, proposed_time = ? WHERE id = ?",
        (new_date, new_time, appointment_id),
    )
    conn.commit()
    conn.close()


# ---- Mesajlar ----

def add_message(patient_id, doctor_id, sender, text, date_str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (patient_id, doctor_id, sender, text, date) VALUES (?, ?, ?, ?, ?)",
        (patient_id, doctor_id, sender, text, date_str),
    )
    conn.commit()
    conn.close()


def get_messages(patient_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM messages WHERE patient_id = ? ORDER BY date DESC", (patient_id,)).fetchall()
    conn.close()
    return rows


# ---- Meslektaş danışma ----

def add_consult_request(patient_id, requesting_doctor_id, target_doctor_id, note, date_str):
    conn = get_connection()
    conn.execute(
        """INSERT INTO consult_requests (patient_id, requesting_doctor_id, target_doctor_id, note, date)
           VALUES (?, ?, ?, ?, ?)""",
        (patient_id, requesting_doctor_id, target_doctor_id, note, date_str),
    )
    conn.commit()
    conn.close()


def get_consult_requests(patient_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT cr.*, d.name as target_doctor_name FROM consult_requests cr
           JOIN doctors d ON cr.target_doctor_id = d.id
           WHERE cr.patient_id = ? ORDER BY cr.date DESC""", (patient_id,)
    ).fetchall()
    conn.close()
    return rows


# ---- AI destekli özet (kural tabanlı basit sürüm) ----

def generate_ai_summary(patient_id):
    """
    Basit, kural tabanlı özet üretici — gerçek uygulamada bu fonksiyon
    Anthropic API'ye (Claude) hastanın notlarını/tahlillerini/mesajlarını
    gönderip 2-3 cümlelik bir özet üretecek şekilde genişletilebilir.
    Şimdilik API anahtarı gerektirmeyen, deterministik bir versiyon.
    """
    lab_rows = get_lab_results(patient_id)
    checkins = get_checkins(patient_id)
    messages = get_messages(patient_id)

    parts = []

    flag_text, _ = compute_risk_flag(lab_rows)
    if "Takip Gerekli" in flag_text:
        parts.append("Son tahlil değeri belirgin bir artış gösteriyor")
    elif "İyileşme" in flag_text:
        parts.append("Son tahlil değerlerinde olumlu bir gerileme var")
    elif "Stabil" in flag_text:
        parts.append("Tahlil değerleri stabil seyrediyor")

    if len(checkins) >= 2:
        pains = [c["pain_level"] for c in checkins if c["pain_level"] is not None]
        if len(pains) >= 2 and pains[-1] > pains[0]:
            parts.append(f"hasta son check-in'lerde ağrı puanını {pains[0]}'dan {pains[-1]}'e yükseltiyor")

    if messages:
        parts.append(f"hastadan {len(messages)} okunmamış mesaj var, son mesaj: \"{messages[0]['text']}\"")

    if not parts:
        return "Henüz yeterli veri yok, ilk değerlendirme sonrası özet oluşacak."

    summary = ", ".join(parts) + ". Öncelikli değerlendirme önerilir." if len(parts) > 1 else parts[0] + "."
    return summary[0].upper() + summary[1:]
