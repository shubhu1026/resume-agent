import streamlit as st
import requests
import os
from resume_updater import update_resume
from docx import Document

st.set_page_config(page_title="AI Resume Tailor", layout="centered")

st.title("🤖 AI Resume Tailor")
st.write("Generate Summary, Skills, and Relevant Projects tailored to a job description.")

# Load custom prompt template
def load_prompt_template():
    with open("prompts/tailor_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def load_docx_text(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


def split_tailored_output(output_text):
    lines = [line.strip() for line in output_text.strip().splitlines() if line.strip()]
    
    summary_lines = []
    skill_lines = []
    project_lines = []

    mode = None

    for line in lines:
        # Detect section headers
        if "Professional Summary" in line:
            mode = "summary"
            continue
        elif "Tailored Skills" in line:
            mode = "skills"
            continue
        elif "Top Projects" in line:
            mode = "projects"
            continue

        # Append content to the correct section
        if mode == "summary":
            summary_lines.append(line)
        elif mode == "skills":
            skill_lines.append(line)
        elif mode == "projects":
            project_lines.append(line)

    return "\n".join(summary_lines), "\n".join(skill_lines), "\n".join(project_lines)


prompt_template = load_prompt_template()

default_resume_path = "docs/default_super_resume.docx"

# Inputs
# super_resume = st.text_area("📄 Paste your Super Resume:", height=250)
user_input_resume = st.text_area("📄 Paste your Super Resume (leave empty to use default):", height=250)

if user_input_resume.strip():
    super_resume = user_input_resume
else:
    super_resume = load_docx_text(default_resume_path)
    st.info("📎 Using default Super Resume (loaded from DOCX file)")

job_posting = st.text_area("💼 Paste the Job Description:", height=250)

if st.button("🎯 Generate Summary, Skills & Projects"):
    with st.spinner("Generating..."):

        full_prompt = f"""{prompt_template}

Job Description:
{job_posting}

Super Resume:
{super_resume}
"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": full_prompt}],
                "temperature": 0.7
            }
        )

        result = response.json()
        tailored_output = result['choices'][0]['message']['content']
        st.success("✅ Tailored Components Generated")
        st.text_area("📄 Output (Summary, Skills, Projects):", tailored_output, height=500)

        # Split the output into summary, skills, and projects
        summary_text, skills_text, projects_text = split_tailored_output(tailored_output)

        st.subheader("✍️ Extracted Sections")
        st.text_area("📝 Summary", summary_text, height=120)
        st.text_area("🧰 Skills", skills_text, height=150)
        st.text_area("🚀 Projects", projects_text, height=250)

        # Define resume paths
        original_resume_path = "resume.docx"
        updated_resume_path = "updated_resume.docx"

        # Update the resume
        try:
            msg1, msg2, msg3, output_file = update_resume(
                summary_text, skills_text, projects_text,
                resume_path=original_resume_path,
                output_path=updated_resume_path
            )

            st.success("📄 Resume updated successfully!")

            with open(output_file, "rb") as f:
                st.download_button(
                    "⬇️ Download Updated Resume",
                    f,
                    file_name="updated_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        except Exception as e:
            st.error(f"❌ Resume update failed: {e}")
