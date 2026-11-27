from ui.application import st, verify_admin_password


def render():
    st.markdown(
        """
        <div class="login-header">
            <div style="font-size: 2.2rem; margin-bottom: 4px;">🔐</div>
            <h1>PORTAL ADMIN &amp; SUPERVISOR</h1>
            <p>Akses Khusus Pengelola Data Master &amp; Monitoring</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        with st.form("form_admin_portal_login"):
            admin_pass_main = st.text_input("Kata Sandi Admin", type="password", placeholder="Masukkan kata sandi admin")
            btn_admin_portal = st.form_submit_button("🔓 Masuk Halaman Admin", type="primary", use_container_width=True)
            if btn_admin_portal:
                if verify_admin_password(admin_pass_main):
                    st.session_state["admin_logged_in"] = True
                    st.session_state["admin_view"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("❌ Kata sandi admin salah!")
    st.stop()
