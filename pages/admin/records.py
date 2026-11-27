import pandas as pd

import streamlit as st

from core.storage import (
    load_database,
    load_supervisi_database,
    save_database,
    save_supervisi_database,
)


def _row_snapshot(row):
    return tuple("" if pd.isna(value) else str(value) for value in row.tolist())


def _apply_record_edit(dataframe, row_index, edited_row):
    updated = dataframe.copy()
    for column in dataframe.columns:
        updated.at[row_index, column] = edited_row[column]
    return updated


def _delete_record(dataframe, row_index, expected_snapshot):
    if row_index not in dataframe.index:
        return None
    if _row_snapshot(dataframe.loc[row_index]) != expected_snapshot:
        return None
    return dataframe.drop(index=row_index).reset_index(drop=True)


def _record_label(dataframe, row_index, columns):
    row = dataframe.loc[row_index]
    details = [
        str(row.get(column, "")).strip()
        for column in columns
        if str(row.get(column, "")).strip()
    ]
    return f"Baris {row_index + 1} · {' · '.join(details)}"


def _render_record_manager(title, key, load_records, save_records, label_columns):
    records = load_records().reset_index(drop=True)
    if records.empty:
        st.info("Belum ada data untuk dikelola.")
        return

    search = st.text_input(
        "Cari data",
        key=f"{key}_search",
        placeholder="Cari tanggal, team, SPG, merek, atau informasi lainnya",
    )
    filtered_records = records
    if search.strip():
        matches = records.astype(str).apply(
            lambda column: column.str.contains(search.strip(), case=False, regex=False)
        )
        filtered_records = records[matches.any(axis=1)]

    if filtered_records.empty:
        st.info("Tidak ada data yang cocok dengan pencarian.")
        return

    st.caption(f"{len(filtered_records)} data ditemukan. Pilih satu data untuk diedit atau dihapus.")
    selected_index = st.selectbox(
        "Pilih data",
        options=filtered_records.index.tolist(),
        format_func=lambda index: _record_label(records, index, label_columns),
        key=f"{key}_selected",
    )
    st.dataframe(filtered_records, use_container_width=True, hide_index=True)

    pending_key = f"{key}_pending_delete"
    selected_row = records.loc[selected_index]
    selected_snapshot = _row_snapshot(selected_row)
    with st.form(key=f"{key}_edit_form_{selected_index}"):
        edited = st.data_editor(
            records.loc[[selected_index], records.columns],
            hide_index=True,
            num_rows="fixed",
            use_container_width=True,
            key=f"{key}_editor_{selected_index}",
        )
        save_clicked = st.form_submit_button("💾 Simpan perubahan", type="primary")

    if save_clicked:
        if len(edited) != 1:
            st.error("Perubahan tidak disimpan karena baris yang diedit tidak valid.")
        else:
            updated = _apply_record_edit(records, selected_index, edited.iloc[0])
            save_records(updated)
            st.success(f"Perubahan pada {title.lower()} berhasil disimpan.")
            st.rerun()

    if st.button("🗑️ Hapus data terpilih", key=f"{key}_delete_{selected_index}"):
        st.session_state[pending_key] = {
            "row_index": selected_index,
            "snapshot": selected_snapshot,
            "label": _record_label(records, selected_index, label_columns),
        }

    pending_delete = st.session_state.get(pending_key)
    if pending_delete:
        st.warning(f"Yakin ingin menghapus permanen: **{pending_delete['label']}**?")
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            confirm_delete = st.button(
                "Ya, hapus permanen",
                type="primary",
                key=f"{key}_confirm_delete",
            )
        with cancel_col:
            cancel_delete = st.button("Batalkan", key=f"{key}_cancel_delete")

        if cancel_delete:
            del st.session_state[pending_key]
            st.rerun()
        if confirm_delete:
            latest_records = load_records().reset_index(drop=True)
            reduced_records = _delete_record(
                latest_records,
                pending_delete["row_index"],
                pending_delete["snapshot"],
            )
            if reduced_records is None:
                del st.session_state[pending_key]
                st.error("Data sudah berubah sejak dipilih. Muat ulang lalu pilih kembali.")
            else:
                save_records(reduced_records)
                del st.session_state[pending_key]
                st.success(f"{title} berhasil dihapus.")
                st.rerun()


def render():
    st.markdown("## 🧾 Edit & Hapus Transaksi dan Laporan")
    st.caption("Pilih data untuk memperbarui isinya atau menghapusnya secara permanen.")

    spg_tab, supervisi_tab = st.tabs(["Transaksi Penjualan SPG", "Laporan Supervisi"])
    with spg_tab:
        st.markdown("#### Transaksi Penjualan SPG")
        _render_record_manager(
            "transaksi penjualan SPG",
            "admin_spg_records",
            load_database,
            save_database,
            ["Waktu", "Promotor", "Nama_SPG", "Brand_Rokok", "Nama_Konsumen"],
        )

    with supervisi_tab:
        st.markdown("#### Laporan Supervisi")
        _render_record_manager(
            "laporan supervisi",
            "admin_supervisi_records",
            load_supervisi_database,
            save_supervisi_database,
            ["Waktu", "Promotor", "Kecamatan", "Warkop_LKK"],
        )

    st.stop()
