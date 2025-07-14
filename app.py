import streamlit as st
import requests
import json
from resume_updater import update_resume
from docx import Document

st.set_page_config(page_title="AI Resume Tailor", layout="centered")

st.title("🤖 AI Resume Tailor")
st.write("Generate Summary, Skills, and Relevant Projects tailored to a job description.")

# Load custom prompt template
def load_prompt_template():
    with open("prompts/tailor_prompt_new.txt", "r", encoding="utf-8") as f:
        return f.read()

def load_docx_text(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def extract_json_from_text(text):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to extract or parse JSON: {e}")

prompt_template = load_prompt_template()

default_resume_path = "docs/default_super_resume.docx"

# Inputs
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

        # Parse JSON output from LLM
        try:
            parsed = extract_json_from_text(tailored_output)
        except Exception as e:
            st.error(f"❌ Failed to extract and parse JSON output: {e}")
            st.text_area("⚠️ Raw Output from LLM", tailored_output, height=500)
            st.stop()

        summary_list = parsed.get("summary", [])
        skills_list = parsed.get("skills", [])
        projects_list = parsed.get("projects", [])

        st.success("✅ Tailored Components Generated")
        st.json(parsed)
        st.text_area("📄 Output (Summary, Skills, Projects):", tailored_output, height=500)

        # Prepare inputs for resume_updater (convert lists to strings)
        summary_text = "\n".join(summary_list)
        skills_text = "\n".join(skills_list)

        # Flatten projects: title + bullets (each bullet with a bullet symbol)
        projects_lines = []
        for project in projects_list:
            projects_lines.append(project['title'])  # project title as plain line
            # Prefix each bullet with bullet character
            for bullet in project.get('bullets', []):
                projects_lines.append("• " + bullet.strip())

        projects_text = "\n".join(projects_lines)

        # Show extracted text areas for review
        st.subheader("✍️ Extracted Sections")
        st.text_area("📝 Summary", summary_text, height=120)
        st.text_area("🧰 Skills", skills_text, height=150)
        st.text_area("🚀 Projects", projects_text, height=250)

        # Paths for input and output resumes
        original_resume_path = "docs/resume.docx"
        updated_resume_path = "docs/updated_resume.docx"

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
