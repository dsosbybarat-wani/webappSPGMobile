import json
import os
import threading
import uuid

import requests

from config.constants import SUPABASE_ENTRY_QUEUE_FILE
from core.backup import get_supabase_config
from core.storage import write_json_atomic


_QUEUE_LOCK = threading.Lock()
_ENTRY_TYPES = {"spg_sale", "supervisor_report"}


def _read_queue(queue_path):
    if not os.path.exists(queue_path):
        return []
    try:
        with open(queue_path, "r", encoding="utf-8") as file:
            queue = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Antrean sinkronisasi Supabase tidak dapat dibaca.") from exc

    if not isinstance(queue, list) or any(
        not isinstance(entry, dict)
        or not {"id", "entry_type", "data"}.issubset(entry)
        for entry in queue
    ):
        raise RuntimeError("Format antrean sinkronisasi Supabase tidak valid.")
    return queue


def enqueue_supabase_entry(entry_type, data, queue_path=SUPABASE_ENTRY_QUEUE_FILE):
    if entry_type not in _ENTRY_TYPES:
        raise ValueError(f"Tipe entry Supabase tidak dikenal: {entry_type}")
    if not isinstance(data, dict):
        raise ValueError("Data entry Supabase harus berupa object.")

    entry = {
        "id": str(uuid.uuid4()),
        "entry_type": entry_type,
        "data": data,
    }
    with _QUEUE_LOCK:
        queue = _read_queue(queue_path)
        queue.append(entry)
        write_json_atomic(queue_path, queue)
    return entry["id"]


def _post_supabase_entry(entry):
    supabase_url, supabase_key = get_supabase_config()
    try:
        response = requests.post(
            f"{supabase_url}/rest/v1/app_entries",
            params={"on_conflict": "id"},
            json=[entry],
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=ignore-duplicates,return=minimal",
            },
            timeout=(10, 30),
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Supabase entry sync mengembalikan HTTP {response.status_code}: "
            f"{response.text[:300]}"
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError("Tidak dapat menghubungi Supabase untuk menyinkronkan entry.") from exc


def flush_supabase_entry_queue(queue_path=SUPABASE_ENTRY_QUEUE_FILE):
    synced_count = 0
    with _QUEUE_LOCK:
        queue = _read_queue(queue_path)
        while queue:
            _post_supabase_entry(queue[0])
            queue = queue[1:]
            write_json_atomic(queue_path, queue)
            synced_count += 1
    return synced_count


def pending_supabase_entry_count(queue_path=SUPABASE_ENTRY_QUEUE_FILE):
    with _QUEUE_LOCK:
        return len(_read_queue(queue_path))
