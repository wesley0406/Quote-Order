import json
import os
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
import time, pickle
from category_encoders import TargetEncoder
from sklearn.preprocessing import OneHotEncoder
import numpy as np
import tensorflow as tf
import datetime
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Add, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, Callback
from tensorflow.keras.utils import plot_model

# Import the pre_train data
from Pre_Train_data import FETCH_ERP_SCREW

class NaNInfMonitor(Callback):
    def on_batch_end(self, batch, logs=None):
        if logs is None:
            logs = {}
        for metric, value in logs.items():
            if np.isnan(value) or np.isinf(value):
                print(f"Warning: {metric} is {value} at batch {batch}. Stopping training.")
                self.model.stop_training = True

class PackingRatioMetric(Callback):
    def __init__(self, X_train, y_train, screw_volume, scale_target=False, scaler=None):
        super(PackingRatioMetric, self).__init__()
        self.X_train = X_train
        self.y_train = y_train
        self.screw_volume = screw_volume
        self.scale_target = scale_target
        self.scaler = scaler

    def on_epoch_end(self, epoch, logs=None):
        preds = self.model.predict(self.X_train, verbose=0)
        if self.scale_target and self.scaler is not None:
            preds = self.scaler.inverse_transform(preds)
            y_true = self.scaler.inverse_transform(self.y_train.reshape(-1, 1))
        else:
            y_true = self.y_train
        packing_ratios = self.screw_volume / (preds.flatten() + 1e-6)  # Avoid division by zero
        mean_packing_ratio = np.mean(packing_ratios) * 100  # Convert to percentage
        print(f"Epoch {epoch + 1}: Mean Packing Ratio = {mean_packing_ratio:.2f}%")
        logs["packing_ratio"] = mean_packing_ratio

