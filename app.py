from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure email details using environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Default to 587 if not set
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017")
db = client["login"]
users_collection = db["users"]

# Configure email details
  # Replace with your email
  # Replace with your email password

# Function to send an email and update password in DB
def send_reset_email(user_email, username):
    new_password = "newpass123"
    
    # Create the email content
    subject = "Password Reset Request"
    body = f"Hello,\n\nYour password has been reset.\nYour new password is: {new_password}\n\nPlease change it once you log in."

    # Create the message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = user_email
    msg['Subject'] = subject

    # Attach the body with the email
    msg.attach(MIMEText(body, 'plain'))

    # Set up the server
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
        server.quit()
        
        # Update password in MongoDB
        users_collection.update_one({"username": username}, {"$set": {"password": new_password, "force_reset": True}})
        
        print(f"Password reset email sent to {user_email} and password updated in database.")
    except Exception as e:
        print(f"Error: {e}")

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    user = users_collection.find_one({"username": username})

    if user:
        if user["password"] == password:
            if user.get("force_reset"):
                return redirect(url_for("reset_password", username=username))
            return "Login successful!"
        else:
            return "Invalid username or password"
    else:
        return "User not found"

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    username = request.args.get("username")
    if request.method == "POST":
        new_password = request.form["new_password"]
        users_collection.update_one({"username": username}, {"$set": {"password": new_password, "force_reset": False}})
        return redirect(url_for("home"))
    return render_template("reset_password.html", username=username)

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    email = request.form["email"]  # Get the email from the form

    # Check if the user already exists
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return "User already exists!"

    # Insert the new user into the database with username, password, and email
    users_collection.insert_one({
        "username": username,
        "password": password,
        "email": email  # Store the email in MongoDB
    })

    return redirect(url_for("home"))

@app.route("/forget", methods=["GET", "POST"])
def forgetpass():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]

        # Check if both username and email match a user in the database
        user = users_collection.find_one({"username": username, "email": email})

        if user:
            send_reset_email(email, username)
            message = "A new password has been sent to your email."
        else:
            message = "No user found with the provided username and email."

    return render_template("forget.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)



