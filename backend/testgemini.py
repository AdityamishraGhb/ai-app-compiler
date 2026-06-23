from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API Key Loaded:", bool(api_key))

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Say hello")

print(response.text)
from dotenv import load_dotenv
import os

load_dotenv()

print("API Key Loaded:", bool(os.getenv("GEMINI_API_KEY")))
print("Raw Value:", os.getenv("GEMINI_API_KEY"))