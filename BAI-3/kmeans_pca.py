# File: kmeans_pca.py (Sua loi + Khong dau)

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
import os

# --- 1. Tai du lieu ---
# Su dung os.path de tim file CSV trong thu muc cha ('../BAI-1')
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
csv_path = os.path.join(current_dir, '..', 'BAI-1', 'results.csv') # Duong dan tuong doi den file input
try:
    data = pd.read_csv(csv_path)
    print("Da tai du lieu thanh cong tu results.csv")
except FileNotFoundError:
    print(f"Loi: Khong tim thay file 'results.csv' tai duong dan: {csv_path}. Hay dam bao file nay ton tai.")
    exit()
except Exception as e:
    print(f"Loi khac khi doc file CSV: {e}")
    exit()


# --- 2. Tien xu ly du lieu ---
print("Bat dau tien xu ly du lieu...")

# Xu ly cot 'Age' dac biet
if 'Age' in data.columns:
    print("Dang xu ly cot 'Age'...")
    # Thay the 'N/a' bang NaN truoc khi tach chuoi
    data['Age'] = data['Age'].replace('N/a', np.nan)
    # Tach chuoi va lay phan tu dau tien (nam), chuyen thanh so
    data['Age'] = pd.to_numeric(data['Age'].astype(str).str.split('-').str[0], errors='coerce')
    print("Da xu ly xong cot 'Age'.")
else:
    print("Canh bao: Khong tim thay cot 'Age' trong du lieu.")

# Xac dinh cac cot so va cot phan loai
# Lay cac cot co kieu du lieu so hoc
numerical_cols = data.select_dtypes(include=np.number).columns.tolist()
# Neu 'Age' ban dau khong phai so nhung da xu ly thanh so, can them vao numerical_cols
if 'Age' in data.columns and pd.api.types.is_numeric_dtype(data['Age']) and 'Age' not in numerical_cols:
     numerical_cols.append('Age')

# Cac cot phan loai du kien
categorical_cols = ['Nation', 'Team', 'Position']

# Loai bo cac cot khong can thiet cho clustering (vi du: cot dinh danh dau tien)
player_identifiers = data.columns[0]
# Kiem tra xem cot dinh danh co trong DataFrame khong truoc khi drop
if player_identifiers in data.columns:
    features = data.drop(columns=[player_identifiers])
else:
    features = data.copy() # Neu khong co cot dinh danh, su dung toan bo data lam features
    print(f"Canh bao: Khong tim thay cot dinh danh '{player_identifiers}'. Su dung tat ca cac cot lam features.")
    player_identifiers = 'Index_Fallback' # Su dung index lam dinh danh thay the
    features.index.name = player_identifiers # Dat ten cho index
    data[player_identifiers] = data.index # Them cot index vao data goc de tham chieu

# Cap nhat lai danh sach cot so va phan loai sau khi drop cot dinh danh
numerical_cols = [col for col in numerical_cols if col in features.columns]
categorical_cols = [col for col in categorical_cols if col in features.columns]
# Dam bao 'Age' khong nam trong categorical_cols
if 'Age' in categorical_cols:
    categorical_cols.remove('Age')


print(f"Cac cot so duoc xac dinh: {numerical_cols}")
print(f"Cac cot phan loai duoc xac dinh: {categorical_cols}")

# Xu ly cac cot so: Loai bo dau phay va chuyen doi sang kieu so
print("Dang xu ly cac cot so (loai bo dau phay, chuyen doi kieu)...")
for col in numerical_cols:
    # Kiem tra xem cot co ton tai trong features khong
    if col in features.columns:
        # Thay the 'N/a' bang NaN truoc
        features[col] = features[col].replace('N/a', np.nan)
        # Neu cot khong phai la kieu so hoc, xu ly no
        if not pd.api.types.is_numeric_dtype(features[col]):
            print(f"  Xu ly cot so dang chuoi/object: {col}")
            # Loai bo dau phay
            features[col] = features[col].astype(str).str.replace(',', '', regex=False)
            # Chuyen doi sang so, loi se thanh NaN
            features[col] = pd.to_numeric(features[col], errors='coerce')
        # Dam bao cac cot da la so cung duoc xu ly NaN va co kieu float
        else:
             features[col] = pd.to_numeric(features[col], errors='coerce') # Dam bao kieu float

