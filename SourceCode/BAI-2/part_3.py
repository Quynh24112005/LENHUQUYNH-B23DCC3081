import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import math
from typing import List
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

selected_stats = [
    'Expected: xG',
    'Per 90 minutes: Gls',
    'Shooting: Standard: SoT%',
    'Performance: assists',
    'Passing: Expected: KP',
    'Passing: Expected: PrgP'
]
plot_color = 'navy'
OUTPUT_FOLDER = f'histograms_facetgrid_{len(selected_stats)}stats_filled0_output'
DEFAULT_BINS = 15
TEAM_COLUMN = 'Team'
PLOT_STYLE = "whitegrid"
DEFAULT_COL_WRAP = 5

def create_folder(path: str):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(name: str, max_len: int = 100) -> str:
    name = str(name)
    name = name.replace(':', '_').replace('/', '_').replace('\\', '_')
    name = name.replace('%', 'Percent').replace(' ', '_').replace('.', '_dot_')
    name = re.sub(r'[<>*?"|]', '', name)
    name = "_".join(filter(None, name.split('_')))
    return name.strip('_')[:max_len]

cleaned_data = None
valid_stat_columns = []

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    current_dir = os.getcwd()

csv_path = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI1\results.csv'
output_path = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI2'
os.makedirs(output_path, exist_ok=True)
print(f"Thu muc luu bieu do: {output_path}")


def read_csv_file(file_path):
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc, low_memory=False, dtype='object')
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Loi khi doc CSV '{os.path.basename(file_path)}' voi encoding '{enc}': {e}")
            return None
    print(f"Khong the doc tep {os.path.basename(file_path)} voi cac encoding da thu.")
    return None

if not os.path.isfile(csv_path):
    print(f"Loi: Tep khong ton tai: {csv_path}")
    df = None
else:
    df = read_csv_file(csv_path)
    if df is not None:
        print(f"Da tai du lieu tu: {os.path.basename(csv_path)}")
    else:
        print(f"Khong the tai du lieu tu {csv_path}")

if df is not None:
    missing_required = [col for col in [TEAM_COLUMN] + selected_stats if col not in df.columns]
    if TEAM_COLUMN not in df.columns:
        print(f"Loi nghiem trong: Khong tim thay cot doi '{TEAM_COLUMN}'. Khong the tiep tuc.")
        df = None
    elif missing_required:
        print(f"Canh bao: Cac cot sau khong tim thay trong CSV va se bi bo qua: {', '.join(missing_required)}")
        selected_stats = [stat for stat in selected_stats if stat in df.columns]

    if df is not None and selected_stats:
        required_columns = [TEAM_COLUMN] + selected_stats
        try:
            cleaned_data = df[required_columns].copy()
            print(f"Bat dau xu ly {len(selected_stats)} chi so: {', '.join(selected_stats)}")
            for stat in selected_stats:
                numeric_col = pd.to_numeric(cleaned_data[stat], errors='coerce')
                if not numeric_col.isnull().all():
                    print(f"  -> Xu ly cot '{stat}': Chuyen sang so va fillna(0).")
                    cleaned_data[stat] = numeric_col.fillna(0)
                    valid_stat_columns.append(stat)
                else:
                    print(f"  -> Canh bao: Cot '{stat}' khong chua du lieu so hop le hoac toan NaN. Da loai bo.")
                    if stat in cleaned_data.columns:
                        cleaned_data.drop(columns=[stat], inplace=True)
            if not valid_stat_columns:
                print("Khong con cot chi so nao hop le de ve bieu do.")
                cleaned_data = None
            else:
                print(f"Cac cot chi so hop le se duoc ve: {', '.join(valid_stat_columns)}")
        except KeyError as e:
            print(f"Loi KeyError khi truy cap cot: {e}. Kiem tra lai ten cot trong 'selected_stats' va file CSV.")
            cleaned_data = None
        except Exception as e:
            print(f"Loi khong xac dinh trong qua trinh lam sach du lieu: {e}")
            cleaned_data = None
    elif df is not None and not selected_stats:
        print("Khong co chi so nao trong 'selected_stats' duoc tim thay trong tep CSV.")
        cleaned_data = None

