import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os

class EEGModelTrainer:
    """Handles complete ML training pipeline"""
    
    def __init__(self):
        self.models = {}
        self.scaler = None
        self.feature_names = None
        self.results = {}
        
    def load_data(self, file_path='data/processed_features.csv'):
        """Load processed features from CSV"""
        
        print("="*60)
        print("STEP 1: LOADING DATA")
        print("="*60)
        
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            print("\nPlease run preprocess_data.py first!")
            return None, None, None
        
        print(f"Loading from: {file_path}")
        data = pd.read_csv(file_path)

        if 'label' not in data.columns:
            print("⚠ No labels found. Creating dummy labels for demo.")
            np.random.seed(42)
            data['label'] = np.random.randint(0, 2, size=len(data))
        
        feature_columns = [col for col in data.columns if col != 'label']
        X = data[feature_columns]
        y = data['label']
        self.feature_names = feature_columns
        
        print(f"✓ Loaded {len(data)} samples with {len(feature_columns)} features")
        print("\nLabel distribution:")
        print(f"  Class 0: {sum(y==0)}")
        print(f"  Class 1: {sum(y==1)}")
        
        return X, y, feature_columns
    
    def split_and_normalize(self, X, y):
        """Split data and normalize features"""
        
        print("\n" + "="*60)
        print("STEP 2: SPLITTING AND NORMALIZING DATA")
        print("="*60)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Testing set:  {len(X_test)} samples")
        
        print("\nNormalizing features...")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        print("✓ Features normalized")
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_models(self, X_train, y_train):
        """Train multiple ML models"""
        
        print("\n" + "="*60)
        print("STEP 3: TRAINING MODELS")
        print("="*60)
        
        print("\n[1/3] Logistic Regression...")
        lr = LogisticRegression(random_state=42, max_iter=1000)
        lr.fit(X_train, y_train)
        self.models['Logistic Regression'] = lr
        
        print("\n[2/3] Random Forest...")
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        self.models['Random Forest'] = rf
        
        print("\n[3/3] Gradient Boosting...")
        gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
        gb.fit(X_train, y_train)
        self.models['Gradient Boosting'] = gb
        
        print("✓ All models trained")
    
    def evaluate_models(self, X_train, X_test, y_train, y_test):
        """Evaluate all models"""
        
        print("\n" + "="*60)
        print("STEP 4: EVALUATING MODELS")
        print("="*60)
        
        for name, model in self.models.items():
            print(f"\nMODEL: {name}")
            
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            train_acc = accuracy_score(y_train, train_pred)
            test_acc = accuracy_score(y_test, test_pred)
            
            print(f"Training Accuracy: {train_acc:.3f}")
            print(f"Testing Accuracy:  {test_acc:.3f}")
            
            print("\nClassification Report:")
            print(classification_report(y_test, test_pred))
            
            cm = confusion_matrix(y_test, test_pred)
            self.results[name] = {'train_acc': train_acc, 'test_acc': test_acc, 'confusion_matrix': cm}
            
            self.plot_confusion_matrix(cm, name)
            
            if hasattr(model, 'feature_importances_'):
                self.plot_feature_importance(model, name)
    
    def plot_confusion_matrix(self, cm, model_name):
        plt.figure(figsize=(6,5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title(f'Confusion Matrix - {model_name}')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        os.makedirs('results', exist_ok=True)
        plt.savefig(f'results/confusion_matrix_{model_name}.png', dpi=300)
        plt.close()
    
    def plot_feature_importance(self, model, model_name):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        top_n = min(10, len(self.feature_names))
        
        plt.figure(figsize=(10,5))
        plt.bar(range(top_n), importances[indices[:top_n]])
        plt.xticks(range(top_n), [self.feature_names[i] for i in indices[:top_n]], rotation=45)
        plt.title(f'Top Features - {model_name}')
        plt.tight_layout()
        os.makedirs('results', exist_ok=True)
        plt.savefig(f'results/feature_importance_{model_name}.png', dpi=300)
        plt.close()
    
    def save_model(self, model_name, model):
        os.makedirs('models', exist_ok=True)
        joblib.dump(model, f'models/eeg_model_{model_name}.pkl')
        joblib.dump(self.scaler, f'models/eeg_scaler_{model_name}.pkl')
        joblib.dump(self.feature_names, f'models/eeg_features_{model_name}.pkl')
        print(f"✓ Saved {model_name} model, scaler, and features")
    
def main():
    trainer = EEGModelTrainer()
    
    X, y, feature_names = trainer.load_data()
    if X is None:
        return
    
    X_train, X_test, y_train, y_test = trainer.split_and_normalize(X, y)
    trainer.train_models(X_train, y_train)
    trainer.evaluate_models(X_train, X_test, y_train, y_test)
    
    # Save the best model based on test accuracy
    best_model_name = max(trainer.results, key=lambda x: trainer.results[x]['test_acc'])
    trainer.save_model(best_model_name, trainer.models[best_model_name])
    
    print("\nTraining complete! Check results/ and models/ folders.")

if __name__ == "__main__":
    main()
