import streamlit as st
from dotenv import load_dotenv
import os
import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup  # Import BeautifulSoup for HTML parsing

# Load environment variables
load_dotenv()

# Function to convert HTML content to plain text with bullet points
def html_to_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Process unordered lists (<ul>)
    for ul in soup.find_all('ul'):
        items = ul.find_all('li')
        bullet_points = "\n".join(f"• {item.get_text(strip=True)}" for item in items)
        ul.replace_with(bullet_points)
    
    # Process ordered lists (<ol>)
    for ol in soup.find_all('ol'):
        items = ol.find_all('li')
        numbered_items = "\n".join(f"{i+1}. {item.get_text(strip=True)}" for i, item in enumerate(items))
        ol.replace_with(numbered_items)
    
    return soup.get_text(separator="\n", strip=True)

# Function to get diet recommendations and recipes
def get_diet_recommendations(diet_type, api_key):
    # Spoonacular API endpoint for recipes
    api_url = (
        f"https://api.spoonacular.com/recipes/complexSearch?"
        f"diet={diet_type}&number=5&apiKey={api_key}"
    )
    
    response = requests.get(api_url)
    results = response.json().get("results", [])

    return results

def get_recipe_details(recipe_id, api_key):
    # Spoonacular API endpoint for recipe details
    api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}"
    
    response = requests.get(api_url)
    return response.json()

def diet_recommendation_app():
    st.title("Diet Recommendation App")

    # User input for diet type
    diet_type = st.selectbox("Select your diet type:", ["vegan", "vegetarian", "paleo", "keto", "gluten-free"])

    # API Key from environment variables
    api_key = os.getenv("spoonacular_api_key")

    if st.button("Get Recommendations"):
        if api_key:
            recipes = get_diet_recommendations(diet_type, api_key)
            
            if recipes:
                for recipe in recipes:
                    recipe_id = recipe["id"]
                    recipe_details = get_recipe_details(recipe_id, api_key)
                    
                    # Display recipe details
                    st.subheader(recipe_details.get("title"))
                    
                    # Display recipe image
                    image_url = recipe_details.get("image")
                    if image_url:
                        response = requests.get(image_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption=recipe_details.get("title"))
                    
                    # Display recipe instructions
                    instructions_html = recipe_details.get("instructions")
                    if instructions_html:
                        instructions_text = html_to_text(instructions_html)
                        st.write("Instructions:")
                        st.write(instructions_text)
                    
                    st.write("\n")
            else:
                st.write("No recipes found for this diet type.")
        else:
            st.write("API key is missing. Please add your Spoonacular API key.")

if __name__ == "__main__":
    diet_recommendation_app()
