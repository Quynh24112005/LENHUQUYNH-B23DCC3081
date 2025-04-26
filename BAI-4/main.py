# Assignment 1 - Part IV Solution (Revised)

# --- Import Libraries ---
import pandas as pd
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
# Bạn có thể cần cài đặt chromedriver thủ công nếu dòng dưới lỗi
# from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np # Để dùng np.nan

# --- Configuration ---
RESULTS_CSV_PATH = 'results.csv' # Đường dẫn file kết quả từ Bài 1
TRANSFER_VALUES_OUTPUT_CSV = 'transfer_values.csv'
PREDICTED_VALUES_OUTPUT_CSV = 'predicted_transfer_values.csv'
MIN_MINUTES_PLAYED = 900
SCRAPING_TIMEOUT = 15 # Thời gian chờ tối đa (giây) cho mỗi thao tác scraping

# --- Step 1: Scrape Transfer Values ---

print("Bắt đầu đọc dữ liệu cầu thủ...")
try:
    players_df = pd.read_csv(RESULTS_CSV_PATH)
    # !! Quan trọng: Kiểm tra tên cột phút thi đấu trong file results.csv của bạn
    # !! Nếu tên cột khác 'Minutes', hãy thay đổi ở dòng dưới
    if 'Minutes' not in players_df.columns:
         # Giả sử tên cột là 'Min' nếu 'Minutes' không tồn tại
         # *** THAY 'Min' BẰNG TÊN CỘT ĐÚNG TRONG FILE CỦA BẠN ***
         minutes_col = 'Min'
         print(f"Cảnh báo: Không tìm thấy cột 'Minutes', sử dụng cột '{minutes_col}' thay thế.")
    else:
         minutes_col = 'Minutes'
         
    # Chuyển đổi cột phút sang số, lỗi sẽ thành NaN
    players_df[minutes_col] = pd.to_numeric(players_df[minutes_col], errors='coerce')
    
    # Lọc cầu thủ
    players_to_scrape = players_df[players_df[minutes_col] > MIN_MINUTES_PLAYED].copy()
    
    # !! Quan trọng: Kiểm tra tên cột tên cầu thủ trong file results.csv của bạn
    # !! Nếu tên cột khác 'Player', hãy thay đổi ở dòng dưới
    if 'Player' not in players_to_scrape.columns:
        # *** THAY 'PlayerName' BẰNG TÊN CỘT ĐÚNG TRONG FILE CỦA BẠN ***
        player_name_col = 'PlayerName' 
        print(f"Cảnh báo: Không tìm thấy cột 'Player', sử dụng cột '{player_name_col}' thay thế.")
    else:
        player_name_col = 'Player'
        
    print(f"Đã đọc {len(players_df)} cầu thủ, lọc còn {len(players_to_scrape)} cầu thủ có > {MIN_MINUTES_PLAYED} phút.")

except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file {RESULTS_CSV_PATH}. Hãy đảm bảo file này tồn tại.")
    exit()
except KeyError as e:
    print(f"Lỗi: Không tìm thấy cột cần thiết ({e}) trong {RESULTS_CSV_PATH}. Kiểm tra lại tên cột.")
    exit()
except Exception as e:
    print(f"Lỗi không xác định khi đọc file: {e}")
    exit()


print("Thiết lập trình duyệt Selenium...")
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Chạy ẩn, không mở cửa sổ trình duyệt
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage') # Cần thiết khi chạy trong môi trường hạn chế như Docker
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36") # Giả lập user agent

try:
    # Sử dụng WebDriver Manager
    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
    # Hoặc nếu cài thủ công:
    # CHROME_DRIVER_PATH = '/đường/dẫn/tới/chromedriver'
    # service = ChromeService(executable_path=CHROME_DRIVER_PATH)
    # driver = webdriver.Chrome(service=service, options=options)
    
    wait = WebDriverWait(driver, SCRAPING_TIMEOUT)
    print("Trình duyệt đã sẵn sàng.")
except Exception as e:
    print(f"Lỗi khi khởi tạo WebDriver: {e}")
    print("Hãy đảm bảo Chrome và ChromeDriver đã được cài đặt đúng cách.")
    exit()

