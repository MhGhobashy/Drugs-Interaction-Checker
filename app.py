import streamlit as st
import pandas as pd
import re
import easyocr
from rapidfuzz import process, fuzz
from itertools import combinations
import os
from PIL import Image
import io

# Load dataset
data = pd.read_csv('db_drug_interactions.csv')
unique_drugs = pd.concat([data['Drug 1'], data['Drug 2']]).unique()

# OCR Function to extract text from image
reader = easyocr.Reader(['en'])

# Streamlit App title
st.title("Drugs Interaction Checker")

# Matte color scheme
COLORS = {
    "success": "#4caf50",      # Matte green
    "warning": "#ffd700",      # Matte gold
    "danger": "#c94c4c",       # Matte red
    "neutral": "#607d8b"       # Matte slate
}

def extract_text_from_image(image_path):
    results = reader.readtext(image_path)
    text = ' '.join([res[1] for res in results])
    return text

def clean_ocr_text(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    spelling_variations = {
        'amoxycillin': 'amoxicillin',
        'paracetamol': 'acetaminophen'
    }
    
    text = text.lower()
    for wrong_spelling, correct_spelling in spelling_variations.items():
        text = text.replace(wrong_spelling, correct_spelling)
    return text

def identify_active_ingredient(text, drug_list):
    text = clean_ocr_text(text)
    
    if 'vitamin' in text.lower():
        text = handle_vitamin_exception(text)

    drug_list_lower = [drug.lower() for drug in drug_list]
    results = process.extract(text, drug_list_lower, scorer=fuzz.partial_ratio)
    threshold = 90
    filtered_results = [result for result in results if result[1] > threshold]
    matched_ingredients = []
  
    for result in filtered_results:
        if result[0] in drug_list_lower:
            matched_ingredients.append(drug_list[drug_list_lower.index(result[0])])
    
    return matched_ingredients if matched_ingredients else ["Unknown active ingredient"]

def handle_vitamin_exception(text):
    words = text.lower().split()
    vitamin_index = [i for i, word in enumerate(words) if word == 'vitamin']
    
    if vitamin_index:
        for idx in vitamin_index:
            if idx + 1 < len(words):
                vitamin_combination = f"vitamin {words[idx + 1]}"
                text += f" {vitamin_combination}"
    return text

def search_interaction(drug1, drug2, data):
    data = data.copy()
    data['Drug 1'] = data['Drug 1'].str.lower()
    data['Drug 2'] = data['Drug 2'].str.lower()
    
    interaction_row = data[(
        (data['Drug 1'].str.contains(drug1.lower())) & 
        (data['Drug 2'].str.contains(drug2.lower()))
    ) | (
        (data['Drug 1'].str.contains(drug2.lower())) & 
        (data['Drug 2'].str.contains(drug1.lower()))
    )]
    return interaction_row['Interaction Description'].values[0] if not interaction_row.empty else "No interaction found"

def display_message(message, color_key):
    color = COLORS.get(color_key, COLORS["neutral"])
    st.markdown(
        f"""
        <div style="
            background-color: {color}; 
            padding: 15px; 
            border-radius: 12px; 
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
            margin-bottom: 10px;
            color: white;
        ">
            <p style="font-size: 16px; font-family: 'Arial', sans-serif;">
                {message}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def process_images(uploaded_images, df):
    all_ingredients = []
    temp_files = []

    for i, image in enumerate(uploaded_images):
        # Convert the uploaded file to an image object
        img = Image.open(image)
        
        # Save temporary file (optional, for debugging)
        temp_path = f"temp_{i}.png"
        img.save(temp_path)
        temp_files.append(temp_path)
        
        # Extract text from the image
        text = extract_text_from_image(temp_path)
        ingredients = identify_active_ingredient(text, unique_drugs)
        all_ingredients.extend(ingredients)
        
        # Display the image and ingredients
        col1, col2 = st.columns([1, 3])
        with col1:
            # Display the image directly from the file-like object
            st.image(img, use_container_width=True)
        with col2:
            st.write(f"**Image {i+1} ingredients:**")
            st.write(", ".join(ingredients) if ingredients else st.write("No ingredients identified"))

    # Clean up temporary files
    for file in temp_files:
        os.remove(file)

    return all_ingredients

# Streamlit UI
st.header("Upload Drug Images")

uploaded_files = st.file_uploader(
    "Upload images of drug packaging (multiple allowed)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    all_ingredients = process_images(uploaded_files, data)
    
    if len(all_ingredients) < 2:
        display_message("Need at least 2 ingredients to check interactions", "warning")
    else:
        interaction_found = False
        pairs = combinations(set(all_ingredients), 2)
        
        for drug1, drug2 in pairs:
            if "Unknown" in drug1 or "Unknown" in drug2:
                display_message(f"Skipping unknown ingredient pair: {drug1} & {drug2}", "warning")
                continue
                
            interaction = search_interaction(drug1, drug2, data)
            if interaction != "No interaction found":
                interaction_found = True
                display_message(f"**Interaction between {drug1} and {drug2}:** {interaction}", "danger")
            else:
                display_message(f"No interaction between {drug1} and {drug2}", "success")
        
        if not interaction_found and len(all_ingredients) >= 2:
            display_message("No interactions found between any identified ingredients", "success")
