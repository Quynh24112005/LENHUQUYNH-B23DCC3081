import os, traceback, joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from scipy.stats import randint, uniform

# --- Config ---
DATA_STATS = "Report/OUTPUT_BAI1/results.csv"
DATA_VALS = "Report/OUTPUT_BAI4/players_over_900_filtered.csv"
OUT_DIR = "Report\OUTPUT_BAI4\Report_Model_Output"
MODEL_PATH = os.path.join(OUT_DIR, "gbr_model.joblib")
PREPROC_PATH = os.path.join(OUT_DIR, "preprocessor.joblib")
PLOTS_PATH = os.path.join(OUT_DIR, "plots")

TARGET = "TransferValue_EUR_Millions"
ID_COLS = ["Player", "Nation", "Team", "Team_TransferSite"]
CAT_COLS = ["Position"]

os.makedirs(PLOTS_PATH, exist_ok=True)

def load_data(stats_path, val_path, target_col):
    try:
        stats, vals = pd.read_csv(stats_path), pd.read_csv(val_path)
        if target_col not in vals.columns: return None
        merged = pd.merge(stats, vals, on="Player", how="right")
        merged.dropna(subset=[target_col], inplace=True)
        return merged
    except: traceback.print_exc(); return None

def preprocess_data(df, target, id_cols, cat_cols):
    df[f"{target}_log"] = np.log1p(df[target])
    y = df[f"{target}_log"]
    X = df.drop(columns=[target, f"{target}_log"] + [c for c in id_cols if c in df.columns])
    X.replace("N/a", np.nan, inplace=True)

    for col in X.select_dtypes("object"):
        cleaned = pd.to_numeric(X[col].astype(str).str.replace(",", ""), errors="coerce")
        if cleaned.notna().mean() > 0.7: X[col] = cleaned

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    num_cols = X_train.select_dtypes("number").columns.tolist()
    cat_all = list(set(cat_cols) & set(X_train.columns)) + list(X_train.select_dtypes("object").columns)

    drop_cols = X_train.columns[X_train.isnull().mean() > 0.5].tolist()
    X_train.drop(columns=drop_cols, inplace=True)
    X_test.drop(columns=drop_cols, inplace=True)
    num_cols = [c for c in num_cols if c not in drop_cols]
    cat_all = [c for c in cat_all if c not in drop_cols]

    for col in cat_all:
        X_train[col] = X_train[col].fillna("Missing").astype(str)
        X_test[col] = X_test[col].fillna("Missing").astype(str)

    return X_train, X_test, y_train, y_test, num_cols, cat_all

def build_pipeline(num_cols, cat_cols):
    num_pipe = Pipeline([
        ("imp", KNNImputer()), ("scale", StandardScaler())
    ])
    cat_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    return ColumnTransformer([
        ("num", num_pipe, num_cols),
        ("cat", cat_pipe, cat_cols)
    ])

def evaluate(model, X_test, y_test, feat_names):
    y_pred_log = model.predict(X_test)
    y_pred, y_true = np.expm1(y_pred_log), np.expm1(y_test)
    y_pred[y_pred < 0] = 0

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"R2: {r2_score(y_true, y_pred):.3f}, RMSE: {rmse:.2f}, MAE: {mean_absolute_error(y_true, y_pred):.2f}")

    if hasattr(model, "feature_importances_"):
        fi = pd.DataFrame({"feature": feat_names, "importance": model.feature_importances_}).sort_values("importance", ascending=False).head(20)
        plt.figure(figsize=(10, 6))
        sns.barplot(x="importance", y="feature", data=fi)
        plt.tight_layout(); plt.savefig(os.path.join(PLOTS_PATH, "feature_importance.png")); plt.close()

    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.5)
    lim = max(y_true.max(), y_pred.max()) * 1.05
    plt.plot([0, lim], [0, lim], 'r--')
    plt.xlabel("Actual"); plt.ylabel("Predicted"); plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_PATH, "pred_vs_actual.png")); 
    plt.close()
    # Residual plot
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, y_true - y_pred, alpha=0.6, color='green', edgecolor='black')
    plt.axhline(0, color='red', linestyle='--', linewidth=2)
    plt.xlabel(f'Predicted {TARGET} (M EUR)')
    plt.ylabel('Residuals (Actual - Predicted) (M EUR)')
    plt.title('Residual Plot (Goc)')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_PATH, 'residuals.png'))
    plt.close()


def train_model(X_train, X_test, y_train, y_test, preproc):
    X_train_proc = preproc.fit_transform(X_train)
    X_test_proc = preproc.transform(X_test)
    model = GradientBoostingRegressor(random_state=42)
    param_dist = {
        "n_estimators": randint(300, 1000),
        "learning_rate": uniform(0.01, 0.1),
        "max_depth": randint(3, 5),
        "min_samples_split": randint(2, 10),
        "subsample": uniform(0.7, 0.3)
    }
    search = RandomizedSearchCV(model, param_dist, n_iter=30, cv=5, n_jobs=-1, scoring="r2", verbose=1, random_state=42)
    search.fit(X_train_proc, y_train)
    evaluate(search.best_estimator_, X_test_proc, y_test, preproc.get_feature_names_out())
    return search.best_estimator_, preproc

def main():
    data = load_data(DATA_STATS, DATA_VALS, TARGET)
    if data is None: return
    X_train, X_test, y_train, y_test, num_cols, cat_cols = preprocess_data(data, TARGET, ID_COLS, CAT_COLS)
    preproc = build_pipeline(num_cols, cat_cols)
    model, prep = train_model(X_train, X_test, y_train, y_test, preproc)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(prep, PREPROC_PATH)

if __name__ == "__main__":
    main()