transfer_data = []
print(f"Bắt đầu scraping dữ liệu giá trị chuyển nhượng cho {len(players_to_scrape)} cầu thủ...")

# Lặp qua DataFrame đã lọc
for index, row in players_to_scrape.iterrows():
    name = row[player_name_col]
    print(f"Đang tìm kiếm: {name}...")
    value = 'N/a' # Giá trị mặc định nếu không tìm thấy

    try:
        driver.get('https://www.footballtransfers.com/')
        
        # *** THAY THẾ SELECTOR CHO Ô TÌM KIẾM NẾU CẦN ***
        search_box_selector = (By.CSS_SELECTOR, 'input[placeholder*="Search player"]') 
        search_box = wait.until(EC.element_to_be_clickable(search_box_selector))
        search_box.clear()
        search_box.send_keys(name)
        search_box.send_keys(Keys.RETURN)
        
        # Chờ kết quả tải xong (có thể cần chờ một phần tử cụ thể của trang kết quả)
        # *** THAY THẾ SELECTOR CHO PHẦN TỬ GIÁ TRỊ NẾU CẦN ***
        # Thử tìm trực tiếp giá trị (trường hợp trang cầu thủ hiện ngay)
        try:
            value_element_selector = (By.CSS_SELECTOR, '.player-info__value > span') 
            value_element = wait.until(EC.visibility_of_element_located(value_element_selector))
            value = value_element.text
            print(f"  Tìm thấy giá trị trực tiếp: {value}")
        except TimeoutException:
            # Nếu không thấy giá trị trực tiếp, thử click vào kết quả đầu tiên
            print(f"  Không thấy giá trị trực tiếp, thử click kết quả đầu tiên...")
            try:
                 # *** THAY THẾ SELECTOR CHO LINK KẾT QUẢ ĐẦU TIÊN NẾU CẦN ***
                 first_result_selector = (By.CSS_SELECTOR, '.search-result-item a') 
                 first_result = wait.until(EC.element_to_be_clickable(first_result_selector))
                 first_result.click()
                 
                 # Chờ trang cầu thủ tải và tìm giá trị
                 # *** THAY THẾ SELECTOR CHO PHẦN TỬ GIÁ TRỊ TRÊN TRANG CẦU THỦ NẾU CẦN ***
                 value_element_selector_profile = (By.CSS_SELECTOR, '.player-info__value > span') 
                 value_element = wait.until(EC.visibility_of_element_located(value_element_selector_profile))
                 value = value_element.text
                 print(f"  Tìm thấy giá trị sau khi click: {value}")
            except TimeoutException:
                 print(f"  Không tìm thấy giá trị hoặc kết quả đầu tiên cho {name} sau khi chờ.")
                 value = 'N/a'
            except NoSuchElementException:
                 print(f"  Không tìm thấy phần tử link kết quả đầu tiên cho {name}.")
                 value = 'N/a'

        transfer_data.append({player_name_col: name, 'TransferValue_Raw': value})
        
        # Thêm độ trễ nhỏ, ngẫu nhiên để tránh bị chặn
        time.sleep(random.uniform(1.5, 3.5)) 

    except TimeoutException:
        print(f"  Lỗi Timeout khi tìm kiếm hoặc tải trang cho {name}.")
        transfer_data.append({player_name_col: name, 'TransferValue_Raw': 'N/a'})
    except NoSuchElementException:
        print(f"  Lỗi NoSuchElement: Không tìm thấy ô tìm kiếm cho {name} (kiểm tra selector!).")
        transfer_data.append({player_name_col: name, 'TransferValue_Raw': 'N/a'})
    except Exception as e:
        print(f"  Lỗi không xác định khi xử lý {name}: {e}")
        transfer_data.append({player_name_col: name, 'TransferValue_Raw': 'N/a'})

# Đóng trình duyệt
driver.quit()
print("Đã đóng trình duyệt Selenium.")

# Tạo DataFrame và lưu giá trị thô
df_transfer_raw = pd.DataFrame(transfer_data)
df_transfer_raw.to_csv('transfer_values_raw.csv', index=False) # Lưu file thô để kiểm tra
print(f"Đã lưu giá trị chuyển nhượng thô vào transfer_values_raw.csv")

