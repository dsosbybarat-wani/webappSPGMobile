from ui.application import load_master_plat_kendaraan, save_master_plat_kendaraan, st


def render():
    st.markdown("## 🚗 Master Data: Plat Nomor Kendaraan Operasional")
    st.caption("Tambah atau hapus daftar plat nomor kendaraan operasional secara fleksibel.")

    plat_list = load_master_plat_kendaraan()

    with st.form("form_tambah_plat"):
        st.markdown("#### Tambah Plat Nomor Kendaraan Baru")
        new_plat_input = st.text_input("Plat Nomor Kendaraan", placeholder="Contoh: L 1234 ABC")
        btn_add_plat = st.form_submit_button("➕ Tambah Plat Kendaraan")

        if btn_add_plat:
            p_clean = new_plat_input.strip().upper()
            if p_clean:
                if p_clean not in plat_list:
                    plat_list.append(p_clean)
                    save_master_plat_kendaraan(plat_list)
                    st.success(f"✅ Plat kendaraan '{p_clean}' berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Plat nomor kendaraan tersebut sudah ada dalam daftar.")
            else:
                st.warning("Mohon masukkan nomor plat kendaraan.")

    st.markdown("---")
    st.markdown("#### 📋 Daftar Plat Kendaraan Terdaftar")
    for idx, p in enumerate(plat_list):
        col_p1, col_p2 = st.columns([0.8, 0.2])
        with col_p1:
            st.write(f"**{idx+1}.** `{p}`")
        with col_p2:
            if st.button("🗑️ Hapus", key=f"del_plat_{idx}"):
                plat_list.pop(idx)
                save_master_plat_kendaraan(plat_list)
                st.success("Plat kendaraan berhasil dihapus!")
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
