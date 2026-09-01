"""
Yörünge MVP — TeknoChallenge demo uygulaması
Çalıştırmak için: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import date
import db

st.set_page_config(page_title="Yörünge", page_icon="🛰️", layout="wide")

db.init_db()
db.seed_demo_data()

# ---------------- LOGO ----------------
LOGO_SVG = """
<div style="display:flex;align-items:center;gap:4px;margin-bottom:1.2rem">
<svg width="150" height="46" viewBox="0 0 200 100">
<g transform="rotate(-6 100 50)">
<ellipse cx="100" cy="50" rx="95" ry="17" fill="none" stroke="#A9AFBD" stroke-width="3"/>
<circle cx="191" cy="56" r="5" fill="#2F6FE0"/>
</g>
<text x="100" y="62" text-anchor="middle" font-size="40" font-weight="600" font-family="sans-serif" fill="#2F6FE0">Yörünge</text>
</svg>
</div>
"""
st.sidebar.markdown(LOGO_SVG, unsafe_allow_html=True)
st.sidebar.caption("Tanı sonrası tedavi sürecini dijitalleştiren platform")

role = st.sidebar.radio("Görünüm seçin", ["Hasta", "Doktor", "Hastane Yönetimi"])

patients = db.get_patients()
doctors = db.get_doctors()
patient_options = {p["name"]: p["id"] for p in patients}
doctor_options = {d["name"]: d["id"] for d in doctors}

TODAY = date.today()


# =========================================================
# HASTA GÖRÜNÜMÜ
# =========================================================
if role == "Hasta":
    st.title("☀️ Günaydın")

    if not patient_options:
        st.info("Sistemde kayıtlı hasta yok.")
    else:
        selected_name = st.selectbox("Hasta profili", list(patient_options.keys()))
        patient_id = patient_options[selected_name]
        patient = db.get_patient(patient_id)

        st.subheader("Bugün kendinizi nasıl hissediyorsunuz?")
        with st.form("checkin_form"):
            col1, col2, col3 = st.columns(3)
            mood = None
            with col1:
                if st.form_submit_button("🙂 İyi"):
                    mood = "İyi"
            with col2:
                if st.form_submit_button("😐 Orta"):
                    mood = "Orta"
            with col3:
                if st.form_submit_button("😣 Kötü"):
                    mood = "Kötü"

            pain = st.slider("Ağrı şiddeti (0: ağrı yok — 10: dayanılmaz)", 0, 10, 3)
            checkin_submit = st.form_submit_button("Bugünkü durumu kaydet")
            if checkin_submit or mood:
                db.add_checkin(patient_id, TODAY.isoformat(), mood or "Belirtilmedi", pain)
                st.success("Kaydedildi, doktorunuz görebilecek.")
                st.rerun()

        # Tedavi özeti
        st.markdown(
            f"""<div style='background:#EAF1FE;border-radius:10px;padding:14px;margin:10px 0'>
            <b>Tedavi özetiniz</b><br>
            {patient['diagnosis']} · {patient['treatment_stage']}<br>
            </div>""",
            unsafe_allow_html=True,
        )

        # Hatırlatmalar
        col1, col2 = st.columns(2)
        with col1:
            st.info("💊 **İlaç hatırlatması**\n\nBugünkü dozunuzu almayı unutmayın.")
        with col2:
            st.info("🩸 **Tahlil hatırlatması**\n\nBu hafta bir kan tahlili yaptırmanız önerilir.")

        st.divider()

        # Online görüşme talebi
        st.subheader("📹 Online görüşme talebi oluştur")
        with st.form("meeting_request"):
            doctor_name = st.selectbox("Doktor seçin", list(doctor_options.keys()))
            req_date = st.date_input("Tarih", value=TODAY)
            req_time = st.time_input("Saat")
            submit_req = st.form_submit_button("Talebi gönder")
            if submit_req:
                db.add_appointment(patient_id, doctor_options[doctor_name], req_date.isoformat(), str(req_time), "hasta")
                st.success("Talebiniz gönderildi, doktorunuzun onayı bekleniyor.")
                st.rerun()

        st.subheader("Randevularınız")
        appts = db.get_appointments(patient_id=patient_id)
        for a in appts:
            status_color = {"Onaylandı": "green", "Onay bekliyor": "orange", "Yeni tarih önerildi": "blue"}.get(a["status"], "gray")
            st.markdown(f"- **{a['doctor_name']}** — {a['date']} {a['time'] or ''} · :{status_color}[{a['status']}]" +
                        (f" (önerilen yeni tarih: {a['proposed_date']} {a['proposed_time']})" if a["status"] == "Yeni tarih önerildi" else ""))

        st.divider()

        # Doktor özeti
        st.subheader("Doktorunuz")
        for d in doctors[:1]:
            with st.expander(f"{d['name']} — özet için tıklayın"):
                notes = db.get_doctor_notes(patient_id)
                if notes:
                    last = notes[0]
                    st.write(f"**Uzmanlık:** {d['specialty']}")
                    st.write(f"**Son not:** {last['note_text']}")
                    if last["prescription"]:
                        st.write(f"**Reçete:** {last['prescription']}")
                else:
                    st.caption("Henüz not girilmemiş.")


# =========================================================
# DOKTOR GÖRÜNÜMÜ
# =========================================================
elif role == "Doktor":
    st.title("☀️ Merhaba, Dr. Elif Karaca")

    appts_all = db.get_appointments()
    today_appts = [a for a in appts_all if a["date"] == TODAY.isoformat()]
    pending_appts = [a for a in appts_all if a["status"] == "Onay bekliyor"]

    urgent_patients = []
    for p in patients:
        lab_rows = db.get_lab_results(p["id"])
        flag_text, flag_color = db.compute_risk_flag(lab_rows)
        if flag_color == "red":
            urgent_patients.append((p, flag_text))

    col1, col2, col3 = st.columns(3)
    col1.metric("Bugün randevu", len(today_appts))
    col2.metric("Acil bildirim", len(urgent_patients))
    col3.metric("Onay bekleyen", len(pending_appts))

    if urgent_patients:
        st.error("⚠️ **Acil bildirimler — önce bunlara bakın**\n\n" +
                  "\n".join([f"- {p['name']} — {flag}" for p, flag in urgent_patients]))

    tab1, tab2, tab3 = st.tabs(["Randevularım", "Tahlil sonuçları", "Hasta mesajları"])

    with tab1:
        for a in appts_all:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{a['patient_name']}** — {a['date']} {a['time'] or ''} · {a['status']}")
                if a["status"] == "Onay bekliyor":
                    with c2:
                        if st.button("Onayla", key=f"appr_{a['id']}"):
                            db.approve_appointment(a["id"])
                            st.rerun()
                    with st.expander("Yeni tarih öner"):
                        with st.form(f"newdate_{a['id']}"):
                            nd = st.date_input("Yeni tarih", value=TODAY, key=f"nd_{a['id']}")
                            nt = st.time_input("Yeni saat", key=f"nt_{a['id']}")
                            if st.form_submit_button("Öneriyi gönder"):
                                db.propose_new_date(a["id"], nd.isoformat(), str(nt))
                                st.rerun()

    with tab2:
        for p in patients:
            lab_rows = db.get_lab_results(p["id"])
            if lab_rows:
                st.write(f"**{p['name']}** — son tahlil: {lab_rows[-1]['test_name']} = {lab_rows[-1]['value']} {lab_rows[-1]['unit']} ({lab_rows[-1]['date']})")

    with tab3:
        for p in patients:
            msgs = db.get_messages(p["id"])
            for m in msgs:
                if m["sender"] == "patient":
                    st.write(f"**{p['name']}:** {m['text']} _({m['date']})_")

    st.divider()
    st.subheader("Hasta detayı")
    selected_name = st.selectbox("Hasta seçin", list(patient_options.keys()))
    patient_id = patient_options[selected_name]
    patient = db.get_patient(patient_id)
    lab_rows = db.get_lab_results(patient_id)
    flag_text, flag_color = db.compute_risk_flag(lab_rows)

    st.markdown(f"**{patient['name']}** · {patient['age']} yaş · {patient['diagnosis']} · :{flag_color}[{flag_text}]")

    if lab_rows:
        df = pd.DataFrame([dict(r) for r in lab_rows])
        st.line_chart(df.set_index("date")["value"])

    with st.container(border=True):
        st.write("✨ **AI Özeti**")
        st.write(db.generate_ai_summary(patient_id))

    with st.expander("💬 Meslektaşından görüş al"):
        with st.form("consult_form"):
            other_doctors = {name: did for name, did in doctor_options.items() if did != 1}
            target = st.selectbox("Doktor", list(other_doctors.keys()) or list(doctor_options.keys()))
            consult_note = st.text_area("Kısa not")
            if st.form_submit_button("Danışma isteği gönder"):
                db.add_consult_request(patient_id, 1, doctor_options[target], consult_note, TODAY.isoformat())
                st.success("Danışma isteği gönderildi.")

    st.subheader("Değerlendirme / Not Ekle")
    with st.form("new_note"):
        note_text = st.text_area("Değerlendirme notu")
        prescription = st.text_input("Reçete / İlaç")
        next_appt = st.date_input("Sonraki Randevu", value=TODAY)
        if st.form_submit_button("Kaydet"):
            db.add_doctor_note(patient_id, 1, TODAY.isoformat(), note_text, prescription, next_appt.isoformat())
            st.success("Not kaydedildi, hasta bildirim alacak.")
            st.rerun()

    st.subheader("Geçmiş Notlar")
    for n in db.get_doctor_notes(patient_id):
        with st.container(border=True):
            st.caption(f"{n['date']} · {n['doctor_name']}")
            st.write(n["note_text"])
            if n["prescription"]:
                st.markdown(f"💊 **Reçete:** {n['prescription']}")


# =========================================================
# HASTANE YÖNETİMİ
# =========================================================
else:
    st.title("Hastane Yönetim Paneli")
    st.caption("Pilot veri toplandıkça bu metrikler otomatik güncellenecek")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Azalan yüz yüze ziyaret", "—", help="Pilot sonrası hesaplanacak")
    col2.metric("Tasarruf edilen zaman", "—", help="Pilot sonrası hesaplanacak")
    col3.metric("Maliyet tasarrufu", "—", help="Pilot sonrası hesaplanacak")
    col4.metric("Verimlilik skoru", "—", help="Pilot sonrası hesaplanacak")

    st.info("Doktor başına yönetilen hasta sayısı grafiği, pilot verisi toplandıkça burada oluşacak.")
