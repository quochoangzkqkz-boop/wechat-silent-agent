"""
Neuro Agent 核心控制器 (Cognitive Controller v2.2)
支持：
1. 长期记忆引擎 (Episodic & Semantic Long-Term Memory)
2. 计算机与系统操作 (文档巡检、论文精读、Word 保存、桌面全屏截屏回传)
3. 工业级工程制图与 SolidWorks 宏生成 (CAD 2D 绘图与 3D 参数化建模)
4. GitHub 深度接入 (个人仓库巡检、全网开源项目搜索、README 精读、创建 Issue、Git 提交推送)
5. 浏览器与联网操控 (Edge Playwright 网页抓取、长截图回传、实时搜索引擎检索、物理打开网页)
"""

import os
import json
import sys
import datetime
import httpx2 as httpx
from openai import OpenAI

# 导入本地长期记忆引擎 (持久化 SQLite + 记忆加权衰减)
from memory import memory_engine

# 导入计算机与文档操作技能库
from computer_tools import (
    list_desktop_documents,
    read_document,
    save_document,
    send_email_or_draft,
    search_and_send_file,
    capture_desktop_screenshot
)

# 导入 CAD 工程制图与 SolidWorks 宏生成技能库
from cad_tools import (
    draw_cad_part,
    generate_solidworks_macro
)

# 导入 GitHub 交互技能库
from github_tools import (
    github_user_profile,
    github_list_user_repos,
    github_search_repositories,
    github_get_repo_details,
    github_create_issue,
    git_repo_status_and_push
)

# 导入浏览器与联网检索技能库
from browser_tools import (
    browser_search_web,
    browser_open_url_and_read,
    browser_capture_webpage,
    browser_open_headed_page
)

# 确保本地 Ollama 请求不被任何系统代理或 VPN 拦截
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 1. 连接本地 Ollama 引擎 (兼容 OpenAI 标准接口)
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",
    http_client=httpx.Client(trust_env=False)
)

# 2. 基础技能
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """获取当前真实时间与日期"""
    now = datetime.datetime.now()
    return f"当前系统时间为: {now.strftime('%Y-%m-%d %H:%M:%S')} (时区: {timezone})"

def remember_fact(fact: str, category: str = "user_fact", importance: int = 7) -> str:
    """将关于用户、偏好、事件或重要结论存入长期记忆库"""
    result = memory_engine.save(fact, category, importance)
    return result

def recall_memories(query: str) -> str:
    """主动向长期海马体检索与某个话题相关的记忆"""
    memories = memory_engine.search(query, limit=5)
    if not memories:
        return f"海马体中暂未检索到关于 '{query}' 的特定记忆。"
    res = [f"检索到 {len(memories)} 条关联记忆:"]
    for m in memories:
        res.append(f"- [{m['category']}] {m['content']} (重要度: {m['importance']})")
    return "\n".join(res)

# 技能映射表
AVAILABLE_TOOLS = {
    # 基础与记忆技能
    "get_current_time": get_current_time,
    "remember_fact": remember_fact,
    "recall_memories": recall_memories,

    # 计算机与桌面操作技能
    "capture_desktop_screenshot": capture_desktop_screenshot,
    "list_desktop_documents": list_desktop_documents,
    "read_document": read_document,
    "save_document": save_document,
    "send_email_or_draft": send_email_or_draft,
    "search_and_send_file": search_and_send_file,

    # 浏览器与网络检索技能
    "browser_search_web": browser_search_web,
    "browser_open_url_and_read": browser_open_url_and_read,
    "browser_capture_webpage": browser_capture_webpage,
    "browser_open_headed_page": browser_open_headed_page,

    # GitHub 技能
    "github_user_profile": github_user_profile,
    "github_list_user_repos": github_list_user_repos,
    "github_search_repositories": github_search_repositories,
    "github_get_repo_details": github_get_repo_details,
    "github_create_issue": github_create_issue,
    "git_repo_status_and_push": git_repo_status_and_push,

    # 工业 CAD 与 SolidWorks 技能
    "draw_cad_part": draw_cad_part,
    "generate_solidworks_macro": generate_solidworks_macro,
}

