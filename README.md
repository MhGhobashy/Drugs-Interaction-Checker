# Drug Interaction Checker

This is a Streamlit-based web application that checks for potential drug interactions based on active ingredients extracted from images. The app uses Optical Character Recognition (OCR) to extract text from images of drug labels, performs fuzzy matching to identify active ingredients, and then checks for interactions using a drug interaction dataset.

## Features

- **EasyOCR Integration**: Extracts text from uploaded images.
- **Fuzzy Matching**: Uses `rapidfuzz` to identify active ingredients even with variations in spelling.
- **Drug Interaction Lookup**: Searches a dataset for known interactions between active ingredients.
- **User-Friendly Interface**: Upload two images, see extracted active ingredients, and check for potential interactions.
- **Responsive Design**: Modern, sleek interface with visual feedback (colored boxes) for interactions.

## Dataset

You can find the dataset on my [Kaggle profile](https://www.kaggle.com/datasets/mghobashy/drug-drug-interactions)

The drug interaction dataset used in this app was created by:
1. **Source**: Downloading interaction data from [The Drug-Drug Interaction (DDI) source](https://tdcommons.ai/multi_pred_tasks/ddi/).
2. **Mapping Interactions**: The interaction mapping provided by the website was used to map interaction types.
3. **Drug Name Mapping**: Drug IDs were obtained from the dataset, and the corresponding drug names were mapped by querying the **DrugBank** database to match Drug IDs to actual drug names.

The dataset contains the following columns:
    - `Drug 1`: Name of the first drug
    - `Drug 2`: Name of the second drug
    - `Interaction Description`: A description of the interaction between the two drugs
    
## Usage

Upload Images: Upload two images containing drug names or drug labels.
Extract and Identify Active Ingredients: The app will extract text using OCR, clean it up, and identify potential active ingredients using fuzzy matching.
Check for Interactions: The app compares the identified active ingredients from both images and checks the dataset for known interactions.
Visual Feedback: The app displays interaction results in green or red boxes:
  Green Box: No interaction found.
  Red Box: Interaction detected.

Special Cases
If the word `Vitamin` is detected, the app will also check the word following Vitamin (e.g., Vitamin A, Vitamin C) to ensure proper identification.

## Contributing

Feel free to open issues or submit pull requests if you'd like to contribute to this project. All contributions are welcome!
