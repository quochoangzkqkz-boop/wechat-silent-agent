"""
Computer Operations & Document Agent Tools
Supports:
1. Recursive file & document discovery across Desktop, Downloads, and Documents
2. Deep document reading (.docx, .txt, .md, .py)
3. Word document revision & generation
4. Draft email creation
"""

import os
import glob
import re
import datetime
from typing import Optional, List, Dict

DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
DOCUMENTS_PATH = os.path.join(os.path.expanduser("~"), "Documents")

def list_desktop_documents() -> str:
    """Scan documents and papers located on the user's desktop."""
    extensions = ["*.docx", "*.txt", "*.md", "*.pdf", "*.doc"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(DESKTOP_PATH, ext)))
    
    if not files:
        return "No common documents found directly on Desktop."
    
    file_names = [os.path.basename(f) for f in files]
    return f"Found {len(file_names)} documents on Desktop:\n" + "\n".join([f"- {name}" for name in file_names[:15]])

def _resolve_file_path(file_name_or_path: str) -> Optional[str]:
    """Resolve file path across current directory, Desktop, and subfolders."""
    clean_name = file_name_or_path.strip().strip('"').strip("'").strip("《").strip("》").strip("}").strip("{")
    
    if os.path.isfile(clean_name):
        return clean_name
    
    desktop_candidate = os.path.join(DESKTOP_PATH, clean_name)
    if os.path.isfile(desktop_candidate):
        return desktop_candidate
    
    candidates = glob.glob(os.path.join(DESKTOP_PATH, f"*{clean_name}*"))
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
            
    # Check Downloads
    dl_candidate = os.path.join(DOWNLOADS_PATH, clean_name)
    if os.path.isfile(dl_candidate):
        return dl_candidate
        
    return None

def read_document(file_name_or_path: str, max_chars: int = 3500) -> str:
    """
    Read document content (.docx, .txt, .md).
    :param file_name_or_path: filename or absolute path
    :param max_chars: maximum characters to read
    """
    resolved_path = _resolve_file_path(file_name_or_path)
    if not resolved_path:
        return f"Error: Cannot locate file '{file_name_or_path}'."
        
    ext = os.path.splitext(resolved_path)[1].lower()
    
    try:
        if ext == ".docx":
            import docx
            doc = docx.Document(resolved_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            content = "\n".join(full_text)
        else:
            with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
        truncated = content[:max_chars]
        is_cut = " (Content truncated...)" if len(content) > max_chars else ""
        return f"--- [{os.path.basename(resolved_path)}] ---\n{truncated}{is_cut}"
    except Exception as e:
        return f"Error reading document: {str(e)}"

def save_document(file_name_or_path: str, content: str) -> str:
    """
    Save written or revised content directly to Desktop as Word (.docx) or Text.
    """
    file_name = os.path.basename(file_name_or_path.strip().strip('"').strip("'"))
    target_path = os.path.join(DESKTOP_PATH, file_name)
    ext = os.path.splitext(target_path)[1].lower()
    
    try:
        if ext == ".docx":
            import docx
            doc = docx.Document()
            paragraphs = content.split("\n")
            for p in paragraphs:
                if p.strip():
                    doc.add_paragraph(p)
            doc.save(target_path)
        else:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
        return f"Document successfully saved to Desktop: '{target_path}'"
    except Exception as e:
        return f"Failed to save document: {str(e)}"

def send_email_or_draft(recipient: str, subject: str, body: str) -> str:
    """Create an email draft file on Desktop."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_filename = f"Email_Draft_{timestamp}.txt"
    draft_path = os.path.join(DESKTOP_PATH, draft_filename)
    
    draft_content = f"""============================================================
【AI Agent Email Dispatch - Draft】
To: {recipient}
Subject: {subject}
Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================

{body}

============================================================
"""
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(draft_content)
        
    return f"Email draft saved to Desktop: '{draft_path}'"

def search_and_send_file(keyword: str) -> str:
    """
    Recursively search across Desktop (including subfolders), Downloads, and Documents
    for matching files and prepare them for transmission.
    """
    clean_kw = keyword.strip().strip('"').strip("'").strip("《").strip("》")
    search_dirs = [DESKTOP_PATH, DOWNLOADS_PATH, DOCUMENTS_PATH]
    
    sub_kws = [clean_kw]
    parts = [p for p in re.split(r"[\s_、，,·\-\+]+", clean_kw) if len(p) >= 2]
    sub_kws.extend(parts)
    for sz in [4, 3, 2]:
        for i in range(len(clean_kw) - sz + 1):
            sub_kws.append(clean_kw[i:i+sz])
    sub_kws = list(dict.fromkeys(sub_kws))

    scored_files = []
    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        for root, dirs, files in os.walk(s_dir):
            for f in files:
                if f.startswith("~$"):
                    continue
                f_lower = f.lower()
                score = 0
                if clean_kw.lower() in f_lower:
                    score += 100
                for sk in sub_kws:
                    if len(sk) >= 2 and sk.lower() in f_lower:
                        score += len(sk) * 2
                if score > 8:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ['.pdf', '.docx', '.dxf']:
                        score += 15
                    elif ext in ['.caj', '.doc', '.zip']:
                        score += 10
                    scored_files.append((score, os.path.join(root, f)))
                    
    if not scored_files:
        return f"No matching files found for keyword '{keyword}' in Desktop, Downloads, or Documents."
        
    scored_files.sort(key=lambda x: x[0], reverse=True)
    best_file = scored_files[0][1]
            
    summary = f"Found matching file: '{best_file}'"
    if len(scored_files) > 1:
        other_names = [os.path.basename(p[1]) for p in scored_files[1:4]]
        summary += f"\n(Related files found: {', '.join(other_names)})"
    return summary
