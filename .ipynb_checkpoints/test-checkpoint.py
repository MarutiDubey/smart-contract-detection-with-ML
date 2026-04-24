import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Features CSV file ko load karo
df = pd.read_csv('features.csv')

X = df.drop("label", axis=1)  # Features
y = df["label"]               # Labels (1 = vulnerable, 0 = safe)

if len(df) < 2 or y.nunique() < 2:
    # Single row ya single class case: split/train possible nahi hai
    print("Not enough samples or classes for train/test split. Showing data:")
    print(df)
else:
    # Data ko train aur test me divide karo
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42)

    # Random Forest model banao aur train karo
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Test data pe prediction karo
    y_pred = model.predict(X_test)

    # Performance report print karo
    print("Classification Report:\n", classification_report(y_test, y_pred))
