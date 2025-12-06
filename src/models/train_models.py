import os
from pathlib import Path
import numpy as np
import pandas as pd

import joblib
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, classification_report, confusion_matrix

def prepare_features(df):
    df = df.copy()
    scaler_chuva = StandardScaler()
    scaler_mare = StandardScaler()
    scaler_vuln = StandardScaler()
    df['chuva_mm_z'] = scaler_chuva.fit_transform(df[['chuva_mm']])
    df['mare_m_z'] = scaler_mare.fit_transform(df[['mare_m']])
    df['vulnerabilidade_z'] = scaler_vuln.fit_transform(df[['vulnerabilidade']])
    df['chuva_x_vuln'] = df['chuva_mm_z'] * df['vulnerabilidade_z']
    df['mare_x_vuln'] = df['mare_m_z'] * df['vulnerabilidade_z']
    df['chuva_x_mare'] = df['chuva_mm_z'] * df['mare_m_z']
    df['chuva_sq'] = df['chuva_mm_z'] ** 2
    df['mare_sq'] = df['mare_m_z'] ** 2
    df['mes'] = pd.to_datetime(df['date']).dt.month
    df['estacao_chuvosa'] = df['mes'].isin([3, 4, 5, 6, 7, 8]).astype(int)
    if 'densidade_pop' in df.columns:
        scaler_dens = StandardScaler()
        df['densidade_pop_z'] = scaler_dens.fit_transform(df[['densidade_pop']])
    if 'altitude' in df.columns:
        scaler_alt = StandardScaler()
        df['altitude_z'] = scaler_alt.fit_transform(df[['altitude']])
    return df, {'scaler_chuva': scaler_chuva, 'scaler_mare': scaler_mare, 'scaler_vuln': scaler_vuln}

def calculate_risk_index(row):
    chuva_norm = min(row['chuva_mm'] / 100.0, 1.0)
    mare_norm = min(max((row['mare_m'] - 1.0) / 0.8, 0), 1.0)
    vuln_norm = row['vulnerabilidade']
    dens_norm = min(row.get('densidade_pop', 10000) / 20000.0, 1.0)
    risco = (0.35 * chuva_norm + 0.25 * mare_norm + 0.30 * vuln_norm + 0.10 * dens_norm)
    return min(risco, 1.0)

def train_and_save_models(csv_path, models_dir):
    print("Carregando dados...")
    df = pd.read_csv(csv_path, parse_dates=['date'])
    print(f"   - {len(df)} registros, {df['bairro'].nunique()} bairros")
    print("Preparando features...")
    df, scalers = prepare_features(df)
    df['risk_index'] = df.apply(calculate_risk_index, axis=1)
    df['risk_class'] = pd.cut(df['risk_index'], bins=[0, 0.3, 0.6, 1.0], labels=['baixo', 'moderado', 'alto'], include_lowest=True)
    df['risk_alto'] = (df['risk_class'] == 'alto').astype(int)
    print("Distribuicao de risco:")
    print(df['risk_class'].value_counts().sort_index())
    print("Treinando regressao...")
    features_reg = ['chuva_mm_z', 'mare_m_z', 'vulnerabilidade_z', 'chuva_x_vuln', 'mare_x_vuln', 'chuva_x_mare', 'chuva_sq', 'mare_sq', 'estacao_chuvosa']
    if 'densidade_pop_z' in df.columns:
        features_reg.append('densidade_pop_z')
    if 'altitude_z' in df.columns:
        features_reg.append('altitude_z')
    X_reg = df[features_reg].values
    y_reg = df['ocorrencias'].values
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train_reg, y_train_reg)
    y_pred_reg = ridge.predict(X_test_reg)
    mse = mean_squared_error(y_test_reg, y_pred_reg)
    r2 = r2_score(y_test_reg, y_pred_reg)
    print(f"   MSE: {mse:.3f}, R2: {r2:.3f}, RMSE: {np.sqrt(mse):.3f}")
    print("Treinando classificacao...")
    features_clf = ['chuva_mm_z', 'mare_m_z', 'vulnerabilidade_z', 'chuva_x_vuln', 'mare_x_vuln', 'chuva_sq', 'estacao_chuvosa']
    if 'densidade_pop_z' in df.columns:
        features_clf.append('densidade_pop_z')
    if 'altitude_z' in df.columns:
        features_clf.append('altitude_z')
    X_clf = df[features_clf].values
    y_clf = df['risk_alto'].values
    X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(X_clf, y_clf, test_size=0.2, random_state=42, stratify=y_clf)
    clf = LogisticRegression(max_iter=500, class_weight='balanced', C=0.5)
    clf.fit(X_train_clf, y_train_clf)
    y_pred_clf = clf.predict(X_test_clf)
    print(classification_report(y_test_clf, y_pred_clf))
    cm = confusion_matrix(y_test_clf, y_pred_clf)
    print(f"   Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
    print(f"Salvando modelos em {models_dir}...")
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(ridge, models_dir / 'linear_regression_occ.joblib')
    joblib.dump(clf, models_dir / 'logistic_risk.joblib')
    joblib.dump(scalers, models_dir / 'scalers.joblib')
    joblib.dump(features_reg, models_dir / 'features_regression.joblib')
    joblib.dump(features_clf, models_dir / 'features_classification.joblib')
    print("Treinamento concluido!")

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    csv_path = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
    models_dir = repo_root / 'models'
    if not csv_path.exists():
        print(f"Dados nao encontrados: {csv_path}")
        exit(1)
    train_and_save_models(csv_path, models_dir)
