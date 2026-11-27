import os

import sqlparse
import streamlit as st
from sqlparse.tokens import Comment


def get_supabase_database_url():
    try:
        database_url = st.secrets.get(
            "SUPABASE_DB_URL",
            os.environ.get("SUPABASE_DB_URL"),
        )
    except FileNotFoundError:
        database_url = os.environ.get("SUPABASE_DB_URL")

    if not database_url:
        raise RuntimeError(
            "SUPABASE_DB_URL belum diatur. Simpan connection string PostgreSQL "
            "Supabase di Streamlit secrets atau environment."
        )
    return database_url


def split_sql_statements(query):
    statements = []
    for statement in sqlparse.split(query):
        parsed_statements = sqlparse.parse(statement)
        contains_sql = any(
            token.value.strip()
            and token.value != ";"
            and token.ttype not in Comment
            for parsed in parsed_statements
            for token in parsed.flatten()
        )
        if contains_sql:
            statements.append(statement.strip())
    if not statements:
        raise ValueError("Masukkan setidaknya satu perintah SQL.")
    return statements


def execute_supabase_sql(query, max_rows=1000):
    from psycopg import Error as PsycopgError
    from psycopg import connect

    statements = split_sql_statements(query)
    database_url = get_supabase_database_url()
    results = []

    try:
        with connect(
            database_url,
            connect_timeout=10,
            sslmode="require",
            options="-c statement_timeout=60000 -c lock_timeout=10000",
        ) as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
                    if cursor.description:
                        columns = [column.name for column in cursor.description]
                        rows = cursor.fetchmany(max_rows + 1)
                        results.append(
                            {
                                "columns": columns,
                                "rows": rows[:max_rows],
                                "truncated": len(rows) > max_rows,
                                "rowcount": cursor.rowcount,
                            }
                        )
                    else:
                        results.append(
                            {
                                "columns": [],
                                "rows": [],
                                "truncated": False,
                                "rowcount": cursor.rowcount,
                            }
                        )
    except PsycopgError as exc:
        raise RuntimeError(f"Eksekusi SQL gagal: {exc}") from exc

    return results
