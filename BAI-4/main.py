# thu.py (Phiên bản cuối cùng - Sua ScrapeOrder bat dau tu 1)
import os
import re
import time
import json
import logging
import traceback
from contextlib import contextmanager
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# --- Phan con lai cua config, imports, get_driver, helpers giu nguyen ---
# Lay thu muc chua tep script nay (thu.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# === Cau hinh ===
config = {
    "output_folder": os.path.join(current_dir, "output_part4_final"),
    "part1_results_filename": r"D:\PTIT\NAM2\KI2\Python\ASS-1\BAI-1\results.csv", # Duong dan tuyet doi
    "scraped_all_data_filename": "scraped_all_data_temp.csv",
    "estimation_output_filename": "estimation_data.csv",
    "scraping": {
        "transfer_url": "https://www.footballtransfers.com/us/players/uk-premier-league",
        "wait_time": 15,
        "player_table_selector": "tbody#player-table-body",
        "player_row_selector": "tr",
        "player_name_selector": "td.td-player div.text > a",
        "nation_selector": "td.nationality span.ficon",
        "position_selector": "td.td-player span.sub-text.d-none.d-md-block",
        "age_selector": "td.m-hide.age",
        "team_name_selector": "td.td-team span.td-team__teamname",
        "skill_selector": "div.table-skill__skill",
        "potential_selector": "div.table-skill__pot",
        "etv_selector": "td.text-center > span.player-tag",
        "next_page_selector": "button.pagination_next_button:not([disabled])"
    },
    "processing": {
        "internal_etv_var": "ETV_Parsed",
        "part1_minutes_column": "Playing Time: minutes",
        "min_minutes_threshold": 900,
        "part1_player_column": "Player"
    }
}
config['scraped_file_path'] = os.path.join(config['output_folder'], config['scraped_all_data_filename'])
config['final_output_path'] = os.path.join(config['output_folder'], config['estimation_output_filename'])
config['part1_file_path'] = config['part1_results_filename']
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@contextmanager
def get_driver():
    opts = Options()
    # opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--log-level=3')
    opts.add_argument("start-maximized")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(45)
        yield driver
    except Exception as e:
        logging.error(f"LOI: Khong the khoi tao WebDriver: {e}")
        logging.error("Dam bao ChromeDriver da duoc cai dat, tuong thich voi Chrome va nam trong PATH he thong.")
        yield None
    finally:
        if driver:
            try:
                driver.quit()
                logging.debug("WebDriver da dong.")
            except Exception as e_quit:
                logging.warning(f"Loi khi dong WebDriver: {e_quit}")

def get_element_text(elem, selector, default='N/a'):
    try:
        target = elem.select_one(selector)
        return target.get_text(strip=True) if target else default
    except Exception: return default

def get_element_attribute(elem, selector, attribute, default='N/a'):
    try:
        target = elem.select_one(selector)
        return target.get(attribute, default) if target else default
    except Exception: return default

def parse_value(val):
    if not isinstance(val, str) or val == 'N/a' or val == '': return None
    val = re.sub(r'[€£$ ]', '', val.lower().strip())
    mul = 1.0
    if 'm' in val: mul = 1_000_000.0; val = val.replace('m', '')
    elif 'k' in val: mul = 1_000.0; val = val.replace('k', '')
    try: return (float(val) * mul) / 1_000_000.0
    except ValueError: logging.warning(f"Khong the chuyen doi gia tri ETV: {val}"); return None

def parse_skill_potential(val_str):
    if not isinstance(val_str, str) or val_str == 'N/a' or val_str == '': return None
    try:
        cleaned_val = val_str.strip()
        return float(cleaned_val)
    except ValueError:
        try:
            cleaned_val = val_str.split('/')[0].strip()
            return float(cleaned_val)
        except (ValueError, IndexError):
            logging.warning(f"Khong the chuyen doi skill/potential thanh float: {val_str}")
            return None

