import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
import os

pca_file_path = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI3\pca_clusters.csv'
print("Thu muc lam viec hien tai cua script plotting.py:", os.getcwd())
print("Duong dan tuyet doi toi file PCA:", pca_file_path)

EXPLAINED_VARIANCE_PERCENTAGE = 55.50  
# --- 1. Tai du lieu PCA va Cluster ---
try:
    pca_data = pd.read_csv(pca_file_path)
    print(f"Da tai du lieu PCA va cluster tu '{pca_file_path}'")
except FileNotFoundError:
    print(f"Loi: Khong tim thay file '{pca_file_path}'.")
    print("Cac ly do co the:")
    print("  1. Ban chua chay thanh cong file 'kmeans_pca.py'.")
    print(f"  2. File 'pca_clusters.csv' khong duoc tao ra tai dung duong dan tren.")
    exit()
except Exception as e:
    print(f"Loi khac khi doc file CSV '{pca_file_path}': {e}")
    exit()


# --- 2. Ve bieu do phan cum 2D ---
print("Bat dau ve bieu do phan cum 2D...")
plt.figure(figsize=(12, 8))

if 'Cluster' not in pca_data.columns or 'PCA1' not in pca_data.columns or 'PCA2' not in pca_data.columns:
     print("Loi: File pca_clusters.csv thieu cot 'Cluster', 'PCA1', hoac 'PCA2'.")
     exit()

try:
    num_clusters = len(pca_data['Cluster'].unique())
    if num_clusters == 0:
        print("Loi: Khong co gia tri cluster nao trong du lieu.")
        exit()
    print(f"So luong cum tim thay: {num_clusters}")
    palette = sns.color_palette("viridis", n_colors=num_clusters)
except Exception as e:
    print(f"Loi khi xac dinh so luong cum hoac tao palette: {e}")
    exit()

try:
    scatter_plot = sns.scatterplot(
        x='PCA1',
        y='PCA2',
        hue='Cluster',
        palette=palette,
        data=pca_data,
        legend='full',
        alpha=0.7,
        s=50
    )
except Exception as plot_e:
     print(f"Loi khong mong doi khi ve scatterplot: {plot_e}")
     exit()

plt.title(f'Phan cum cau thu bang K-means (K={num_clusters}) (sau PCA)', fontsize=14)
plt.xlabel('PC1', fontsize=12)
plt.ylabel('PC2', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)

if EXPLAINED_VARIANCE_PERCENTAGE is not None:
    plt.text(0.97, 0.03,
             f'Total Variance Explained: {EXPLAINED_VARIANCE_PERCENTAGE:.2f}%',
             verticalalignment='bottom', 
             horizontalalignment='right', 
             transform=plt.gca().transAxes, 
             fontsize=9, 
             bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7))
else:
    print("Khong co gia tri EXPLAINED_VARIANCE_PERCENTAGE de hien thi.")

plt.legend(title=f'Cluster (K={num_clusters})', bbox_to_anchor=(1.02, 1), loc='upper left')

# --- Lưu biểu đồ ---
output_plot_file = r'D:\PTIT\NAM2\KI2\Python\ASS-1\Report\OUTPUT_BAI3\kmeans_pca_cluster_plot_with_variance.png'
try:
    plt.tight_layout(rect=[0, 0, 0.9, 1]) 
    plt.savefig(output_plot_file, dpi=300)
    print(f"Da luu bieu do phan cum voi phuong sai vao '{output_plot_file}'.")
except Exception as save_e:
    print(f"Loi khi luu bieu do: {save_e}")

# --- Hiển thị biểu đồ ---
plt.show()

print("\nHoan thanh ve bieu do plotting.py!")