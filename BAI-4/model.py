import os
import re
import time
import json
import logging
from contextlib import contextmanager
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
current_dir = os.path.dirname(os.path.abspath(__file__))
# Hardcoded config
config = {
     "output_folder": os.path.join(current_dir, "output"),
    "scraping": {
        "transfer_url": "https://www.footballtransfers.com/us/players/uk-premier-league",
        "wait_time": 10,
        "player_table_selector": ".table",
        "player_row_selector": ".row",
        "player_name_selector": ".name",
        "team_name_selector": ".team",
        "etv_selector": ".value",
        "next_page_selector": ".next"
    },
    "processing": {
        "target_variable": "TransferValue",
        "part1_minutes_column": "Playing Time: minutes",
        "min_minutes_threshold": 900,
        "part1_player_column": "Player",
        "part1_team_column": "Team"
    },
    "part1_results_filename": os.path.join(current_dir,'..','BAI-1', "results.csv"),    
    "transfer_value_output_filename": "transfer_output.csv",
    "estimation_ready_data_filename": "estimation.csv"
}

config['transfer_file'] = os.path.join(config['output_folder'], config['transfer_value_output_filename'])
config['estimation_file'] = os.path.join(config['output_folder'], config['estimation_ready_data_filename'])
config['part1_file'] = config['part1_results_filename']

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@contextmanager
def get_driver():
    opts = Options()
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--log-level=3')
    driver = webdriver.Chrome(options=opts)
    try:
        yield driver
    finally:
        driver.quit()


def get_text(elem, selector, default='N/a'):
    try:
        target = elem.select_one(selector)
        return target.get_text(strip=True) if target else default
    except:
        return default


def parse_value(val):
    if not isinstance(val, str) or val == 'N/a':
        return None
    val = re.sub(r'[€£$]', '', val.lower().strip())
    mul = 1
    if 'm' in val:
        mul = 1_000_000
        val = val.replace('m', '')
    elif 'k' in val:
        mul = 1_000
        val = val.replace('k', '')
    try:
        return (float(val) * mul) / 1_000_000
    except:
        return None


def scrape(driver):
    data = {}
    cfg = config['scraping']
    wait = WebDriverWait(driver, cfg['wait_time'])
    driver.get(cfg['transfer_url'])
    page = 1
    while True:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"{cfg['player_table_selector']} {cfg['player_row_selector']}")))
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.select_one(cfg['player_table_selector'])
            if not table:
                break
            rows = table.select(cfg['player_row_selector'])
            for row in rows:
                player = get_text(row, cfg['player_name_selector'])
                team = get_text(row, cfg['team_name_selector'])
                etv = get_text(row, cfg['etv_selector'])
                if player != 'N/a' and team != 'N/a':
                    key = (player, team)
                    if key not in data:
                        data[key] = {
                            'Player': player,
                            'Team_TransferSite': team,
                            'TransferValueRaw': etv,
                            config['processing']['target_variable']: parse_value(etv)
                        }
            try:
                next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, cfg['next_page_selector'])))
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)
                page += 1
            except (NoSuchElementException, TimeoutException):
                break
        except TimeoutException:
            break
    return data


def process(scraped):
    try:
        df1 = pd.read_csv(config['part1_file'])
    except:
        logging.error("Failed to load Part1 file.")
        return None

    minutes_col = config['processing']['part1_minutes_column']
    min_minutes = config['processing']['min_minutes_threshold']
    player_col = config['processing']['part1_player_column']
    team_col = config['processing']['part1_team_column']
    target_var = config['processing']['target_variable']

    if minutes_col not in df1.columns:
        logging.error("Minutes column missing.")
        return None

    df1['minutes_numeric'] = pd.to_numeric(df1[minutes_col].str.replace(',', ''), errors='coerce')
    df1 = df1.dropna(subset=['minutes_numeric'])
    df1 = df1[df1['minutes_numeric'] > min_minutes].drop(columns=['minutes_numeric'])

    if scraped:
        df2 = pd.DataFrame.from_dict(scraped, orient='index').reset_index()
        if 'index' in df2.columns and isinstance(df2['index'].iloc[0], tuple):
            df2[['Player', 'Team_TransferSite']] = pd.DataFrame(df2['index'].tolist(), index=df2.index)
            df2 = df2.drop(columns=['index'])
        merged = pd.merge(df1, df2[['Player', 'Team_TransferSite', 'TransferValueRaw', target_var]],
                          left_on=[player_col, team_col], right_on=['Player', 'Team_TransferSite'], how='left')
        merged[target_var].fillna(pd.NA, inplace=True)
        merged['TransferValueRaw'].fillna('N/a', inplace=True)
        merged['Team_TransferSite'].fillna('N/a', inplace=True)
    else:
        merged = df1.copy()
        merged['Team_TransferSite'] = 'N/a'
        merged['TransferValueRaw'] = 'N/a'
        merged[target_var] = pd.NA

    os.makedirs(config['output_folder'], exist_ok=True)
    merged.to_csv(config['transfer_file'], index=False, encoding='utf-8-sig')
    merged.to_csv(config['estimation_file'], index=False, encoding='utf-8-sig')

    return merged


def main():
    start = time.time()
    with get_driver() as driver:
        scraped = scrape(driver)
        final = process(scraped)
        if final is not None:
            logging.info(f"Done. Final data shape: {final.shape}")
        else:
            logging.warning("No data processed.")
    logging.info(f"Total time: {time.time() - start:.2f}s")


if __name__ == '__main__':
    main()
