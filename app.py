import streamlit as st
import pandas as pd
import re
import easyocr
from rapidfuzz import process, fuzz

# Load dataset
data = pd.read_csv('db_drug_interactions.csv')
unique_drugs = pd.concat([data['Drug 1'], data['Drug 2']]).unique()

# OCR Function to extract text from image
reader = easyocr.Reader(['en'])

# Streamlit App title
st.title("Drugs Interaction Checker")

def extract_text_from_image(image_path):
    # Use EasyOCR to extract text from the image
    results = reader.readtext(image_path)
    # Combine all the detected text parts into a single string
    text = ' '.join([res[1] for res in results])
    return text

def clean_ocr_text(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    spelling_variations = {
        'amoxycillin': 'amoxicillin',
        'paracetamol': 'acetaminophen'
        # Add more variations if needed
    }
    
    text = text.lower()  # Convert text to lowercase first
    for wrong_spelling, correct_spelling in spelling_variations.items():
        text = text.replace(wrong_spelling, correct_spelling)
    
    return text

def identify_active_ingredient(text, drug_list):
    text = clean_ocr_text(text)
    
    # Handle cases where 'Vitamin' is found followed by another word
    if 'vitamin' in text.lower():
        text = handle_vitamin_exception(text)

    # Lowercase all drug names in the drug list
    drug_list_lower = [drug.lower() for drug in drug_list]
    
    # Perform fuzzy matching
    results = process.extract(text, drug_list_lower, scorer=fuzz.partial_ratio)
    threshold = 90
    filtered_results = [result for result in results if result[1] > threshold]
    matched_ingredients = []
  
    for result in filtered_results:
        if result[0] in drug_list_lower:
            matched_ingredients.append(drug_list[drug_list_lower.index(result[0])])
    
    if matched_ingredients:
        return matched_ingredients
    return ["Unknown active ingredient"]

def handle_vitamin_exception(text):
    """
    Handle special case when 'vitamin' is found in the text.
    This function ensures 'Vitamin' is followed by another word (e.g., 'A', 'B', 'C') and extracts both.
    """
    words = text.lower().split()
    
    # Find the index of the word 'vitamin'
    vitamin_index = [i for i, word in enumerate(words) if word == 'vitamin']
    
    if vitamin_index:
        # For each occurrence of 'vitamin', check the following word and append it
        for idx in vitamin_index:
            if idx + 1 < len(words):
                vitamin_combination = f"vitamin {words[idx + 1]}"
                text += f" {vitamin_combination}"  # Add 'vitamin + next word' to the search text
                
    return text

def search_interaction(drug1, drug2, data):
    # Lowercase the drug names in the DataFrame
    data = data.copy()
    data['Drug 1'] = data['Drug 1'].str.lower()
    data['Drug 2'] = data['Drug 2'].str.lower()
    
    # Find interactions in the DataFrame
    interaction_row = data[(
        (data['Drug 1'].str.contains(drug1, case=False)) & 
        (data['Drug 2'].str.contains(drug2, case=False))
    ) | (
        (data['Drug 1'].str.contains(drug2, case=False)) & 
        (data['Drug 2'].str.contains(drug1, case=False))
    )]
    if not interaction_row.empty:
        return interaction_row['Interaction Description'].values[0]
    else:
        return "No interaction found"

def display_message(message, color):
    # Updated to use a more modern design with shadow and rounded corners
    st.markdown(
        f"""
        <div style="
            background-color: {color}; 
            padding: 15px; 
            border-radius: 12px; 
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
            margin-bottom: 10px;
        ">
            <p style="color: white; font-size: 16px; font-family: 'Arial', sans-serif; text-align: center;">
                {message}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def find_interaction_between_images(image1_path, image2_path, df):
    # Extract text from images
    text1 = extract_text_from_image(image1_path)
    text2 = extract_text_from_image(image2_path)
    
    # Identify active ingredients from both images
    active_ingredients1 = identify_active_ingredient(text1, unique_drugs)
    active_ingredients2 = identify_active_ingredient(text2, unique_drugs)
    
    st.write(f"Active ingredients in image 1: {active_ingredients1}")
    st.write(f"Active ingredients in image 2: {active_ingredients2}")
    
    interaction_found = False
    # Compare all active ingredients between the two images
    for ingredient1 in active_ingredients1:
        for ingredient2 in active_ingredients2:
            if ingredient1 != "Unknown active ingredient" and ingredient2 != "Unknown active ingredient":
                interaction = search_interaction(ingredient1, ingredient2, df)
                if interaction != "No interaction found":
                    interaction_found = True
                    display_message(f"Interaction between '{ingredient1}' and '{ingredient2}': {interaction}", "red")
                else:
                    display_message(f"No interaction between '{ingredient1}' and '{ingredient2}'", "green")
            else:
                display_message(f"Could not identify active ingredients between '{ingredient1}' and '{ingredient2}'.", "yellow")
    
    if not interaction_found:
        display_message("No interactions found between any of the identified ingredients.", "green")

# Streamlit file upload and interaction section
st.header("Upload Images for Drug Interaction")

uploaded_image1 = st.file_uploader("Upload the first image", type=["png", "jpg", "jpeg"])
uploaded_image2 = st.file_uploader("Upload the second image", type=["png", "jpg", "jpeg"])

if uploaded_image1 and uploaded_image2:
    # Create two columns for side-by-side display
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(uploaded_image1, caption='Uploaded Image 1', use_column_width=True)
    
    with col2:
        st.image(uploaded_image2, caption='Uploaded Image 2', use_column_width=True)
    
    with open("temp_image1.png", "wb") as f:
        f.write(uploaded_image1.getbuffer())
    
    with open("temp_image2.png", "wb") as f:
        f.write(uploaded_image2.getbuffer())
    
    # Process the images and display the interaction results
    find_interaction_between_images("temp_image1.png", "temp_image2.png", data)
