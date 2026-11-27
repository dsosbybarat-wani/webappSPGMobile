from ui.application import (
    DEFAULT_SPG_PIN,
    DEFAULT_SUPERVISI_PIN,
    SCHEDULE_DETAIL_FILE,
    _read_json_safe,
    get_scheduled_slots_for_date,
    load_master_akses,
    load_master_spgs,
    save_master_akses,
    st,
)


def render():
    st.markdown("## 🔑 Pengaturan PIN & Hak Akses SPG / Supervisi")
    st.caption(
        "Atur PIN login Supervisi dan SPG agar setiap peran/orang tidak saling masuk ke akun atau mengubah data milik rekan lain."
    )
    akses_cfg = load_master_akses()
    spv_list_known = sorted(
        set(
            [s.get("supervisi", "") for s in get_scheduled_slots_for_date(None) if s.get("supervisi")]
            + list(akses_cfg.get("supervisi_pins", {}).keys())
        )
    )
    sched_detail_raw = _read_json_safe(SCHEDULE_DETAIL_FILE)
    if isinstance(sched_detail_raw, dict):
        for rec in sched_detail_raw.values():
            if isinstance(rec, dict):
                spv_v = str(rec.get("supervisi") or "").strip()
                if spv_v and spv_v not in spv_list_known:
                    spv_list_known.append(spv_v)
    spv_list_known = sorted(set(spv_list_known))
    spg_list_known = sorted(set(load_master_spgs() + list(akses_cfg.get("spg_pins", {}).keys())))

    with st.form("form_pengaturan_akses_pin"):
        col_pin1, col_pin2 = st.columns(2)
        with col_pin1:
            sup_def_pin = st.text_input(
                "PIN Default Supervisi",
                value=akses_cfg.get("supervisi_default_pin", DEFAULT_SUPERVISI_PIN),
                key="cfg_sup_def_pin",
            )
        with col_pin2:
            spg_def_pin = st.text_input(
                "PIN Default SPG",
                value=akses_cfg.get("spg_default_pin", DEFAULT_SPG_PIN),
                key="cfg_spg_def_pin",
            )

        req_spg_pin = st.checkbox(
            "Wajibkan PIN saat login SPG (mengunci nama SPG per sesi agar tidak saling mengganti nama)",
            value=bool(akses_cfg.get("require_spg_pin", False)),
            key="cfg_req_spg_pin",
        )

        st.markdown("---")
        st.markdown("#### 🧑‍💼 PIN Khusus Per Nama Supervisi (Opsional)")
        edited_sup_pins = {}
        for idx_sp, sp_nm in enumerate(spv_list_known):
            edited_sup_pins[sp_nm] = st.text_input(
                f"PIN Supervisi — {sp_nm}",
                value=akses_cfg.get("supervisi_pins", {}).get(sp_nm, ""),
                placeholder=f"Kosongkan untuk pakai PIN default ({sup_def_pin})",
                key=f"cfg_sup_pin_{idx_sp}_{sp_nm}",
            )

        st.markdown("---")
        st.markdown("#### 👩‍💼 PIN Khusus Per Nama SPG (Opsional)")
        edited_spg_pins = {}
        for idx_sg, sg_nm in enumerate(spg_list_known):
            edited_spg_pins[sg_nm] = st.text_input(
                f"PIN SPG — {sg_nm}",
                value=akses_cfg.get("spg_pins", {}).get(sg_nm, ""),
                placeholder=f"Kosongkan untuk pakai PIN default ({spg_def_pin})",
                key=f"cfg_spg_pin_{idx_sg}_{sg_nm}",
            )

        if st.form_submit_button("💾 Simpan Pengaturan PIN & Akses", type="primary", use_container_width=True):
            new_cfg = {
                "supervisi_default_pin": sup_def_pin.strip() or DEFAULT_SUPERVISI_PIN,
                "spg_default_pin": spg_def_pin.strip() or DEFAULT_SPG_PIN,
                "require_spg_pin": req_spg_pin,
                "supervisi_pins": {k: v.strip() for k, v in edited_sup_pins.items() if v.strip()},
                "spg_pins": {k: v.strip() for k, v in edited_spg_pins.items() if v.strip()},
            }
            if save_master_akses(new_cfg):
                st.success("✅ Pengaturan PIN & hak akses berhasil disimpan!")
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard", key="btn_back_master_akses"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
