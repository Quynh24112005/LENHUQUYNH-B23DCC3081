import sys
import time
from typing import List, Dict, Optional, Any
import pandas as pd
import traceback

from config import (
    FBREF_BASE_URL, TABLE_IDS, TABLE_URLS, STATS_BY_TABLE,
    MIN_MINUTES, OUT_FILE, EXPORT_STATS,                
    HEADER_ORDER, HEADER_MAP                               
)
from scraper import get_players_from_table, update_players, Player

def get_first_name(full_name: Optional[str]) -> str:
    if not isinstance(full_name, str) or ' ' not in full_name:
        return full_name or ""
    return full_name.split(' ')[0]

def clean_numeric_commas(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='ignore')
    return df

def main():
    print(f"[INFO] Bat dau qua trinh lay du lieu cau thu Premier League...")
    print(f"[INFO] Lay du lieu tu mua giai tai: {FBREF_BASE_URL}")

    required_stats = set(EXPORT_STATS)

    main_table_id = TABLE_IDS['standard']
    main_url_suffix = TABLE_URLS[main_table_id]

    base_fetch_fields = set(f for f in STATS_BY_TABLE[main_table_id] if f in required_stats)
    base_fetch_fields.add('player')
    base_fetch_fields.add('minutes')
    base_req_fields = list(base_fetch_fields)

    addtl_tables = []
    for table_id, table_fields in STATS_BY_TABLE.items():
        if table_id == main_table_id:
            continue
        req_table_fields = [f for f in table_fields if f in required_stats]
        if req_table_fields:
            url_suffix = TABLE_URLS.get(table_id)
            if url_suffix:
                addtl_tables.append({
                    'url_suffix': url_suffix,
                    'table_id': table_id,
                    'fields': req_table_fields
                })
            else:
                print(f"[WARNING] Khong tim thay URL suffix cho table_id: {table_id}")

    print(f"[INFO] Lay du lieu cau thu co ban tu bang '{main_table_id}'...")
    players = get_players_from_table(
        url=f"{FBREF_BASE_URL}{main_url_suffix}",
        table_id=main_table_id,
        fetch_fields=base_req_fields,
        min_mins=MIN_MINUTES
    )

    if not players:
        print(f"[ERROR] Khong lay duoc du lieu cau thu ban dau (> {MIN_MINUTES} phut). Chuong trinh ket thuc.")
        sys.exit(1)

    for table_info in addtl_tables:
        update_players(
            players=players,
            url=f"{FBREF_BASE_URL}{table_info['url_suffix']}",
            table_id=table_info['table_id'],
            update_fields=table_info['fields']
        )
        print("-" * 30)

    print("[INFO] Chuan bi xuat du lieu...")
    if not players:
        print("[ERROR] Khong co du lieu cau thu nao sau khi xu ly. Chuong trinh ket thuc.")
        sys.exit(1)

    print("[INFO] Sap xep du lieu cau thu theo ten (First Name)...")
    sorted_players = sorted(players, key=lambda p: get_first_name(p.data.get('player', '')).lower())

    final_stat_order = EXPORT_STATS
    final_headers = HEADER_ORDER

    if sorted_players:
        sample_keys = set(sorted_players[0].data.keys())
        missing_stats = set(final_stat_order) - sample_keys
        if missing_stats:
            valid_missing = [k for k in missing_stats if k in HEADER_MAP.values()]
            if valid_missing:
                print(f"[WARNING] Cac data_stat sau day co the bi thieu trong du lieu da lay: {valid_missing}")

    print("[INFO] Tao DataFrame tu du lieu da sap xep...")
    try:
        data_to_export = [p.export(final_stat_order) for p in sorted_players]
        df = pd.DataFrame(data_to_export, columns=final_headers)
        df = clean_numeric_commas(df)

    except Exception as e:
        print(f"[ERROR] Loi khi tao DataFrame: {e}")
        traceback.print_exc()
        sys.exit(1)

    print(f"[INFO] Luu DataFrame vao file {OUT_FILE}...")
    try:
        df.to_csv(OUT_FILE, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] Du lieu da duoc luu thanh cong vao file {OUT_FILE}")

        print(f"\n[INFO] Du lieu cua {len(df)} cau thu (da sap xep theo First Name):")
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(df.to_string())

    except IOError as e:
        print(f"[ERROR] Loi khi luu file CSV '{OUT_FILE}': {e}")
    except Exception as e:
        print(f"[ERROR] Loi khong xac dinh khi xu ly DataFrame hoac luu file: {e}")

if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"\n[INFO] Tong thoi gian thuc thi: {end_time - start_time:.2f} giay.")
