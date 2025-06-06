import streamlit as st
from PyPDF2 import PdfReader
from docx import Document  # ✅ ADDED
from resume_parser import extract_resume_data
from job_matching import job_match_tool
from candidate_categorization import categorization_tool
from decision_making import decision_tool
import time
import pandas as pd
import pyodbc
from datetime import datetime
import os
import psycopg2
from psycopg2 import sql

# ✅ PostgreSQL Supabase connection
def get_sql_connection():
    return psycopg2.connect(
        host="db.hqxyqkwnweppfppxnkhg.supabase.co",
        port="5432",
        database="postgres",
        user="postgres",
        password="qg0yKi0jEn9YbniB",
        sslmode="require"
    )

# ✅ Save result to Supabase
def save_result_to_sql(row):
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ResumeResults (
                Id SERIAL PRIMARY KEY,
                ResumeName VARCHAR(255),
                JobMatchScore INT,
                Category VARCHAR(255),
                Decision VARCHAR(255),
                Timestamp TIMESTAMP
            );
        ''')
        cursor.execute('''
            INSERT INTO ResumeResults (ResumeName, JobMatchScore, Category, Decision, Timestamp)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            row["Resume Name"],
            row["Job Match Score"],
            row["Category"],
            row["Decision"],
            datetime.now()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"⚠️ Failed to save to Supabase: {e}")

# ✅ Extract text from PDF
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"
    return text.strip()

# ✅ Extract text from DOCX
def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    return "\n".join(para.text for para in doc.paragraphs).strip()

# ✅ Main orchestrator
def orchestrator(resume_text, job_description, resume_name, progress_bar):
    try:
        progress_bar.progress(10)
        st.write(f"📄 Processing **{resume_name}**...")

        st.write("🔍 **Step 1:** Extracting structured resume data...")
        resume_data = extract_resume_data(resume_text) if resume_text else None

        if resume_data:
            st.success("✅ Resume Data Extracted!")
        else:
            st.error(f"❌ **{resume_name}:** Failed to extract structured data.")
            st.info("🔍 Debug: Here's the raw text extracted from the file:")
            st.code(resume_text[:1000] + ("..." if len(resume_text) > 1000 else ""), language="text")
            return {"error": "Resume parsing failed."}

        progress_bar.progress(30)
        time.sleep(1)

        st.write("🎯 **Step 2:** Running Job Matching Tool...")
        input_data = {"resume_data": resume_data, "job_description": job_description}
        job_match_result = job_match_tool.run(input_data)
        similarity_score = job_match_result.get("similarity_score", 0)

        st.success(f"✅ Job Match Score: {similarity_score}")
        progress_bar.progress(50)
        time.sleep(1)

        st.write("📌 **Step 3:** Categorizing Candidate...")
        categorization_result = categorization_tool.run(str(similarity_score))
        st.success(f"✅ Category: {categorization_result}")
        progress_bar.progress(70)
        time.sleep(1)

        st.write("📢 **Step 4:** Making Final Decision...")
        decision_result = decision_tool.run(f"Decide action for category {categorization_result}")
        st.success(f"✅ Final Decision: {decision_result}")
        progress_bar.progress(100)
        time.sleep(1)

        return {
            "Resume Name": resume_name,
            "Job Match Score": similarity_score,
            "Category": categorization_result,
            "Decision": decision_result
        }

    except Exception as e:
        st.error(f"🚨 An error occurred while processing {resume_name}: {e}")
        return {"Resume Name": resume_name, "error": str(e)}

# ✅ Streamlit UI
st.set_page_config(page_title="Resume Screening", layout="wide")
st.title("📂 **AI-Powered Resume Screening System**")

uploaded_files = st.file_uploader(
    "📤 Upload Resumes (PDF or Word files)", 
    type=["pdf", "docx"],  # ✅ MODIFIED
    accept_multiple_files=True
)
job_description = st.text_area("📝 **Enter Job Description**", height=200)

if uploaded_files and st.button("🚀 Process Resumes"):
    if not job_description:
        st.error("⚠️ Please enter a job description.")
    else:
        st.write("🔄 **Processing Resumes...** Please wait.")
        results = []

        for index, file in enumerate(uploaded_files):
            filename = file.name.lower()
            if filename.endswith(".pdf"):
                resume_text = extract_text_from_pdf(file)
            elif filename.endswith(".docx"):
                resume_text = extract_text_from_docx(file)  # ✅ NEW
            else:
                st.warning(f"⚠️ Unsupported file type for {file.name}")
                continue

            progress_bar = st.progress(0)
            result = orchestrator(resume_text, job_description, file.name, progress_bar)

            if result and "error" not in result:
                save_result_to_sql(result)
                results.append(result)

        st.subheader("📊 Final Summary")

        if results:
            df = pd.DataFrame(results)
            st.table(df)

            os.makedirs("outputs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/screening_results_{timestamp}.csv"
            df.to_csv(output_file, index=False)

            with open(output_file, "rb") as f:
                st.download_button(
                    label="📥 Download Screening Results as CSV",
                    data=f,
                    file_name=os.path.basename(output_file),
                    mime="text/csv"
                )
