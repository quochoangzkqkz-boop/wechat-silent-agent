"""
Neuro GitHub 智能体技能库 (GitHub Agent Tools)
集成 GitHub REST API 与本地 Git 命令，支持：
1. 个人资料与仓库巡检 (github_user_profile, github_list_user_repos)
2. 全网开源项目检索 (github_search_repositories)
3. 仓库详情与 README 精读 (github_get_repo_details)
4. Issue 管理与起草 (github_create_issue, github_list_repo_issues)
5. 本地仓库一键提交与远程推送 (git_repo_status_and_push)
"""

import os
import subprocess
import requests
from typing import Optional, List, Dict

GITHUB_API_BASE = "https://api.github.com"
GIT_EXE = r"C:\Users\Administrator\.git-bin\cmd\git.exe"

def _get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token
    token_file = os.path.expanduser("~/.github_token")
    if os.path.isfile(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

def _get_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Neuro-Silent-Agent/2.1"
    }
    tok = _get_token()
    if tok:
        headers["Authorization"] = f"token {tok}"
    return headers

def github_user_profile() -> str:
    """获取当前授权 GitHub 用户的基本信息、公开仓库数与关注状态"""
    url = f"{GITHUB_API_BASE}/user"
    try:
        r = requests.get(url, headers=_get_headers(), timeout=10)
        if r.status_code != 200:
            return f"获取 GitHub 用户信息失败: HTTP {r.status_code} - {r.text}"
        data = r.json()
        return (
            f"GitHub 用户: {data.get('login')} ({data.get('name', '未设置姓名')})\n"
            f"主页: {data.get('html_url')}\n"
            f"公开仓库数: {data.get('public_repos')}\n"
            f"Followers: {data.get('followers')} | Following: {data.get('following')}\n"
            f"个人简介: {data.get('bio', '无')}"
        )
    except Exception as e:
        return f"请求 GitHub API 异常: {str(e)}"

def github_list_user_repos(limit: int = 10) -> str:
    """列出当前用户拥有的 GitHub 代码仓库列表及 Star 数"""
    url = f"{GITHUB_API_BASE}/user/repos?sort=updated&per_page={limit}"
    try:
        r = requests.get(url, headers=_get_headers(), timeout=10)
        if r.status_code != 200:
            return f"获取仓库列表失败: HTTP {r.status_code}"
        repos = r.json()
        if not repos:
            return "当前用户下暂无公开或私有仓库。"
        lines = [f"最近更新的 {len(repos)} 个 GitHub 仓库:"]
        for repo in repos:
            name = repo.get("name")
            desc = repo.get("description") or "无描述"
            stars = repo.get("stargazers_count", 0)
            url = repo.get("html_url")
            lines.append(f"- ⭐ {stars} | {name}: {desc} ({url})")
        return "\n".join(lines)
    except Exception as e:
        return f"获取仓库异常: {str(e)}"

def github_search_repositories(query: str, limit: int = 5) -> str:
    """
    在 GitHub 全网搜索开源项目、论文代码、热门工具库
    :param query: 搜索关键词，例如 'wechat bot', 'deepseek agent', 'rocm llama'
    :param limit: 返回结果数量
    """
    url = f"{GITHUB_API_BASE}/search/repositories?q={requests.utils.quote(query)}&sort=stars&order=desc&per_page={limit}"
    try:
        r = requests.get(url, headers=_get_headers(), timeout=10)
        if r.status_code != 200:
            return f"搜索 GitHub 失败: HTTP {r.status_code}"
        items = r.json().get("items", [])
        if not items:
            return f"在 GitHub 上未找到关于 '{query}' 的相关开源项目。"
        lines = [f"在 GitHub 上检索到与 '{query}' 相关的顶尖开源项目:"]
        for it in items:
            full_name = it.get("full_name")
            stars = it.get("stargazers_count", 0)
            desc = it.get("description") or "无描述"
            link = it.get("html_url")
            lang = it.get("language") or "Mixed"
            lines.append(f"- ⭐ {stars} [{lang}] {full_name}: {desc}\n  链接: {link}")
        return "\n".join(lines)
    except Exception as e:
        return f"GitHub 搜索异常: {str(e)}"

