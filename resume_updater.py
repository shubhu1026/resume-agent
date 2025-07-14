from docx import Document

def is_section_header(para):
    return para.style.name == "Normal" and para.text.isupper() and para.text.strip() != ""

def replace_section_flexible(doc, section_title, new_content):
    paragraphs = doc.paragraphs
    inside_section = False
    section_paragraphs = []

    # Find section paragraphs to replace
    for para in paragraphs:
        if para.text.strip().upper() == section_title.upper():
            inside_section = True
            continue
        if inside_section:
            if is_section_header(para):
                break
            section_paragraphs.append(para)

    if not section_paragraphs:
        return f"❌ Section '{section_title}' not found."

    # new_content can be list of lines or string
    if isinstance(new_content, str):
        new_lines = [line.strip() for line in new_content.strip().split('\n') if line.strip()]
    else:
        new_lines = new_content  # assume already list of cleaned lines

    # Replace existing paragraphs text or delete if fewer new lines
    for i in range(min(len(section_paragraphs), len(new_lines))):
        section_paragraphs[i].text = new_lines[i]

    if len(new_lines) < len(section_paragraphs):
        # Remove extra old paragraphs from XML tree
        for para in section_paragraphs[len(new_lines):]:
            p = para._element
            p.getparent().remove(p)

    elif len(new_lines) > len(section_paragraphs):
        last_para = section_paragraphs[-1]
        for line in new_lines[len(section_paragraphs):]:
            p = last_para._parent.add_paragraph(line)
            p.style = last_para.style

    return f"✅ Section '{section_title}' updated successfully."

def clean_bullets(lines):
    # Remove leading bullets and whitespace, keep content only
    return [line.lstrip("• ").strip() for line in lines.splitlines() if line.strip()]

def update_resume(summary, skills_text, projects_text, resume_path='your_resume.docx', output_path='updated_resume.docx'):
    doc = Document(resume_path)

    # summary should be a string (multi-line ok)
    # skills and projects need to be lists of lines without bullets
    skills = clean_bullets(skills_text)
    projects = clean_bullets(projects_text)

    msg1 = replace_section_flexible(doc, "SUMMARY", summary)
    msg2 = replace_section_flexible(doc, "SKILLS", skills)
    msg3 = replace_section_flexible(doc, "PROJECTS", projects)

    doc.save(output_path)
    return msg1, msg2, msg3, output_path
