import pandas as pd
import numpy as np
import os
import traceback

# --- Buoc 1: Doc config va xac dinh duong dan ---
current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    from config import OUT_FILE, HEADER_ORDER
    input_path = os.path.join(current_dir, OUT_FILE)
    print("Da import du lieu tu config.py")
except ImportError:
    print("Loi: Khong the import tu config.py. Dung duong dan mac dinh.")
    input_path = os.path.join(current_dir, '..', 'BAI-1', 'results.csv')
    HEADER_ORDER = None
except Exception as e:
    print(f"Loi khong xac dinh: {e}")
    input_path = os.path.join(current_dir, '..', 'BAI-1', 'results.csv')
    HEADER_ORDER = None

output_path = os.path.join(current_dir, 'top_3.txt')

# --- Buoc 2: Doc file CSV ---
if not os.path.exists(input_path):
    print(f"Loi: Tep '{input_path}' khong ton tai.")
    exit()

try:
    df = pd.read_csv(input_path, na_values=['N/a'])
    print("Da doc du lieu CSV thanh cong.")
except Exception as e:
    print(f"Loi khi doc file CSV: {e}")
    exit()

# --- Buoc 3: Xac dinh cot thong ke ---
player_column = 'Player'

if player_column not in df.columns:
    print(f"Loi: Cot '{player_column}' khong ton tai trong file.")
    exit()

# Xac dinh cot khong thong ke
if HEADER_ORDER:
    non_stat_cols = [col for col in ['Player', 'Nation', 'Team', 'Position', 'Age'] if col in HEADER_ORDER]
else:
    non_stat_cols = [col for col in ['Player', 'Nation', 'Team', 'Position', 'Age'] if col in df.columns]

if player_column not in non_stat_cols:
    non_stat_cols.append(player_column)

# Loc cot thong ke (kieu so)
stat_columns = []
for col in df.columns:
    if col in non_stat_cols:
        continue
    numeric_col = pd.to_numeric(df[col], errors='coerce')
    if not numeric_col.isnull().all():
        df[col] = numeric_col
        stat_columns.append(col)

if not stat_columns:
    print("Khong tim thay cot thong ke phu hop.")
    exit()

# --- Buoc 4: Xu ly top 3 va ghi ra file ---
try:
    with open(output_path, 'w', encoding='utf-8') as f:
        print("Dang xu ly va ghi top 3...")

        for stat in stat_columns:
            f.write(f"Chi so: {stat}\n")
            df_stat = df[[player_column, stat]].dropna()

            if df_stat.empty:
                f.write("Khong co du lieu hop le\n\n")
                continue

            if df_stat[stat].nunique() == 1:
                f.write(f"Tat ca cau thu cung gia tri: {df_stat[stat].iloc[0]}\n")
                top_3 = bottom_3 = df_stat.head(3)
            else:
                top_3 = df_stat.sort_values(by=stat, ascending=False).head(3)
                bottom_3 = df_stat.sort_values(by=stat, ascending=True).head(3)

            f.write("3 cau thu diem cao nhat:\n")
            for _, row in top_3.iterrows():
                f.write(f"   {row[player_column]}: {row[stat]}\n")

            f.write("3 cau thu diem thap nhat:\n")
            for _, row in bottom_3.iterrows():
                f.write(f"   {row[player_column]}: {row[stat]}\n")

            f.write("\n")

    print(f"Hoan thanh. Da luu ket qua vao: {output_path}")

except Exception as e:
    print("Loi khi ghi file:")
    traceback.print_exc()