# 技能规范描述 (遵循 OpenAI Tools 规范，DeepSeek-R1 / Qwen2.5 原生高精度支持)
TOOLS_SCHEMA = [
    # 桌面操作
    {
        "type": "function",
        "function": {
            "name": "capture_desktop_screenshot",
            "description": "截取当前电脑桌面全屏并保存为图片，用于回传给手机微信用户查看电脑屏幕实时画面。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_and_send_file",
            "description": "按关键词在电脑的桌面、下载、文档等目录中深度模糊搜索文件、论文、书籍、图纸并准备回传给手机微信。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索的文件关键词或文件名，例如 '布克哈特', '文艺复兴', '机械设计' 等"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    # 浏览器与网络
    {
        "type": "function",
        "function": {
            "name": "browser_search_web",
            "description": "使用搜索引擎联网检索最新的实时信息、热点新闻、学术论文、技术资料与解决方案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或查询短语"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回搜索结果条数，默认 5 条"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_open_url_and_read",
            "description": "使用浏览器深入访问目标网址或网页链接，智能解析并提取网页核心正文文本内容供分析理解。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "目标网页网址，如 'https://github.com/trending'"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "最大读取字符数，默认 3000"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_capture_webpage",
            "description": "使用无头浏览器访问指定网址，对网页进行高清截屏并保存为 PNG 图片，自动回传给用户微信手机端查看。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "目标网页网址"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "保存的截图文件名前缀，例如 'github_trending'"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_open_headed_page",
            "description": "在用户的电脑物理桌面上直接唤起默认 Edge 浏览器打开指定网址，便于用户在电脑大屏上浏览互动。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "需要在电脑屏幕上打开的目标网址"
                    }
                },
                "required": ["url"]
            }
        }
    },
    # GitHub 技能
    {
        "type": "function",
        "function": {
            "name": "github_user_profile",
            "description": "查看当前用户的 GitHub 个人资料、公开仓库总数、Followers 状态等。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_user_repos",
            "description": "获取当前用户账号下所有的 GitHub 仓库列表、Star 数量与最新更新时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回仓库数量，默认 10"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_search_repositories",
            "description": "在 GitHub 全球开源社区搜索高星项目、论文开源实现、热门 AI Agent 库等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，例如 'wechat agent', 'deepseek r1 rocm'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回项目数，默认 5"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_get_repo_details",
            "description": "查看指定 GitHub 开源仓库的详细指标与 README 文档摘要。",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "仓库完整路径，如 'quochoangzkqkz-boop/wechat-silent-agent' 或纯仓库名"
                    }
                },
                "required": ["repo_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_create_issue",
            "description": "在指定的 GitHub 仓库中创建新的 Issue 议题或需求跟踪条目。",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "目标仓库名"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue 标题"
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue 正文描述"
                    }
                },
                "required": ["repo_name", "title", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_repo_status_and_push",
            "description": "一键将本地 wechat-silent-agent 仓库暂存、提交并推送到 GitHub 远程仓库。",
            "parameters": {
                "type": "object",
                "properties": {
                    "commit_message": {
                        "type": "string",
                        "description": "Git 提交信息说明"
                    }
                },
                "required": []
            }
        }
    },
    # 文档与系统
    {
        "type": "function",
        "function": {
            "name": "list_desktop_documents",
            "description": "扫描用户桌面上的文档、论文和工程文件列表。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "读取桌面或指定路径的文档全文内容（支持 .docx, .txt, .md, .py）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name_or_path": {
                        "type": "string",
                        "description": "文件名或绝对路径"
                    }
                },
                "required": ["file_name_or_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_document",
            "description": "将文字成果保存为 Word (.docx) 或文本文件到桌面。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "文档标题"
                    },
                    "content": {
                        "type": "string",
                        "description": "文档正文"
                    }
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_or_draft",
            "description": "起草或准备学术邮件与工作信函并保存为草稿。",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    # CAD 与 SolidWorks
    {
        "type": "function",
        "function": {
            "name": "draw_cad_part",
            "description": "根据几何参数绘制 AutoCAD 工业图纸 (.dxf)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_type": {"type": "string"},
                    "parameters": {"type": "object"}
                },
                "required": ["part_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_solidworks_macro",
            "description": "生成 SolidWorks VBA 3D 参数化建模宏脚本 (.bas)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "macro_name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["macro_name", "description"]
            }
        }
    },
    # 记忆与时间
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前确切的日期、星期几或具体时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "default": "Asia/Shanghai"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "将用户的关键信息、偏好、目标永久存入长期海马体记忆库。",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "核心事实陈述"},
                    "category": {"type": "string", "default": "user_fact"},
                    "importance": {"type": "integer", "default": 7}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memories",
            "description": "主动从长期海马体中检索相关记忆事实。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]

