import pandas as pd
import os
import argparse
from feature_extractor import extract_features

def main():
    parser = argparse.ArgumentParser(description="Extract features from CSV dataset")
    parser.add_argument("--csv", default="data/8label.csv", help="Path to input CSV (e.g. data/4label.csv)")
    parser.add_argument("--output", default="data/features.csv", help="Path to output CSV")
    args = parser.parse_args()
    
    csv_path = args.csv
    out_path = args.output
    
    print(f"Loading data from {csv_path}...")
    if not os.path.exists(csv_path):
        print(f"[ERROR] Could not find {csv_path}. Make sure it exists.")
        return

    df = pd.read_csv(csv_path)
    
    # Mapping table mapping raw string labels to numeric labels used by feature_extractor.py
    label_map = {
        './Dataset/reentrancy (RE)/': 1,
        './Dataset/integer overflow (OF)/': 3,
        './Dataset/unchecked external call (UC)': 5,
        './Dataset/timestamp dependency (TP)/': 6,
        './Dataset/block number dependency (BN)': 6,
        './Dataset/dangerous delegatecall (DE)/': 12,
        './Dataset/ether strict equality (SE)': 13,
        './Dataset/ether frozen (EF)': 14,
        
        # 4label.csv paths
        '/content/drive/My Drive/SC_Dataset/reentrancy (RE)/': 1,
        '/content/drive/My Drive/SC_Dataset/integer overflow (OF)/': 3,
        '/content/drive/My Drive/SC_Dataset/timestamp dependency (TP)/': 6,
        '/content/drive/My Drive/SC_Dataset/dangerous delegatecall (DE)/': 12
    }
    rows = []
    print(f"Extracting 33 features from {len(df)} contracts in CSV...")
    
    for idx, row in df.iterrows():
        code = str(row.get('code', ''))
        label_str = str(row.get('label', ''))
        filename = str(row.get('filename', f'contract_{idx}.sol'))
        
        # Apply extraction
        features = extract_features(code)
        
        # Map label
        numeric_label = label_map.get(label_str, 0) # default to Safe (0) if unknown
        
        rows.append({
            "file": filename,
            **features,
            "label": numeric_label
        })
        
        if (idx + 1) % 500 == 0:
            print(f"  Processed {idx + 1} / {len(df)} contracts...")
            
    out_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    out_df.to_csv(out_path, index=False)
    
    print(f"\n[OK] Awesome! Extracted features for {len(out_df)} samples to {out_path}")
    print("      Now you can run the model training with this massive jump in data.")

if __name__ == "__main__":
    main()
