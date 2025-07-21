import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# 1. Create the data
data = {
    'Height': [170, 165, 160, 180, 175, 155],
    'Weight': [50, 60, 80, 75, 85, 45],
    'Label':  ['Thin', 'Normal', 'Fat', 'Normal', 'Fat', 'Thin']
}
df = pd.DataFrame(data)

# 2. Encode labels to numbers: Thin=0, Normal=1, Fat=2
le = LabelEncoder()
df['Label_encoded'] = le.fit_transform(df['Label'])


# 3. Prepare features and target
X = df[['Height', 'Weight']]
y = df['Label_encoded']

# 4. Train Random Forest
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier(n_estimators=10, random_state=42)
clf.fit(X, y)

# 5. Make a prediction
sample = pd.DataFrame([[160, 70]], columns=['Height', 'Weight'])
pred = clf.predict(sample)
print(le.inverse_transform(pred))
pred_label = le.inverse_transform(pred)[0]

print(f"Prediction for Height=160 cm, Weight=70 kg: {pred_label}")
