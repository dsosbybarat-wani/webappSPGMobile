from ui.application import st, verify_admin_password


def render():
    with st.sidebar:
        st.markdown("### 🔐 Panel Admin & Supervisor")
        st.caption("Pusat kontrol data lapangan dan konfigurasi master.")

        if not st.session_state["admin_logged_in"]:
            with st.form("form_admin_login"):
                pass_input = st.text_input("Kata Sandi Admin", type="password", placeholder="••••••••")
                btn_pass = st.form_submit_button("Masuk Dashboard Admin", use_container_width=True)

                if btn_pass:
                    if verify_admin_password(pass_input):
                        st.session_state["admin_logged_in"] = True
                        st.session_state["admin_view"] = "Dashboard"
                        st.success("✅ Berhasil masuk sebagai Admin!")
                        st.rerun()
                    else:
                        st.error("❌ Password salah!")
        else:
            st.success("🟢 :red[Mode Admin Aktif]")

            st.markdown("##### 📊 :red[Monitoring & Laporan]")
            if st.button("🏠 Dashboard Utama", use_container_width=True, type="primary" if st.session_state["admin_view"] == "Dashboard" else "secondary"):
                st.session_state["admin_view"] = "Dashboard"
                st.rerun()
            if st.button("📅 Entry & Jadwal SPG", use_container_width=True, type="primary" if st.session_state["admin_view"] == "Master_Jadwal_Excel" else "secondary"):
                st.session_state["admin_view"] = "Master_Jadwal_Excel"
                st.rerun()
            if st.button("📈 Analitik Lapangan", use_container_width=True, type="primary" if st.session_state["admin_view"] == "Analitik" else "secondary"):
                st.session_state["admin_view"] = "Analitik"
                st.rerun()
            if st.button("🗺️ Peta Rute & Poligon", use_container_width=True, type="primary" if st.session_state["admin_view"] == "Peta_Rute" else "secondary"):
                st.session_state["admin_view"] = "Peta_Rute"
                st.rerun()

            st.markdown("##### ⚙️ :red[Master Data]")
            if st.button("🔑 PIN & Hak Akses User", use_container_width=True, type="primary" if st.session_state["admin_view"] == "Master_Akses" else "secondary"):
                st.session_state["admin_view"] = "Master_Akses"
                st.rerun()
            if st.button("🏷️ Master Nama Team", use_container_width=True):
                st.session_state["admin_view"] = "Master_Nama_Team"
                st.rerun()
            if st.button("👥 Team & Alokasi Brand", use_container_width=True):
                st.session_state["admin_view"] = "Master_Team"
                st.rerun()
            if st.button("👩‍💼 Master Nama SPG", use_container_width=True):
                st.session_state["admin_view"] = "Master_SPG"
                st.rerun()
            if st.button("🚬 Merek Rokok & Target", use_container_width=True):
                st.session_state["admin_view"] = "Master_Brand"
                st.rerun()
            if st.button("💰 Harga Rokok Konsumen", use_container_width=True):
                st.session_state["admin_view"] = "Master_Harga"
                st.rerun()
            if st.button("🚗 Plat Kendaraan", use_container_width=True):
                st.session_state["admin_view"] = "Master_Plat"
                st.rerun()
            if st.button("📍 Lokasi Warkop (Excel)", use_container_width=True):
                st.session_state["admin_view"] = "Master_Lokasi"
                st.rerun()

            st.markdown("---")
            if st.button("🔒 Keluar Mode Admin", use_container_width=True):
                st.session_state["admin_logged_in"] = False
                st.query_params.clear()
                st.rerun()
