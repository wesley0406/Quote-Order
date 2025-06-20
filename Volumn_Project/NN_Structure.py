from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
import time
from category_encoders import TargetEncoder
import numpy as np
import tensorflow as tf
import datetime


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Add, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# import the pre_train data
from Pre_Train_data import FETCH_ERP_SCREW


class Neural_Network_Arch() :
	def __init__(self): 
		self.Train_data = FETCH_ERP_SCREW().Result.copy()
		self.model = None  # Placeholder for NN model
		self.scaler = None  # Placeholder for scaler
		self.encoder = None  # Placeholder for categorical encoder
		self.container_volumes = None  # Placeholder for unique container volumes
		self._predict_container_volume()

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
			x = Dense(128, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01))(inputs)
			x = BatchNormalization()(x)
			x = Dropout(0.3)(x)
			
			# Residual block 1
			x1 = Dense(64, activation='relu')(x)
			x1 = BatchNormalization()(x1)
			x1 = Dense(64, activation='relu')(x1)
			x1 = BatchNormalization()(x1)
			
			# Project x to match x1's shape
			x_proj1 = Dense(64, activation='linear')(x)
			x = Add()([x_proj1, x1])
			x = Dropout(0.3)(x)
			
			# Residual block 2
			x2 = Dense(32, activation='relu')(x)
			x2 = BatchNormalization()(x2)
			x2 = Dense(32, activation='relu')(x2)
			x2 = BatchNormalization()(x2)
			# Project x to match x2's shape
			x_proj2 = Dense(32, activation='linear')(x)
			x = Add()([x_proj2, x2])
			x = Dropout(0.3)(x)
			
			# Output layer
			outputs = Dense(1, activation='linear')(x)
			
			model = tf.keras.Model(inputs, outputs)
			
			model.compile(
				optimizer=tf.keras.optimizers.AdamW(learning_rate=0.001),
				loss=tf.keras.losses.Huber(),
				metrics=['mae', 'mse']
			)
			
			return model
		
		except Exception as e:
			print(f"Error in _build_model: {str(e)}")
			raise

	def _prepare_feature_NN(self) :
		
		# Log transformations
		for col in ['Screw volume in the box', 'small_pack_qty', 'qty_per_ctn']:
			self.Train_data[f'log_{col}'] = np.log1p(self.Train_data[col].fillna(0))

		# Numeric features
		numeric_features = [
			'Screw volume in the box', 'Diameter', 'Length', 'small_pack_qty', 'qty_per_ctn', 'Packing_Ratio', 
			'log_Screw volume in the box', 'log_small_pack_qty', 'log_qty_per_ctn'
		]

		# Categorical features
		categorical_features = ['Screw_Type', 'Head_Type']

		# Handle missing values
		self.Train_data[numeric_features] = self.Train_data[numeric_features].fillna(self.Train_data[numeric_features].median())
		self.Train_data[categorical_features] = self.Train_data[categorical_features].fillna('Unknown')

		# Scale numeric features
		if self.scaler is None:
			self.scaler = RobustScaler()
			X_numeric = self.scaler.fit_transform(self.Train_data[numeric_features])
		else:
			X_numeric = self.scaler.transform(self.Train_data[numeric_features])

		 # Clip large values to prevent overflow
		# for col in numeric_features:
		#     if col in self.Train_data:
		#         self.Train_data[col] = self.Train_data[col].clip(lower=-1e6, upper=1e6)
		# Encode categorical features
		if self.encoder is None:
			self.encoder = TargetEncoder(cols=categorical_features)
			X_categorical = self.encoder.fit_transform(self.Train_data[categorical_features], self.Train_data['decision box/master volume'])
		else:
			X_categorical = self.encoder.transform(self.Train_data[categorical_features])

		# Combine features
		X = np.hstack([X_numeric, X_categorical])
		
		# Target (if training)
		y = self.Train_data['decision box/master volume'].values if 'decision box/master volume' in self.Train_data else None

		return X, y, self.scaler, self.encoder

	def _predict_container_volume(self, train = True):

		# Prepare data
		X, y, self.scaler, self.encoder = self._prepare_feature_NN()


		if train:
			# Split data
			X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size = 0.2)
			X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size = 0.5)

			# Build and train model
			self.model = self._build_model(input_dim = X.shape[1])
			
			callbacks = [
				# EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
				ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
			]
			
			history = self.model.fit(
				X_train, y_train,
				validation_data=(X_val, y_val),
				batch_size = 64,
				epochs = 200,
				callbacks=callbacks,
				verbose=1
			)
			
			# Save training history to Excel
			history_df = pd.DataFrame(history.history)
			history_df['epoch'] = range(1, len(history_df) + 1)
			history_df = history_df[['epoch', 'loss', 'mae', 'mse', 'val_loss', 'val_mae', 'val_mse']]
			today = datetime.date.today()
			history_df.to_excel('training_history_{}.xlsx'.format(today), index=False)
			print("Training history saved to training_history.xlsx")

			# Evaluate on test set
			test_results = self.model.evaluate(X_test, y_test, return_dict=True)
			print(f"Test MAE: {test_results['mae']:.2f}, MSE: {test_results['mse']:.2f}")

		#save the current model
		model.save(r"C:\Users\wesley\Desktop\workboard\Volumn_Project\NN_Model\Ver_{today}")  # SavedModel folder format


if __name__ == "__main__":
	start = time.time()
	Neural_Network_Arch()
	end = time.time()
	print("耗時{}".format(end - start))