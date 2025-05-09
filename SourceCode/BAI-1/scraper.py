# -*- coding: utf-8 -*-
import time
from typing import List, Dict, Optional, Any

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def safe_cast_int(value_str: Optional[str], default: int = 0) -> int:
    if not value_str or value_str == 'N/a':
        return default
    try:
        cleaned_str = value_str.replace(',', '')
        return int(cleaned_str)
    except (ValueError, TypeError):
        print(f"[LOI] Khong the chuyen '{value_str}' sang so nguyen.")
        return default

class Player:
    def __init__(self, **kwargs: Any):
        self.data: Dict[str, Any] = kwargs

    def update(self, **kwargs: Any) -> None:
        self.data.update(kwargs)

    def export(self, export_keys: List[str]) -> List[Any]:
        return [self.data.get(key, 'N/a') for key in export_keys]

    def __repr__(self) -> str:
        name = self.data.get('player', 'Unknown Player')
        team = self.data.get('team', 'Unknown Team')
        age = self.data.get('age', 'N/A')
        return f"<Player: {name} ({age} - {team})>"

def get_soup(url: str, table_id: str, retries: int = 3, delay: int = 5) -> Optional[BeautifulSoup]:
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = None
    for attempt in range(retries):
        try:
            print(f"[THU] Lan thu {attempt + 1}/{retries} de lay du lieu tu {url} voi bang {table_id}")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, table_id)))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table_check = soup.find('table', id=table_id)
            if table_check and len(table_check.find_all('tr')) > 1:
                print(f"[THANH CONG] Da lay duoc noi dung cua bang {table_id}")
                return soup
            else:
                print(f"[CANH BAO] Bang {table_id} ton tai nhung trong hoac chua tai xong (lan {attempt + 1})")
                if driver: driver.quit()
                time.sleep(delay)
                continue
        except Exception as e:
            print(f"[LOI] Lan thu {attempt + 1}/{retries} that bai voi URL {url}, bang {table_id}: {e}")
            if driver: driver.quit()
            if attempt < retries - 1:
                print(f"Doi {delay} giay roi thu lai...")
                time.sleep(delay)
            else:
                print("[LOI] Da thu toi da. Khong the lay du lieu.")
                return None
        finally:
            if driver: driver.quit()
    return None

def _parse_player_row(row: Tag, fields: List[str]) -> Optional[Dict[str, str]]:
    player_data: Dict[str, str] = {}
    player_name: Optional[str] = None

    for field in fields:
        cell = row.find('td', {'data-stat': field})
        player_data[field] = cell.text.strip() if cell else 'N/a'
        if field == 'player':
            player_name = player_data[field]

    if not player_name or player_name == 'Player' or player_name == 'N/a':
        return None

    return player_data

def get_players_from_table(url: str, table_id: str, fetch_fields: List[str], min_mins: int) -> List[Player]:
    print(f"[THONG TIN] Dang lay du lieu cau thu tu bang '{table_id}' tai {url}...")
    soup = get_soup(url, table_id)
    if not soup:
        print(f"[LOI] Khong the tao soup tu bang '{table_id}'. Bo qua.")
        return []

    table = soup.find('table', id=table_id)
    if not table:
        print(f"[LOI] Khong tim thay bang co ID '{table_id}' tai {url}.")
        return []

    rows = table.find_all('tr')
    players: List[Player] = []
    processed_count = 0

    extract_fields = set(fetch_fields)
    extract_fields.add('player')
    extract_fields.add('minutes')

    for row in rows:
        if row.find('th', {'scope': 'col'}): continue

        player_data = _parse_player_row(row, list(extract_fields))
        if not player_data: continue

        mins_played = safe_cast_int(player_data.get('minutes'))
        if mins_played <= min_mins: continue

        players.append(Player(**player_data))
        processed_count += 1

    print(f"[THONG TIN] Tim thay {processed_count} cau thu hop le (> {min_mins} phut) trong bang: {table_id}")
    return players

def update_players(players: List[Player], url: str, table_id: str, update_fields: List[str]) -> None:
    print(f"[THONG TIN] Dang cap nhat du lieu tu bang '{table_id}' tai {url}...")
    soup = get_soup(url, table_id)
    if not soup:
        print(f"[CANH BAO] Bo qua cap nhat tu bang {table_id} do loi khi lay du lieu.")
        return

    table = soup.find('table', id=table_id)
    if not table:
        print(f"[LOI] Khong tim thay bang cap nhat co ID '{table_id}' tai {url}.")
        return

    rows = table.find_all('tr')
    updates_count = 0
    player_key_field = 'player'

    for row in rows:
        if row.find('th', {'scope': 'col'}): continue

        name_cell = row.find('td', {'data-stat': player_key_field})
        if not name_cell: continue
        update_name = name_cell.text.strip()

        found_players = [p for p in players if p.data.get('player') == update_name]
        if found_players:
            updates_data: Dict[str, str] = {}
            for field in update_fields:
                cell = row.find('td', {'data-stat': field})
                updates_data[field] = cell.text.strip() if cell else 'N/a'

            for player_obj in found_players:
                player_obj.update(**updates_data)
                updates_count += 1

    print(f"[THONG TIN] Da cap nhat {updates_count} ban ghi tu bang {table_id}.")
    time.sleep(1.5)
