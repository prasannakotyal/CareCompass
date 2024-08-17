import mysql.connector
import streamlit as st

# Function to create a MySQL connection
def create_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Hello@03",
            database="users"
        )
        if conn.is_connected():
            print("Connected to MySQL database")
    except mysql.connector.Error as e:
        print(e)
    return conn

# Function to create a profile table
def create_table(conn):
    sql_create_profiles_table = """
    CREATE TABLE IF NOT EXISTS profiles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        age INT,
        weight INT,
        height INT,
        sex ENUM('male', 'female'),
        activity_level VARCHAR(255)
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_profiles_table)
    except mysql.connector.Error as e:
        print(e)

# Function to insert a profile into the database
def insert_profile(conn, profile):
    sql_insert_profile = """
    INSERT INTO profiles (name, age, weight, height, sex, activity_level)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor = conn.cursor()
    cursor.execute(sql_insert_profile, profile)
    conn.commit()
    return cursor.lastrowid

# Function to retrieve a profile from the database
def retrieve_profile(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1;")
    row = cursor.fetchone()
    return row

# Main function to run the Streamlit app
def main():
    st.title("Profile Information")

    # Connect to MySQL database
    conn = create_connection()
    if conn is not None:
        # Create profiles table if not exists
        create_table(conn)

        # User input for profile details
        name = st.text_input("Enter your name:")
        age = st.number_input("Enter your age:", min_value=1, max_value=150)
        weight = st.number_input("Enter your weight in KGs:", min_value=1.0, max_value=500.0, step=0.1)
        height = st.number_input("Enter your height in Cms:", min_value=1.0, max_value=300.0, step=0.1)
        sex = st.radio("Select your sex:", options=["male", "female"])
        activity_level = st.selectbox(
            "Select your activity level:",
            options=["sedentary", "lightly active", "moderately active", "very active"],
        )

        # Buttons to save and load profile
        if st.button("Save Profile"):
            profile = (name, age, weight, height, sex, activity_level)
            profile_id = insert_profile(conn, profile)
            st.success("Profile saved successfully!")

        if st.button("Load Profile"):
            profile = retrieve_profile(conn)
            if profile:
                st.write("Name:", profile[1])
                st.write("Age:", profile[2])
                st.write("Weight (KGs):", profile[3])
                st.write("Height (Cms):", profile[4])
                st.write("Sex:", profile[5])
                st.write("Activity Level:", profile[6])
            else:
                st.warning("No profile found!")

        # Close the database connection
        conn.close()

if __name__ == "__main__":
    main()
