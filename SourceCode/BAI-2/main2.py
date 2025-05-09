import pandas as pd
import numpy as np
import os
import traceback

input_path = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI1\results.csv'
output_path = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI2\top_3.txt'

try:
    from config import HEADER_ORDER
    print("Da import HEADER_ORDER tu config.py")
except ImportError:
    print("Khong the import tu config.py. Su dung mac dinh.")
    HEADER_ORDER = None
except Exception as e:
    print(f"Loi khong xac dinh khi import: {e}")
    HEADER_ORDER = None

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

stat_columns = []
for col in df.columns:
    if col in non_stat_cols:
        continue

    # Loại bỏ dấu ',' rồi chuyển sang kiểu số
    clean_col = df[col].astype(str).str.replace(',', '', regex=False)
    numeric_col = pd.to_numeric(clean_col, errors='coerce')

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