# --- Step 2: Clean Transfer Values and Merge Data ---

print("Bắt đầu làm sạch dữ liệu giá trị chuyển nhượng...")

def clean_value(val):
    """Hàm làm sạch giá trị tiền tệ (ví dụ: €100m, €500k, 1.5m)"""
    if pd.isna(val) or isinstance(val, (int, float)) or val.strip().lower() in ['n/a', '']:
        return np.nan # Trả về NaN nếu là số, NaN, N/a hoặc rỗng
    
    val = str(val).strip().lower()
    val = re.sub(r'[€$£,]', '', val) # Bỏ ký hiệu tiền tệ và dấu phẩy
    
    multiplier = 1
    if 'm' in val:
        multiplier = 1_000_000
        val = re.sub(r'm', '', val).strip()
    elif 'k' in val:
        multiplier = 1_000
        val = re.sub(r'k', '', val).strip()
        
    try:
        # Xử lý trường hợp còn lại (chỉ có số hoặc số thập phân)
        cleaned_val = float(val) * multiplier
        return cleaned_val
    except ValueError:
        # Nếu không thể chuyển đổi thành số sau khi làm sạch
        print(f"  Cảnh báo: Không thể chuyển đổi giá trị '{val}' thành số.")
        return np.nan # Trả về NaN nếu không chuyển đổi được

# Áp dụng hàm làm sạch
df_transfer_raw['TransferValue'] = df_transfer_raw['TransferValue_Raw'].apply(clean_value)

# Lưu file đã làm sạch (bao gồm cả giá trị gốc để đối chiếu)
df_transfer_cleaned = df_transfer_raw[[player_name_col, 'TransferValue_Raw', 'TransferValue']]
df_transfer_cleaned.to_csv(TRANSFER_VALUES_OUTPUT_CSV, index=False)
print(f"Đã lưu giá trị chuyển nhượng đã làm sạch vào {TRANSFER_VALUES_OUTPUT_CSV}")

# Gộp dữ liệu gốc với dữ liệu chuyển nhượng đã làm sạch
print("Gộp dữ liệu thống kê và giá trị chuyển nhượng...")
# Sử dụng how='inner' để chỉ giữ lại những cầu thủ có trong cả hai bảng VÀ có giá trị chuyển nhượng hợp lệ
full_data = pd.merge(players_to_scrape, df_transfer_cleaned[[player_name_col, 'TransferValue']], on=player_name_col, how='inner')

# Loại bỏ các hàng mà TransferValue là NaN sau khi merge và làm sạch
initial_rows = len(full_data)
full_data = full_data.dropna(subset=['TransferValue'])
print(f"Đã gộp dữ liệu. Bỏ {initial_rows - len(full_data)} hàng không có giá trị chuyển nhượng hợp lệ.")
print(f"Số lượng cầu thủ còn lại để huấn luyện: {len(full_data)}")

# --- Step 3: Feature Selection and Preprocessing ---

print("Chuẩn bị dữ liệu cho mô hình...")

# *** QUAN TRỌNG: CHỌN VÀ ĐẢM BẢO TÊN CỘT ĐÚNG VỚI FILE results.csv CỦA BẠN ***
# Đây là danh sách gợi ý, bạn cần điều chỉnh dựa trên file results.csv thực tế
# và phần giải thích trong báo cáo của bạn.
features = [
    'Age', 
    minutes_col, # Sử dụng biến tên cột phút đã xác định ở trên
    # Performance
    'Gls', 'Ast', 
    # Expected
    'xG', 'xAG', 
    # Shooting
    'SoT%', 'SoT/90', 'G/Sh', 'Dist', 
    # Passing
    'Cmp%', 'KP', '1/3', 'PPA', 'PrgP',
    # Goal/Shot Creation
    'SCA90', 'GCA90',
    # Defensive
    'TklW', 'Blocks', 'Int',
    # Possession
    'Succ%', # % Rê bóng thành công
    'PrgC', # Kéo bóng tịnh tiến
    'PrgR' # Nhận bóng tịnh tiến
    # Thêm các đặc trưng khác nếu cần và có trong file results.csv
]

