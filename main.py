import streamlit as st
from PyPDF2 import PdfReader
from resume_parser import extract_resume_data
from job_matching import job_match_tool
from candidate_categorization import categorization_tool
from decision_making import decision_tool
import time
import pandas as pd

# ✅ Add SQL imports
import pyodbc
from datetime import datetime
import os

# ✅ SQL Server connection setup (edit these values)
def get_sql_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=LAPTOP-29L4TA1D\SQLEXPRESS01;'
        'DATABASE=resumeoutputdata;'
        'Trusted_Connection=yes;'
    )

# ✅ Save a single row to SQL Server
def save_result_to_sql(row):
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            IF OBJECT_ID('ResumeResults', 'U') IS NULL
            CREATE TABLE ResumeResults (
                Id INT IDENTITY(1,1) PRIMARY KEY,
                ResumeName NVARCHAR(255),
                JobMatchScore INT,
                Category NVARCHAR(255),
                Decision NVARCHAR(255),
                Timestamp DATETIME
            )
        ''')

        # Insert result
        cursor.execute('''
            INSERT INTO ResumeResults (ResumeName, JobMatchScore, Category, Decision, Timestamp)
            VALUES (?, ?, ?, ?, ?)
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
        st.error(f"⚠️ Failed to save to database: {e}")

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file using PyPDF2."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"
    return text.strip()

def orchestrator(resume_text, job_description, resume_name, progress_bar):
    """Processes each resume and updates UI in sections."""
    try:
        progress_bar.progress(10)
        st.write(f"📄 Processing **{resume_name}**...")

        st.write("🔍 **Step 1:** Extracting structured resume data...")
        resume_data = extract_resume_data(resume_text) if resume_text else None

        if not resume_data:
            st.error(f"❌ **{resume_name}:** Failed to extract structured data.")
            return {"error": "Resume parsing failed."}

        st.success("✅ Resume Data Extracted!")
        progress_bar.progress(30)
        time.sleep(1)

        st.write("🎯 **Step 2:** Running Job Matching Tool...")
        input_data = {"resume_data": resume_data, "job_description": job_description}
        job_match_result = job_match_tool.run(input_data) if resume_text else {"similarity_score": 5}
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

st.set_page_config(page_title="Resume Screening", layout="wide")
st.title("📂 **AI-Powered Resume Screening System**")

uploaded_pdfs = st.file_uploader("📤 Upload Resumes (Multiple PDFs Allowed)", type="pdf", accept_multiple_files=True)
job_description = st.text_area("📝 **Enter Job Description**", height=200)

if uploaded_pdfs and st.button("🚀 Process Resumes"):
    if not job_description:
        st.error("⚠️ Please enter a job description.")
    else:
        st.write("🔄 **Processing Resumes...** Please wait.")
        results = []

        for index, pdf in enumerate(uploaded_pdfs):
            resume_text = extract_text_from_pdf(pdf)
            progress_bar = st.progress(0)
            result = orchestrator(resume_text, job_description, pdf.name, progress_bar)

            if result and "error" not in result:
                save_result_to_sql(result)  # ✅ Save to SQL Server
                results.append(result)

        st.subheader("📊 Final Summary")

        if results:
            df = pd.DataFrame(results)  # Convert results to a DataFrame
            st.table(df)  # Display results in a table

            # ✅ Save the DataFrame to a CSV with timestamp
            os.makedirs("outputs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/screening_results_{timestamp}.csv"
            df.to_csv(output_file, index=False)

            # ✅ Add download button in Streamlit
            with open(output_file, "rb") as f:
                st.download_button(
                    label="📥 Download Screening Results as CSV",
                    data=f,
                    file_name=os.path.basename(output_file),
                    mime="text/csv"
                )
