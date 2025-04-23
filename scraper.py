# -*- coding: utf-8 -*-
# scraper.py
import time
from typing import List, Dict, Optional, Any

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def safe_cast_int(value_str: Optional[str], default: int = 0) -> int:
    """
    Chuyển đổi chuỗi sang số nguyên một cách an toàn.
    Loại bỏ dấu phẩy và trả về giá trị mặc định nếu lỗi hoặc 'N/a'.
    """
    if not value_str or value_str == 'N/a':
        return default
    try:
        cleaned_str = value_str.replace(',', '')
        return int(cleaned_str)
    except (ValueError, TypeError):
        print(f"[DEBUG] safe_cast_int: Không thể chuyển đổi '{value_str}' thành int.")
        return default

class Player:
    """Lớp đại diện cho một cầu thủ và dữ liệu thống kê của họ."""
    def __init__(self, **kwargs: Any):
        """Khởi tạo đối tượng Player với dữ liệu ban đầu."""
        self.data: Dict[str, Any] = kwargs

    def update(self, **kwargs: Any) -> None:
        """Cập nhật dữ liệu cho cầu thủ."""
        self.data.update(kwargs)

    def export(self, export_keys: List[str]) -> List[Any]: 
        """
        Xuất dữ liệu theo đúng thứ tự các data_stat key được yêu cầu.
        Trả về 'N/a' nếu key không tồn tại trong dữ liệu của cầu thủ.
        """
        return [self.data.get(key, 'N/a') for key in export_keys]

    def __repr__(self) -> str:
        """Biểu diễn đối tượng Player dưới dạng chuỗi."""
        name = self.data.get('player', 'Unknown Player')
        team = self.data.get('team', 'Unknown Team')
        age = self.data.get('age', 'N/A')
        return f"<Player: {name} ({age} - {team})>"


def get_soup(url: str, table_id: str, retries: int = 3, delay: int = 5) -> Optional[BeautifulSoup]:
    """
    Sử dụng Selenium để tải trang web, đợi bảng xuất hiện và trả về đối tượng BeautifulSoup.
    Thực hiện thử lại nếu gặp lỗi và có độ trễ giữa các lần thử.
    """
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = None
    for attempt in range(retries):
        try:
            print(f"[DEBUG] Attempt {attempt + 1}/{retries} to fetch {url} for table {table_id}")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, table_id)))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table_check = soup.find('table', id=table_id)
            if table_check and len(table_check.find_all('tr')) > 1:
                print(f"[DEBUG] Successfully fetched content for table {table_id}")
                return soup
            else:
                print(f"[WARNING] Table {table_id} found but empty or not fully loaded on attempt {attempt + 1}.")
                if driver: driver.quit()
                time.sleep(delay)
                continue
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1}/{retries} failed for URL {url}, table {table_id}: {e}")
            if driver: driver.quit()
            if attempt < retries - 1:
                print(f"Waiting {delay} seconds before retrying...")
                time.sleep(delay)
            else:
                print("[ERROR] Max retries reached. Failed to fetch content.")
                return None
        finally:
            if driver: driver.quit()
    return None

def _parse_player_row(row: Tag, fields: List[str]) -> Optional[Dict[str, str]]: 
    """Phân tích một hàng <tr> trong bảng HTML để lấy dữ liệu cầu thủ."""
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
    """
    Lấy dữ liệu cầu thủ từ bảng HTML, lọc theo số phút và trả về list các đối tượng Player.
    Cho phép các cầu thủ trùng tên.
    """
    print(f"[INFO] Fetching initial player data from table '{table_id}' at {url}...")
    soup = get_soup(url, table_id)
    if not soup:
        print(f"[ERROR] Could not get soup for table '{table_id}'. Skipping.")
        return []

    table = soup.find('table', id=table_id)
    if not table:
        print(f"[ERROR] Table with ID '{table_id}' not found at {url}.")
        return []

    rows = table.find_all('tr')
    players: List[Player] = [] 
    processed_count = 0

    # Xác định các trường cần thiết để lấy từ HTML (luôn bao gồm 'player' và 'minutes')
    extract_fields = set(fetch_fields)
    extract_fields.add('player')
    extract_fields.add('minutes')

    for row in rows:
        if row.find('th', {'scope': 'col'}): continue

        player_data = _parse_player_row(row, list(extract_fields))
        if not player_data: continue

        player_name = player_data['player']

        # Lọc theo số phút (> min_mins)
        mins_played = safe_cast_int(player_data.get('minutes'))
        if mins_played <= min_mins: continue

        # Tạo đối tượng Player và thêm vào list
        players.append(Player(**player_data))
        processed_count += 1

    print(f"[INFO] Found {processed_count} valid players (> {min_mins} minutes) in table: {table_id}")
    return players

def update_players(players: List[Player], url: str, table_id: str, update_fields: List[str]) -> None: 
    """
    Cập nhật dữ liệu cho các cầu thủ trong danh sách `players`.
    Tìm và cập nhật TẤT CẢ các cầu thủ có cùng tên.
    """
    print(f"[INFO] Updating player data from table '{table_id}' at {url}...")
    soup = get_soup(url, table_id)
    if not soup:
        print(f"[WARNING] Skipping update from table {table_id} due to fetch error.")
        return

    table = soup.find('table', id=table_id)
    if not table:
        print(f"[ERROR] Update table with ID '{table_id}' not found at {url}.")
        return

    rows = table.find_all('tr')
    updates_count = 0 
    player_key_field = 'player'

    for row in rows:
        if row.find('th', {'scope': 'col'}): continue

        name_cell = row.find('td', {'data-stat': player_key_field})
        if not name_cell: continue
        update_name = name_cell.text.strip()

        # Tìm tất cả cầu thủ trong list có cùng tên
        found_players = [p for p in players if p.data.get('player') == update_name]
        if found_players:
            # Lấy dữ liệu cập nhật từ hàng hiện tại
            updates_data: Dict[str, str] = {}
            for field in update_fields:
                cell = row.find('td', {'data-stat': field})
                updates_data[field] = cell.text.strip() if cell else 'N/a'

            # Cập nhật cho TẤT CẢ các cầu thủ tìm được có cùng tên
            for player_obj in found_players:
                player_obj.update(**updates_data)
                updates_count += 1

    print(f"[INFO] Applied updates from table {table_id} to relevant player entries (total updates: {updates_count}).")
    time.sleep(1.5)