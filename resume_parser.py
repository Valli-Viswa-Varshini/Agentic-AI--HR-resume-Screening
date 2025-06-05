import os
import json
from openai import OpenAI
import streamlit as st

# Set API key securely
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_resume_data(text):
    prompt = f"""
    Extract structured information from the following resume text:

    {text}

    Format the response strictly as a JSON object with the following fields:
    {{
      "name": "Full Name",
      "email": "Email Address",
      "phone": "Phone Number",
      "skills": ["Skill1", "Skill2", "Skill3"],
      "experience": ["Job1 Description", "Job2 Description"],
      "education": ["Degree1", "Degree2"]
    }}

    Ensure valid JSON response.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert resume parser. Extract key details and return structured JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    try:
        raw_text = response.choices[0].message.content.strip()
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return None
