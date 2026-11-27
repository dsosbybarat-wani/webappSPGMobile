from ui.application import (
    get_harga_konsumen_brand,
    load_harga_konsumen,
    load_master_brands,
    load_target_rules,
    refresh_target_rules,
    save_harga_konsumen,
    save_master_brands,
    save_target_rules,
    st,
)


def render():
    st.markdown("## 💰 Master Data: Harga Rokok Konsumen")
    st.caption(
        "Tambah merk baru dan atur/edit harga jual konsumen per bungkus. "
        "Harga otomatis terhubung ke menu report untuk menghitung jumlah uang terkumpul dari penjualan 2 orang SPG hari itu."
    )

    current_brands = load_master_brands()
    harga_map = load_harga_konsumen()
    target_rules_data = load_target_rules()

    with st.form("form_tambah_merk_harga_konsumen"):
        st.markdown("#### ➕ Tambah Merk Baru & Harga Konsumen")
        col_hm1, col_hm2 = st.columns([0.6, 0.4])
        with col_hm1:
            new_merk_nama = st.text_input(
                "Nama Merk Rokok Baru",
                placeholder="Contoh: Djarum Black Tea 16",
            )
        with col_hm2:
            new_merk_harga = st.number_input(
                "Harga Konsumen per Bungkus (Rp)",
                min_value=0,
                value=20000,
                step=500,
            )
        col_ht1, col_ht2 = st.columns(2)
        with col_ht1:
            new_merk_tspg = st.number_input("Target per SPG (Bungkus)", min_value=1, value=30, step=1)
        with col_ht2:
            new_merk_tteam = st.number_input("Target per Team (Bungkus)", min_value=1, value=60, step=1)

        btn_add_merk_harga = st.form_submit_button("💾 Simpan Merk & Harga Baru", type="primary")
        if btn_add_merk_harga:
            b_clean = str(new_merk_nama or "").strip()
            if not b_clean:
                st.warning("Mohon masukkan nama merk rokok baru.")
            else:
                if not any(str(b).strip().casefold() == b_clean.casefold() for b in current_brands):
                    current_brands.append(b_clean)
                    save_master_brands(current_brands)
                    target_rules_data[b_clean] = {
                        "target_spg": int(new_merk_tspg),
                        "target_team": int(new_merk_tteam),
                    }
                    save_target_rules(target_rules_data)
                    refresh_target_rules()

                harga_map[b_clean] = int(new_merk_harga)
                if save_harga_konsumen(harga_map):
                    st.success(
                        f"✅ Merk **{b_clean}** dengan harga **Rp {int(new_merk_harga):,} / bks** berhasil disimpan!"
                    )
                    st.rerun()

    st.markdown("---")
    st.markdown("#### ✏️ Edit Harga Rokok Konsumen per Merk")

    all_merk_list = list(dict.fromkeys(
        [str(b).strip() for b in current_brands if str(b).strip()]
        + [str(k).strip() for k in harga_map.keys() if str(k).strip()]
    ))

    if not all_merk_list:
        st.info("Belum ada merk rokok terdaftar.")
    else:
        with st.form("form_edit_harga_konsumen"):
            edited_harga_dict = {}
            for idx, merk_item in enumerate(all_merk_list):
                harga_saat_ini = get_harga_konsumen_brand(merk_item, harga_map)
                col_m_info, col_m_input = st.columns([0.55, 0.45])
                with col_m_info:
                    st.markdown(f"**🚬 {merk_item}**")
                    st.caption(f"Harga aktif: Rp {harga_saat_ini:,} / bungkus")
                with col_m_input:
                    edited_harga_dict[merk_item] = st.number_input(
                        f"Harga {merk_item} (Rp)",
                        min_value=0,
                        value=int(harga_saat_ini),
                        step=500,
                        label_visibility="collapsed",
                        key=f"inp_harga_konsumen_{idx}_{merk_item}",
                    )

            btn_save_edit_harga = st.form_submit_button(
                "💾 Simpan Perubahan Harga Konsumen",
                type="primary",
                use_container_width=True,
            )
            if btn_save_edit_harga:
                if save_harga_konsumen(edited_harga_dict):
                    st.success("✅ Perubahan harga rokok konsumen berhasil disimpan!")
                    st.rerun()

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