print("Da xu ly xong cac cot so.")

# Xu ly gia tri 'N/a' trong cac cot phan loai - Thay the bang NaN
print("Dang xu ly 'N/a' trong cac cot phan loai...")
for col in categorical_cols:
    if col in features.columns:
         features[col] = features[col].replace('N/a', np.nan)
print("Da thay the 'N/a' trong cot phan loai bang NaN.")


# Tao pipeline xu ly cho cot so: Impute (thay the NaN bang gia tri trung binh) va Scale
numerical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler())
])

# Tao pipeline xu ly cho cot phan loai: Impute (thay the NaN bang gia tri pho bien nhat) va OneHotEncode
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    # sparse_output=False de tra ve dense array, handle_unknown='ignore' de xu ly gia tri moi
    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

# Ket hop cac transformer su dung ColumnTransformer
# Su dung remainder='drop' de bo qua cac cot khong duoc chi dinh ro rang (an toan hon)
# Neu ban muon giu lai cac cot khac, hay dung remainder='passthrough', nhung dam bao chung khong gay loi
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_cols),
        ('cat', categorical_transformer, categorical_cols)
    ],
    remainder='drop' # Bo qua cac cot khong xac dinh de tranh loi tiem an
)

# Ap dung tien xu ly
try:
    processed_data = preprocessor.fit_transform(features)
    print("Tien xu ly du lieu hoan tat.")
    # Kiem tra xem processed_data co chua NaN/inf khong sau khi xu ly
    if np.isnan(processed_data).any() or np.isinf(processed_data).any():
        print("Canh bao: Du lieu da xu ly van chua NaN hoac gia tri vo cung.")
        # Lay ten cot sau khi transform (phuc tap hon voi one-hot encoding)
        # Thay the NaN/inf bang 0 (hoac chien luoc khac)
        processed_data = np.nan_to_num(processed_data, nan=0.0, posinf=np.finfo(np.float64).max, neginf=np.finfo(np.float64).min)
        print("Da thay the NaN/inf bang gia tri 0 hoac gia tri min/max cua float.")

except Exception as e:
    print(f"Loi trong qua trinh tien xu ly: {e}")
    # Cung cap them thong tin debug neu loi xay ra
    print("\n--- Thong tin Debug ---")
    print("Kiem tra kieu du lieu cac cot truoc khi vao preprocessor:")
    print(features[numerical_cols + categorical_cols].info())
    print("\nKiem tra gia tri NaN trong cac cot features:")
    print(features[numerical_cols + categorical_cols].isnull().sum())
    # Kiem tra cac gia tri duy nhat trong cot phan loai (co the giup tim ra van de)
    for col in categorical_cols:
        if col in features.columns:
             print(f"  Gia tri duy nhat trong '{col}': {features[col].unique()[:10]}...") # In 10 gia tri dau
    exit()

# --- 3. Xac dinh so cum toi uu (k) bang phuong phap Elbow ---
print("Xac dinh so cum toi uu (k) bang phuong phap Elbow...")
inertia = []
k_range = range(1, 11) # Kiem tra tu 1 den 10 cum

for k in k_range:
    kmeans_test = KMeans(n_clusters=k, random_state=42, n_init=10)
    try:
        # Dam bao du lieu la float64 truoc khi fit
        kmeans_test.fit(processed_data.astype(np.float64))
        inertia.append(kmeans_test.inertia_)
    except ValueError as ve:
        print(f"Loi khi chay K-means voi k={k}: {ve}")
        print("Kiem tra lai du lieu processed_data xem co gia tri khong hop le khong.")
        print(processed_data[:5]) # In 5 hang dau de kiem tra
        exit()
    except Exception as fit_e:
         print(f"Loi khac khi chay K-means voi k={k}: {fit_e}")
         exit()