# --- Scraping Function (Thay doi dong khoi tao counter) ---
def scrape(driver):
    if not driver:
        logging.error("WebDriver khong kha dung de scraping.")
        return []
    data_list = []
    # *** THAY ĐỔI Ở ĐÂY: Khởi tạo từ 1 ***
    scrape_order_counter = 1
    # ***********************************
    cfg = config['scraping']
    wait = WebDriverWait(driver, cfg['wait_time'])
    try:
        driver.get(cfg['transfer_url'])
        logging.info(f"Da truy cap URL: {cfg['transfer_url']}")
    except Exception as e:
        logging.error(f"Loi tai URL {cfg['transfer_url']}: {e}")
        return []

    page = 1
    last_known_element = None
    while True:
        logging.info(f"--- Bat dau quet trang {page} ---")
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, cfg['player_table_selector'])))
            last_row_selector = f"{cfg['player_table_selector']} {cfg['player_row_selector']}:last-child"
            last_known_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, last_row_selector)))
            logging.debug(f"Bang va hang cuoi trang {page} da hien thi.")
            time.sleep(1.5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table_body = soup.select_one(cfg['player_table_selector'])
            if not table_body:
                logging.warning(f"Khong tim thay table body tren trang {page}. Ket thuc quet.")
                break
            rows = table_body.select(cfg['player_row_selector'])
            if not rows:
                logging.info(f"Khong tim thay hang cau thu nao tren trang {page}. Ket thuc quet.")
                break

            logging.info(f"Tim thay {len(rows)} hang tren trang {page}.")
            for row in rows:
                player = get_element_text(row, cfg['player_name_selector'])
                if player and player != 'N/a':
                    nation = get_element_attribute(row, cfg['nation_selector'], 'title')
                    position = get_element_text(row, cfg['position_selector'])
                    age = get_element_text(row, cfg['age_selector'])
                    team = get_element_text(row, cfg['team_name_selector'])
                    skill_raw = get_element_text(row, cfg['skill_selector'])
                    potential_raw = get_element_text(row, cfg['potential_selector'])
                    etv_raw = get_element_text(row, cfg['etv_selector'])

                    skill_parsed = parse_skill_potential(skill_raw)
                    potential_parsed = parse_skill_potential(potential_raw)
                    etv_parsed = parse_value(etv_raw)

                    data_list.append({
                        'ScrapeOrder': scrape_order_counter, # Gan gia tri counter
                        'Player': player.strip(),
                        'Nation_Internal': nation,
                        'Position': position,
                        'Age': age,
                        'Team_Internal': team,
                        'Skill': skill_parsed,
                        'Potential': potential_parsed,
                        'ETV_Raw_Internal': etv_raw,
                        config['processing']['internal_etv_var']: etv_parsed
                    })
                    scrape_order_counter += 1 # Tang counter sau khi gan

            # Pagination
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, cfg['next_page_selector'])))
                driver.execute_script("arguments[0].click();", next_btn)
                logging.info("Da nhan nut 'Next page'.")
                try:
                    WebDriverWait(driver, cfg['wait_time']).until(EC.staleness_of(last_known_element))
                    logging.debug(f"Noi dung trang {page} da cu.")
                except TimeoutException:
                    logging.warning("Noi dung trang cu khong bi stale. Su dung delay co dinh.")
                    time.sleep(3)
                page += 1
            except (NoSuchElementException, TimeoutException):
                logging.info("Khong tim thay nut 'Next page' kha dung. Ket thuc phan trang.")
                break
            except Exception as e_click:
                 logging.error(f"Loi khi nhan nut next page: {e_click}")
                 break

        except StaleElementReferenceException:
            logging.warning(f"Loi StaleElementReferenceException tren trang {page}. Thu lai...")
            time.sleep(1)
            continue
        except TimeoutException as e_page:
            logging.error(f"Loi Timeout khi cho phan tu tren trang {page}: {e_page.msg}")
            break
        except Exception as e:
             logging.error(f"Loi khong xac dinh khi quet trang {page}: {e}", exc_info=True)
             break
    logging.info(f"Ket thuc qua trinh quet. Thu thap duoc {len(data_list)} ban ghi.")
    return data_list