def plot_histogram_all_players_facet(df: pd.DataFrame, stat: str, output_dir: str, bins: int, color: str):
    print(f"  Dang ve histogram tong cho: {stat}")
    if stat not in df.columns:
        print(f"  -> Loi: Cot '{stat}' khong ton tai trong DataFrame.")
        return
    if df[stat].nunique() <= 1:
        print(f"  -> Canh bao: Cot '{stat}' co it hon 2 gia tri duy nhat. Bo qua ve bieu do tong.")
        return

    plt.figure(figsize=(10, 6))
    try:
        sns.histplot(df[stat], bins=bins, kde=True, color=color)
        plt.title(f'Phan phoi {stat} (Toan giai, NaN da thay bang 0)', fontsize=14)
        plt.xlabel(stat)
        plt.ylabel('Tan suat')
        plt.tight_layout()
        filename = os.path.join(output_dir, f"hist_overall_{sanitize_filename(stat)}.png")
        plt.savefig(filename)
        plt.close()
        print(f"    -> Da luu: {os.path.basename(filename)}")
    except Exception as e:
        print(f"    -> Loi khi ve bieu do tong cho '{stat}': {e}")
        plt.close()

def plot_histograms_per_team_facet(df: pd.DataFrame, stat: str, output_dir: str, bins: int, team_col: str, col_wrap: int):
    print(f"  Dang ve FacetGrid theo doi cho: {stat}")
    if stat not in df.columns:
        print(f"  -> Loi: Cot '{stat}' khong ton tai.")
        return
    if team_col not in df.columns:
        print(f"  -> Loi: Cot doi '{team_col}' khong ton tai.")
        return
    if df[stat].nunique() <= 1:
        print(f"  -> Canh bao: Cot '{stat}' co it hon 2 gia tri duy nhat. Bo qua ve FacetGrid.")
        return

    num_teams = df[team_col].nunique()
    print(f"    -> Ve cho {num_teams} doi.")

    num_rows = math.ceil(num_teams / col_wrap)
    height_per_row = 3
    aspect_ratio = 1.2

    g = None
    try:
        g = sns.FacetGrid(df, col=team_col, col_wrap=col_wrap, sharex=True, sharey=False, height=height_per_row, aspect=aspect_ratio)
        g.map(sns.histplot, stat, bins=bins, kde=False)
        g.set_titles("{col_name}", size=10)
        g.set_axis_labels(stat, "Tan suat")
        g.figure.subplots_adjust(top=0.92, hspace=0.4, wspace=0.2)
        g.figure.suptitle(f'Phan phoi {stat} theo Doi (NaN da thay bang 0)', fontsize=14, y=0.98)
        filename = os.path.join(output_dir, f"hist_facet_teams_{sanitize_filename(stat)}.png")
        g.savefig(filename)
        plt.close(g.figure)
        print(f"    -> Da luu: {os.path.basename(filename)}")
    except Exception as e:
        print(f"    -> Loi khi ve FacetGrid cho '{stat}': {e}")
        if g and hasattr(g, 'figure'):
            plt.close(g.figure)
        elif plt.gcf():
            plt.close()

if __name__ == '__main__':
    if cleaned_data is not None and valid_stat_columns:
        sns.set_theme(style=PLOT_STYLE)
        print(f"\nBat dau ve bieu do cho {len(valid_stat_columns)} chi so hop le (su dung FacetGrid, fillna(0)):")
        print(f"Danh sach chi so: {', '.join(valid_stat_columns)}")
        print("\n--- Ve bieu do toan giai ---")
        for stat in valid_stat_columns:
            plot_histogram_all_players_facet(cleaned_data, stat, output_dir=output_path, bins=DEFAULT_BINS, color=plot_color)
        print("\n--- Ve bieu do theo doi (FacetGrid) ---")
        for stat in valid_stat_columns:
            plot_histograms_per_team_facet(cleaned_data, stat, output_dir=output_path, bins=DEFAULT_BINS, team_col=TEAM_COLUMN, col_wrap=DEFAULT_COL_WRAP)
        print(f"\nHoan thanh. Da luu cac bieu do vao thu muc: '{output_path}'.")
        print("Luu y: Cac bieu do duoc tao tu du lieu da thay the gia tri thieu (NaN) bang 0.")
    else:
        print("\nKhong co du lieu hop le hoac khong tim thay tep CSV de ve bieu do.")