# Ve bieu do Elbow (luu vao file de xem)
try:
    plt.figure(figsize=(10, 6))
    plt.plot(k_range, inertia, marker='o')
    plt.title('Phuong phap Elbow de xac dinh k toi uu')
    plt.xlabel('So luong cum (k)')
    plt.ylabel('Inertia (Tong binh phuong khoang cach trong cum)')
    plt.xticks(k_range)
    plt.grid(True)
    elbow_plot_path = os.path.join(current_dir, 'elbow_plot.png') # Luu cung thu muc voi script
    plt.savefig(elbow_plot_path)
    print(f"Da luu bieu do Elbow vao '{elbow_plot_path}'. Hay xem bieu do nay va chon gia tri 'k' tai diem 'khuyu tay'.")
    # plt.show() # Hien thi bieu do neu ban muon
    plt.close() # Dong figure de giai phong bo nho
except Exception as plot_e:
    print(f"Loi khi ve hoac luu bieu do Elbow: {plot_e}")


# --- Yeu cau nguoi dung nhap k toi uu ---
optimal_k = None
while True:
    try:
        optimal_k_input = input("Dua vao bieu do elbow_plot.png, nhap so cum toi uu (k) ban chon (hoac bo trong de thoat): ")
        if not optimal_k_input: # Neu nguoi dung nhap enter (bo trong)
             print("Da huy bo viec chon k.")
             exit()
        optimal_k = int(optimal_k_input)
        if optimal_k > 0 and optimal_k < len(data): # K phai lon hon 0 va nho hon so diem du lieu
            break
        else:
            print(f"So cum phai la mot so nguyen duong va nho hon so luong cau thu ({len(data)}).")
    except ValueError:
        print("Vui long nhap mot so nguyen hop le.")
    except Exception as input_e:
         print(f"Loi khong mong doi khi nhap k: {input_e}")

print(f"Ban da chon k = {optimal_k}.")

# --- 4. Ap dung K-means voi k toi uu ---
print(f"Ap dung K-means voi k = {optimal_k}...")
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
try:
    cluster_labels = kmeans.fit_predict(processed_data.astype(np.float64))
    # Them cot cluster vao dataframe goc (dam bao index khop nhau)
    data['Cluster'] = cluster_labels
    print("Da gan nhan cum cho cac cau thu.")
except Exception as kmeans_e:
    print(f"Loi khi ap dung K-means: {kmeans_e}")
    exit()


# --- 5. Ap dung PCA de giam chieu du lieu xuong 2 ---
print("Ap dung PCA de giam chieu du lieu xuong 2...")
pca = PCA(n_components=2)
try:
    pca_components = pca.fit_transform(processed_data.astype(np.float64))
    print(f"PCA giai thich duoc {sum(pca.explained_variance_ratio_)*100:.2f}% phuong sai.")

    # Tao DataFrame voi ket qua PCA va nhan cum
    pca_df = pd.DataFrame(data=pca_components, columns=['PCA1', 'PCA2'])
    pca_df['Cluster'] = cluster_labels
    # Gan lai dinh danh cau thu (dam bao thu tu khong thay doi)
    # Su dung .values de tranh van de ve index
    pca_df[player_identifiers] = data[player_identifiers].values

    print("PCA hoan tat.")
except Exception as pca_e:
    print(f"Loi khi ap dung PCA: {pca_e}")
    exit()

# --- 6. Luu ket qua ---
# Luu du lieu goc voi cot Cluster
try:
    output_file_clustered = os.path.join(current_dir, 'results_clustered.csv')
    data.to_csv(output_file_clustered, index=False)
    print(f"Da luu du lieu voi nhan cum vao '{output_file_clustered}'.")
except Exception as save_e1:
    print(f"Loi khi luu file results_clustered.csv: {save_e1}")

# Luu du lieu PCA va cluster de ve bieu do
try:
    output_file_pca = os.path.join(current_dir, 'pca_clusters.csv')
    pca_df.to_csv(output_file_pca, index=False)
    print(f"Da luu thanh phan PCA va nhan cum vao '{output_file_pca}'.")
except Exception as save_e2:
    print(f"Loi khi luu file pca_clusters.csv: {save_e2}")


print("\nHoan thanh xu ly kmeans_pca.py!")
print("Tiep theo, chay file plotting.py de ve bieu do phan cum 2D.")