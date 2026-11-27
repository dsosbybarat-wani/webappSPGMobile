from ui.application import build_polygon_features, get_geo_districts, load_database, pd, pdk, st


def render():
    st.markdown("## 🗺️ Visualisasi Peta Rute & Poligon Kecamatan")
    st.caption("Pantau urutan kunjungan, jam, rute perjalanan, dan batas wilayah poligon kecamatan berdasarkan filter Team SPG, Nama SPG, dan Tanggal.")

    df_peta_all = load_database()
    if not df_peta_all.empty and "Latitude" in df_peta_all.columns and "Longitude" in df_peta_all.columns:
        df_peta_all = df_peta_all.copy()
        df_peta_all["Latitude"] = pd.to_numeric(df_peta_all["Latitude"], errors="coerce")
        df_peta_all["Longitude"] = pd.to_numeric(df_peta_all["Longitude"], errors="coerce")
        df_peta_all["Waktu_Dt"] = pd.to_datetime(df_peta_all["Waktu"], errors="coerce")
        df_peta_all["Tanggal"] = df_peta_all["Waktu_Dt"].dt.strftime("%d-%m-%Y")
        df_peta_all = df_peta_all.dropna(subset=["Latitude", "Longitude"])

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            list_team_filter = ["Semua Team"] + sorted(df_peta_all["Promotor"].dropna().astype(str).unique().tolist())
            pilih_team = st.selectbox("Filter Team SPG", list_team_filter, key="peta_filter_team")
        with col_p2:
            list_spg_filter = ["Semua SPG"] + sorted(df_peta_all["Nama_SPG"].dropna().astype(str).unique().tolist())
            pilih_spg = st.selectbox("Filter Nama SPG", list_spg_filter, key="peta_filter_spg")
        with col_p3:
            list_tgl_filter = ["Semua Tanggal"] + sorted(df_peta_all["Tanggal"].dropna().astype(str).unique().tolist(), reverse=True)
            pilih_tgl = st.selectbox("Filter Tanggal", list_tgl_filter, key="peta_filter_tgl")

        col_opt1, col_opt2 = st.columns([0.65, 0.35])
        with col_opt1:
            mode_warna_titik = st.selectbox(
                "Warna Titik Kunjungan",
                options=["Per Tanggal", "Per Nama SPG", "Seragam (Oranye)"],
                key="peta_warna_titik",
            )
        with col_opt2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            tampilkan_label = st.checkbox(
                "Tampilkan label urutan & jam",
                value=True,
                key="peta_toggle_label",
            )

        df_filtered_map = df_peta_all.copy()
        if pilih_team != "Semua Team":
            df_filtered_map = df_filtered_map[df_filtered_map["Promotor"].astype(str) == pilih_team]
        if pilih_spg != "Semua SPG":
            df_filtered_map = df_filtered_map[df_filtered_map["Nama_SPG"].astype(str) == pilih_spg]
        if pilih_tgl != "Semua Tanggal":
            df_filtered_map = df_filtered_map[df_filtered_map["Tanggal"].astype(str) == pilih_tgl]

        relevant_kotas = []
        if not df_filtered_map.empty and "Kota_Kab" in df_filtered_map.columns:
            seen_kota = set()
            for raw_kota in df_filtered_map["Kota_Kab"].dropna().astype(str):
                cleaned_kota = raw_kota.strip()
                key = cleaned_kota.casefold()
                if cleaned_kota and key not in seen_kota:
                    seen_kota.add(key)
                    relevant_kotas.append(cleaned_kota)

        if not relevant_kotas:
            relevant_kotas = ["Surabaya", "Gresik"]

        layers_list = []
        kecamatan_dari_data = []
        if not df_filtered_map.empty and "Kecamatan" in df_filtered_map.columns:
            seen_kec = set()
            for raw_kec in df_filtered_map["Kecamatan"].dropna().astype(str):
                kc_clean = raw_kec.strip()
                if kc_clean and kc_clean != "-" and kc_clean.casefold() not in seen_kec:
                    seen_kec.add(kc_clean.casefold())
                    kecamatan_dari_data.append(kc_clean)

        opsi_kec_peta = []
        seen_opsi = set()
        for kota_name in relevant_kotas:
            for kc_item in get_geo_districts(kota_name):
                if kc_item.casefold() not in seen_opsi:
                    seen_opsi.add(kc_item.casefold())
                    opsi_kec_peta.append(kc_item)
        for kc_item in kecamatan_dari_data:
            if kc_item.casefold() not in seen_opsi:
                seen_opsi.add(kc_item.casefold())
                opsi_kec_peta.append(kc_item)

        default_kec_peta = [
            kc for kc in kecamatan_dari_data
            if any(kc.casefold() == op.casefold() for op in opsi_kec_peta)
        ]
        if not default_kec_peta and opsi_kec_peta:
            default_kec_peta = opsi_kec_peta[:3]

        if "peta_filter_kecamatan_geojson_pending" in st.session_state:
            st.session_state["peta_filter_kecamatan_geojson"] = [
                x for x in st.session_state.pop("peta_filter_kecamatan_geojson_pending")
                if x in opsi_kec_peta
            ]

        if "peta_filter_kecamatan_geojson" not in st.session_state:
            st.session_state["peta_filter_kecamatan_geojson"] = default_kec_peta
        else:
            st.session_state["peta_filter_kecamatan_geojson"] = [
                x for x in st.session_state["peta_filter_kecamatan_geojson"]
                if x in opsi_kec_peta
            ]

        col_poly_sel, col_poly_reset = st.columns([0.78, 0.22])
        with col_poly_sel:
            kecamatan_peta_terpilih = st.multiselect(
                "Poligon Kecamatan Ditampilkan (On-Demand)",
                options=opsi_kec_peta,
                key="peta_filter_kecamatan_geojson",
                max_selections=8,
                help="Maksimal 8 kecamatan untuk performa optimal.",
            )
        with col_poly_reset:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Reset Poligon", key="btn_reset_peta_polygon", use_container_width=True):
                st.session_state["peta_filter_kecamatan_geojson_pending"] = list(default_kec_peta)
                st.rerun()

        if not kecamatan_peta_terpilih:
            st.caption("ℹ️ Tidak ada kecamatan yang dipilih pada filter poligon—poligon tidak digambar (titik & rute tetap tampil).")

        if len(kecamatan_peta_terpilih) > 8:
            st.warning("⚠️ Maksimal 8 kecamatan untuk performa optimal. Menampilkan 8 pertama.")
            kecamatan_peta_terpilih = kecamatan_peta_terpilih[:8]

        features_gabungan = build_polygon_features(tuple(kecamatan_peta_terpilih))

        if features_gabungan:
            layers_list.append(
                pdk.Layer(
                    "GeoJsonLayer",
                    data={"type": "FeatureCollection", "features": features_gabungan},
                    stroked=True,
                    filled=True,
                    get_fill_color="properties.fill_color",
                    get_line_color="properties.line_color",
                    get_line_width=3,
                    line_width_min_pixels=2,
                    pickable=True,
                    auto_highlight=True,
                )
            )
        elif kecamatan_peta_terpilih:
            st.warning(
                "⚠️ File GeoJSON untuk kecamatan terpilih tidak ditemukan atau kosong di folder `geojson_by_kecamatan/`."
            )

        if not df_filtered_map.empty:
            df_filtered_map = df_filtered_map.sort_values(
                by=["Waktu_Dt", "Waktu"], ascending=[True, True], na_position="last"
            ).reset_index(drop=True)

            if pilih_tgl == "Semua Tanggal" and df_filtered_map["Tanggal"].nunique(dropna=True) > 1:
                df_filtered_map["Urutan"] = df_filtered_map.groupby("Tanggal", dropna=False).cumcount() + 1
            else:
                df_filtered_map["Urutan"] = df_filtered_map.index + 1

            df_filtered_map["Jam_Label"] = df_filtered_map["Waktu_Dt"].dt.strftime("%H:%M").fillna("-")
            df_filtered_map["Warkop_Label"] = df_filtered_map["Warkop_LKK"].fillna("-").astype(str)
            df_filtered_map["Indikator_Titik"] = (
                "#" + df_filtered_map["Urutan"].astype(str)
                + " (" + df_filtered_map["Jam_Label"] + ") - "
                + df_filtered_map["Warkop_Label"]
            )
            _lat_str = df_filtered_map["Latitude"].map(lambda x: f"{x:.6f}")
            _lon_str = df_filtered_map["Longitude"].map(lambda x: f"{x:.6f}")
            df_filtered_map["Koordinat_Str"] = _lat_str + ", " + _lon_str
            df_filtered_map["Link_Google_Maps"] = (
                "https://www.google.com/maps/search/?api=1&query=" + _lat_str + "," + _lon_str
            )

            point_palette_rgba = [
                [234, 88, 12, 235],
                [37, 99, 235, 235],
                [22, 163, 74, 235],
                [147, 51, 234, 235],
                [219, 39, 119, 235],
                [13, 148, 136, 235],
                [202, 138, 4, 235],
                [71, 85, 105, 235],
            ]
            point_palette_hex = [
                "#EA580C", "#2563EB", "#16A34A", "#9333EA",
                "#DB2777", "#0D9488", "#CA8A04", "#475569",
            ]

            if mode_warna_titik == "Per Tanggal":
                categories = sorted(df_filtered_map["Tanggal"].fillna("-").astype(str).unique().tolist())
                cat_to_idx = {cat: idx % len(point_palette_rgba) for idx, cat in enumerate(categories)}
                df_filtered_map["_color_idx"] = df_filtered_map["Tanggal"].fillna("-").astype(str).map(cat_to_idx)
                df_filtered_map["Titik_Color"] = df_filtered_map["_color_idx"].apply(lambda i: point_palette_rgba[i])
            elif mode_warna_titik == "Per Nama SPG":
                categories = sorted(df_filtered_map["Nama_SPG"].fillna("-").astype(str).unique().tolist())
                cat_to_idx = {cat: idx % len(point_palette_rgba) for idx, cat in enumerate(categories)}
                df_filtered_map["_color_idx"] = df_filtered_map["Nama_SPG"].fillna("-").astype(str).map(cat_to_idx)
                df_filtered_map["Titik_Color"] = df_filtered_map["_color_idx"].apply(lambda i: point_palette_rgba[i])
            else:
                categories = ["Semua Titik"]
                cat_to_idx = {"Semua Titik": 0}
                df_filtered_map["_color_idx"] = 0
                df_filtered_map["Titik_Color"] = [point_palette_rgba[0]] * len(df_filtered_map)

            koordinat_rute = df_filtered_map[["Longitude", "Latitude"]].values.tolist()
            center_lat = float(df_filtered_map["Latitude"].mean())
            center_lon = float(df_filtered_map["Longitude"].mean())

            if len(koordinat_rute) >= 2:
                path_layer = pdk.Layer(
                    "PathLayer",
                    data=[
                        {
                            "path": koordinat_rute,
                            "name": f"Rute ({len(koordinat_rute)} titik)",
                        }
                    ],
                    get_path="path",
                    get_color=[220, 38, 38, 220],
                    get_width=6,
                    pickable=True,
                )
                layers_list.append(path_layer)

            scatter_layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_filtered_map,
                get_position=["Longitude", "Latitude"],
                get_fill_color="Titik_Color",
                get_line_color=[255, 255, 255, 240],
                line_width_min_pixels=2,
                get_radius=75,
                pickable=True,
            )
            layers_list.append(scatter_layer)

            if tampilkan_label:
                text_layer = pdk.Layer(
                    "TextLayer",
                    data=df_filtered_map,
                    get_position=["Longitude", "Latitude"],
                    get_text="Indikator_Titik",
                    get_size=12,
                    get_color=[15, 23, 42, 255],
                    get_background_color=[255, 255, 255, 225],
                    get_background_padding=[4, 2, 4, 2],
                    get_pixel_offset=[0, -18],
                    pickable=False,
                )
                layers_list.append(text_layer)

            view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12, pitch=30)
            deck_map = pdk.Deck(
                layers=layers_list,
                initial_view_state=view_state,
                tooltip={
                    "html": (
                        "<b>Kunjungan Ke:</b> #{Urutan} (Jam: {Jam_Label})<br/>"
                        "<b>Wilayah / Kecamatan:</b> {Kota_Kab} / {Kecamatan}<br/>"
                        "<b>Team & SPG:</b> {Promotor} ({Nama_SPG})<br/>"
                        "<b>Plat Mobil:</b> {Plat_Mobil}<br/>"
                        "<b>Warkop / LKK:</b> {Warkop_LKK}<br/>"
                        "<b>Brand:</b> {Brand_Rokok} ({Jumlah_Bungkus} bks)<br/>"
                        "<b>Koordinat:</b> {Koordinat_Str}<br/>"
                        "<b>Waktu Lengkap:</b> {Waktu}"
                    ),
                    "style": {"backgroundColor": "#0F172A", "color": "white"},
                },
            )
            st.pydeck_chart(deck_map)

            if mode_warna_titik != "Seragam (Oranye)" and categories:
                legend_items = []
                for cat in categories:
                    hex_col = point_palette_hex[cat_to_idx[cat]]
                    legend_items.append(
                        f"<span style='display:inline-flex;align-items:center;gap:6px;margin-right:14px;margin-bottom:4px;'>"
                        f"<span style='width:12px;height:12px;border-radius:50%;background:{hex_col};display:inline-block;border:1px solid #fff;'></span>"
                        f"<span>{cat}</span></span>"
                    )
                st.markdown(
                    f"<div style='font-size:0.85rem;margin-top:4px;margin-bottom:10px;'><b>Legenda ({mode_warna_titik}):</b> {''.join(legend_items)}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("#### 🔗 Buka Titik di Google Maps")
            option_map = {
                f"#{row['Urutan']} | {row['Tanggal']} {row['Jam_Label']} | {row['Warkop_LKK']} ({row['Koordinat_Str']})": row["Link_Google_Maps"]
                for _, row in df_filtered_map.iterrows()
            }
            col_pick_gmap, col_btn_gmap = st.columns([0.65, 0.35])
            with col_pick_gmap:
                selected_point_label = st.selectbox(
                    "Pilih titik kunjungan",
                    options=list(option_map.keys()),
                    key="peta_pilih_titik_gmap",
                )
            with col_btn_gmap:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.link_button(
                    "📍 Buka Google Maps",
                    url=option_map[selected_point_label],
                    use_container_width=True,
                )

            st.markdown("#### 🧭 Urutan Titik Kunjungan Terfilter")
            df_urutan_view = df_filtered_map[
                [
                    "Urutan",
                    "Tanggal",
                    "Jam_Label",
                    "Promotor",
                    "Nama_SPG",
                    "Kota_Kab",
                    "Kecamatan",
                    "Warkop_LKK",
                    "Brand_Rokok",
                    "Jumlah_Bungkus",
                    "Koordinat_Str",
                    "Link_Google_Maps",
                ]
            ].rename(columns={"Jam_Label": "Jam", "Koordinat_Str": "Koordinat"})
            st.dataframe(
                df_urutan_view,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Link_Google_Maps": st.column_config.LinkColumn(
                        "Google Maps",
                        display_text="Buka Maps 📍",
                    )
                },
            )
        else:
            st.warning("Tidak ada data koordinat yang cocok dengan filter yang dipilih.")
    else:
        st.info("Belum ada data koordinat GPS yang terekam pada sistem.")

    st.markdown("---")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state["admin_view"] = "Dashboard"
        st.rerun()
    st.stop()
