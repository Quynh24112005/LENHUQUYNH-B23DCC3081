# -*- coding: utf-8 -*-

FBREF_BASE_URL = 'https://fbref.com/en/comps/9'
PL_SUFFIX = '/stats/Premier-League-Stats' 
OUT_FILE = 'Report\\OUTPUT_BAI1\\results.csv' 
MIN_MINUTES = 90

TABLE_IDS = {
    'standard': 'stats_standard',
    'keeper': 'stats_keeper',
    'shooting': 'stats_shooting',
    'passing': 'stats_passing',
    'gca': 'stats_gca',
    'defense': 'stats_defense',
    'possession': 'stats_possession',
    'misc': 'stats_misc',
}

TABLE_URLS = { 
    TABLE_IDS['standard']: PL_SUFFIX, 
    TABLE_IDS['keeper']: '/keepers/Premier-League-Stats',
    TABLE_IDS['shooting']: '/shooting/Premier-League-Stats',
    TABLE_IDS['passing']: '/passing/Premier-League-Stats',
    TABLE_IDS['gca']: '/gca/Premier-League-Stats',
    TABLE_IDS['defense']: '/defense/Premier-League-Stats',
    TABLE_IDS['possession']: '/possession/Premier-League-Stats',
    TABLE_IDS['misc']: '/misc/Premier-League-Stats',
}

HEADER_MAP = { 
    'Player': 'player',
    'Nation': 'nationality',
    'Team': 'team',
    'Position': 'position',
    'Age': 'age',
    'Playing Time: matches played': 'games',
    'Playing Time: starts': 'games_starts',
    'Playing Time: minutes': 'minutes',
    'Performance: goals': 'goals',
    'Performance: assists': 'assists',
    'Performance: yellow cards': 'cards_yellow',
    'Performance: red cards': 'cards_red',
    'Expected: xG': 'xg',
    'Expected: xAG': 'xg_assist', 
    'PrgC': 'progressive_carries',
    'PrgP': 'progressive_passes',
    'PrgR': 'progressive_passes_received',
    'Per 90 minutes: Gls': 'goals_per90',
    'Per 90 minutes: Ast': 'assists_per90',
    'Per 90 minutes: xG': 'xg_per90',
    'Per 90 minutes: xAG': 'xg_assist_per90',
    'Goalkeeping: Performance: GA90': 'gk_goals_against_per90',
    'Goalkeeping: Performance: Save%': 'gk_save_pct',
    'Goalkeeping: Performance: CS%': 'gk_clean_sheets_pct',
    'Goalkeeping: Penalty Kicks: Save%': 'gk_pens_save_pct',
    'Shooting: Standard: SoT%': 'shots_on_target_pct',
    'Shooting: Standard: SoT/90': 'shots_on_target_per90',
    'Shooting: Standard: G/Sh': 'goals_per_shot',
    'Shooting: Standard: Dist': 'average_shot_distance',
    'Passing: Total: Cmp': 'passes_completed',
    'Passing: Total: Cmp%': 'passes_pct',
    'Passing: Total: TotDist': 'passes_progressive_distance', 
    'Passing: Short: Cmp%': 'passes_pct_short',
    'Passing: Medium: Cmp%': 'passes_pct_medium',
    'Passing: Long: Cmp%': 'passes_pct_long',
    'Passing: Expected: KP': 'assisted_shots', 
    'Passing: Expected: 1/3': 'passes_into_final_third',
    'Passing: Expected: PPA': 'passes_into_penalty_area',
    'Passing: Expected: CrsPA': 'crosses_into_penalty_area',
    'Passing: Expected: PrgP': 'progressive_passes', 
    'Goal and Shot Creation: SCA: SCA': 'sca',
    'Goal and Shot Creation: SCA: SCA90': 'sca_per90',
    'Goal and Shot Creation: GCA: GCA': 'gca',
    'Goal and Shot Creation: GCA: GCA90': 'gca_per90',
    'Defensive Actions: Tackles: Tkl': 'tackles',
    'Defensive Actions: Tackles: TklW': 'tackles_won',
    'Defensive Actions: Challenges: Att': 'challenges', 
    'Defensive Actions: Challenges: Lost': 'challenges_lost',
    'Defensive Actions: Blocks: Blocks': 'blocks',
    'Defensive Actions: Blocks: Sh': 'blocked_shots', 
    'Defensive Actions: Blocks: Pass': 'blocked_passes', 
    'Defensive Actions: Blocks: Int': 'interceptions',
    'Possession: Touches: Touches': 'touches',
    'Possession: Touches: Def Pen': 'touches_def_pen_area',
    'Possession: Touches: Def 3rd': 'touches_def_3rd',
    'Possession: Touches: Mid 3rd': 'touches_mid_3rd',
    'Possession: Touches: Att 3rd': 'touches_att_3rd',
    'Possession: Touches: Att Pen': 'touches_att_pen_area',
    'Possession: Take-Ons: Att': 'take_ons',
    'Possession: Take-Ons: Succ%': 'take_ons_won_pct',
    'Possession: Take-Ons: Tkld%': 'take_ons_tackled_pct',
    'Possession: Carries: Carries': 'carries',
    'Possession: Carries: PrgDist': 'carries_progressive_distance', 
    'Possession: Carries: 1/3': 'carries_into_final_third',
    'Possession: Carries: CPA': 'carries_into_penalty_area', 
    'Possession: Carries: Mis': 'miscontrols', 
    'Possession: Carries: Dis': 'dispossessed', 
    'Possession: Receiving: Rec': 'passes_received',
    'Possession: Receiving: PrgR': 'progressive_passes_received',
    'Miscellaneous: Performance: Fls': 'fouls',
    'Miscellaneous: Performance: Fld': 'fouled',
    'Miscellaneous: Performance: Off': 'offsides',
    'Miscellaneous: Performance: Crs': 'crosses',
    'Miscellaneous: Performance: Recov': 'ball_recoveries',
    'Miscellaneous: Aerial Duels: Won': 'aerials_won',
    'Miscellaneous: Aerial Duels: Lost': 'aerials_lost',
    'Miscellaneous: Aerial Duels: Won%': 'aerials_won_pct',
}