# Kiểm tra xem các cột đặc trưng có tồn tại không
missing_features = [f for f in features if f not in full_data.columns]
if missing_features:
    print(f"Lỗi: Các cột đặc trưng sau không tồn tại trong dữ liệu đã gộp: {missing_features}")
    print("Hãy kiểm tra lại danh sách 'features' và file 'results.csv'.")
    exit()

# Chọn đặc trưng (X) và mục tiêu (y)
X = full_data[features].copy() # Tạo bản sao để tránh SettingWithCopyWarning
y = full_data['TransferValue']

# Xử lý các giá trị thiếu (NaN) trong các cột đặc trưng (X)
# Sử dụng SimpleImputer để thay thế NaN bằng giá trị trung bình của cột
print("Xử lý giá trị thiếu trong các đặc trưng (thay bằng trung bình)...")
# Chuyển đổi tất cả các cột đặc trưng sang dạng số, lỗi sẽ thành NaN
for col in features:
    X[col] = pd.to_numeric(X[col], errors='coerce')

imputer = SimpleImputer(strategy='mean') 
X_imputed = imputer.fit_transform(X)
# Chuyển lại thành DataFrame để giữ tên cột
X = pd.DataFrame(X_imputed, columns=features, index=X.index) 

# Kiểm tra lại NaN sau khi impute
if X.isnull().values.any():
     print("Cảnh báo: Vẫn còn giá trị NaN trong X sau khi impute. Kiểm tra lại dữ liệu.")
     # Có thể dropna ở đây nếu vẫn còn: X = X.dropna()
     # Hoặc điều tra nguyên nhân
     # Cần đảm bảo y cũng được lọc tương ứng nếu dropna X: y = y[X.index]

# --- Step 4: Train Model ---
# Chia dữ liệu thành tập huấn luyện và tập kiểm tra
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Chia dữ liệu: {len(X_train)} mẫu huấn luyện, {len(X_test)} mẫu kiểm tra.")

print("Huấn luyện mô hình Random Forest Regressor...")
# Khởi tạo và huấn luyện mô hình (có thể tinh chỉnh hyperparameters sau)
# Giải thích lựa chọn mô hình này trong báo cáo của bạn
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1) # n_jobs=-1 để dùng tất cả CPU cores
model.fit(X_train, y_train)
print("Huấn luyện hoàn tất.")

# --- Step 5: Evaluate Model ---
print("Đánh giá mô hình...")
y_pred = model.predict(X_test)

# Tính toán các chỉ số lỗi
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse) # Hoặc mean_squared_error(y_test, y_pred, squared=False)
mae = mean_absolute_error(y_test, y_pred)
r2 = model.score(X_test, y_test) # R-squared

print(f"Kết quả đánh giá trên tập kiểm tra:")
print(f"  Mean Squared Error (MSE): {mse:,.2f}")
print(f"  Root Mean Squared Error (RMSE): {rmse:,.2f} (cùng đơn vị với giá trị)")
print(f"  Mean Absolute Error (MAE): {mae:,.2f} (sai số tuyệt đối trung bình)")
print(f"  R-squared (R2): {r2:.4f} (tỷ lệ phương sai được giải thích)")

# (Tùy chọn) Xem độ quan trọng của các đặc trưng
# feature_importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
# print("\nĐộ quan trọng của các đặc trưng:")
# print(feature_importances)

# --- Step 6: Save Predictions ---
print("Lưu kết quả dự đoán...")
results_df = X_test.copy()
results_df['Actual Transfer Value'] = y_test
results_df['Predicted Transfer Value'] = y_pred
# Nối lại tên cầu thủ để dễ xem
player_names_test = full_data.loc[X_test.index, player_name_col]
results_df.insert(0, player_name_col, player_names_test) 

results_df.to_csv(PREDICTED_VALUES_OUTPUT_CSV, index=False, float_format='%.2f')
print(f"Đã lưu kết quả dự đoán vào file {PREDICTED_VALUES_OUTPUT_CSV}")

print("\nHoàn thành Bài 4!")
print("Đừng quên viết báo cáo giải thích lựa chọn đặc trưng, mô hình và phân tích kết quả.")