# --- Processing Function (Giu nguyen logic loc theo ten) ---
def process(scraped_data_list):
    """
    Tai results.csv, tao set ten hop le (>900phut).
    Loc du lieu quet theo set ten nay.
    Sap xep, doi ten/chon cot, va luu ket qua cuoi cung.
    """
    if not scraped_data_list:
        logging.warning("Khong co du lieu duoc quet de xu ly.")
        return None

    # 1. Tai results.csv va tao set ten cau thu hop le (>900 phut)
    valid_player_set = set()
    try:
        results_file_path = config['part1_file_path']
        if not os.path.exists(results_file_path):
            logging.error(f"LOI: Khong tim thay tep input: '{results_file_path}'. Vui long kiem tra duong dan.")
            logging.error("Hay dam bao ban chay script nay tu dung vi tri (vi du: ASS-1/BAI-4).")
            return None
        df_results = pd.read_csv(results_file_path)
        logging.info(f"Da tai du lieu tu '{results_file_path}'. Shape: {df_results.shape}")

        player_col = config['processing']['part1_player_column']
        minutes_col = config['processing']['part1_minutes_column']
        if player_col not in df_results.columns or minutes_col not in df_results.columns:
            logging.error(f"Cac cot '{player_col}' hoac '{minutes_col}' khong ton tai trong {results_file_path}.")
            return None

        df_results['minutes_numeric'] = pd.to_numeric(df_results[minutes_col].astype(str).str.replace(',', '', regex=False), errors='coerce')
        df_results = df_results.dropna(subset=['minutes_numeric'])
        min_minutes = config['processing']['min_minutes_threshold']
        df_filtered_results = df_results[df_results['minutes_numeric'] >= min_minutes]

        valid_player_set = set(df_filtered_results[player_col].astype(str).str.strip().unique())
        logging.info(f"Da xac dinh duoc {len(valid_player_set)} ten cau thu hop le voi >= {min_minutes} phut.")

    except Exception as e:
        logging.error(f"Loi khi xu ly tep results '{results_file_path}': {e}")
        return None

    if not valid_player_set:
        logging.warning("Khong tim thay cau thu nao hop le (>900 phut) tu results.csv.")

    # 2. Chuyen doi du lieu quet thanh DataFrame
    df_scraped = pd.DataFrame(scraped_data_list)
    internal_req_cols = ['ScrapeOrder', 'Player', 'Position', 'Age', 'Team_Internal', 'Skill', 'Potential', 'ETV_Raw_Internal', config['processing']['internal_etv_var']]
    for col in internal_req_cols:
        if col not in df_scraped.columns: df_scraped[col] = pd.NA
    logging.info(f"Da chuyen doi du lieu quet thanh DataFrame. Shape: {df_scraped.shape}")
    try:
        os.makedirs(config['output_folder'], exist_ok=True)
        df_scraped.to_csv(config['scraped_file_path'], index=False, encoding='utf-8-sig')
        logging.info(f"Da luu du lieu quet trung gian vao '{config['scraped_file_path']}'")
    except Exception as e: logging.warning(f"Khong the luu du lieu quet trung gian: {e}")


    # 3. *** LOC DU LIEU QUET THEO SET TEN HOP LE ***
    if df_scraped.empty:
         logging.warning("Du lieu quet rong, khong the loc.")
         df_filtered = pd.DataFrame()
    elif not valid_player_set:
         logging.warning("Set ten cau thu hop le rong, ket qua loc se rong.")
         df_filtered = pd.DataFrame()
    else:
         df_filtered = df_scraped[df_scraped['Player'].astype(str).str.strip().isin(valid_player_set)].copy()
         logging.info(f"Shape du lieu sau khi loc theo ten hop le: {df_filtered.shape}")

    if df_filtered.empty:
        logging.warning("Khong co cau thu nao tu du lieu quet khop voi danh sach ten hop le (>900 phut).")
        final_columns_target = ['Player', 'Team_TransferSite', 'Age', 'Position', 'Skill', 'Potential', 'TransferValueRaw', 'TransferValue_EUR_Millions']
        empty_df = pd.DataFrame(columns=final_columns_target)
        try:
             os.makedirs(config['output_folder'], exist_ok=True)
             empty_df.to_csv(config['final_output_path'], index=False, encoding='utf-8-sig')
             logging.info(f"Da luu tep rong voi header dung vao '{config['final_output_path']}'")
        except Exception as e: logging.error(f"Loi khi luu tep output rong: {e}")
        return empty_df

    # 4. Sap xep theo thu tu quet ban dau
    if 'ScrapeOrder' in df_filtered.columns:
        df_filtered_sorted = df_filtered.sort_values(by='ScrapeOrder').reset_index(drop=True)
        logging.info("Da sap xep du lieu theo thu tu quet.")
    else:
        logging.warning("Khong tim thay cot 'ScrapeOrder' de sap xep.")
        df_filtered_sorted = df_filtered

    # 5. Doi ten va chon cac cot cuoi cung khop voi estimation_data.csv
    final_columns_target = ['Player', 'Team_TransferSite', 'Age', 'Position', 'Skill', 'Potential', 'TransferValueRaw', 'TransferValue_EUR_Millions']
    rename_mapping = {
        'Team_Internal': 'Team_TransferSite',
        'ETV_Raw_Internal': 'TransferValueRaw',
        config['processing']['internal_etv_var']: 'TransferValue_EUR_Millions'
    }
    cols_to_rename_exist = {k: v for k, v in rename_mapping.items() if k in df_filtered_sorted.columns}
    df_renamed = df_filtered_sorted.rename(columns=cols_to_rename_exist)
    final_df_cols_exist = [col for col in final_columns_target if col in df_renamed.columns]
    missing_target_cols = [col for col in final_columns_target if col not in final_df_cols_exist]
    if missing_target_cols:
        logging.warning(f"Cac cot muc tieu bi thieu sau khi xu ly/doi ten: {missing_target_cols}. Chung se khong co trong output.")
    df_final_output = df_renamed[final_df_cols_exist]

    # 6. Luu ket qua cuoi cung
    try:
        for col in ['Skill', 'Potential', 'TransferValue_EUR_Millions']:
             if col in df_final_output.columns:
                  df_final_output[col] = pd.to_numeric(df_final_output[col], errors='coerce').astype(float)
        if 'Age' in df_final_output.columns:
             df_final_output['Age'] = df_final_output['Age'].astype(str)

        df_final_output.to_csv(config['final_output_path'], index=False, encoding='utf-8-sig')
        logging.info(f"Du lieu cuoi cung da duoc luu vao '{config['final_output_path']}'")
    except Exception as e:
        logging.error(f"Loi khi luu tep output cuoi cung: {e}")
        return None
    return df_final_output

# --- Main Execution Block ---
def main():
    """Ham chinh dieu phoi qua trinh scraping va processing."""
    start_time = time.time()
    logging.info("Bat dau scraping va xu ly du lieu (Phien ban 1 tep, loc theo ten)...")
    scraped_player_data = []

    with get_driver() as driver:
        if driver:
            scraped_player_data = scrape(driver)
        else:
            logging.error("Khong the lay WebDriver, bo qua buoc scraping.")

    final_data = process(scraped_player_data)

    if final_data is not None:
         logging.info(f"Xu ly hoan tat. Shape DataFrame cuoi cung: {final_data.shape}")
    else:
         logging.error("Xu ly that bai hoac tra ve None.")

    end_time = time.time()
    logging.info(f"Tap lenh hoan thanh trong {end_time - start_time:.2f} giay.")

# Diem vao chinh cua chuong trinh
if __name__ == "__main__":
    main()