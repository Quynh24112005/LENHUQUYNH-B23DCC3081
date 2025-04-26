# -*- coding: utf-8 -*-
import pandas as pd
import os
import numpy as np

# --- Dinh nghia duong dan ---
# Su dung '.' vi chung ta dang chay trong moi truong ao, khong co __file__
# Khi ban chay tren may, neu file CSV khong cung thu muc, hay sua duong dan nay
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
csv_path = os.path.join(current_dir,'..','BAI-1', 'results.csv') # File input (dam bao file nay o cung thu muc voi ma code)
# Doi ten file output de co ca median cua doi
output_filename = 'results2.csv'
output_path = os.path.join(current_dir, output_filename) # Duong dan file output

# --- Danh sach gia tri NA ---
# Cac gia tri se duoc coi la NA khi doc file CSV
na_values_list = ['N/a', 'n/a', 'NA', 'na', 'NaN', 'nan', '']

try:
    # --- Buoc 1: Doc du lieu ---
    print(f"Dang doc du lieu tu: {csv_path}")
    df = pd.read_csv(csv_path, na_values=na_values_list, encoding='utf-8')
    df.columns = df.columns.str.strip()
    if 'Team' in df.columns:
        df['Team'] = df['Team'].str.strip()
    print("Doc du lieu thanh cong.")

    # --- Buoc 2: Xac dinh va chuan bi cac cot so ---
    exclude_cols = [
        'Player', 'Nation', 'Team', 'Position', 'Age',
        'Playing Time: matches played', 'Playing Time: starts'
    ]
    available_cols = df.columns.tolist()
    stats_columns = [col for col in available_cols if col not in exclude_cols]

    if 'Playing Time: minutes' in df.columns:
        df['Playing Time: minutes'] = df['Playing Time: minutes'].astype(str).str.replace(',', '', regex=False)
        df['Playing Time: minutes'] = pd.to_numeric(df['Playing Time: minutes'], errors='coerce')

    percent_cols = [col for col in df.columns if '%' in col]
    for col in percent_cols:
        if col in df.columns and df[col].dtype == 'object':
            if df[col].astype(str).str.contains('%').any():
                df[col] = df[col].astype(str).str.replace('%', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in stats_columns:
        if df[col].dtype == 'object':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    numeric_cols = df[stats_columns].select_dtypes(include=np.number).columns.tolist()

    if not numeric_cols:
        print("Loi: Khong tim thay cot du lieu so de tinh toan thong ke.")
        exit()

    print(f"So cot so se duoc tinh toan: {len(numeric_cols)}")

    # --- Buoc 3: Tinh toan thong ke tong the (all) ---
    print("Dang tinh toan thong ke tong the (all)...")
    overall_stats = df[numeric_cols].agg(['median', 'mean', 'std']).T
    overall_stats.columns = ['Median', 'Mean', 'Std']
    print("Tinh toan thong ke tong the hoan tat.")

    # --- Buoc 4: Tao dong 'all' ---
    all_row_data = {'': ['all']}
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
    print("Tao dong 'all' hoan tat.")

    # --- Buoc 5: Tinh toan thong ke theo doi (Median, Mean, Std) ---
    print("Dang tinh toan thong ke theo doi (Median, Mean, Std)...")
    if 'Team' not in df.columns:
        print("Loi: Khong tim thay cot 'Team' de nhom.")
        exit()
    team_stats = df.groupby('Team')[numeric_cols].agg(['median', 'mean', 'std'], numeric_only=True)
    print("Tinh toan thong ke theo doi hoan tat.")

    # --- Buoc 6: Tao DataFrame ket qua theo doi ---
    team_names = team_stats.index.tolist()
    team_results_data = {'': team_names}

    for col in numeric_cols:
        col_median = f'Median of {col}'
        col_mean = f'Mean of {col}'
        col_std = f'Std of {col}'

        median_key = (col, 'median')
        mean_key = (col, 'mean')
        std_key = (col, 'std')

        if median_key in team_stats.columns:
            team_results_data[col_median] = team_stats[median_key].reindex(team_names).values
        else:
            team_results_data[col_median] = [pd.NA] * len(team_names)

        if mean_key in team_stats.columns:
            team_results_data[col_mean] = team_stats[mean_key].reindex(team_names).values
        else:
            team_results_data[col_mean] = [pd.NA] * len(team_names)

        if std_key in team_stats.columns:
            team_results_data[col_std] = team_stats[std_key].reindex(team_names).values
        else:
            team_results_data[col_std] = [pd.NA] * len(team_names)

    team_results_df = pd.DataFrame(team_results_data)
    print("Tao DataFrame ket qua theo doi hoan tat.")

    # --- Buoc 7: Ket hop ---
    print("Dang ket hop ket qua...")
    team_results_df = team_results_df.reindex(columns=all_row_df.columns, fill_value=pd.NA)
    final_results = pd.concat([all_row_df, team_results_df], ignore_index=True)
    print("Ket hop hoan tat.")

    # --- Buoc 9: Luu ket qua cuoi cung ---
    print(f"Dang luu ket qua vao: {output_path}")
    final_results.to_csv(output_path, index=False, encoding='utf-8-sig')
    print("Luu file thanh cong!")

    # --- Buoc 10: Xem truoc ---
    print("\nXem truoc 5 dong dau cua ket qua cuoi cung:")
    with pd.option_context('display.max_rows', 5, 'display.max_columns', 10):
        print(final_results.head())

except FileNotFoundError:
    print(f"Loi: Khong tim thay tep dau vao tai duong dan '{csv_path}'.")
    print("Hay dam bao tep 'results.csv' nam trong cung thu muc voi ma Python nay.")
except KeyError as e:
    print(f"Loi: Khong tim thay cot {e}. Kiem tra lai du lieu dau vao hoac danh sach exclude_cols.")
except Exception as e:
    print(f"Da xay ra loi khong xac dinh: {e}")
