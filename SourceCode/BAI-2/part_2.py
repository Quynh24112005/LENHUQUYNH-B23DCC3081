# -*- coding: utf-8 -*-
import pandas as pd
import os
import numpy as np
import traceback

INPUT_CSV = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI1\results.csv'
STATS_SUMMARY_FILE = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI2\results2.csv'

# --- Cau hinh ---
EXCLUDED_COLUMNS_FROM_TOP3 = [
    'Player', 'Nation', 'Team', 'Position', 'Age'
]
na_values_list = ['N/a', 'n/a', 'NA', 'na', 'NaN', 'nan', '']

try:
    # --- Buoc 1: Doc du lieu ---
    print(f"Doc du lieu tu: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV, na_values=na_values_list, encoding='utf-8')
    df.columns = df.columns.str.strip()
    if 'Team' not in df.columns:
        print("Loi: Khong tim thay cot 'Team'.")
        exit()
    df['Team'] = df['Team'].str.strip()
    print("Doc du lieu thanh cong.")

    # --- Buoc 2: Xac dinh va chuan bi cac cot so ---
    print("\n--- Buoc 2: Xac dinh va chuan bi cot so ---")
    potential_numeric_cols = [col for col in df.columns if col not in EXCLUDED_COLUMNS_FROM_TOP3]
    numeric_cols = []
    print(f"Tong so cot tiem nang (tru cac cot loai tru): {len(potential_numeric_cols)}")

    problematic_cols_check = ['Possession: Receiving: Rec', 'Possession: Receiving: PrgR', 'Possession: Carries: PrgC']
    print(f"Se kiem tra chi tiet cac cot: {problematic_cols_check}")

    for col in potential_numeric_cols:
        if col in df.columns:
            is_problematic = col in problematic_cols_check
            if is_problematic:
                print(f"\n--- Kiem tra cot '{col}' ---")
                print(f"   Kieu du lieu goc: {df[col].dtype}")
                print(f"   5 gia tri dau:\n{df[col].head().to_string(index=False)}")
                print(f"   So gia tri NA ban dau: {df[col].isna().sum()}")

            original_dtype = df[col].dtype
            if df[col].dtype == 'object':
                if is_problematic: print("   Phat hien kieu object, thay the dau phay...")
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                if is_problematic: print("   Da thay the dau phay.")

            if is_problematic: print("   Chuyen sang so dung pd.to_numeric...")
            df[col] = pd.to_numeric(df[col], errors='coerce')
            converted_dtype = df[col].dtype
            if is_problematic: print(f"   Kieu du lieu sau chuyen doi: {converted_dtype}")

            has_valid_numeric = df[col].notna().any()
            if is_problematic: print(f"   Co gia tri hop le? {has_valid_numeric}")

            if has_valid_numeric:
                numeric_cols.append(col)
                if is_problematic: print(f"   => Cot '{col}' DUOC them vao danh sach cot so.")
            else:
                print(f"Canh bao: Cot '{col}' khong the chuyen thanh so hoac chi co NA.")
                if is_problematic:
                    print(f"   => Cot '{col}' KHONG DUOC them.")
                    print(f"      Kieu goc: {original_dtype}, Sau chuyen doi: {converted_dtype}")
                    print(f"      5 gia tri dau sau khi coerce:\n{df[col].head().to_string(index=False)}")
        else:
            print(f"Canh bao: Cot '{col}' khong ton tai trong DataFrame.")

    print("\n--- Kiem tra cuoi cung sau Buoc 2 ---")
    for check_col in problematic_cols_check:
        if check_col in numeric_cols:
            print(f"Cot '{check_col}' CO trong danh sach cuoi.")
        else:
            print(f"Cot '{check_col}' KHONG CO trong danh sach cuoi.")
    print(f"Tong so cot la so: {len(numeric_cols)}")

    if not numeric_cols:
        print("Loi: Khong tim thay cot so hop le.")
        exit()

    # --- Buoc 3: Tinh toan thong ke tong the ---
    print("\n--- Buoc 3: Tinh thong ke tong the ---")
    overall_stats = df[numeric_cols].agg(['median', 'mean', 'std']).T
    overall_stats.columns = ['Median', 'Mean', 'Std']
    print("Tinh toan thong ke tong the hoan tat.")

    # --- Buoc 4: Tao hang 'all' ---
    print("\n--- Buoc 4: Tao hang 'all' ---")
    all_row_data = {'Team': ['all']}
    for col in numeric_cols:
        col_median = f'Median of {col}'
        col_mean = f'Mean of {col}'
        col_std = f'Std of {col}'
        if col in overall_stats.index:
            all_row_data[col_median] = [overall_stats.loc[col, 'Median']]
            all_row_data[col_mean] = [overall_stats.loc[col, 'Mean']]
            all_row_data[col_std] = [overall_stats.loc[col, 'Std']]
        else:
            all_row_data[col_median] = [pd.NA]
            all_row_data[col_mean] = [pd.NA]
            all_row_data[col_std] = [pd.NA]
    all_row_df = pd.DataFrame(all_row_data)
    print("Tao hang 'all' hoan tat.")

    # --- Buoc 5: Tinh thong ke theo doi ---
    print("\n--- Buoc 5: Tinh thong ke theo doi ---")
    team_stats = df.groupby('Team')[numeric_cols].agg(['median', 'mean', 'std'], numeric_only=True)
    print("Tinh thong ke theo doi hoan tat.")

    # --- Buoc 6: Tao DataFrame theo doi ---
    print("\n--- Buoc 6: Tao DataFrame theo doi ---")
    team_names = team_stats.index.tolist()
    team_results_data = {'Team': team_names}
    for col in numeric_cols:
        col_median = f'Median of {col}'
        col_mean = f'Mean of {col}'
        col_std = f'Std of {col}'
        median_key = (col, 'median')
        mean_key = (col, 'mean')
        std_key = (col, 'std')
        team_results_data[col_median] = team_stats[median_key].reindex(team_names).values if median_key in team_stats.columns else [pd.NA] * len(team_names)
        team_results_data[col_mean] = team_stats[mean_key].reindex(team_names).values if mean_key in team_stats.columns else [pd.NA] * len(team_names)
        team_results_data[col_std] = team_stats[std_key].reindex(team_names).values if std_key in team_stats.columns else [pd.NA] * len(team_names)
    team_results_df = pd.DataFrame(team_results_data)
    print("Tao DataFrame theo doi hoan tat.")

    # --- Buoc 7: Ket hop ket qua ---
    print("\n--- Buoc 7: Ket hop ket qua ---")
    final_results = pd.concat([all_row_df, team_results_df], ignore_index=True)
    print("Ket hop hoan tat.")

    # --- Buoc 8: Luu ket qua ---
    print("\n--- Buoc 8: Luu ket qua ---")
    print(f"Luu ket qua vao: {STATS_SUMMARY_FILE}")
    final_results.to_csv(STATS_SUMMARY_FILE, index=False, encoding='utf-8-sig', float_format='%.3f')
    print("Luu tep thanh cong!")

    # --- Buoc 9: Xem truoc ket qua ---
    print("\n--- Buoc 9: Xem truoc ket qua ---")
    print("\n5 dong dau cua ket qua:")
    with pd.option_context('display.max_rows', 5, 'display.max_columns', 10, 'display.width', 1000):
        print(final_results.head())

# --- Xu ly loi ---
except FileNotFoundError:
    print(f"Loi: Khong tim thay tep tai '{INPUT_CSV}'.")
except KeyError as e:
    print(f"Loi: Khong tim thay cot {e}.")
except Exception as e:
    print("Loi khac xay ra:")
    traceback.print_exc()
