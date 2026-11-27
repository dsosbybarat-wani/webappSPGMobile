from config.constants import DB_FILE, DB_SUPERVISI_KONTAK_FILE
from ui.application import (
    add_custom_week_columns,
    clean_brand_target_name,
    datetime,
    get_custom_week_info,
    load_database,
    load_supervisi_database,
    pd,
    render_google_sheet_backup_controls,
    render_dashboard_card,
    st,
    style_status_target,
    timedelta,
)
from ui.components import format_sales_table


def render():
    st.markdown("## 📊 Dashboard Admin & Manajemen Lapangan")
    st.caption("Pilih menu master data atau pantau rekapitulasi tim secara real-time.")

    st.markdown("#### 📦 Master Data")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        if st.button("🔑 PIN & Hak Akses User\nAtur PIN SPG & Supervisi", use_container_width=True):
            st.session_state["admin_view"] = "Master_Akses"
            st.rerun()
        if st.button("🏷️ Master Nama Team\nAtur nama team 1 - 20", use_container_width=True):
            st.session_state["admin_view"] = "Master_Nama_Team"
            st.rerun()
        if st.button("👥 Master Team & Brand\nAtur brand rokok per team", use_container_width=True):
            st.session_state["admin_view"] = "Master_Team"
            st.rerun()
    with col_m2:
        if st.button("🚗 Master Plat Kendaraan\nTambah & hapus plat mobil", use_container_width=True):
            st.session_state["admin_view"] = "Master_Plat"
            st.rerun()
        if st.button("🚬 Merek Rokok & Target\nKelola daftar merek & target", use_container_width=True):
            st.session_state["admin_view"] = "Master_Brand"
            st.rerun()
        if st.button("💰 Harga Rokok Konsumen\nAdd & edit harga merk", use_container_width=True):
            st.session_state["admin_view"] = "Master_Harga"
            st.rerun()
    with col_m3:
        if st.button("📍 Lokasi Warkop (Excel)\nKelola dari Master Warkop", use_container_width=True):
            st.session_state["admin_view"] = "Master_Lokasi"
            st.rerun()
        if st.button("📅 Entry & Monitoring Jadwal SPG\nSemua Team", use_container_width=True):
            st.session_state["admin_view"] = "Master_Jadwal_Excel"
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📈 Analitik & Pemetaan")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        if st.button("📊 Analitik Lapangan\nDemografi & Kecamatan", use_container_width=True):
            st.session_state["admin_view"] = "Analitik"
            st.rerun()
    with col_a2:
        if st.button("🗺️ Peta Rute All User\nFilter Team/SPG/Tanggal", use_container_width=True):
            st.session_state["admin_view"] = "Peta_Rute"
            st.rerun()
    with col_a3:
        if st.button("⬅️ Keluar Admin", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.session_state["admin_view"] = "Dashboard"
            st.rerun()

    st.markdown("---")
    st.markdown("#### ☁️ Backup & Load Data")
    render_google_sheet_backup_controls()

    st.markdown("---")
    st.markdown("#### 📥 Unduh Data Utama")
    st.caption("Unduhan ini hanya tersedia dari Dashboard Admin.")
    col_download_laporan, col_download_supervisi = st.columns(2)
    with col_download_laporan:
        st.download_button(
            "⬇️ Download Rekap Laporan SPG",
            data=load_database().to_csv(index=False).encode("utf-8-sig"),
            file_name=DB_FILE,
            mime="text/csv",
            use_container_width=True,
            key="download_rekap_laporan_admin",
        )
    with col_download_supervisi:
        st.download_button(
            "⬇️ Download Rekap Kontak Supervisi",
            data=load_supervisi_database().to_csv(index=False).encode("utf-8-sig"),
            file_name=DB_SUPERVISI_KONTAK_FILE,
            mime="text/csv",
            use_container_width=True,
            key="download_rekap_supervisi_admin",
        )

    st.markdown("---")
    st.markdown("#### 🌐 Ringkasan Cepat Data Masuk (All User)")

    df_all_users = load_database()
    df_all_supervisi = load_supervisi_database()

    if not df_all_users.empty:
        df_all_users["Waktu_Dt"] = pd.to_datetime(df_all_users["Waktu"], errors="coerce")
        df_all_users["Tanggal"] = df_all_users["Waktu_Dt"].dt.strftime("%d-%m-%Y")
        df_all_users = add_custom_week_columns(df_all_users, "Waktu_Dt")
        df_all_users["Jumlah_Bungkus"] = pd.to_numeric(df_all_users["Jumlah_Bungkus"], errors="coerce").fillna(0)

        today_dt = datetime.utcnow() + timedelta(hours=7)
        today_str = today_dt.strftime("%d-%m-%Y")
        current_month_str = today_dt.strftime("%m-%Y")
        current_week_label, _ = get_custom_week_info(today_dt)

        df_today = df_all_users[df_all_users["Tanggal"] == today_str].copy()
        omset_hari_ini = int(df_today["Jumlah_Bungkus"].sum())
        konsumen_hari_ini = len(df_today)

        if not df_today.empty:
            df_today_lb = (
                df_today.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok"])
                .agg(Total_Omset_Team=("Jumlah_Bungkus", "sum"))
                .reset_index()
            )
            df_today_lb["Brand_Rokok_Clean"] = df_today_lb["Brand_Rokok"].apply(clean_brand_target_name)
            df_today_lb = (
                df_today_lb.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok_Clean"])
                .agg(Total_Omset_Team=("Total_Omset_Team", "sum"))
                .reset_index()
                .rename(columns={"Brand_Rokok_Clean": "Brand_Rokok"})
            )
            df_today_lb["Target_Team"] = df_today_lb["Brand_Rokok"].apply(
                lambda brand: get_target_for_brand(brand, "target_team", 50)
            )
            target_hari_ini = int(df_today_lb["Target_Team"].sum())
        else:
            target_hari_ini = 100

        if target_hari_ini <= 0:
            target_hari_ini = 100

        persen_pencapaian = int((omset_hari_ini / target_hari_ini) * 100) if target_hari_ini > 0 else 0

        df_week = df_all_users[df_all_users["Periode_Minggu"] == current_week_label]
        omset_minggu_ini = int(df_week["Jumlah_Bungkus"].sum())
        konsumen_minggu_ini = len(df_week)

        df_all_users["Bulan_Tahun"] = df_all_users["Waktu_Dt"].dt.strftime("%m-%Y")
        df_month = df_all_users[df_all_users["Bulan_Tahun"] == current_month_str]
        omset_bulan_ini = int(df_month["Jumlah_Bungkus"].sum())
        konsumen_bulan_ini = len(df_month)

        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        with kpi_col1:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{omset_hari_ini:,} bks</div>
                    <div class="card-subtext">dari {target_hari_ini} target bks</div>
                </div>""",
                "Omset Hari Ini",
            )
        with kpi_col2:
            bar_width = min(persen_pencapaian, 100)
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value-green">{persen_pencapaian}%</div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: {bar_width}%;"></div>
                    </div>
                </div>""",
                "Pencapaian Omset Hari Ini",
            )
        with kpi_col3:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{konsumen_hari_ini:,}</div>
                    <div class="card-subtext" style="opacity: 0;">-</div>
                </div>""",
                "Konsumen Beli Hari Ini",
            )

        kpi_col4, kpi_col5, kpi_col6 = st.columns(3)
        with kpi_col4:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{omset_minggu_ini:,} bks</div>
                    <div class="card-subtext">{konsumen_minggu_ini:,} Konsumen Minggu Ini</div>
                </div>""",
                "Omset Minggu Ini",
            )
        with kpi_col5:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{omset_bulan_ini:,} bks</div>
                    <div class="card-subtext" style="opacity: 0;">-</div>
                </div>""",
                "Omset Bulan Ini",
            )
        with kpi_col6:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{konsumen_bulan_ini:,}</div>
                    <div class="card-subtext" style="opacity: 0;">-</div>
                </div>""",
                "Konsumen Beli Bulan Ini",
            )

        all_weeks_admin = sorted(df_all_users["Periode_Minggu"].dropna().unique().tolist(), reverse=True)
        all_dates_admin = sorted(df_all_users["Tanggal"].dropna().unique().tolist(), reverse=True)
        all_teams_admin = sorted(df_all_users["Promotor"].dropna().unique().tolist())
        all_spgs_admin = sorted(df_all_users["Nama_SPG"].dropna().unique().tolist())

        st.markdown("---")
        st.markdown("### 🏆 Leaderboard Team SPG (Berdasarkan Target Team)")

        col_lb_w, col_lb_tgl, col_lb_team = st.columns(3)
        with col_lb_w:
            filter_lb_week = st.multiselect("Filter Periode Minggu (Leaderboard)", options=all_weeks_admin, default=all_weeks_admin, key="admin_lb_week")
        with col_lb_tgl:
            filter_lb_tgl = st.multiselect("Filter Tanggal (Leaderboard)", options=all_dates_admin, default=all_dates_admin, key="admin_lb_tgl")
        with col_lb_team:
            filter_lb_team = st.multiselect("Filter Team SPG (Leaderboard)", options=all_teams_admin, default=all_teams_admin, key="admin_lb_team")

        df_lb_filtered = df_all_users.copy()
        if filter_lb_week:
            df_lb_filtered = df_lb_filtered[df_lb_filtered["Periode_Minggu"].isin(filter_lb_week)]
        if filter_lb_tgl:
            df_lb_filtered = df_lb_filtered[df_lb_filtered["Tanggal"].isin(filter_lb_tgl)]
        if filter_lb_team:
            df_lb_filtered = df_lb_filtered[df_lb_filtered["Promotor"].isin(filter_lb_team)]

        if not df_lb_filtered.empty:
            df_team_leaderboard = (
                df_lb_filtered.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok"])
                .agg(Total_Omset_Team=("Jumlah_Bungkus", "sum"), Total_Konsumen_Beli=("Nama_Konsumen", "count"))
                .reset_index()
            )
            df_team_leaderboard["Brand_Rokok_Clean"] = df_team_leaderboard["Brand_Rokok"].apply(clean_brand_target_name)
            df_team_leaderboard = (
                df_team_leaderboard.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok_Clean"])
                .agg(Total_Omset_Team=("Total_Omset_Team", "sum"), Total_Konsumen_Beli=("Total_Konsumen_Beli", "sum"))
                .reset_index()
                .rename(columns={"Brand_Rokok_Clean": "Brand_Rokok"})
            )
            df_team_leaderboard["Target_Team"] = df_team_leaderboard["Brand_Rokok"].apply(
                lambda brand: get_target_for_brand(brand, "target_team", 50)
            )
            df_team_leaderboard["Status_Target_Team"] = df_team_leaderboard.apply(
                lambda r: "Achieved" if r["Total_Omset_Team"] >= r["Target_Team"] else "Not Achieved",
                axis=1
            )

            cols_lb_order = ["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok", "Total_Omset_Team", "Total_Konsumen_Beli", "Target_Team", "Status_Target_Team"]
            df_team_leaderboard = df_team_leaderboard[[c for c in cols_lb_order if c in df_team_leaderboard.columns]]

            st.dataframe(
                format_sales_table(
                    df_team_leaderboard.style.map(style_status_target, subset=["Status_Target_Team"])
                ),
                use_container_width=True,
            )
        else:
            st.info("Tidak ada data untuk filter Leaderboard yang dipilih.")

        st.markdown("---")
        st.markdown("### 🚬 Jumlah Rokok Laku Per SPG dan Per Merk")

        col_rk_w, col_rk1, col_rk2, col_rk3 = st.columns(4)
        with col_rk_w:
            filter_rk_week = st.multiselect("Filter Minggu (Rokok Laku)", options=all_weeks_admin, default=all_weeks_admin, key="admin_rk_week")
        with col_rk1:
            filter_rk_tgl = st.multiselect("Filter Tanggal (Rokok Laku)", options=all_dates_admin, default=all_dates_admin, key="admin_rk_tgl")
        with col_rk2:
            filter_rk_team = st.multiselect("Filter Team (Rokok Laku)", options=all_teams_admin, default=all_teams_admin, key="admin_rk_team")
        with col_rk3:
            filter_rk_spg = st.multiselect("Filter Nama SPG (Rokok Laku)", options=all_spgs_admin, default=all_spgs_admin, key="admin_rk_spg")

        df_rk_filtered = df_all_users.copy()
        if filter_rk_week:
            df_rk_filtered = df_rk_filtered[df_rk_filtered["Periode_Minggu"].isin(filter_rk_week)]
        if filter_rk_tgl:
            df_rk_filtered = df_rk_filtered[df_rk_filtered["Tanggal"].isin(filter_rk_tgl)]
        if filter_rk_team:
            df_rk_filtered = df_rk_filtered[df_rk_filtered["Promotor"].isin(filter_rk_team)]
        if filter_rk_spg:
            df_rk_filtered = df_rk_filtered[df_rk_filtered["Nama_SPG"].isin(filter_rk_spg)]

        if not df_rk_filtered.empty:
            df_rokok_summary = (
                df_rk_filtered.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Nama_SPG", "Brand_Rokok"])
                .agg(Jumlah_Bungkus=("Jumlah_Bungkus", "sum"))
                .reset_index()
                .pivot_table(index=["Tanggal", "Periode_Minggu", "Promotor", "Nama_SPG"], columns="Brand_Rokok", values="Jumlah_Bungkus", fill_value=0)
                .reset_index()
            )
            numeric_sales_columns = [
                column
                for column in df_rokok_summary.columns
                if pd.api.types.is_numeric_dtype(df_rokok_summary[column])
            ]
            st.dataframe(
                format_sales_table(df_rokok_summary, columns=numeric_sales_columns),
                use_container_width=True,
            )
        else:
            st.info("Tidak ada data untuk filter Rokok Laku yang dipilih.")
