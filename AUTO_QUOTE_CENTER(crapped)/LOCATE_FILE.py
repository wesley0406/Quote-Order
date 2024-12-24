import os
import pandas as pd
import sqlite3  # Assuming the database is SQLite
from fuzzywuzzy import process
from openai import OpenAI
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def extract_data_by_dimension(file_path, target_dimension): # 
    try:
        # Load the Excel file into a DataFrame without headers initially
        df = pd.read_excel(file_path, header=None)
    except Exception as e:
        return f"Error loading file: {e}"
    
    # Print the first few rows for debugging
    #print("Initial DataFrame preview:\n", df.head(15))
    
    # Locate the row containing "尺寸"
    header_row_index = None

    for row_index, row in df.iterrows():
        for col_index, cell in enumerate(row):
            if '尺寸' in str(cell):
                header_row_index = row_index
                col = col_index
    # Check which size column exists and contains the target dimension

    if header_row_index is not None:
        # Set this row as the header
        df.columns = df.iloc[header_row_index]
        df = df.drop(header_row_index).reset_index(drop=True)
        if '尺寸' in df.columns[col]:
            # Define possible column names for forming price and check which one exists
            possible_price_columns = ['加工價', '單價']
            size_columns = ['尺寸', '英制尺寸', '公制尺寸']
            matching_size_column = None
            forming_price_column = None
            
            for size_col in size_columns:
                if size_col in df.columns:
                    print("find column!")
                    if df[size_col].astype(str).str.contains(target_dimension).any():
                        matching_size_column = size_col
                        break  
            if matching_size_column:
                # Use the identified size column to search for the desired dimension
                target_row = df[df[matching_size_column].astype(str).str.contains(target_dimension)]
                
            for forming in possible_price_columns:
                if forming in df.columns:
                    forming_price_column = str(forming)
                    break
            #target_row = df[df[df.columns[col]].astype(str).str.contains(target_dimension)]
            
            if not target_row.empty:
                # Extract relevant data: wire diameter (線徑), forming price (加工價), weight (單重)
                wire_diameter = target_row['線徑'].values[0]
                forming_price = target_row[forming_price_column].values[0]
                weight = target_row['單重'].values[0]

                return wire_diameter, forming_price, weight
            else:
                return "Dimension not found in the data."
        else:
            return "'尺寸' column not found in the DataFrame."
    else:
        return "Header row containing '尺寸' not found."

def get_drawing_number_by_product_code(db_path, product_code):

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query to get the drawing number based on the product code
        query = "SELECT DRAWING_NUMBER, SIZE FROM CUSTOMER_PRODUCT_SUMMARY WHERE PRODUCT_CODE = ?"
        cursor.execute(query, (product_code,))
        result = cursor.fetchone()
        
        # Close the connection
        conn.close()
        
        # Check if the drawing number was found
        if result:
            return result  # Return the drawing number
        else:
            return f"Drawing number for product code '{product_code}' not found in the database."
    
    except sqlite3.Error as e:
        return f"Database error: {e}"

def find_forming_price_file(directory, drawing_number):
    """
    Search the directory for a forming price file containing the drawing number in its name.
    
    :param directory: The root directory to search.
    :param drawing_number: The drawing number to search for.
    :return: The path to the forming price file if found, otherwise None.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if drawing_number in file:
                return os.path.join(root, file)
    return None

# Example usage
DB= r'Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db'  # Replace with your actual database path
FORMING = r"Z:\跨部門\螺絲報價\1-1 螺絲類別報價"
PRODUCT = '614CD'  # Replace with your product code

# drawing_number, size = get_drawing_number_by_product_code(DB, PRODUCT)
# ff = find_forming_price_file(FORMING, drawing_number)
# result = extract_data_by_dimension(ff, size.replace("X", "x"))
# print(ff)
# print(result)


# Function to get embeddings from OpenAI API

def get_embeddings(text):
    response = client.embeddings.create(
        model = "text-embedding-ada-002",
        input = [text],
        timeout = 10
        )
    # Extract and return the response text
    return np.array(response.data[0].embedding)

# Function to calculate cosine similarity
def calculate_similarity(embedding1, embedding2):
    return cosine_similarity([embedding1], [embedding2])[0][0]

# Function to find the most similar product name
def find_most_similar_product(target_product, directory):
    target_embedding = get_embeddings(target_product)
    most_similar_product = None
    highest_similarity = -1

    # Walk through the directory and read all files
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors = "ignore") as f:
                for line in f:
                    product_name = line.strip()
                    product_embedding = get_embeddings(product_name)
                    similarity = calculate_similarity(target_embedding, product_embedding)

                    # Update the most similar product if similarity is higher
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        most_similar_product = product_name

    return most_similar_product, highest_similarity

# Example usage
target_product = "機械螺絲 8.8 梅花孔 盤頭, 機械牙"
directory = r'Z:\跨部門\螺絲報價\1-1 螺絲類別報價'  
similar_product, similarity_score = find_most_similar_product(target_product, directory)

print(f"Most similar product: {similar_product}")
print(f"Similarity score: {similarity_score}")




