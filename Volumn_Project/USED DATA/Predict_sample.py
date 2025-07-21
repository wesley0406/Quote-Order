import pandas as pd
import numpy as np
import tensorflow as tf
from Pre_Train_data import FETCH_ERP_SCREW  # Import FETCH_ERP class
import pickle
import os, sys
from math import pi
from fractions import Fraction



from Pre_Train_data import FETCH_ERP_SCREW  # Import FETCH_ERP class
from NN_Structure import Neural_Network_Arch

class Prediction_Package():
    def __init__(self):
        #self.Box_ref = pd.read_excel(r"Z:\業務部\業務一課\Q.工具程式\CAYSIE\Box_ref.xlsx")
        self.model_path = "NN_Model/Ver_2025-07-02_OnehotE.keras"
        self.reference_data_path = r"C:\Users\wesley\Desktop\workboard\Volumn_Project\ALL_DATA.xlsx"
        self.scaler_path = r"Encode&Scaler/scaler_2025-07-02.pkl"
        self.encoder_path = r"Encode&Scaler/encoder_2025-07-02.pkl"
        self.EXP_FOLDER = r"C:\Users\wesley\Desktop\workboard\Volumn_Project\Experiment_Data"
        self.S_Box = pd.read_excel("Box_Choice.xlsx", sheet_name = "S_Box")
        self.N_Box = pd.read_excel("Box_Choice.xlsx", sheet_name = "N_Box")
        self.Result = None
        self.load_preprocessors(self.scaler_path , self.encoder_path)


    def parse_diameter(self, val):
            if 'M' in val:
                return float(val.lstrip('M'))  # M0050 → 5.0 mm
            elif '#' in val:
                return (int(val.split('#')[1].lstrip('0'))*0.013+0.06)*25.4  # I#006 → #6 → 3.5052 mm
            else:
                return None

    def preprocess_length(self, val, unit='mm'):

        if unit == 'mm':
            return float(val)  # 40 → 40.0 mm
        elif unit == 'inch':
            if "/" in val and "-":
                inches_len = int(val.split("-")[0])*25.4
                min_inches_len = float(Fraction(val.split("-")[1]))*25.4
            elif "/" in val : 
                inches_len = 0
                min_inches_len = float(Fraction(val))*25.4
            else :
                inches_len = int(val)*25.4


            return (inches_len + min_inches_len) # 1-1/4 → 1.25 inch →31.75mm



    def load_preprocessors(self,scaler_path, encoder_path):
        
        scaler = None
        encoder = None
        try:
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                print(f"Loaded scaler from {scaler_path}")
            if os.path.exists(encoder_path):
                with open(encoder_path, 'rb') as f:
                    encoder = pickle.load(f)
                print(f"Loaded encoder from {encoder_path}")
            return scaler, encoder
        except Exception as e:
            print(f"Error loading preprocessors: {str(e)}")
            return None, None

    def estimate_screw_volume(self, diam, length):

        # Convert length to float
        if pd.isna(length) or length == "":
            return None
        # Validate inputs
        if pd.isna(diam) or diam == "" :
            return None

        # Calculate radius and volume
        radius = diam / 2
        volume = pi * (radius ** 2) * length
        return round(volume, 2)  # Round to 2 decimal places for readability


    def predict_product(self):

        NN_MAC = Neural_Network_Arch()

        #Predict decision box/master volume for a single row using a .keras model.

        
        try:
            # Define single row (example based on prior context)
            Predict_Sample = pd.read_excel(os.path.join(self.EXP_FOLDER, "20250701.xlsx"))

            Predict_Sample['Length'] = Predict_Sample.apply(lambda row: self.preprocess_length(str(row['Length']), unit = 'inch' 
                        if '#' in str(row['Diameter']) else 'mm'), axis=1)
            Predict_Sample["Diameter"] = Predict_Sample["Diameter"].apply(self.parse_diameter)
            
            Predict_Sample["Screw volume in the box"] = Predict_Sample.apply(lambda row : 
                self.estimate_screw_volume(row['Diameter'], row["Length"])*row["Quantity"], axis = 1)

            

            # Load preprocessors or fit using reference data
            scaler, encoder = self.load_preprocessors(self.scaler_path, self.encoder_path)
            if scaler is None or encoder is None:
                print("Fitting preprocessors using reference data")
                ref_data = pd.read_excel(reference_data_path)
                erp_ref = FETCH_ERP()
                erp_ref.ALL_DATA = ref_data.copy()
                erp_ref._fetch_screw_volume()
                erp_ref._calculate_screw_volume_in_box()
                X_ref, y_ref, scaler, encoder = erp_ref._prepare_features(erp_ref.ALL_DATA)
                erp.scaler = scaler
                erp.encoder = encoder
                # Save for future use
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                with open(encoder_path, 'wb') as f:
                    pickle.dump(encoder, f)
                print(f"Saved scaler to {scaler_path}, encoder to {encoder_path}")
            else:
                NN_MAC.scaler = scaler
                NN_MAC.encoder = encoder

            # Prepare features for single row
            print(Predict_Sample)

            NN_MAC.Train_data = Predict_Sample[['Screw volume in the box', 'Diameter', 'Length', "pdc_4", "pdc_5",'Screw_Type', 'Head_Type']]
            X, _, _, _ = NN_MAC._prepare_feature_NN()
            print(f"Feature shape for single row: {X.shape}")

            # Load model
            model = tf.keras.models.load_model(self.model_path)
            print(f"Loaded model: {self.model_path}")

            # Make prediction
            pred = model.predict(X, batch_size=1).flatten()
            Predict_Sample['predicted_decision_volume'] = pred
            self.Result = Predict_Sample

        except Exception as e:
            print(f"Error in predict_single_row: {e}")
            raise
    def Match_Box(self):

        #check if we got the result
        if self.Result.empty :
            raise ValueError("please check if you run the NN model")

        # prepare the expect box type
        self.S_Box["Volume(mm³)"] = self.S_Box["Volume"].apply(lambda x : int(x.split("x")[0])*int(x.split("x")[1])*int(x.split("x")[2]))
        self.N_Box["Volume(mm³)"] = self.N_Box["Volume"].apply(lambda x : int(x.split("x")[0])*int(x.split("x")[1])*int(x.split("x")[2]))

        # Get box volume list for comparison
        available_volumes_S = self.S_Box["Volume(mm³)"].values
        available_volumes_N = self.N_Box["Volume(mm³)"].values
        

        def find_closest_box(vol):

            closest_volume_S = min(available_volumes_S, key = lambda v: abs(v - vol))
            closest_volume_N = min(available_volumes_N, key = lambda v: abs(v - vol))

            matched_S = self.S_Box[self.S_Box["Volume(mm³)"] == closest_volume_S].iloc[0]
            matched_N = self.N_Box[self.N_Box["Volume(mm³)"] == closest_volume_N].iloc[0]

            return matched_S["Quote_Code"] + "/" + matched_N["Quote_Code"]


        self.Result["Matched_Box"] = self.Result["predicted_decision_volume"].apply(find_closest_box)
        self.Result.to_excel(os.path.join(self.EXP_FOLDER, "Test_result_20250701.xlsx"))

        print(self.Result)
            

if __name__ == "__main__":
    bot = Prediction_Package()
    bot.predict_product()
    bot.Match_Box()
    