HEADER_ORDER = [ 
    'Player', 'Nation', 'Team', 'Position', 'Age', 'Playing Time: matches played',
    'Playing Time: starts', 'Playing Time: minutes', 'Performance: goals',
    'Performance: assists', 'Performance: yellow cards', 'Performance: red cards',
    'Expected: xG', 'Expected: xAG', 'PrgC', 'PrgP', 'PrgR', 'Per 90 minutes: Gls',
    'Per 90 minutes: Ast', 'Per 90 minutes: xG', 'Per 90 minutes: xAG',
    'Goalkeeping: Performance: GA90', 'Goalkeeping: Performance: Save%',
    'Goalkeeping: Performance: CS%', 'Goalkeeping: Penalty Kicks: Save%',
    'Shooting: Standard: SoT%', 'Shooting: Standard: SoT/90', 'Shooting: Standard: G/Sh',
    'Shooting: Standard: Dist', 'Passing: Total: Cmp', 'Passing: Total: Cmp%',
    'Passing: Total: TotDist', 'Passing: Short: Cmp%', 'Passing: Medium: Cmp%',
    'Passing: Long: Cmp%', 'Passing: Expected: KP', 'Passing: Expected: 1/3',
    'Passing: Expected: PPA', 'Passing: Expected: CrsPA', 'Passing: Expected: PrgP', 
    'Goal and Shot Creation: SCA: SCA', 'Goal and Shot Creation: SCA: SCA90',
    'Goal and Shot Creation: GCA: GCA', 'Goal and Shot Creation: GCA: GCA90',
    'Defensive Actions: Tackles: Tkl', 'Defensive Actions: Tackles: TklW',
    'Defensive Actions: Challenges: Att', 'Defensive Actions: Challenges: Lost',
    'Defensive Actions: Blocks: Blocks', 'Defensive Actions: Blocks: Sh', 
    'Defensive Actions: Blocks: Pass', 
    'Defensive Actions: Blocks: Int', 
    'Possession: Touches: Touches', 'Possession: Touches: Def Pen', 
    'Possession: Touches: Def 3rd', 
    'Possession: Touches: Mid 3rd', 
    'Possession: Touches: Att 3rd', 
    'Possession: Touches: Att Pen', 
    'Possession: Take-Ons: Att', 'Possession: Take-Ons: Succ%',
    'Possession: Take-Ons: Tkld%', 'Possession: Carries: Carries',
    'Possession: Carries: PrgDist', 
    'Possession: Carries: 1/3', 
    'Possession: Carries: CPA', 
    'Possession: Carries: Mis', 
    'Possession: Carries: Dis', 
    'Possession: Receiving: Rec','Possession: Receiving: PrgR',
    'Miscellaneous: Performance: Fls', 'Miscellaneous: Performance: Fld',
    'Miscellaneous: Performance: Off', 'Miscellaneous: Performance: Crs',
    'Miscellaneous: Performance: Recov', 'Miscellaneous: Aerial Duels: Won',
    'Miscellaneous: Aerial Duels: Lost', 'Miscellaneous: Aerial Duels: Won%'
]

