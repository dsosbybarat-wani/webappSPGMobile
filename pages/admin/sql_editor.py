import pandas as pd
import streamlit as st

from core.supabase_sql import execute_supabase_sql, get_supabase_database_url


def render():
    st.markdown("## 🛠️ SQL Editor Supabase")
    st.caption("Jalankan query PostgreSQL langsung ke database Supabase.")
    st.warning(
        "Query dapat mengubah atau menghapus data permanen. Gunakan role database "
        "dengan hak akses minimum yang diperlukan."
    )
    st.info(
        "Untuk backup/restore snapshot lengkap aplikasi, gunakan **Dashboard Utama → "
        "Backup & Load Data**. Editor ini menjalankan SQL dan dapat memuat file `.sql`."
    )

    try:
        get_supabase_database_url()
    except RuntimeError as exc:
        st.error(str(exc))

    uploaded_sql = st.file_uploader(
        "Unggah skrip SQL untuk dimuat ke editor",
        type=["sql"],
        key="supabase_sql_upload",
    )
    if uploaded_sql and st.button("Muat file SQL ke editor", key="supabase_sql_load_file"):
        try:
            st.session_state["supabase_sql_query"] = uploaded_sql.getvalue().decode("utf-8-sig")
        except UnicodeDecodeError:
            st.error("File SQL harus menggunakan encoding UTF-8.")

    with st.form("supabase_sql_editor_form"):
        query = st.text_area(
            "Query / skrip SQL",
            height=280,
            key="supabase_sql_query",
            placeholder="SELECT * FROM public.nama_tabel LIMIT 100;",
        )
        confirm_execution = st.checkbox(
            "Saya memahami query dapat mengubah atau menghapus data Supabase.",
            key="supabase_sql_confirm",
        )
        execute_clicked = st.form_submit_button("▶️ Jalankan SQL", type="primary")

    if execute_clicked:
        if not confirm_execution:
            st.error("Centang konfirmasi sebelum menjalankan SQL.")
        else:
            st.session_state.pop("supabase_sql_results", None)
            try:
                with st.spinner("Menjalankan SQL di Supabase..."):
                    st.session_state["supabase_sql_results"] = execute_supabase_sql(query)
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))

    results = st.session_state.get("supabase_sql_results", [])
    for index, result in enumerate(results, start=1):
        st.markdown(f"#### Hasil statement {index}")
        if result["columns"]:
            result_frame = pd.DataFrame(result["rows"], columns=result["columns"])
            st.dataframe(result_frame, use_container_width=True)
            st.download_button(
                "⬇️ Unduh hasil sebagai CSV",
                data=result_frame.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"supabase-query-{index}.csv",
                mime="text/csv",
                key=f"supabase_sql_download_{index}",
            )
            if result["truncated"]:
                st.warning("Hasil dibatasi hingga 1.000 baris.")
        else:
            st.success(f"Berhasil dijalankan. Baris terdampak: {result['rowcount']}.")

    st.stop()
