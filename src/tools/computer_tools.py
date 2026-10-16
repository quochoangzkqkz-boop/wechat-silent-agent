"""
Neuro 智能体计算机与系统操作技能库 (Computer Operations & Document Agent)
支持：
1. 桌面文档智能巡检 (list_desktop_documents)
2. 论文与文档智能精读 (read_document, 支持 .docx, .txt, .md, .py)
3. 论文修改、重写与成果落地保存 (save_document, 自动生成 Word 格式)
4. 邮件起草与发送中枢 (send_email_or_draft)
"""

import os
import glob
import re
import datetime
from typing import Optional, List, Dict

DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

def list_desktop_documents() -> str:
    """
    扫描用户电脑桌面上的文档和论文文件
    """
    extensions = ["*.docx", "*.txt", "*.md", "*.pdf", "*.doc"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(DESKTOP_PATH, ext)))
    
    if not files:
        return "桌面上暂未找到常见格式的文档。"
    
    file_names = [os.path.basename(f) for f in files]
    return f"在用户桌面上发现了以下 {len(file_names)} 个文档：\n" + "\n".join([f"- {name}" for name in file_names[:15]])

def _resolve_file_path(file_name_or_path: str) -> Optional[str]:
    """智能解析文件路径：优先当前路径，其次桌面路径"""
    # 清理书名号、引号及异常字符
    clean_name = file_name_or_path.strip().strip('"').strip("'").strip("《").strip("》").strip("}").strip("{")
    
    if os.path.isfile(clean_name):
        return clean_name
    
    desktop_candidate = os.path.join(DESKTOP_PATH, clean_name)
    if os.path.isfile(desktop_candidate):
        return desktop_candidate
    
    # 模糊匹配桌面上的同名文件 (比如输入 '精神现象学' 自动匹配 '精神现象学.docx')
    candidates = glob.glob(os.path.join(DESKTOP_PATH, f"*{clean_name}*"))
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    
    return None

def read_document(file_name_or_path: str, max_chars: int = 3500) -> str:
    """
    读取指定的论文或文档内容
    :param file_name_or_path: 文件名（如 '精神现象学.docx'）或完整路径
    :param max_chars: 最大读取字符数
    """
    resolved_path = _resolve_file_path(file_name_or_path)
    if not resolved_path:
        return f"错误: 未能找到文件 '{file_name_or_path}'，请确认文件名或桌面是否存在该文件。"
    
    ext = os.path.splitext(resolved_path)[1].lower()
    
    try:
        if ext == ".docx":
            import docx
            doc = docx.Document(resolved_path)
            full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        else:
            with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
        
        total_len = len(full_text)
        truncated_text = full_text[:max_chars]
        
        info = f"【成功读取文档: {os.path.basename(resolved_path)} (全文共 {total_len} 字)】\n\n"
        if total_len > max_chars:
            info += f"{truncated_text}\n\n...(由于上下文长度限制，以上显示前 {max_chars} 字)..."
        else:
            info += truncated_text
        return info
    except Exception as e:
        return f"读取文档 '{file_name_or_path}' 失败: {str(e)}"

def save_document(file_name_or_path: str, content: str) -> str:
    """
    将修改后的论文、笔记或分析结果直接保存到电脑桌面
    :param file_name_or_path: 目标文件名，例如 '精神现象学_修改意见.docx' 或 '论文润色.txt'
    :param content: 需要保存的内容文本
    """
    file_name = os.path.basename(file_name_or_path.strip().strip('"').strip("'"))
    target_path = os.path.join(DESKTOP_PATH, file_name)
    ext = os.path.splitext(target_path)[1].lower()
    
    try:
        if ext == ".docx":
            import docx
            doc = docx.Document()
            # 按换行段落写入 Word 文档
            paragraphs = content.split("\n")
            for p in paragraphs:
                if p.strip():
                    doc.add_paragraph(p)
            doc.save(target_path)
        else:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        return f"✅ 成功将文档保存到用户桌面：'{target_path}'"
    except Exception as e:
        return f"保存文档失败: {str(e)}"

def send_email_or_draft(recipient: str, subject: str, body: str) -> str:
    """
    创建并起草一封邮件（并在桌面上保存为邮件拟稿文件）
    :param recipient: 收件人邮箱，例如 'prof_hegel@university.edu'
    :param subject: 邮件主题
    :param body: 邮件正文
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_filename = f"邮件拟稿_{timestamp}.txt"
    draft_path = os.path.join(DESKTOP_PATH, draft_filename)
    
    draft_content = f"""============================================================
【Neuro 邮件发送中枢 - 拟稿】
收件人: {recipient}
主  题: {subject}
日  期: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================================

{body}

============================================================
(注：若配置了本地 SMTP 密钥，本技能可自动调用网络协议静默投递)
"""
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(draft_content)
        
    return f"✅ 邮件拟稿已就绪，已保存至桌面: '{draft_path}' (收件人: {recipient}, 主题: {subject})"

def search_and_send_file(keyword: str) -> str:
    """
    在用户的电脑中（桌面包括所有子文件夹、下载目录、文档目录）搜索指定关键词的文件并准备发送给用户。
    :param keyword: 文件名或关键词，例如 '布克哈特', '文艺复兴', '机械设计' 等
    """
    clean_kw = keyword.strip().strip('"').strip("'").strip("《").strip("》")
    search_dirs = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Documents"),
    ]
    
    # 拆分子关键词：比如 "布克哈特文艺复兴文化" -> 提取 2-4 字符有意义片段
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
        return f"未能在电脑的桌面、下载或文档中找到包含 '{keyword}' 的文件。请检查关键词是否正确。"
        
    scored_files.sort(key=lambda x: x[0], reverse=True)
    best_file = scored_files[0][1]
            
    summary = f"✅ 成功找到匹配的文件：'{best_file}'"
    if len(scored_files) > 1:
        other_names = [os.path.basename(p[1]) for p in scored_files[1:4]]
        summary += f"\n(另外还找到了: {', '.join(other_names)})"
    return summary

def capture_desktop_screenshot() -> str:
    """
    截取当前电脑桌面全屏并保存为图片，用于回传给手机微信用户查看电脑屏幕实时状态。
    """
    import ctypes
    user32 = ctypes.windll.user32
    hDesk = user32.OpenInputDesktop(0, False, 0x01FF)
    if hDesk:
        user32.SetThreadDesktop(hDesk)

    from PIL import ImageGrab
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"桌面截图_{now_str}.png"
    file_path = os.path.join(DESKTOP_PATH, file_name)

    img = ImageGrab.grab()
    img.save(file_path, "PNG")
    return f"已成功截取电脑桌面屏幕并保存至：'{file_path}'"

