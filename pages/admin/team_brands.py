from ui.application import (
    load_master_brands,
    load_master_team_brands,
    load_master_team_names,
    pd,
    save_master_team_brands,
    st,
)


def render():
    st.markdown("## 👥 Master Data: Team 1 - 20 & Alokasi Brand Rokok")
    st.caption("Atur pilihan merek rokok yang dapat dibawa oleh masing-masing Team SPG (Team 1 sampai 20).")

    all_available_brands = load_master_brands()
    team_brands_dict = load_master_team_brands()
    team_name_mapping = load_master_team_names()
    active_team_slots = [
        (f"Team SPG {i}", team_name_mapping[f"Team SPG {i}"])
        for i in range(1, 21)
        if team_name_mapping[f"Team SPG {i}"]
    ]
    team_options = [team_name for _, team_name in active_team_slots]
    if not team_options:
        st.info("Belum ada nama team. Unggah jadwal SPG untuk mengisi daftar team.")
        if st.button("⬅️ Kembali ke Dashboard", key="btn_back_master_team_empty"):
            st.session_state["admin_view"] = "Dashboard"
            st.rerun()
        st.stop()

    selected_team_config = st.selectbox(
        "Pilih Team SPG untuk Konfigurasi Brand",
        options=team_options,
        key="sb_pilih_team_master",
    )

    current_assigned_brands = team_brands_dict.get(selected_team_config, [])
    valid_defaults = [b for b in current_assigned_brands if b in all_available_brands]

    with st.form(key=f"form_config_{selected_team_config}"):
        st.markdown(f"#### Alokasi Merek untuk `{selected_team_config}`")
        selected_brands_input = st.multiselect(
            "Pilih Brand Rokok yang Diizinkan",
            options=all_available_brands,
            default=valid_defaults,
            key=f"ms_brands_{selected_team_config}",
        )
        btn_save_team_brand = st.form_submit_button("💾 Simpan Alokasi Brand Team")

        if btn_save_team_brand:
            team_brands_dict[selected_team_config] = selected_brands_input
            if save_master_team_brands(team_brands_dict):
                st.success(f"✅ Alokasi brand rokok untuk **{selected_team_config}** berhasil disimpan!")
                st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Ringkasan Alokasi Brand Seluruh Team (1 - 20)")
    fresh_team_brands = load_master_team_brands()
    summary_list = []
    for t_key, t_name in active_team_slots:
        b_list = fresh_team_brands.get(t_name, fresh_team_brands.get(t_key, []))
        summary_list.append({
            "Team": t_name,
            "Brand Diizinkan": ", ".join(b_list) if b_list else "(Belum ada brand)",
        })

    st.dataframe(pd.DataFrame(summary_list), use_container_width=True)

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard", key="btn_back_master_team"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
