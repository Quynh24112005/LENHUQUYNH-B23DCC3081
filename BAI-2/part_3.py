import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# --- 1. Xac dinh duong dan va doc du lieu ---
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, '..', 'BAI-1', 'results.csv')

# Tao thu muc luu bieu do
output_image_dir = os.path.join(current_dir, 'histograms')
os.makedirs(output_image_dir, exist_ok=True)
print(f"Cac tep anh histogram se duoc luu tai: {output_image_dir}")

try:
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Tep khong ton tai tai duong dan: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='latin1')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='iso-8859-1')

    print(f"Tai du lieu thanh cong tu: {csv_path}")

except FileNotFoundError as fnf_error:
    print(f"Loi: {fnf_error}")
    df = None
except Exception as e:
    print(f"Loi khong xac dinh khi doc tep CSV: {e}")
    df = None

# --- 2. Chon cac cot chi so ---
columns_to_plot = [
    'Playing Time: matches played',
    'Playing Time: starts',
    'Performance: goals'
]

# --- 3. Kiem tra va xu ly du lieu ---
data_to_plot = {}
if df is not None:
    for col in columns_to_plot:
        if col not in df.columns:
            print(f"Loi: Khong tim thay cot '{col}' trong tep CSV.")
            print(f"Cac cot co san: {list(df.columns)}")
            continue

        column_data = df[col].copy()
        column_data_numeric = pd.to_numeric(column_data, errors='coerce')
        column_data_filled = column_data_numeric.fillna(0)
        data_to_plot[col] = column_data_filled
        print(f"Da xu ly cot: '{col}'")
else:
    print("Khong the xu ly du lieu do khong co DataFrame.")

# --- 4. Ve va luu bieu do histogram ---
def sanitize_filename(name):
    name = name.replace(' ', '_')
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name

sns.set_style("whitegrid")

if data_to_plot:
    print("\nBat dau ve va luu bieu do...")
    for col_name, data in data_to_plot.items():
        fig = plt.figure(figsize=(8, 5))
        sns.histplot(data, kde=False, bins='auto')
        plt.title(f'Phan phoi cua: {col_name}', fontsize=14)
        plt.xlabel(col_name, fontsize=12)
        plt.ylabel('So luong cau thu', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)

        safe_col_name = sanitize_filename(col_name)
        output_filename = f'histogram_{safe_col_name}.png'
        output_path = os.path.join(output_image_dir, output_filename)

        try:
            plt.savefig(output_path, bbox_inches='tight')
            print(f"Da luu bieu do vao: {output_path}")
        except Exception as save_error:
            print(f"Loi khi luu bieu do '{output_path}': {save_error}")

        plt.close(fig)

    print("\nHoan thanh viec ve va luu bieu do histogram.")
else:
    print("\nKhong co du lieu hop le de ve bieu do.")
