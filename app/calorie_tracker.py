import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px

# Function to calculate BMR
def calculate_bmr(weight, height, age, sex):
    if sex == "male":
        bmr = 13.397 * weight + 4.799 * height - 5.677 * age + 88.362
    else:
        bmr = 9.247 * weight + 3.098 * height - 4.330 * age + 447.593
    return bmr

# Function to calculate BMI
def calculate_bmi(weight, height):
    bmi = (weight / (height / 100) ** 2)
    return bmi

# Function to interpret BMI levels
def interpret_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 24.9:
        return "Normal Weight"
    elif 25 <= bmi < 29.9:
        return "Overweight"
    else:
        return "Obese"

# Function to calculate daily calories
def calculate_daily_calories(bmr, activity_level):
    if activity_level == "sedentary":
        calories = bmr * 1.2
    elif activity_level == "lightly active":
        calories = bmr * 1.375
    elif activity_level == "moderately active":
        calories = bmr * 1.55
    else:
        calories = bmr * 1.725
    return calories

# Function to build nutritional values
def build_nutritional_values(weight, calories):
    protein_calories = weight * 4
    res_calories = calories - protein_calories
    carb_calories = calories / 2.
    fat_calories = calories - carb_calories - protein_calories
    res = {'Protein Calories': protein_calories, 'Carbohydrates Calories': carb_calories, 'Fat Calories': fat_calories}
    return res

# Function to extract grams from nutritional values
def extract_gram(table):
    protein_grams = table['Protein Calories'] / 4.
    carbs_grams = table['Carbohydrates Calories'] / 4.
    fat_grams = table['Fat Calories'] / 9.
    res = {'Protein Grams': protein_grams, 'Carbohydrates Grams': carbs_grams, 'Fat Grams': fat_grams}
    return res

def calorie_tracker_app():
    st.title("Holistic Calorie Tracker")
    
    # User input with default values
    weight = st.slider("Enter your weight in KGs:", 40.0, 200.0, 70.0)
    height = st.slider("Enter your height in Cms:", 100.0, 250.0, 170.0)
    age = st.slider("Enter your age:", 1, 100, 25)
    sex = st.radio("Select your sex:", options=["male", "female"])
    activity_level = st.selectbox(
        "Select your activity level:",
        options=["sedentary", "lightly active", "moderately active", "very active"],
    )

    # Calculate BMR, BMI, and Daily Calories
    bmr = calculate_bmr(weight, height, age, sex)
    bmi = calculate_bmi(weight, height)
    bmi_category = interpret_bmi(bmi)
    calories = calculate_daily_calories(bmr, activity_level)

    # Display BMR, BMI, and Daily Calories
    st.subheader("Your Daily Calorie Needs:")
    st.write(f"Basal Metabolic Rate (BMR): {bmr:.2f} calories")
    st.write(f"Body Mass Index (BMI): {bmi:.2f} - {bmi_category}")
    st.write(f"Daily Caloric Needs: {calories:.2f} calories")

    # Build Nutritional Values and Extract Grams
    nutritional_values = build_nutritional_values(weight, calories)
    gram_info = extract_gram(nutritional_values)

    # Display Nutritional Information using Plotly Express
    nutrients = ["Protein", "Carbohydrates", "Fat"]
    values = [gram_info["Protein Grams"], gram_info["Carbohydrates Grams"], gram_info["Fat Grams"]]

    # Bar Chart for Nutritional Information
    fig1 = px.bar(x=nutrients, y=values, color=nutrients, labels={'x': 'Nutrients', 'y': 'Grams'},
                  title='Nutritional Information (Grams)')
    st.plotly_chart(fig1)

    # Doughnut Chart for Calorie Distribution
    labels = ["Protein", "Carbohydrates", "Fat"]
    sizes = [nutritional_values["Protein Calories"], nutritional_values["Carbohydrates Calories"],
             nutritional_values["Fat Calories"]]

    fig2 = px.pie(values=sizes, names=labels, color=labels, hole=0.3, title='Calorie Distribution')
    st.plotly_chart(fig2)