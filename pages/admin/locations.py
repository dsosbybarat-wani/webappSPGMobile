from ui.application import (
    BytesIO,
    VISIT_STATUS_OPTIONS,
    VISIT_STATUS_TIDAK_WAJIB,
    VISIT_STATUS_WAJIB,
    _warkop_status_key,
    build_warkop_status_dataframe,
    datetime,
    get_geo_districts,
    get_scheduled_slots_for_date,
    load_master_lokasi_excel,
    load_warkop_visit_status_map,
    pd,
    save_master_lokasi_excel,
    save_warkop_visit_status_map,
    st,
    timedelta,
)


def render():
    st.markdown("## 📍 Entry & Pengaturan Warkop Wajib / Tidak Wajib Kunjung")
    st.caption("Selaras dengan **Jadwal SPG**: pilih tanggal & jadwal aktif (Team — Kota / Sektor Kecamatan) untuk melihat daftar warkop yang bisa dikunjungi lalu tentukan mana yang **Wajib Kunjung** dan **Opsional**.")

    df_lokasi_excel = load_master_lokasi_excel()
    status_map_current = load_warkop_visit_status_map()
    df_warkop_view = build_warkop_status_dataframe(df_lokasi_excel, status_map_current)

    c_stat1, c_stat2, c_stat3 = st.columns(3)
    jml_wajib = int((df_warkop_view["Status Kunjungan"] == VISIT_STATUS_WAJIB).sum()) if not df_warkop_view.empty else 0
    jml_tidak_wajib = int((df_warkop_view["Status Kunjungan"] == VISIT_STATUS_TIDAK_WAJIB).sum()) if not df_warkop_view.empty else 0
    with c_stat1:
        st.metric("Total Titik Warkop / LKK", len(df_warkop_view))
    with c_stat2:
        st.metric("🔒 Wajib Kunjung", jml_wajib)
    with c_stat3:
        st.metric("🔓 Opsional", jml_tidak_wajib)

    tab_wrk_jadwal, tab_wrk_add, tab_wrk_manage, tab_wrk_excel = st.tabs(
        [
            "🗓️ Pengaturan per Jadwal SPG",
            "➕ Tambah Warkop Baru",
            "✏️ Kelola Warkop Aktif",
            "📥 Download / Upload Excel",
        ]
    )

    with tab_wrk_jadwal:
        st.markdown("#### Pilih Tanggal & Jadwal SPG Aktif")
        st.caption("Menampilkan jadwal SPG pada tanggal terpilih beserta daftar warkop pada wilayah/sektor kecamatan jadwal tersebut.")

        default_sched_date = (datetime.utcnow() + timedelta(hours=7)).date()
        selected_sched_date = st.date_input(
            "Tanggal Jadwal SPG",
            value=default_sched_date,
            key="wrk_sched_date",
        )

        sched_slots_today = get_scheduled_slots_for_date(selected_sched_date)
        all_sched_slots = get_scheduled_slots_for_date(None)

        if not sched_slots_today:
            st.warning(
                f"Tidak ada jadwal SPG aktif pada tanggal **{selected_sched_date.strftime('%d %b %Y')}**. "
                "Anda dapat memilih jadwal dari tanggal lain di bawah atau menambahkan jadwal pada menu **Entry & Jadwal SPG**."
            )
            active_slot_pool = all_sched_slots
        else:
            active_slot_pool = sched_slots_today

        if active_slot_pool:
            slot_labels = [
                f"{s['tanggal_str']} — {s['team']} | Wilayah / Sektor: {s['kota']} — {s['kecamatan']}"
                for s in active_slot_pool
            ]
            selected_slot_idx = st.selectbox(
                "Jadwal SPG Aktif",
                options=range(len(slot_labels)),
                format_func=lambda i: slot_labels[i],
                key="wrk_sched_slot_select",
            )
            chosen_slot = active_slot_pool[selected_slot_idx]
            slot_kota = chosen_slot["kota"]
            slot_kec = chosen_slot["kecamatan"]
            slot_team = chosen_slot["team"]
            slot_tgl_str = chosen_slot["tanggal_str"]

            st.info(
                f"📅 **Jadwal Terpilih:** **{slot_tgl_str}** • Team: **{slot_team}** • "
                f"Wilayah / Sektor: **{slot_kota} — {slot_kec}**"
            )

            sub_wrk_df = df_warkop_view[
                (df_warkop_view["Kota"].astype(str).str.strip().str.casefold() == slot_kota.strip().casefold())
                & (df_warkop_view["Kecamatan"].astype(str).str.strip().str.casefold() == slot_kec.strip().casefold())
            ].copy()

            all_wrk_names = sub_wrk_df["Nama Warkop / LKK"].tolist() if not sub_wrk_df.empty else []
            default_wajib_names = [
                r["Nama Warkop / LKK"]
                for _, r in sub_wrk_df.iterrows()
                if r["Status Kunjungan"] == VISIT_STATUS_WAJIB
            ] if not sub_wrk_df.empty else []

            if not all_wrk_names:
                st.warning(
                    f"Belum ada daftar warkop terdaftar untuk wilayah/sektor **{slot_kota} — {slot_kec}**. "
                    "Tambahkan warkop baru pada tab **Tambah Warkop Baru**."
                )
            else:
                with st.form("form_batch_status_warkop"):
                    st.markdown(f"#### List Warkop yang Bisa Dikunjungi ({slot_kota} — {slot_kec})")
                    st.caption(
                        f"Tersedia **{len(all_wrk_names)}** warkop pada sektor **{slot_kec}**. "
                        "Centang satu per satu warkop yang **Wajib Kunjung**; yang tidak dicentang otomatis menjadi **Opsional**."
                    )
                    checked_wajib = []
                    for idx, w in enumerate(all_wrk_names):
                        is_checked = st.checkbox(
                            w,
                            value=(w in default_wajib_names),
                            key=f"chk_wajib_{slot_kota}_{slot_kec}_{slot_tgl_str}_{idx}_{w}",
                        )
                        if is_checked:
                            checked_wajib.append(w)
                    opsional_preview = [w for w in all_wrk_names if w not in checked_wajib]
                    st.caption(
                        f"Ringkasan: **{len(checked_wajib)} Wajib Kunjung** • "
                        f"**{len(opsional_preview)} Opsional** "
                        f"({', '.join(opsional_preview) if opsional_preview else '-'})"
                    )
                    btn_save_batch = st.form_submit_button(
                        "💾 Simpan Status Wajib / Opsional Jadwal Ini",
                        type="primary",
                    )

                    if btn_save_batch:
                        wajib_set = {str(x).strip().casefold() for x in checked_wajib}
                        for _, r in sub_wrk_df.iterrows():
                            k_str = _warkop_status_key(r["Kota"], r["Kecamatan"], r["Nama Warkop / LKK"])
                            if str(r["Nama Warkop / LKK"]).strip().casefold() in wajib_set:
                                status_map_current[k_str] = VISIT_STATUS_WAJIB
                            else:
                                status_map_current[k_str] = VISIT_STATUS_TIDAK_WAJIB
                        if save_warkop_visit_status_map(status_map_current):
                            st.success(
                                f"✅ Status warkop untuk **{slot_team}** ({slot_kota} — {slot_kec}, {slot_tgl_str}) "
                                f"disimpan: **{len(checked_wajib)} Wajib Kunjung** & **{len(opsional_preview)} Opsional**."
                            )
                            st.rerun()
        else:
            st.info("Belum ada data jadwal pada `Jadwal SPG.xlsx`.")

    with tab_wrk_add:
        st.markdown("#### Tambah titik warkop / LKK baru")
        st.caption("Tentukan Kota, Kecamatan, Nama Warkop/LKK, Alamat, dan status Wajib Kunjung atau Opsional.")
        with st.form("form_tambah_lokasi_excel"):
            col_kota_input = st.selectbox("Kota / Kabupaten", options=["Surabaya", "Gresik"], key="add_l_kota")
            kec_geo_opts = get_geo_districts(col_kota_input)
            kec_existing_opts = sorted(
                df_warkop_view[df_warkop_view["Kota"].str.casefold() == col_kota_input.casefold()]["Kecamatan"]
                .dropna()
                .unique()
                .tolist()
            )
            kec_combined_opts = sorted(set(kec_geo_opts + kec_existing_opts))
            col_kec_select = st.selectbox(
                "Pilih Kecamatan (atau ketik manual di bawah)",
                options=[""] + kec_combined_opts,
                key="add_l_kec_select",
            )
            col_kec_input = st.text_input(
                "Kecamatan",
                value=col_kec_select,
                placeholder="Contoh: Tegalsari atau Sawahan",
                key="add_l_kec_input",
            )
            col_warkop_input = st.text_input("Nama Warkop / LKK", placeholder="Contoh: Warkop Barokah", key="add_l_warkop")
            col_alamat_input = st.text_input("Alamat Warkop", placeholder="Contoh: Jl. Ngagel Tirto No. 10", key="add_l_alamat")
            col_status_input = st.selectbox(
                "Status Kunjungan",
                options=VISIT_STATUS_OPTIONS,
                index=1,
                key="add_l_status",
                help="Pilih Wajib Kunjung untuk titik prioritas wajib, atau Opsional untuk titik non-wajib.",
            )
            btn_add_excel = st.form_submit_button("💾 Simpan Warkop Baru", type="primary")

            if btn_add_excel:
                kec_clean = col_kec_input.strip()
                wrk_clean = col_warkop_input.strip()
                if kec_clean and wrk_clean:
                    kota_col_name = next((c for c in df_lokasi_excel.columns if "kota" in c.lower()), "Kota")
                    kec_col_name = next((c for c in df_lokasi_excel.columns if "kec" in c.lower() or "wilayah" in c.lower()), "Kecamatan")
                    warkop_col_name = next((c for c in df_lokasi_excel.columns if "warkop" in c.lower() or "lkk" in c.lower() or "nama" in c.lower()), "Nama Warkop / LKK")
                    alamat_col_name = next((c for c in df_lokasi_excel.columns if "alamat" in c.lower() or "address" in c.lower()), "Alamat Warkop / LKK")

                    new_row = {
                        kota_col_name: col_kota_input,
                        kec_col_name: kec_clean,
                        warkop_col_name: wrk_clean,
                        alamat_col_name: col_alamat_input.strip() if col_alamat_input.strip() else "-",
                    }
                    df_lokasi_excel = pd.concat([df_lokasi_excel, pd.DataFrame([new_row])], ignore_index=True)
                    status_map_current[_warkop_status_key(col_kota_input, kec_clean, wrk_clean)] = col_status_input
                    if save_master_lokasi_excel(df_lokasi_excel) and save_warkop_visit_status_map(status_map_current):
                        st.success(f"✅ Warkop '{wrk_clean}' ({col_status_input}) berhasil disimpan!")
                        st.rerun()
                else:
                    st.warning("Mohon isi nama Kecamatan dan Nama Warkop/LKK.")

    with tab_wrk_manage:
        st.markdown("#### Kelola & edit data warkop aktif")
        st.caption("Filter berdasarkan Kota, Kecamatan, atau Status Kunjungan untuk mengubah atau menghapus titik warkop.")
        if df_warkop_view.empty:
            st.info("Belum ada data warkop aktif.")
        else:
            col_f_k, col_f_kec, col_f_st = st.columns(3)
            with col_f_k:
                f_kota_opts = ["Semua Kota"] + sorted(df_warkop_view["Kota"].unique().tolist())
                f_kota = st.selectbox("Filter Kota", options=f_kota_opts, key="wrk_manage_kota")
            df_after_kota = df_warkop_view if f_kota == "Semua Kota" else df_warkop_view[df_warkop_view["Kota"] == f_kota]
            with col_f_kec:
                f_kec_opts = ["Semua Kecamatan"] + sorted(df_after_kota["Kecamatan"].unique().tolist())
                f_kec = st.selectbox("Filter Kecamatan", options=f_kec_opts, key="wrk_manage_kec")
            with col_f_st:
                f_st = st.selectbox("Filter Status Kunjungan", options=["Semua Status"] + VISIT_STATUS_OPTIONS, key="wrk_manage_status")

            filtered_manage_df = df_after_kota.copy()
            if f_kec != "Semua Kecamatan":
                filtered_manage_df = filtered_manage_df[filtered_manage_df["Kecamatan"] == f_kec]
            if f_st != "Semua Status":
                filtered_manage_df = filtered_manage_df[filtered_manage_df["Status Kunjungan"] == f_st]

            st.markdown(f"**{len(filtered_manage_df)} titik warkop ditampilkan**")
            edited_wrk_df = st.data_editor(
                filtered_manage_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status Kunjungan": st.column_config.SelectboxColumn(
                        "Status Kunjungan",
                        options=VISIT_STATUS_OPTIONS,
                        required=True,
                    )
                },
                key="editor_excel_warkop_terstruktur",
            )
            if st.button("💾 Simpan Perubahan Tabel Warkop", type="primary", key="btn_save_wrk_table"):
                kota_col_name = next((c for c in df_lokasi_excel.columns if "kota" in c.lower()), "Kota")
                kec_col_name = next((c for c in df_lokasi_excel.columns if "kec" in c.lower() or "wilayah" in c.lower()), "Kecamatan")
                warkop_col_name = next((c for c in df_lokasi_excel.columns if "warkop" in c.lower() or "lkk" in c.lower() or "nama" in c.lower()), "Nama Warkop / LKK")
                alamat_col_name = next((c for c in df_lokasi_excel.columns if "alamat" in c.lower() or "address" in c.lower()), "Alamat Warkop / LKK")

                updated_lokasi = df_lokasi_excel.copy()
                for _, er in edited_wrk_df.iterrows():
                    k_v = str(er.get("Kota", "")).strip()
                    kc_v = str(er.get("Kecamatan", "")).strip()
                    w_v = str(er.get("Nama Warkop / LKK", "")).strip()
                    a_v = str(er.get("Alamat Warkop / LKK", "-")).strip() or "-"
                    st_v = str(er.get("Status Kunjungan", VISIT_STATUS_WAJIB)).strip()
                    if not w_v:
                        continue
                    status_map_current[_warkop_status_key(k_v, kc_v, w_v)] = st_v
                    m_idx = updated_lokasi[
                        updated_lokasi[kec_col_name].astype(str).str.strip().str.casefold().eq(kc_v.casefold())
                        & updated_lokasi[warkop_col_name].astype(str).str.strip().str.casefold().eq(w_v.casefold())
                    ].index
                    if len(m_idx) > 0:
                        updated_lokasi.at[m_idx[0], kota_col_name] = k_v
                        updated_lokasi.at[m_idx[0], alamat_col_name] = a_v

                if save_master_lokasi_excel(updated_lokasi) and save_warkop_visit_status_map(status_map_current):
                    st.success("✅ Perubahan data warkop dan status Wajib / Opsional berhasil disimpan!")
                    st.rerun()

    with tab_wrk_excel:
        st.markdown("#### Unduh dan unggah daftar warkop & status kunjungan melalui Excel")
        st.caption("Download data warkop beserta kolom `Status Kunjungan` (`Wajib Kunjung` / `Opsional`), edit di Excel, lalu unggah kembali.")
        wrk_export_buf = BytesIO()
        with pd.ExcelWriter(wrk_export_buf, engine="openpyxl") as writer:
            df_warkop_view.to_excel(writer, index=False, sheet_name="Master Warkop")

        st.download_button(
            "⬇️ Download Master Warkop & Status Kunjungan (.xlsx)",
            data=wrk_export_buf.getvalue(),
            file_name="Master WarkopLKK Status.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_master_warkop_status_xlsx",
        )

        uploaded_wrk_file = st.file_uploader(
            "Pilih file Excel warkop untuk diunggah",
            type=["xlsx"],
            key="upload_master_warkop_xlsx",
        )
        if uploaded_wrk_file is not None:
            try:
                df_up_wrk = pd.read_excel(uploaded_wrk_file)
                df_up_wrk.columns = [str(c).strip() for c in df_up_wrk.columns]
                st.dataframe(df_up_wrk.head(20), use_container_width=True, hide_index=True)
                if st.button("Ganti Master Warkop dengan File Excel Ini", type="primary", key="btn_confirm_up_wrk"):
                    c_k = next((c for c in df_up_wrk.columns if "kota" in c.lower()), None) or "Kota"
                    c_kc = next((c for c in df_up_wrk.columns if "kec" in c.lower() or "wilayah" in c.lower()), None) or "Kecamatan"
                    c_w = next((c for c in df_up_wrk.columns if "warkop" in c.lower() or "lkk" in c.lower() or "nama" in c.lower()), None) or "Nama Warkop / LKK"
                    c_a = next((c for c in df_up_wrk.columns if "alamat" in c.lower() or "address" in c.lower()), None) or "Alamat Warkop / LKK"
                    c_s = next((c for c in df_up_wrk.columns if "status" in c.lower() or "wajib" in c.lower()), None)

                    base_cols = [c for c in [c_k, c_kc, c_w, c_a] if c in df_up_wrk.columns]
                    df_to_save_wrk = df_up_wrk[base_cols].copy()
                    new_status_map = {}
                    for _, r in df_up_wrk.iterrows():
                        k_val = str(r.get(c_k, "Surabaya")).strip()
                        kc_val = str(r.get(c_kc, "")).strip()
                        w_val = str(r.get(c_w, "")).strip()
                        if not w_val:
                            continue
                        raw_st = str(r.get(c_s, VISIT_STATUS_WAJIB) if c_s else VISIT_STATUS_WAJIB).strip()
                        st_val = VISIT_STATUS_TIDAK_WAJIB if ("tidak" in raw_st.casefold() or "opsional" in raw_st.casefold()) else VISIT_STATUS_WAJIB
                        new_status_map[_warkop_status_key(k_val, kc_val, w_val)] = st_val

                    if save_master_lokasi_excel(df_to_save_wrk) and save_warkop_visit_status_map(new_status_map):
                        st.success("✅ Master Warkop dan status Wajib / Opsional berhasil diperbarui dari Excel!")
                        st.rerun()
            except Exception as exc:
                st.error(f"Gagal membaca file Excel warkop: {exc}")

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard", key="btn_back_master_lokasi"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
