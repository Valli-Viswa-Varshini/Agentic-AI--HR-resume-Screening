import os
import json
import openai
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()  

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")  # or hardcoded "sk-..." for local testing
)


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

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},  # Fix applied
        messages=[
            {"role": "system", "content": "You are an expert resume parser. Extract key details and return structured JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    try:
        raw_text = response["choices"][0]["message"]["content"].strip()
        return json.loads(raw_text)  
    except json.JSONDecodeError:
        return None
