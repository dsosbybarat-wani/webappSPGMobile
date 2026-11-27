from ui.application import load_master_team_names, save_master_team_names, st


def render():
    st.markdown("## 🏷️ Master Data: Nama Team (1 - 20)")
    st.caption("Ubah dan sesuaikan nama alias untuk Team SPG 1 sampai 20. Perubahan akan otomatis terhubung ke menu alokasi brand dan login.")

    team_names_map = load_master_team_names()

    with st.form("form_edit_nama_team"):
        st.markdown("#### Edit Nama Team")
        updated_names = {}

        for i in range(1, 21):
            key = f"Team SPG {i}"
            current_val = team_names_map.get(key, key)
            new_val = st.text_input(f"Nama untuk `{key}`", value=current_val, key=f"input_team_name_{i}")
            updated_names[key] = new_val.strip()

        btn_save_team_names = st.form_submit_button("💾 Simpan Perubahan Nama Team", type="primary")

        if btn_save_team_names:
            if save_master_team_names(updated_names):
                st.success("✅ Perubahan nama team berhasil disimpan dan langsung terhubung ke seluruh sistem!")
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
