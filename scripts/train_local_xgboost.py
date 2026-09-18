import os
import sys
import numpy as np
import pandas as pd
import joblib

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

FEATURE_COLS = [
    'WBC', 'PLT', 'RBC', 'HGB', 'HCT', 'AST', 'ALT', 'GLUCOSE', 'CREATININE',
    'has_sot', 'has_dau_dau', 'has_dau_nguc', 'has_kho_tho', 'has_dau_bung',
    'has_non_oi', 'has_tieu_chay', 'has_chay_mau', 'has_meo_mieng'
]

def train_and_export():
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import classification_report, accuracy_score

    print("=== Đang tạo dataset huấn luyện kết hợp chỉ số máu & triệu chứng lâm sàng ===")
    np.random.seed(42)
    N = 2500
    data = []
    labels = []

    disease_list = [
        'Dengue_A90', 'Infarction_I21', 'Stroke_I64', 'Pneumonia_J18',
        'CommonCold_J00', 'Gastritis_K29', 'Diabetes_E11', 'LiverDisease_K76'
    ]

    for _ in range(N):
        disease_choice = np.random.choice(disease_list)
        row = {
            'WBC': np.random.uniform(4.5, 9.5),
            'PLT': np.random.uniform(180, 350),
            'RBC': np.random.uniform(4.0, 5.2),
            'HGB': np.random.uniform(130, 155),
            'HCT': np.random.uniform(38, 46),
            'AST': np.random.uniform(15, 35),
            'ALT': np.random.uniform(15, 35),
            'GLUCOSE': np.random.uniform(4.2, 5.8),
            'CREATININE': np.random.uniform(60, 95),
            'has_sot': 0, 'has_dau_dau': 0, 'has_dau_nguc': 0, 'has_kho_tho': 0,
            'has_dau_bung': 0, 'has_non_oi': 0, 'has_tieu_chay': 0, 'has_chay_mau': 0, 'has_meo_mieng': 0
        }
        if disease_choice == 'Dengue_A90':
            row['WBC'] = np.random.uniform(1.8, 3.8)
            row['PLT'] = np.random.uniform(20, 95)
            row['has_sot'] = 1
            row['has_dau_dau'] = 1
            row['has_chay_mau'] = np.random.choice([0, 1], p=[0.25, 0.75])
        elif disease_choice == 'Infarction_I21':
            row['has_dau_nguc'] = 1
            row['has_kho_tho'] = 1
        elif disease_choice == 'Stroke_I64':
            row['has_meo_mieng'] = 1
        elif disease_choice == 'Pneumonia_J18':
            row['WBC'] = np.random.uniform(12.5, 24.0)
            row['has_sot'] = 1
            row['has_kho_tho'] = 1
        elif disease_choice == 'CommonCold_J00':
            row['has_sot'] = 1
            row['has_dau_dau'] = 1
        elif disease_choice == 'Gastritis_K29':
            row['has_dau_bung'] = 1
            row['has_non_oi'] = 1
        elif disease_choice == 'Diabetes_E11':
            row['GLUCOSE'] = np.random.uniform(7.5, 18.0)
        elif disease_choice == 'LiverDisease_K76':
            row['AST'] = np.random.uniform(60, 320)
            row['ALT'] = np.random.uniform(80, 420)

        data.append(row)
        labels.append(disease_choice)

    DISEASE_MAP = {
        'Dengue_A90': 0,
        'Infarction_I21': 1,
        'Stroke_I64': 2,
        'Pneumonia_J18': 3,
        'CommonCold_J00': 4,
        'Gastritis_K29': 5,
        'Diabetes_E11': 6,
        'LiverDisease_K76': 7
    }

    df = pd.DataFrame(data)
    y = np.array([DISEASE_MAP[lbl] for lbl in labels])
    X = df[FEATURE_COLS]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"Huấn luyện XGBoost trên {len(X_train)} mẫu...")
    model = xgb.XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        objective='multi:softprob',
        random_state=42,
        tree_method='hist'
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"✅ Độ chính xác (Accuracy): {round(acc * 100, 2)}%")

    # Export weights
    export_dir = os.path.join(os.path.dirname(__file__), "..", "apps", "ai_engine", "models_weights")
    os.makedirs(export_dir, exist_ok=True)

    weights_file = os.path.join(export_dir, "tabular_xgboost.json")
    encoder_file = os.path.join(export_dir, "label_encoder.pkl")

    model.save_model(weights_file)
    joblib.dump(DISEASE_MAP, encoder_file)
    print(f"🎉 Đã xuất thành công model weights thật vào: {weights_file}")

if __name__ == "__main__":
    train_and_export()
