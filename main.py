# -*- coding: utf-8 -*-
# main.py
import sys
import time
from typing import List, Dict, Optional, Any
import pandas as pd
import traceback

# Import các thành phần từ các file config và scraper
from config import (
    FBREF_BASE_URL, TABLE_IDS, TABLE_URLS, STATS_BY_TABLE,
    MIN_MINUTES, OUT_FILE, EXPORT_STATS,                
    HEADER_ORDER, HEADER_MAP                               
)
from scraper import get_players_from_table, update_players, Player

def get_first_name(full_name: Optional[str]) -> str:
    """
    Trích xuất tên (first name) từ họ tên đầy đủ.
    Trả về chuỗi rỗng nếu input không hợp lệ hoặc không có khoảng trắng.
    """
    if not isinstance(full_name, str) or ' ' not in full_name:
        return full_name or ""
    return full_name.split(' ')[0]

def main():
    """Hàm chính điều khiển luồng lấy và xử lý dữ liệu."""

    print(f"[INFO] Bắt đầu quá trình lấy dữ liệu cầu thủ Premier League...")
    print(f"[INFO] Lấy dữ liệu từ mùa giải tại: {FBREF_BASE_URL}")


    required_stats = set(EXPORT_STATS)

    main_table_id = TABLE_IDS['standard']
    main_url_suffix = TABLE_URLS[main_table_id] 
    # Xác định các trường cần fetch từ bảng chính
    base_fetch_fields = set(f for f in STATS_BY_TABLE[main_table_id] if f in required_stats) 
    base_fetch_fields.add('player')
    base_fetch_fields.add('minutes')
    base_req_fields = list(base_fetch_fields) 

    # Xác định các bảng phụ và trường cần lấy
    addtl_tables = [] 
    for table_id, table_fields in STATS_BY_TABLE.items():
        if table_id == main_table_id: continue
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
                print(f"[WARNING] Không tìm thấy URL suffix cho table_id: {table_id}")

    # --- Bắt đầu lấy dữ liệu ---
    print(f"[INFO] Lấy dữ liệu cầu thủ cơ bản từ bảng '{main_table_id}'...")
    players = get_players_from_table(
        url=f"{FBREF_BASE_URL}{main_url_suffix}",
        table_id=main_table_id,
        fetch_fields=base_req_fields, 
        min_mins=MIN_MINUTES          
    )

    if not players:
        print(f"[ERROR] Không lấy được dữ liệu cầu thủ ban đầu (> {MIN_MINUTES} phút). Chương trình kết thúc.")
        sys.exit(1)

    # --- Cập nhật dữ liệu từ các bảng phụ ---
    for table_info in addtl_tables:
        update_players(
            players=players, 
            url=f"{FBREF_BASE_URL}{table_info['url_suffix']}",
            table_id=table_info['table_id'],
            update_fields=table_info['fields'] 
        )
        print("-" * 30)

    # --- Xử lý và xuất dữ liệu ---
    print("[INFO] Chuẩn bị xuất dữ liệu...")
    if not players:
        print("[ERROR] Không có dữ liệu cầu thủ nào sau khi xử lý. Chương trình kết thúc.")
        sys.exit(1)

    print("[INFO] Sắp xếp dữ liệu cầu thủ theo tên (First Name)...")
    sorted_players = sorted(players, key=lambda p: get_first_name(p.data.get('player', '')).lower())

    # Sử dụng thứ tự cột đã xác định từ file config
    final_stat_order = EXPORT_STATS 
    final_headers = HEADER_ORDER  
    print(f"[INFO] Thứ tự cột header cuối cùng theo file CSV mẫu: {final_headers}")

    # Kiểm tra xem có thiếu dữ liệu data_stat nào không
    if sorted_players:
        sample_keys = set(sorted_players[0].data.keys())
        missing_stats = set(final_stat_order) - sample_keys 
        if missing_stats:
             valid_missing = [k for k in missing_stats if k in HEADER_MAP.values()] 
             if valid_missing:
                 print(f"[WARNING] Các data_stat sau đây có thể bị thiếu trong dữ liệu đã lấy: {valid_missing}")

    print("[INFO] Tạo DataFrame từ dữ liệu đã sắp xếp...")
    try:
        data_to_export = [p.export(final_stat_order) for p in sorted_players]
        df = pd.DataFrame(data_to_export, columns=final_headers)
    except Exception as e:
        print(f"[ERROR] Lỗi khi tạo DataFrame: {e}")
        traceback.print_exc()
        sys.exit(1)

    print(f"[INFO] Lưu DataFrame vào file {OUT_FILE}...") 
    try:
        df.to_csv(OUT_FILE, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] Dữ liệu đã được lưu thành công vào file {OUT_FILE}")

        print(f"\n[INFO] Dữ liệu của {len(df)} cầu thủ (đã sắp xếp theo First Name):")
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(df.to_string())

    except IOError as e:
         print(f"[ERROR] Lỗi khi lưu file CSV '{OUT_FILE}': {e}")
    except Exception as e:
         print(f"[ERROR] Lỗi không xác định khi xử lý DataFrame hoặc lưu file: {e}")

# --- Điểm bắt đầu thực thi ---
if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"\n[INFO] Tổng thời gian thực thi: {end_time - start_time:.2f} giây.")