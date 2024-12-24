import openai
import numpy as np 
import os
from sklearn.metrics.pairwise import cosine_similarity

#  OpenAI API key

def get_embeddings(text):
    try:
        # Create embedding using OpenAI API
        response = openai.embeddings.create(
            input=[text],  # The input should be a list of texts
            model="text-embedding-ada-002"  # Specify a compatible embedding model
        )
        # Access the 'data' attribute correctly and return the embedding
        embedding = response.data[0].embedding
        return np.array(embedding)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
def calculate_similarity(embedding1, embedding2):
    return cosine_similarity([embedding1], [embedding2])[0][0]

def find_most_similar_product(target_product):
    target_embedding = get_embeddings(target_product)
    most_similar_category = None
    highest_similarity = -1
    
    # Walk through the directory find the category
    for files in os.listdir(r"Z:\跨部門\螺絲報價\1-1 螺絲類別報價"):
        product_embedding = get_embeddings(files)
        similarity = calculate_similarity(target_embedding, product_embedding)
        # Update the most similar product if similarity is higher
        if similarity > highest_similarity:
            highest_similarity = similarity
            most_similar_category = files

    # Walk through the caregory find the price
    most_related_forming_price = None
    highest_forming_similarity = -1
    RELATED_CATEGORY = os.path.join(r"Z:\跨部門\螺絲報價\1-1 螺絲類別報價", most_similar_category) # locate the category

    for forming_price in os.listdir(RELATED_CATEGORY):
        forming_price_embedding = get_embeddings(forming_price)
        similarity_forming = calculate_similarity(target_embedding, forming_price_embedding)
        if similarity_forming > highest_forming_similarity:
            highest_forming_similarity = similarity_forming
            most_related_forming_price = forming_price


    return os.path.join(RELATED_CATEGORY, most_related_forming_price), highest_forming_similarity

TEST, TEST2 = find_most_similar_product("機械螺絲 4.8 十字 盤頭, 機械牙")
print(TEST, TEST2)
