from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, csv, re, pandas as pd
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
import traceback
import os
import unicodedata
import random

MAIN_URL = "https://www.footballtransfers.com/us/players/uk-premier-league"
RESULTS_CSV_PATH = "Report/OUTPUT_BAI1/results.csv" 
ALL_PLAYERS_FILE = "Report/OUTPUT_BAI4/all_players_scraped.csv" 
OVER_900_FILE = "Report/OUTPUT_BAI4/players_over_900_filtered.csv" 
WAIT_TIMEOUT = 15 
SHORT_WAIT_TIMEOUT = 7 
TIME_SLEEP_AFTER_PAGE_LOAD = 3 
TIME_SLEEP_DETAIL_PAGE = 3 
NEXT_BUTTON_SELECTOR = "button.pagination_next_button:not([disabled])"

def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', name)
    normalized = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return normalized.lower().strip()

def parse_etv(value_str):
    if not value_str or value_str.lower() in ['n/a', 'na', '']:
        return None
    text = re.sub(r'[€£$ ,]', '', value_str.lower())
    multiplier = 1e6 if 'm' in text else (1e3 if 'k' in text else 1.0)
    numeric_part = text.replace('m', '').replace('k', '')
    try:
        return round(float(numeric_part) * multiplier / 1e6, 2)
    except ValueError:
        return None

def load_eligible_players(min_minutes=900):
    eligible_players_set = set()
    try:
        print(f"Dang tai danh sach cau thu du dieu kien tu: {RESULTS_CSV_PATH}")
        df = pd.read_csv(RESULTS_CSV_PATH)
        if 'Player' not in df.columns or 'Playing Time: minutes' not in df.columns:
             print(f"Loi: Thieu cot 'Player' hoac 'Playing Time: minutes' trong '{RESULTS_CSV_PATH}'.")
             return eligible_players_set

        df['mins'] = pd.to_numeric(df['Playing Time: minutes'].astype(str).str.replace(',', '', regex=False), errors='coerce')
        eligible_df = df.dropna(subset=['mins'])
        eligible_df = eligible_df[eligible_df['mins'] > min_minutes]

        for player_name in eligible_df['Player']:
             if pd.notna(player_name):
                  normalized = normalize_name(str(player_name))
                  if normalized:
                      eligible_players_set.add(normalized)

        print(f"Da tai va chuan hoa {len(eligible_players_set)} ten cau thu du dieu kien tu CSV (> {min_minutes} phut).")
        return eligible_players_set

    except FileNotFoundError:
        print(f"Loi: Khong tim thay tep '{RESULTS_CSV_PATH}'. Viec loc file >900 phut se khong thuc hien duoc.")
        return eligible_players_set
    except Exception as e:
        print(f"Loi: Khong the doc hoac xu ly file results.csv: {e}")
        traceback.print_exc()
        return eligible_players_set

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

all_results = [] 
eligible_players_set = load_eligible_players()