class Neural_Network_Arch:
    def __init__(self, config_path='config.json'):
        today = datetime.date.today()
        self.Train_data = FETCH_ERP_SCREW().Result.copy()
        self.SAVE_FILE = r'C:\Users\wesley\Desktop\workboard\Volumn_Project\Training History & Model\{today}'
        self.model = None
        self.scaler = None
        self.encoder = None
        self.target_scaler = None
        self.container_volumes = None
        self.config = self._load_config(os.path.join(self.SAVE_FILE, config_path))

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config['model_config']
        except Exception as e:
            print(f"Error loading config file: {str(e)}")
            raise

    def _build_model(self, input_dim):
        try:
            inputs = Input(shape=(input_dim,))
            x = Dense(128, activation='relu', 
                     kernel_regularizer=tf.keras.regularizers.l2(self.config['l2_regularization']))(inputs)
            x = BatchNormalization()(x)
            x = Dropout(self.config['dropout_rate'])(x)
            x1 = Dense(64, activation='relu')(x)
            x1 = BatchNormalization()(x1)
            x1 = Dense(64, activation='relu')(x1)
            x1 = BatchNormalization()(x1)
            x_proj1 = Dense(64, activation='linear')(x)
            x = Add()([x_proj1, x1])
            x = Dropout(self.config['dropout_rate'])(x)
            x2 = Dense(32, activation='relu')(x)
            x2 = BatchNormalization()(x2)
            x2 = Dense(32, activation='relu')(x2)
            x2 = BatchNormalization()(x2)
            x_proj2 = Dense(32, activation='linear')(x)
            x = Add()([x_proj2, x2])
            x = Dropout(self.config['dropout_rate'])(x)
            outputs = Dense(1, activation='linear')(x)
            model = tf.keras.Model(inputs, outputs)
            
            optimizer = tf.keras.optimizers.AdamW(
                learning_rate=self.config['initial_learning_rate']
            )
            
            model.compile(
                optimizer=optimizer,
                loss=tf.keras.losses.Huber(delta=self.config['huber_delta']),
                metrics=['mae', 'mse']
            )
            
            return model
        
        except Exception as e:
            print(f"Error in _build_model: {str(e)}")
            raise

    def _prepare_feature_NN(self):
        numeric_features = ['Screw volume in the box', 'Diameter', 'Length']
        categorical_features = ["pdc_4", "pdc_5", 'Screw_Type', 'Head_Type']

        if self.Train_data[numeric_features].isna().any().any() or np.isinf(self.Train_data[numeric_features]).any().any():
            print("Warning: NaN or Inf values detected in numeric features before preprocessing.")
        if self.Train_data[categorical_features].isna().any().any():
            print("Warning: NaN values detected in categorical features before preprocessing.")
        
        self.Train_data[numeric_features] = self.Train_data[numeric_features].fillna(self.Train_data[numeric_features].median())
        self.Train_data[categorical_features] = self.Train_data[categorical_features].fillna('Unknown')

        if self.scaler is None:
            self.scaler = RobustScaler()
            X_numeric = self.scaler.fit_transform(self.Train_data[numeric_features])
        else:
            X_numeric = self.scaler.transform(self.Train_data[numeric_features])

        if self.encoder is None:
            self.encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            X_categorical = self.encoder.fit_transform(self.Train_data[categorical_features])
            X_categorical = pd.DataFrame(X_categorical, 
                                       columns=self.encoder.get_feature_names_out(categorical_features),
                                       index=self.Train_data.index)
        else:
            X_categorical = self.encoder.transform(self.Train_data[categorical_features])
            X_categorical = pd.DataFrame(X_categorical, 
                                       columns=self.encoder.get_feature_names_out(categorical_features),
                                       index=self.Train_data.index)

        y = self.Train_data['decision box/master volume'].values if 'decision box/master volume' in self.Train_data else None
        if self.config.get('scale_target', False) and y is not None:
            if self.target_scaler is None:
                self.target_scaler = RobustScaler()
                y = self.target_scaler.fit_transform(y.reshape(-1, 1)).flatten()
            else:
                y = self.target_scaler.transform(y.reshape(-1, 1)).flatten()

   
        # creat a file fo every day info 
        os.makedirs(self.SAVE_FILE, exist_ok=True)
        with open(os.path.join(self.SAVE_FILE ,f'scaler_{today}.pkl'), 'wb') as f:
            pickle.dump(self.scaler, f)
        with open(os.path.join(self.SAVE_FILE ,f'target_scaler_{today}.pkl'), 'wb') as f:
            pickle.dump(self.target_scaler, f)
        with open(os.path.join(self.SAVE_FILE , f'encoder_{today}.pkl'), 'wb') as f:
            pickle.dump(self.encoder, f)

        X = np.hstack([X_numeric, X_categorical])
        if np.isnan(X).any() or np.isinf(X).any() or (y is not None and (np.isnan(y).any() or np.isinf(y).any())):
            print("Warning: NaN or Inf values detected in processed features or target.")

        # Print data statistics for debugging
        if y is not None:
            print(self.Train_data[['Screw volume in the box', 'decision box/master volume']].describe())
            print("Expected Packing Ratio (Screw volume / Box volume):")
            print((self.Train_data['Screw volume in the box'] / self.Train_data['decision box/master volume']).describe())

        return X, y, self.scaler, self.encoder, self.Train_data['Screw volume in the box'].values

    def _predict_container_volume(self, train=True):
        X, y, self.scaler, self.encoder, screw_volume = self._prepare_feature_NN()

        if train:
            X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42)
            X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
            screw_volume_train = train_test_split(self.Train_data['Screw volume in the box'].values, test_size=0.2, random_state=42)[0]
            screw_volume_val = train_test_split(self.Train_data['Screw volume in the box'].values, test_size=0.2, random_state=42)[1]
            screw_volume_val, screw_volume_test = train_test_split(screw_volume_val, test_size=0.5, random_state=42)

            self.model = self._build_model(input_dim=X.shape[1])
            
            callbacks = [
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=self.config['factor_reduce_lr'],
                    patience=self.config['patience_reduce_lr'],
                    min_lr=self.config['min_lr']
                ),
                NaNInfMonitor(),
                PackingRatioMetric(X_train, y_train, screw_volume_train, self.config.get('scale_target', False), self.target_scaler)
            ]
            
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                batch_size=self.config['batch_size'],
                epochs=self.config['epochs'],
                callbacks=callbacks,
                verbose=1
            )
            
            self.model.save(os.path.join(self.SAVE_FILE , f"Ver_{today}_OnehotE.keras"))

            history_df = pd.DataFrame(history.history)
            history_df['epoch'] = range(1, len(history_df) + 1)
            history_df = history_df[['epoch', 'loss', 'mae', 'mse', 'val_loss', 'val_mae', 'val_mse', 'packing_ratio']]

            test_preds = self.model.predict(X_test, verbose=0)
            if self.config.get('scale_target', False) and self.target_scaler is not None:
                test_preds = self.target_scaler.inverse_transform(test_preds)
                y_test_unscaled = self.target_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
            else:
                y_test_unscaled = y_test
            packing_ratios_test = screw_volume_test / (test_preds.flatten() + 1e-6)
            mean_packing_ratio_test = np.mean(packing_ratios_test) * 100
            print(f"Test Mean Packing Ratio: {mean_packing_ratio_test:.2f}%")
            
            #os.makedirs(r'C:\Users\wesley\Desktop\workboard\Volumn_Project\History', exist_ok=True)
            history_df.to_excel(os.path.join(self.SAVE_FILE , 'training_history_{today}_OnehotE.xlsx', index=False)
            print(f"Training history saved to training_history_{today}_OnehotE.xlsx")

            test_results = self.model.evaluate(X_test, y_test, return_dict=True)
            print(f"Test MAE: {test_results['mae']:.2f}, MSE: {test_results['mse']:.2f}")

if __name__ == "__main__":
    start = time.time()
    bot = Neural_Network_Arch()
    bot._predict_container_volume()
    end = time.time()
    print(f"耗時{end - start}")