EXPORT_STATS = [] 
fetched_stats = set()
for col in HEADER_ORDER: 
    stat = HEADER_MAP.get(col) 
    if stat:
        EXPORT_STATS.append(stat)
        fetched_stats.add(stat)
    else:
        print(f"[ERROR] Config: Không tìm thấy mapping data-stat cho cột CSV mẫu: '{col}'.")

STATS_BY_TABLE = {
    TABLE_IDS['standard']: [
        'player', 'nationality', 'position', 'team', 'age', 'games', 'games_starts', 'minutes',
        'goals', 'assists', 'cards_yellow', 'cards_red', 'xg', 'xg_assist',
        'progressive_carries', 'progressive_passes', 'progressive_passes_received',
        'goals_per90', 'assists_per90', 'xg_per90', 'xg_assist_per90'
    ],
    TABLE_IDS['keeper']: [
        'gk_goals_against_per90', 'gk_save_pct', 'gk_clean_sheets_pct', 'gk_pens_save_pct'
    ],
    TABLE_IDS['shooting']: [
        'shots_on_target_pct', 'shots_on_target_per90', 'goals_per_shot', 'average_shot_distance'
    ],
    TABLE_IDS['passing']: [
        'passes_completed', 'passes_pct', 'passes_progressive_distance', 'passes_pct_short',
        'passes_pct_medium', 'passes_pct_long', 'assisted_shots', 'passes_into_final_third',
        'passes_into_penalty_area', 'crosses_into_penalty_area', 'progressive_passes' 
    ],
    TABLE_IDS['gca']: [
        'sca', 'sca_per90', 'gca', 'gca_per90'
    ],
    TABLE_IDS['defense']: [
        'tackles', 'tackles_won', 'challenges', 'challenges_lost', 'blocks',
        'blocked_shots', 'blocked_passes', 'interceptions'
    ],
    TABLE_IDS['possession']: [
        'touches', 'touches_def_pen_area', 'touches_def_3rd', 'touches_mid_3rd',
        'touches_att_3rd', 'touches_att_pen_area', 'take_ons', 'take_ons_won_pct',
        'take_ons_tackled_pct', 'carries', 'carries_progressive_distance', 
        'progressive_carries', 
        'carries_into_final_third', 
        'carries_into_penalty_area', 
        'miscontrols', 'dispossessed', 'passes_received', 
        'progressive_passes_received' 
    ],
    TABLE_IDS['misc']: [
        'fouls', 'fouled', 'offsides', 'crosses', 'ball_recoveries',
        'aerials_won', 'aerials_lost', 'aerials_won_pct'
    ]
}