try:
    print(f"Dang tai trang dau tien: {MAIN_URL}")
    driver.get(MAIN_URL)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody#player-table-body"))
    )
    print("Trang danh sach da tai, tim thay bang cau thu.")
    time.sleep(TIME_SLEEP_AFTER_PAGE_LOAD)

    page_num = 1
    total_rows_processed_across_pages = 0
    total_players_collected_before_filter = 0

    while True:
        print(f"\nDang xu ly du lieu trang {page_num}...")
        try:
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tbody#player-table-body"))
            )
        except TimeoutException:
            print(f"    Timeout khi cho bang du lieu tren trang {page_num}. Co the da het trang hoac loi tai trang.")
            break

        rows_on_current_page = driver.find_elements(By.CSS_SELECTOR, "tbody#player-table-body tr")
        print(f"    Tim thay {len(rows_on_current_page)} cau thu tren trang {page_num}.")
        if not rows_on_current_page and page_num > 1:
            print("    Khong tim thay cau thu nao tren trang nay, co the da het du lieu.")
            break

        for i, row in enumerate(rows_on_current_page):
            name, detail_url, team, age, pos = "N/A", None, "N/A", "N/A", "N/A"
            current_etv_text, highest_etv_text = "N/A", "N/A"
            current_etv_parsed, highest_etv_parsed = None, None
            
            total_rows_processed_across_pages += 1

            try:
                try:
                    link_elem = row.find_element(By.CSS_SELECTOR, "td.td-player div.text > a")
                    name = link_elem.text.strip()
                    detail_url = link_elem.get_attribute("href")
                except NoSuchElementException:
                    continue

                if not name or not detail_url:
                    continue
                
                print(f"    Dang xu ly: {name} (Hang {i+1} - Trang {page_num})") 
                
                try:
                    team = row.find_element(By.CSS_SELECTOR, "td.td-team span.td-team__teamname").text.strip()
                except NoSuchElementException: team = "N/A"

                try:
                    age_raw_text = row.find_element(By.CSS_SELECTOR, "td.m-hide.age").text.strip()
                    age = age_raw_text.split("-")[0].strip()
                except NoSuchElementException: age = "N/A"

                try:
                    pos = row.find_element(By.CSS_SELECTOR, "td.td-player span.sub-text").text.strip()
                except NoSuchElementException: pos = "N/A"
                
                try:
                    etv_elem = row.find_element(By.CSS_SELECTOR, "span.player-tag")
                    current_etv_text = etv_elem.text.strip()
                except NoSuchElementException: current_etv_text = "N/A"
                
                current_etv_parsed = parse_etv(current_etv_text)
                #Highest ETV
                main_window_handle = driver.current_window_handle
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(detail_url)
                
                time.sleep(TIME_SLEEP_DETAIL_PAGE) 

                highest_etv_text = "N/A"
                divs = driver.find_elements(By.CSS_SELECTOR, "div.d-col")
                for div_element in divs: 
                    try:
                        label = div_element.find_element(By.CSS_SELECTOR, "span.txt")
                        if "Highest ETV" in label.text: 
                            value = div_element.find_element(By.CSS_SELECTOR, "span.player-tag")
                            highest_etv_text = value.text.strip()
                            break
                    except: 
                        continue
                
                driver.close()
                driver.switch_to.window(main_window_handle)

                highest_etv_parsed = parse_etv(highest_etv_text)
                if highest_etv_parsed is None:
                    highest_etv_parsed = current_etv_parsed
                
                # Them du lieu vao all_results
                all_results.append({
                    "Player": name,
                    "Team": team,
                    "Age": age,
                    "Position": pos,
                    "TransferValue_EUR_Millions": current_etv_parsed,
                    "Highest_ETV_EUR_Millions": highest_etv_parsed
                })
                total_players_collected_before_filter += 1
                print(f" Da thu thap {name}: Current ETV = {current_etv_parsed}MEUR, Highest = {highest_etv_parsed}MEUR")
                time.sleep(random.uniform(0.5, 1.2))

            except TimeoutException as e_timeout_row:
                print(f" Timeout khi xu ly chi tiet cho {name if name != 'N/A' else f'hang {i+1}'}. Loi: {e_timeout_row}. Bo qua.")
                if driver.current_window_handle != main_window_handle and len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(main_window_handle)
                continue
            except Exception as e_row:
                print(f"    Loi khi xu ly chi tiet cho {name if name != 'N/A' else f'hang {i+1}'}: {type(e_row).__name__} - {e_row}. Bo qua.")
                if driver.current_window_handle != main_window_handle and len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(main_window_handle)
                continue
        
        print(f"    Da xu ly {len(rows_on_current_page)} hang tren trang {page_num}. Tong so cau thu da thu thap: {total_players_collected_before_filter}")
        try:
            next_button = WebDriverWait(driver, SHORT_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, NEXT_BUTTON_SELECTOR))
            )
            print(f"    Tim thay nut 'Next page'. Dang chuyen sang trang {page_num + 1}...")
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(0.5)
            try:
                next_button.click()
            except ElementClickInterceptedException:
                print("        Click thuong bi chan, thu click bang JavaScript...")
                driver.execute_script("arguments[0].click();", next_button)

            page_num += 1
            time.sleep(TIME_SLEEP_AFTER_PAGE_LOAD)

        except TimeoutException:
            print("Khong tim thay nut 'Next page' hoac da het trang. Ket thuc thu thap du lieu tu web.")
            break
        except Exception as e_pagination:
            print(f"Loi trong qua trinh phan trang: {type(e_pagination).__name__} - {e_pagination}")
            traceback.print_exc()
            break

    print(f"\nHoan tat cao du lieu tu tat ca cac trang.")
    print(f"    Tong so hang da duyet qua tren web: {total_rows_processed_across_pages}")
    print(f"    Tong so cau thu co du lieu duoc thu thap (truoc khi loc): {total_players_collected_before_filter}")

except Exception as e_global:
    print(f"Loi tong the nghiem trong trong qua trinh cao du lieu: {e_global}")
    traceback.print_exc()
finally:
    if 'driver' in locals() and driver:
        driver.quit()
        print("\nTrinh duyet da dong.")

if all_results:
    df_all = pd.DataFrame(all_results)
    columns_to_keep = [
        "Player", "Team", "Age", "Position", 
        "TransferValue_EUR_Millions", "Highest_ETV_EUR_Millions"
    ]
    existing_columns = [col for col in columns_to_keep if col in df_all.columns]
    df_all_to_save = df_all[existing_columns] 

    output_dir_all = os.path.dirname(ALL_PLAYERS_FILE)
    if output_dir_all and not os.path.exists(output_dir_all):
        os.makedirs(output_dir_all)
        
    df_all_to_save.to_csv(ALL_PLAYERS_FILE, index=False, encoding="utf-8-sig")
    print(f"Da luu tat ca {len(df_all_to_save)} cau thu cao duoc vao: {ALL_PLAYERS_FILE}")

    if eligible_players_set: 
        df_all_to_save['normalized_player'] = df_all_to_save['Player'].apply(normalize_name)
        df_filtered = df_all_to_save[df_all_to_save['normalized_player'].isin(eligible_players_set)].copy()
        df_filtered = df_filtered.drop(columns=['normalized_player'])
        
        df_over_900_to_save = df_filtered[existing_columns] 

        output_dir_filtered = os.path.dirname(OVER_900_FILE)
        if output_dir_filtered and not os.path.exists(output_dir_filtered):
            os.makedirs(output_dir_filtered)
        df_over_900_to_save.to_csv(OVER_900_FILE, index=False, encoding="utf-8-sig")
        print(f"Da loc va luu {len(df_over_900_to_save)} cau thu >900 phut vao: {OVER_900_FILE}")
    else:
        print("Khong co danh sach cau thu du dieu kien tu CSV de loc cho file OVER_900_FILE.")
        
else:
    print("Khong co du lieu nao duoc cao de luu vao file.")

print("\nChuong trinh ket thuc.")