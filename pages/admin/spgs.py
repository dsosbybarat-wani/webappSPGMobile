from ui.application import load_master_spgs, save_master_spgs, st


def render():
    st.markdown("## 👩‍💼 Master Data: Nama SPG")
    st.caption("Tambah, ubah, atau hapus daftar nama SPG aktif.")

    current_spgs = load_master_spgs()

    with st.form("form_tambah_spg"):
        new_spg_name = st.text_input("Nama SPG Baru", placeholder="Contoh: Siska")
        btn_add_spg = st.form_submit_button("➕ Tambah Nama SPG")
        if btn_add_spg:
            spg_clean = new_spg_name.strip()
            if spg_clean:
                if spg_clean not in current_spgs:
                    current_spgs.append(spg_clean)
                    save_master_spgs(current_spgs)
                    st.success(f"✅ Nama SPG '{spg_clean}' berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Nama SPG tersebut sudah ada dalam daftar.")
            else:
                st.warning("Mohon masukkan nama SPG.")

    st.markdown("---")
    st.markdown("#### 📋 Daftar Nama SPG Terdaftar")
    for idx, s in enumerate(current_spgs):
        col_s1, col_s2 = st.columns([0.8, 0.2])
        with col_s1:
            st.write(f"**{idx+1}.** {s}")
        with col_s2:
            if st.button("🗑️ Hapus", key=f"del_spg_{idx}"):
                current_spgs.pop(idx)
                save_master_spgs(current_spgs)
                st.success("Nama SPG berhasil dihapus!")
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
