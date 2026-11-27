from ui.application import load_database, pd, st


def render():
    st.markdown("## 📊 Analitik & Rekapitulasi All User")
    st.caption("Laporan mendalam performa seluruh tim berdasarkan demografi, wilayah, dan sebaran kecamatan.")

    df_all_users = load_database()
    if not df_all_users.empty:
        df_all_users["Jumlah_Bungkus"] = pd.to_numeric(df_all_users["Jumlah_Bungkus"], errors="coerce").fillna(0)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 👥 Demografi Konsumen (Gender)")
            gender_count = df_all_users["Gender"].value_counts()
            st.bar_chart(gender_count)
        with c2:
            st.markdown("#### 📊 Sebaran Range Umur Konsumen")
            if "Range_Umur" in df_all_users.columns:
                age_count = df_all_users["Range_Umur"].value_counts()
                st.bar_chart(age_count)
            else:
                st.info("Data Range Umur belum tersedia.")

        st.markdown("---")
        st.markdown("#### 🏙️ Sebaran per Wilayah (Kota/Kab)")
        kota_count = df_all_users["Kota_Kab"].value_counts()
        st.bar_chart(kota_count)

        st.markdown("---")
        st.markdown("#### 🗺️ Sebaran Kunjungan & Omset per Kecamatan")

        list_kota_analitik = ["Semua Wilayah"] + sorted(df_all_users["Kota_Kab"].dropna().unique().tolist())
        pilih_kota_kec = st.selectbox("Filter Kota/Kabupaten untuk Sebaran Kecamatan", list_kota_analitik)

        df_kec_analitik = df_all_users.copy()
        if pilih_kota_kec != "Semua Wilayah":
            df_kec_analitik = df_kec_analitik[df_kec_analitik["Kota_Kab"] == pilih_kota_kec]

        if not df_kec_analitik.empty:
            df_sebaran_kec = (
                df_kec_analitik.groupby(["Kota_Kab", "Kecamatan"])
                .agg(
                    Titik_Warkop=("Warkop_LKK", lambda x: x.nunique()),
                    Total_Konsumen=("Nama_Konsumen", "count"),
                    Total_Omset_Bungkus=("Jumlah_Bungkus", "sum"),
                )
                .reset_index()
                .sort_values(by="Total_Omset_Bungkus", ascending=False)
            )
            chart_kec = df_sebaran_kec.set_index("Kecamatan")["Total_Omset_Bungkus"]
            st.bar_chart(chart_kec)
            st.dataframe(df_sebaran_kec, use_container_width=True)
        else:
            st.info("Tidak ada data pada wilayah yang dipilih.")
    else:
        st.info("Belum ada data untuk ditampilkan dalam grafik analitik.")

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