def chat_loop(model_name: str = "neuro"):
    print("=" * 70)
    print(f"🤖 Neuro 智能体已就绪 (底座模型: {model_name} v2.2)")
    print("🐙 GitHub 接入已激活 | 🌐 浏览器与联网操控就绪")
    print("📸 桌面截屏与文件回传就绪 | 📐 CAD/SolidWorks 工业设计就绪")
    print("💡 输入 'quit' 退出。")
    print("=" * 70)

    messages = []
    system_instruction = (
        "你是 Neuro，运行在本地电脑上的全能个人智能体伴侣。\n"
        "【关键行为准则】\n"
        "1. 当用户要求发送、查找、传过来电脑上的某个文件、论文、书籍、图纸时，必须立即调用 search_and_send_file 工具找到文件并回传！\n"
        "2. 当用户要求截图、截屏、看下电脑桌面、看下屏幕、拍照时，必须立即调用 capture_desktop_screenshot 工具截取桌面！\n"
        "3. 当用户要求操作 GitHub（查看个人主页、查看/搜索仓库、读 README、建 Issue、git 提交推送）时，必须立即调用对应的 github_* 或 git_* 工具！\n"
        "4. 当用户要求搜索网络、上网查资料、看网页、截网页长图、打开网页时，必须立即调用对应的 browser_* 工具！\n"
        "5. 当用户要求绘制工程制图或 SolidWorks 建模时，必须立即调用 draw_cad_part 或 generate_solidworks_macro 工具！\n"
        "6. 保持回答干练务实，优先执行工具，切勿答非所问，严禁空谈哲学理论或反问用户！"
    )

    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit"]:
                print("👋 Neuro: 下次见！所有新记忆已安全存入本地数据库。")
                break

            memory_context = memory_engine.get_working_memory_context(user_input, max_items=4)
            current_messages = [{"role": "system", "content": system_instruction}]
            if memory_context:
                current_messages.append({
                    "role": "system",
                    "content": f"以下是你的海马体长期记忆库中检索到的相关信息：\n{memory_context}"
                })
            current_messages.extend(messages)
            current_messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model=model_name,
                messages=current_messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )

            response_msg = response.choices[0].message

            if response_msg.tool_calls:
                current_messages.append(response_msg)
                for tool_call in response_msg.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    print(f"  ⚡ [Skill 触发] 执行技能: {fn_name}({fn_args})")

                    if fn_name in AVAILABLE_TOOLS:
                        tool_result = AVAILABLE_TOOLS[fn_name](**fn_args)
                    else:
                        tool_result = f"错误: 未知技能 {fn_name}"

                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    })

                final_response = client.chat.completions.create(
                    model=model_name,
                    messages=current_messages
                )
                reply = final_response.choices[0].message.content
            else:
                reply = response_msg.content

            print(f"\n🧠 Neuro: {reply}")
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

        except KeyboardInterrupt:
            print("\n👋 退出会话。")
            break
        except Exception as e:
            print(f"\n❌ 发生异常: {e}")

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "neuro"
    chat_loop(model)
