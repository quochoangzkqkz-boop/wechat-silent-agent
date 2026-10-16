"""
Neuro 浏览器交互与网络检索技能库 (Browser Agent Tools)
集成 Microsoft Edge 与 Playwright 自动化引擎，支持：
1. 联网搜索与实时信息检索 (browser_search_web)
2. 网页深度精读与正文抓取 (browser_open_url_and_read)
3. 远程网页高清截图并自动回传图片 (browser_capture_webpage)
4. 在用户电脑物理桌面上打开网页 (browser_open_headed_page)
"""

import os
import re
import urllib.parse
import datetime
import requests
from typing import Optional, List, Dict

DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

def browser_open_headed_page(url: str) -> str:
    """
    在用户的电脑物理桌面上打开默认浏览器（Microsoft Edge）并跳转到指定网址，供用户直接在电脑屏幕上查看。
    :param url: 目标网址，例如 'https://github.com'
    """
    import webbrowser
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"✅ 已成功在电脑桌面上使用浏览器打开网址：{url}"
    except Exception as e:
        return f"打开浏览器失败: {str(e)}"

def browser_capture_webpage(url: str, file_name: str = "网页截图") -> str:
    """
    使用自动化无头浏览器访问目标网址，捕获网页完整高清截图并保存为图片，自动回传给用户微信手机端。
    :param url: 目标网址
    :param file_name: 保存的截图文件名前缀
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_prefix = re.sub(r'[\\/*?:"<>|]', "", file_name)
    save_path = os.path.join(DESKTOP_PATH, f"{clean_prefix}_{now_str}.png")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            page.screenshot(path=save_path, full_page=False)
            browser.close()

        if os.path.isfile(save_path):
            return f"✅ 成功截取网页画面并已保存至：'{save_path}'"
        return "网页截图生成失败。"
    except Exception as e:
        return f"网页截图出现异常: {str(e)}"

def browser_open_url_and_read(url: str, max_chars: int = 3000) -> str:
    """
    深入访问指定网页，提取页面核心标题与可读正文文本（自动去除脚本、广告与杂质）。
    :param url: 目标网址
    :param max_chars: 最大返回正文字符数
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            title = page.title()
            body_text = page.inner_text("body")
            browser.close()

        lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + f"\n\n...(内容过长，已截取前 {max_chars} 字)"

        return f"【网页标题】: {title}\n【URL】: {url}\n\n【正文精读内容】:\n{clean_text}"
    except Exception as e:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = r.apparent_encoding
            text = re.sub(r"<script.*?</script>", "", r.text, flags=re.DOTALL)
            text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            clean_text = "\n".join(lines)[:max_chars]
            return f"【URL】: {url}\n\n【网页内容】:\n{clean_text}"
        except Exception as err2:
            return f"访问网页失败: {str(e)} / {str(err2)}"

def browser_search_web(query: str, limit: int = 5) -> str:
    """
    使用搜索引擎联网检索实时信息、新闻、学术资料、技术文档等。
    :param query: 搜索关键词
    :param limit: 返回条目数
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    encoded_q = urllib.parse.quote(query)
    
    # 优先使用 360 搜索引擎获取中文结果
    try:
        url = f"https://www.so.com/s?q={encoded_q}"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            blocks = re.findall(r'<li class="res-list".*?>(.*?)</li>', r.text, flags=re.DOTALL)
            results = []
            for b in blocks[:limit]:
                tm = re.search(r'<h3\s+class="res-title"><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, flags=re.DOTALL)
                dm = re.search(r'data-mdurl="([^"]+)"', b)
                sm = re.search(r'<p class="res-desc">(.*?)</p>', b, flags=re.DOTALL)
                if tm:
                    title = re.sub(r'<[^>]+>', '', tm.group(2)).strip()
                    link = dm.group(1) if dm else tm.group(1)
                    desc = re.sub(r'<[^>]+>', '', sm.group(1)).strip() if sm else "无摘要"
                    results.append(f"- 【{title}】\n  摘要: {desc}\n  链接: {link}")
            if results:
                return f"🌐 联网搜索 '{query}' 实时结果：\n\n" + "\n\n".join(results)
    except Exception:
        pass

    # 备选：使用 DuckDuckGo 或必应
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.goto(f"https://www.bing.com/search?q={encoded_q}", timeout=15000, wait_until="domcontentloaded")
            items = []
            for el in page.locator("li.b_algo").all()[:limit]:
                h2 = el.locator("h2 a").first
                snippet = el.locator(".b_caption p").first
                if h2.count() > 0:
                    title = h2.inner_text().strip()
                    href = h2.get_attribute("href") or ""
                    snip_text = snippet.inner_text().strip() if snippet.count() > 0 else "无摘要"
                    if title:
                        items.append(f"- 【{title}】\n  摘要: {snip_text}\n  链接: {href}")
            browser.close()
            if items:
                return f"🌐 联网搜索 '{query}' 实时结果：\n\n" + "\n\n".join(items)
    except Exception as e:
        return f"联网搜索出现异常: {str(e)}"

    return f"未检索到关于 '{query}' 的搜索结果。"
