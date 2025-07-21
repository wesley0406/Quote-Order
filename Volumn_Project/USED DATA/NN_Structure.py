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
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.utils import plot_model
import plotly 


# import the pre_train data
from Pre_Train_data import FETCH_ERP_SCREW



class Neural_Network_Arch:
    def __init__(self, config_path = r'Model_Config\config.json'):
        self.Train_data = FETCH_ERP_SCREW().Result.copy()
        self.model = None  # Placeholder for NN model
        self.scaler = None  # Placeholder for scaler
        self.encoder = None  # Placeholder for categorical encoder
        self.container_volumes = None  # Placeholder for unique container volumes
        self.config = self._load_config(config_path)

    def _load_config(self, config_path):

        #Load configuration from a JSON file.
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config['model_config']
        except Exception as e:
            print(f"Error loading config file: {str(e)}")
            raise

    def _build_model(self, input_dim):
        """
        Build a complex NN model with residual connections and batch normalization.
        
        Args:
            input_dim: Number of input features
        
        Returns:
            model: Compiled Keras model
        """
        try:
            inputs = Input(shape=(input_dim,))
            
            # Initial dense layer
            x = Dense(128, activation='relu', 
                     kernel_regularizer=tf.keras.regularizers.l2(self.config['l2_regularization']))(inputs)
            x = BatchNormalization()(x)
            x = Dropout(self.config['dropout_rate'])(x)
            
            # Residual block 1
            x1 = Dense(64, activation='relu')(x)
            x1 = BatchNormalization()(x1)
            x1 = Dense(64, activation='relu')(x1)
            x1 = BatchNormalization()(x1)
            
            # Project x to match x1's shape
            x_proj1 = Dense(64, activation='linear')(x)
            x = Add()([x_proj1, x1])
            x = Dropout(self.config['dropout_rate'])(x)
            
            # Residual block 2
            x2 = Dense(32, activation='relu')(x)
            x2 = BatchNormalization()(x2)
            x2 = Dense(32, activation='relu')(x2)
            x2 = BatchNormalization()(x2)
            # Project x to match x2's shape
            x_proj2 = Dense(32, activation='linear')(x)
            x = Add()([x_proj2, x2])
            x = Dropout(self.config['dropout_rate'])(x)
            
            # Output layer
            outputs = Dense(1, activation='linear')(x)
            
            model = tf.keras.Model(inputs, outputs)
            
            # Configure optimizer
            optimizer = getattr(tf.keras.optimizers, self.config['optimizer'])(
                learning_rate=self.config['initial_learning_rate']
            )
            
            # experimaent on huber loss function 
            # loss_class = getattr(tf.keras.losses, self.config['loss_function'])
            # loss = loss_class(**self.config.get("Huber_params", {}))

            model.compile(
                optimizer = optimizer,
                #oss = loss,
                loss = getattr(tf.keras.losses, self.config['loss_function'])(),  # the default delta for keras is 1.0
                metrics=['mae', 'mse']
            )
            
            return model
        
        except Exception as e:
            print(f"Error in _build_model: {str(e)}")
            raise

    def _prepare_feature_NN(self):
        # Numeric features
        numeric_features = [
            'Screw volume in the box', 'Diameter', 'Length'
        ]

        # Categorical features
        categorical_features = ["pdc_4", "pdc_5", 'Screw_Type', 'Head_Type']

        # Handle missing values
        self.Train_data[numeric_features] = self.Train_data[numeric_features].fillna(self.Train_data[numeric_features].median())
        self.Train_data[categorical_features] = self.Train_data[categorical_features].fillna('Unknown')

        # Scale numeric features
        if self.scaler is None:
            self.scaler = RobustScaler()
            X_numeric = self.scaler.fit_transform(self.Train_data[numeric_features])
        else:
            X_numeric = self.scaler.transform(self.Train_data[numeric_features])

        if self.encoder is None:
            self.encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            X_categorical = self.encoder.fit_transform(self.Train_data[categorical_features])
            # Convert back to DataFrame with proper column names
            X_categorical = pd.DataFrame(X_categorical, 
                                       columns=self.encoder.get_feature_names_out(categorical_features),
                                       index=self.Train_data.index)
        else:
            X_categorical = self.encoder.transform(self.Train_data[categorical_features])
            X_categorical = pd.DataFrame(X_categorical, 
                                       columns=self.encoder.get_feature_names_out(categorical_features),
                                       index=self.Train_data.index)

        # Save the encoder and scaler
        today = datetime.date.today()
        os.makedirs(r'C:\Users\wesley\Desktop\workboard\Volumn_Project\Encode&Scaler', exist_ok=True)
        with open(rf'C:\Users\wesley\Desktop\workboard\Volumn_Project\Encode&Scaler\scaler_{today}.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)

        with open(rf'C:\Users\wesley\Desktop\workboard\Volumn_Project\Encode&Scaler\encoder_{today}.pkl', 'wb') as f:
            pickle.dump(self.encoder, f)

        # Combine features
        X = np.hstack([X_numeric, X_categorical])
        
        # Target (if training)
        y = self.Train_data['decision box/master volume'].values if 'decision box/master volume' in self.Train_data else None

        return X, y, self.scaler, self.encoder

    def _predict_container_volume(self, train=True):
        # Prepare data
        X, y, self.scaler, self.encoder = self._prepare_feature_NN()

        if train:
            # Split data
            X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2)
            X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5)

            # Build and train model
            self.model = self._build_model(input_dim=X.shape[1])
            
            callbacks = [
                ReduceLROnPlateau(
                    monitor = 'val_loss',
                    factor = self.config['factor_reduce_lr'],
                    patience = self.config['patience_reduce_lr'],
                    min_lr = self.config['min_lr']
                )
            ]
            
            history = self.model.fit(
                X_train, y_train,
                validation_data = (X_val, y_val),
                batch_size = self.config['batch_size'],
                epochs = self.config['epochs'],
                callbacks = callbacks,
                verbose = 1
            )
            # Save the current model
            today = datetime.date.today()
            os.makedirs(r'C:\Users\wesley\Desktop\workboard\Volumn_Project\NN_Model', exist_ok=True)
            self.model.save(rf"C:\Users\wesley\Desktop\workboard\Volumn_Project\NN_Model\Ver_{today}_OnehotE.keras")

            # Save training history to Excel
            history_df = pd.DataFrame(history.history)
            history_df['epoch'] = range(1, len(history_df) + 1)
            history_df = history_df[['epoch', 'loss', 'mae', 'mse', 'val_loss', 'val_mae', 'val_mse']]
            
            os.makedirs(r'C:\Users\wesley\Desktop\workboard\Volumn_Project\History', exist_ok=True)
            history_df.to_excel(rf'C:\Users\wesley\Desktop\workboard\Volumn_Project\History\training_history_{today}_OnehotE.xlsx', index=False)
            print(f"Training history saved to training_history_{today}_OnehotE.xlsx")

            # Evaluate on test set
            test_results = self.model.evaluate(X_test, y_test, return_dict=True)
            print(f"Test MAE: {test_results['mae']:.2f}, MSE: {test_results['mse']:.2f}")
 


if __name__ == "__main__":
    start = time.time()
    bot = Neural_Network_Arch()
    bot._predict_container_volume()
    end = time.time()
    print(f"耗時{end - start}")