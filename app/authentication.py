# authentication.py

import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth

# Check if Firebase Admin SDK is not already initialized
if not firebase_admin._apps:
    # Initialize Firebase Admin SDK with service account credentials
    cred = credentials.Certificate("care-compass/assets/care-compass-1224f-dbd593f5314a.json")  # Update with your JSON key file path
    firebase_admin.initialize_app(cred)

# Function to check if the user is authenticated
def user_authenticated(email, password):
    try:
        # Sign in the user with email and password
        user = auth.get_user_by_email(email)
        return True
    except Exception as e:
        return False

# Function to sign up new users
def signup():
    st.title("Sign Up")
    name = st.text_input("Name", key="name_input")
    email = st.text_input("Email", key="email_input")
    password = st.text_input("Password", type="password", key="password_input")
    verify_password = st.text_input("Verify Password", type="password", key="verify_password_input")

    if st.button("Create Account"):
        if not (name and email and password and verify_password):
            st.error("All fields are required!")
        elif password == verify_password:
            try:
                # Create the user in Firebase Authentication
                user = auth.create_user(email=email, password=password)
                st.success("Account created successfully! Please log in.")
                st.session_state.show_login = True
            except Exception as e:
                st.error(f"Error creating account: {e}")
        else:
            st.error("Passwords do not match. Please try again.")

# Function to log in existing users
def login():
    st.title("Login")
    email = st.text_input("Email", key="login_email_input")
    password = st.text_input("Password", type="password", key="login_password_input")

    if st.button("Login"):
        if user_authenticated(email, password):
            st.success("Logged in successfully!")
            return True
        else:
            st.error("Incorrect Email/Password")
            return False

def main():
    if "show_login" not in st.session_state:
        st.session_state.show_login = True

    st.title("HealthGuard Access Portal: Your Key to Wellness")

    if st.session_state.show_login:
        if login():
            st.session_state.show_login = False
    else:
        signup()
        st.write("")  # Add an empty line to separate signup from login
        if st.button("Sign in now"):  # Change button text here
            st.session_state.show_login = True  # This will switch to the login page

    if st.session_state.show_login:
        if st.button("Don't have an account? Create now"):
            st.session_state.show_login = False
