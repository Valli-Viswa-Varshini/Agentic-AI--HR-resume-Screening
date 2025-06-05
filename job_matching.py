import os
from openai import OpenAI
from langchain.tools import StructuredTool
from pydantic import BaseModel
import streamlit as st

# Set API key via env variable
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Initialize OpenAI client
client = OpenAI()

class JobMatchingInput(BaseModel):
    resume_data: dict
    job_description: str

def job_match_score_only(resume_data: dict, job_description: str) -> dict:
    """Returns only the similarity score between resume and job description (10 to 100)."""

    resume_text = "\n".join(f"{k}: {v}" for k, v in resume_data.items() if v).strip()
    job_description = job_description.strip()

    try:
        system_prompt = (
            "You are a resume screening assistant. Based on the job description and resume provided, "
            "output ONLY a numeric score between 10 and 100 indicating how well the resume matches the job. "
            "Do not add any explanation or text. Only return the score."
        )

        user_prompt = (
            f"Job Description:\n{job_description}\n\n"
            f"Resume:\n{resume_text}\n\n"
            "Give a score between 10 and 100. Only the number. No explanation."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        answer = response.choices[0].message.content.strip()
        import re
        match = re.search(r"\b(\d{2,3})\b", answer)
        score = int(match.group(1)) if match else None

        if score is None:
            raise ValueError("Score not found in LLM response.")

        return {"similarity_score": max(10, min(score, 100))}

    except Exception as e:
        print(f"Error during LLM scoring: {str(e)}")
        return {"similarity_score": 0}

job_match_tool = StructuredTool(
    name="PerfectJobMatcher",
    func=job_match_score_only,
    description="Returns only the similarity score (10–100) indicating how well a resume matches a job description.",
    args_schema=JobMatchingInput
)
