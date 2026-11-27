from ui.application import render_schedule_entry, st


def render():
    st.markdown("## 📅 Entry & Monitoring Jadwal SPG (Kecamatan, Team & Tanggal)")
    render_schedule_entry()
    st.stop()
