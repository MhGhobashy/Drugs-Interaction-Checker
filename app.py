import streamlit as st
import pandas as pd
import re
import easyocr
from rapidfuzz import process, fuzz
from itertools import combinations
import os
import io

# Load dataset
data = pd.read_csv('db_drug_interactions.csv')
unique_drugs = pd.concat([data['Drug 1'], data['Drug 2']]).unique()

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Streamlit App title
st.title("Drug Interaction Checker")

# Color scheme
COLORS = {
    "success": "#388E3C",  # Matte green
    "warning": "#FBC02D",  # Matte yellow
    "danger": "#D32F2F",   # Matte red
    "neutral": "#455A64"   # Matte slate
}

def extract_text_from_image(image_path):
    """Extract text from image using EasyOCR"""
    results = reader.readtext(image_path)
    return ' '.join([res[1] for res in results])

def clean_ocr_text(text):
    """Clean and normalize OCR-extracted text"""
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    
    # Spelling corrections
    corrections = {
        'amoxycillin': 'amoxicillin',
        'paracetamol': 'acetaminophen',
        'vitimin': 'vitamin'
    }
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    return text

def identify_active_ingredient(text, drug_list):
    """Identify active ingredients using fuzzy matching"""
    cleaned_text = clean_ocr_text(text)
    
    # Handle vitamin combinations
    if 'vitamin' in cleaned_text:
        cleaned_text = handle_vitamin_exception(cleaned_text)

    # Fuzzy matching with rapidfuzz
    normalized_drugs = [d.lower() for d in drug_list]
    matches = process.extract(
        cleaned_text, 
        normalized_drugs, 
        scorer=fuzz.partial_ratio,
        score_cutoff=90
    )
    
    return [drug_list[normalized_drugs.index(m[0])] for m in matches]

def handle_vitamin_exception(text):
    """Special handling for vitamin combinations"""
    words = text.split()
    for i, word in enumerate(words):
        if word == 'vitamin' and i+1 < len(words):
            text += f" {word} {words[i+1]}"
    return text

def search_interactions(drug_a, drug_b, df):
    """Check for interactions between two drugs"""
    drug_a = drug_a.lower()
    drug_b = drug_b.lower()
    
    interaction = df[
        ((df['Drug 1'].str.lower() == drug_a) & 
         (df['Drug 2'].str.lower() == drug_b)) |
        ((df['Drug 1'].str.lower() == drug_b) & 
         (df['Drug 2'].str.lower() == drug_a))
    ]
    
    return interaction['Interaction Description'].values[0] if not interaction.empty else "No interaction found"

def display_message(message, message_type):
    """Styled message display component"""
    color = COLORS.get(message_type, COLORS['neutral'])
    st.markdown(
        f'<div style="background-color:{color}; padding:12px; border-radius:8px; margin:8px 0;">'
        f'<p style="color:white; margin:0;">{message}</p>'
        '</div>',
        unsafe_allow_html=True
    )

def process_uploaded_images(uploaded_files):
    """Process uploaded images and return ingredients"""
    all_ingredients = []
    
    for idx, uploaded_file in enumerate(uploaded_files):
        # Create temporary file
        temp_path = f"temp_{idx}.png"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # Extract text and identify ingredients
            text = extract_text_from_image(temp_path)
            ingredients = identify_active_ingredient(text, unique_drugs)
            all_ingredients.extend(ingredients)
            
            # Display image and ingredients
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(uploaded_file, use_column_width=True)
            with col2:
                st.subheader(f"Image {idx+1} Analysis")
                st.write("**Detected ingredients:**")
                st.write(", ".join(ingredients) or "No ingredients identified")
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return all_ingredients

# Main app interface
st.header("Upload Medication Images")
uploaded_files = st.file_uploader(
    "Select images of drug packaging",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    ingredients = process_uploaded_images(uploaded_files)
    unique_ingredients = [i for i in set(ingredients) if i != "Unknown active ingredient"]
    
    if len(unique_ingredients) >= 2:
        st.header("Interaction Analysis")
        found_interaction = False
        
        for drug_a, drug_b in combinations(unique_ingredients, 2):
            interaction = search_interactions(drug_a, drug_b, data)
            
            if interaction != "No interaction found":
                found_interaction = True
                display_message(
                    f"⚠️ **Interaction between {drug_a} and {drug_b}:** {interaction}",
                    "danger"
                )
            else:
                display_message(
                    f"✅ No interaction between {drug_a} and {drug_b}",
                    "success"
                )
        
        if not found_interaction:
            display_message("🎉 No dangerous interactions found between any identified ingredients", "success")
    else:
        display_message("⚠️ Please upload at least 2 medications with identifiable ingredients", "warning")
