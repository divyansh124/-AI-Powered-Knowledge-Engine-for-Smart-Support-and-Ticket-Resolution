step 1
--python -m venv [name of myenv]
step 2
run the enviornment
myenv/Scripts/activate
step 3
pip install groq
pip install langchain

pip freeze > requirements.txt

pip install dotenv(if error in main.py)
pip install streamlit

# Update a single cell
sheet.update_cell(2, 3, "Hello World")  # row=2, col=3
# Installing dependencies
pip install -U langchain langchain-community langchain-google-genai langchain-text-splitters faiss-cpu pypdf python-dotenv langchain-groq 
# Set your Google API key
GOOGLE_API_KEY=""
ai.google.dev
# 

Step1:

Go to Google Cloud Console
.

Create a new project (or use existing).

Enable the Google Sheets API and Google Drive API.

Create credentials → Service Account → download the JSON key file (e.g., credentials.json).

Share your Google Sheet with the service account email (something like your-service@project.iam.gserviceaccount.com) and give Editor access.


Step 2:

pip install gspread oauth2client pandas
