from ui.application import (
    TARGET_GROUP_OPTIONS,
    load_master_brands,
    load_target_rules,
    refresh_target_rules,
    save_master_brands,
    save_target_rules,
    st,
)


def render():
    st.markdown("## 🚬 Master Data: Merek Rokok & Target")
    st.caption("Tambah atau hapus brand, dan ubah target per SPG maupun per Team.")

    current_brands = load_master_brands()
    target_rules_data = load_target_rules()

    with st.form("form_tambah_brand"):
        st.markdown("#### Tambah Merek Rokok & Target Baru")
        new_brand_name = st.text_input("Nama Merek Rokok Baru", placeholder="Contoh: Djarum Super Extra")
        t_spg = st.number_input("Target per SPG (Bungkus)", min_value=1, value=30, step=1)
        t_team = st.number_input("Target per Team (Bungkus)", min_value=1, value=60, step=1)
        new_group = st.selectbox(
            "Grup target gabungan",
            options=list(TARGET_GROUP_OPTIONS),
            format_func=lambda group: TARGET_GROUP_OPTIONS[group],
        )
        btn_add_brand = st.form_submit_button("➕ Tambah Merek Rokok")

        if btn_add_brand:
            b_clean = new_brand_name.strip()
            if b_clean:
                if b_clean not in current_brands:
                    current_brands.append(b_clean)
                    save_master_brands(current_brands)
                    target_rules_data[b_clean] = {
                        "target_spg": int(t_spg),
                        "target_team": int(t_team),
                    }
                    if new_group:
                        target_rules_data[b_clean]["group"] = new_group
                    save_target_rules(target_rules_data)
                    refresh_target_rules()
                    st.success(f"✅ Merek rokok '{b_clean}' berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Merek rokok tersebut sudah ada dalam daftar.")
            else:
                st.warning("Mohon masukkan nama merek rokok.")

    st.markdown("---")
    st.markdown("#### 📋 Daftar Merek Rokok & Pengaturan Target")

    for idx, b in enumerate(current_brands):
        rule = target_rules_data.get(b, {"target_spg": 25, "target_team": 50})
        with st.expander(f"🚬 {b} (SPG: {rule.get('target_spg', 25)} bks | Team: {rule.get('target_team', 50)} bks)"):
            with st.form(f"form_edit_target_{idx}"):
                edit_tspg = st.number_input("Target per SPG (Bungkus)", min_value=1, value=int(rule.get("target_spg", 25)), key=f"tspg_{idx}")
                edit_tteam = st.number_input("Target per Team (Bungkus)", min_value=1, value=int(rule.get("target_team", 50)), key=f"tteam_{idx}")
                rule_group = rule.get("group")
                if rule_group == "Black_Siro_Kuro":
                    rule_group = "Black_Matcha"
                group_index = list(TARGET_GROUP_OPTIONS).index(
                    rule_group if rule_group in TARGET_GROUP_OPTIONS else ""
                )
                edit_group = st.selectbox(
                    "Grup target gabungan",
                    options=list(TARGET_GROUP_OPTIONS),
                    index=group_index,
                    format_func=lambda group: TARGET_GROUP_OPTIONS[group],
                    key=f"grp_{idx}",
                )

                col_ed1, col_ed2 = st.columns(2)
                with col_ed1:
                    btn_save_edit = st.form_submit_button("💾 Simpan Perubahan Target")
                with col_ed2:
                    btn_del_brand = st.form_submit_button("🗑️ Hapus Brand Ini")

                if btn_save_edit:
                    target_rules_data[b] = {
                        "target_spg": int(edit_tspg),
                        "target_team": int(edit_tteam),
                    }
                    if edit_group:
                        target_rules_data[b]["group"] = edit_group
                    save_target_rules(target_rules_data)
                    refresh_target_rules()
                    st.success(f"✅ Target brand '{b}' berhasil diperbarui!")
                    st.rerun()

                if btn_del_brand:
                    current_brands.remove(b)
                    save_master_brands(current_brands)
                    if b in target_rules_data:
                        del target_rules_data[b]
                        save_target_rules(target_rules_data)
                    refresh_target_rules()
                    st.success(f"🗑️ Brand '{b}' berhasil dihapus!")
                    st.rerun()

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
