import os
import json
from openai import OpenAI
import streamlit as st

# Set API key securely
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_resume_data(text):
    if not text or text.strip() == "":
        st.error("❌ No text extracted from resume.")
        return None

    prompt = f"""
Extract structured information from the following resume text:

{text}

Respond strictly in this JSON format:
{{
  "name": "Full Name",
  "email": "Email Address",
  "phone": "Phone Number",
  "skills": ["Skill1", "Skill2", "Skill3"],
  "experience": ["Job1 Description", "Job2 Description"],
  "education": ["Degree1", "Degree2"]
}}

Only provide the JSON. No markdown, no explanation, no extra text.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4" or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an expert resume parser. Extract key details and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        raw_text = response.choices[0].message.content.strip()

       
    except json.JSONDecodeError as e:
        st.error("❌ Failed to decode JSON from OpenAI response.")
        st.text(f"Error: {e}")
        return None
    except Exception as e:
        st.error("❌ Unexpected error during resume parsing.")
        st.text(f"Error: {e}")
        return None