def github_get_repo_details(repo_name: str) -> str:
    """
    获取指定仓库的详细信息与 README 摘要
    :param repo_name: 仓库全名或当前名，如 'quochoangzkqkz-boop/wechat-silent-agent'
    """
    if "/" not in repo_name:
        repo_name = f"quochoangzkqkz-boop/{repo_name}"
    
    url = f"{GITHUB_API_BASE}/repos/{repo_name}"
    try:
        r = requests.get(url, headers=_get_headers(), timeout=10)
        if r.status_code != 200:
            return f"获取仓库 '{repo_name}' 失败: HTTP {r.status_code}"
        d = r.json()
        
        # 尝试拉取 README
        readme_url = f"{GITHUB_API_BASE}/repos/{repo_name}/readme"
        r_readme = requests.get(readme_url, headers={"Accept": "application/vnd.github.v3.raw", **_get_headers()}, timeout=10)
        readme_text = r_readme.text[:1200] if r_readme.status_code == 200 else "无法读取 README"

        return (
            f"仓库: {d.get('full_name')}\n"
            f"主页: {d.get('html_url')}\n"
            f"Star: {d.get('stargazers_count')} | Fork: {d.get('forks_count')} | Open Issues: {d.get('open_issues_count')}\n"
            f"简介: {d.get('description', '无')}\n\n"
            f"【README 预览】:\n{readme_text}..."
        )
    except Exception as e:
        return f"获取仓库详情异常: {str(e)}"

def github_create_issue(repo_name: str, title: str, body: str) -> str:
    """
    在指定的 GitHub 仓库中创建新的 Issue 议题或需求跟踪
    :param repo_name: 仓库名，如 'wechat-silent-agent' 或 'quochoangzkqkz-boop/wechat-silent-agent'
    :param title: Issue 标题
    :param body: Issue 详细描述与正文
    """
    if "/" not in repo_name:
        repo_name = f"quochoangzkqkz-boop/{repo_name}"
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/issues"
    try:
        payload = {"title": title, "body": body}
        r = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        if r.status_code in [200, 201]:
            data = r.json()
            return f"✅ 成功在 '{repo_name}' 创建 Issue #{data.get('number')}：'{title}'\n链接: {data.get('html_url')}"
        return f"创建 Issue 失败: HTTP {r.status_code} - {r.text}"
    except Exception as e:
        return f"创建 Issue 异常: {str(e)}"

def git_repo_status_and_push(commit_message: str = "auto: sync updates via neuro agent") -> str:
    """一键为本地 wechat-silent-agent 仓库暂存、提交并推送到 GitHub 远程分支"""
    repo_dir = r"C:\Users\Administrator\.gemini\antigravity\scratch\wechat-silent-agent"
    if not os.path.isdir(repo_dir):
        return f"本地仓库路径不存在: {repo_dir}"
    
    git_bin = GIT_EXE if os.path.isfile(GIT_EXE) else "git"
    try:
        subprocess.run([git_bin, "add", "-A"], cwd=repo_dir, capture_output=True, text=True, check=True)
        commit_res = subprocess.run([git_bin, "commit", "-m", commit_message], cwd=repo_dir, capture_output=True, text=True)
        push_res = subprocess.run([git_bin, "push", "origin", "main"], cwd=repo_dir, capture_output=True, text=True, timeout=20)
        if push_res.returncode == 0:
            return f"✅ Git 提交与远程推送成功！\n提交说明: '{commit_message}'\n远程推送反馈:\n{push_res.stderr or push_res.stdout}"
        return f"Git 推送出现问题:\n{push_res.stderr}"
    except Exception as e:
        return f"执行本地 Git 操作异常: {str(e)}"
