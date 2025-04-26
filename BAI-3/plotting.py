# File: plotting.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns # Dung seaborn cho mau sac dep hon

# --- 1. Tai du lieu PCA va Cluster ---
try:
    pca_data = pd.read_csv('pca_clusters.csv')
    print("Da tai du lieu PCA va cluster tu pca_clusters.csv")
except FileNotFoundError:
    print("Loi: Khong tim thay file 'pca_clusters.csv'. Hay dam bao ban da chay thanh cong file 'kmeans_pca.py' truoc.")
    exit()

# --- 2. Ve bieu do phan cum 2D ---
print("Bat dau ve bieu do phan cum 2D...")
plt.figure(figsize=(12, 8))

# Su dung seaborn de tao bang mau dep va ve scatter plot
# unique_clusters = sorted(pca_data['Cluster'].unique())
sns.scatterplot(
    x='PCA1',
    y='PCA2',
    hue='Cluster', # To mau theo cot 'Cluster'
    palette=sns.color_palette("hsv", n_colors=len(pca_data['Cluster'].unique())),
    data=pca_data,
    legend='full',
    alpha=0.7
)

plt.title('Phan cum cau thu bang K-means (sau PCA)')
plt.xlabel('Thanh phan chinh thu nhat (PCA1)')
plt.ylabel('Thanh phan chinh thu hai (PCA2)')
plt.grid(True)

# Luu bieu do
output_plot_file = 'kmeans_pca_cluster_plot.png'
plt.savefig(output_plot_file)
print(f"Da luu bieu do phan cum vao '{output_plot_file}'.")
plt.show()

print("\nHoan thanh ve bieu do plotting.py!")
