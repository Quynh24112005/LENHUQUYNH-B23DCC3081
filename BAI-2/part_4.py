import pandas as pd
import numpy as np
import os

# --- Buoc 1: Dinh nghia duong dan ---
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(current_dir, 'results2.csv')

try:
    df_results2 = pd.read_csv(csv_file)

    # Doi ten cot dau tien (neu can) va dat lam index
    df_results2 = df_results2.rename(columns={'Unnamed: 0': 'Team'})
    df_results2 = df_results2.set_index('Team')

    # Bo dong 'all' de chi lay du lieu tung doi
    df_teams = df_results2.drop('all', errors='ignore')

    # Tim cac cot co chua gia tri trung binh
    mean_cols = [col for col in df_teams.columns if col.startswith('Mean of')]

    highest_scoring_teams = {}

    print("Dang tim doi co diem trung binh cao nhat moi chi so...\n")
    for col in mean_cols:
        stat_name = col.replace('Mean of ', '', 1)
        numeric_col = pd.to_numeric(df_teams[col], errors='coerce')

        if numeric_col.isnull().all():
            highest_scoring_teams[stat_name] = "N/A (Khong co du lieu hop le)"
            continue

        try:
            team_with_highest = numeric_col.idxmax(skipna=True)
            highest_score = numeric_col.max(skipna=True)

            if pd.isna(team_with_highest):
                highest_scoring_teams[stat_name] = "N/A (Toan bo la NaN)"
            else:
                highest_scoring_teams[stat_name] = f"{team_with_highest} ({highest_score:.2f})"
        except Exception as e:
            highest_scoring_teams[stat_name] = f"N/A (Loi: {e})"

    # Thong ke so lan moi doi dan dau
    leader_teams = [team.split(' (')[0] for team in highest_scoring_teams.values() if isinstance(team, str) and ' (' in team]
    leader_counts = pd.Series(leader_teams).value_counts()

    # --- Hien thi ket qua ---
    print("--- Doi co diem trung binh cao nhat moi chi so ---")
    for stat, team_info in highest_scoring_teams.items():
        print(f"- {stat}: {team_info}")

    print("\n--- Phan tich: Doi thi dau tot nhat ---")
    print("\nSo lan moi doi dan dau:")
    print(leader_counts)

    if not leader_counts.empty:
        top_team = leader_counts.idxmax()
        print(f"\nDua tren so chi so dan dau, '{top_team}' la doi xuat hien nhieu nhat.")

        key_stats = [
            'Performance: goals', 'Performance: assists', 'Expected: xG',
            'Per 90 minutes: Gls', 'Per 90 minutes: Ast', 'Per 90 minutes: xG',
            'Goalkeeping: Performance: GA90',
            'Goalkeeping: Performance: Save%'
        ]

        print("\nKiem tra cac chi so quan trong:")
        for stat in key_stats:
            if stat in highest_scoring_teams:
                if stat == 'Goalkeeping: Performance: GA90':
                    col_name = 'Mean of Goalkeeping: Performance: GA90'
                    if col_name in df_teams.columns:
                        numeric_col = pd.to_numeric(df_teams[col_name], errors='coerce')
                        if not numeric_col.isnull().all():
                            try:
                                team_with_lowest = numeric_col.idxmin(skipna=True)
                                lowest_score = numeric_col.min(skipna=True)
                                if not pd.isna(team_with_lowest):
                                    print(f"- Thap nhat {stat}: {team_with_lowest} ({lowest_score:.2f})")
                                else:
                                    print(f"- Thap nhat {stat}: N/A (Toan bo la NaN)")
                            except Exception as e:
                                print(f"- Thap nhat {stat}: N/A (Loi khi tim min: {e})")
                        else:
                            print(f"- Thap nhat {stat}: N/A (Khong co du lieu hop le)")
                    else:
                        print(f"- {stat}: Khong tim thay cot trong file")
                else:
                    print(f"- Cao nhat {stat}: {highest_scoring_teams[stat]}")
            else:
                print(f"- {stat}: Khong tim thay du lieu trong ket qua.")
    else:
        print("\nKhong the xac dinh doi dan dau do van de ve du lieu.")

except FileNotFoundError:
    print(f"Loi: Khong tim thay tep '{csv_file}'. Vui long dam bao tep ton tai.")
except KeyError as e:
    print(f"Loi: Khong tim thay cot hoac chi muc ({e}).")
except Exception as e:
    print(f"Da xay ra loi trong qua trinh phan tich: {e}")
