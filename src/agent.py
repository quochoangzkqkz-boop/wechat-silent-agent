"""
Neuro Agent 核心控制器 (Cognitive Controller)
支持：
1. 自我认知锚定 (Ontological Grounding)
2. 动态长期记忆引擎 (Episodic & Semantic Long-Term Memory)
3. 计算机系统操作 (文档巡检、论文精读、Word 保存、邮件起草)
4. 工业级工程制图与 SolidWorks 宏生成 (CAD 2D 绘图与 3D 参数化建模)
5. 交互式多轮对话与自主工作记忆注入
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

# 确保本地 Ollama 请求不被任何系统代理或 VPN 拦截
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 1. 连接本地 Ollama 引擎 (兼容 OpenAI 标准接口)
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",  # 本地运行无需真实 API Key
    http_client=httpx.Client(trust_env=False)
)

# 2. 基础技能库
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """获取当前真实时间与日期"""
    now = datetime.datetime.now()
    return f"当前系统时间为: {now.strftime('%Y-%m-%d %H:%M:%S')} (时区: {timezone})"

def philosophic_critique(topic: str) -> str:
    """对某个命题进行认识论反思与前提审查"""
    return f"【认识论审查】对命题 '{topic}'：请注意其是否存在概念偷换或未经证实的先验假设。"

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
    "philosophic_critique": philosophic_critique,
    "remember_fact": remember_fact,
    "recall_memories": recall_memories,
    # 计算机与文档操作技能
    "list_desktop_documents": list_desktop_documents,
    "read_document": read_document,
    "save_document": save_document,
    "send_email_or_draft": send_email_or_draft,
    "search_and_send_file": search_and_send_file,
    "capture_desktop_screenshot": capture_desktop_screenshot,
    # 工业 CAD 与 SolidWorks 技能
    "draw_cad_part": draw_cad_part,
    "generate_solidworks_macro": generate_solidworks_macro,
}

# 技能规范描述 (遵循 OpenAI Tools 规范，Qwen2.5 原生高精度支持)
TOOLS_SCHEMA = [
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
            "name": "get_current_time",
            "description": "当需要知道当前确切的日期、星期几或具体时间时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区名称，例如 Asia/Shanghai",
                        "default": "Asia/Shanghai"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "philosophic_critique",
            "description": "当用户探讨哲学命题或需要对其底层前提进行深度反思与逻辑审查时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "需要被审查的命题或概念"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "当用户分享了个人身份、兴趣爱好、重要目标、观点或你认为未来必须记住的关键事实时，主动调用此工具存入长期记忆。",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "需要永久保存的核心事实陈述"
                    },
                    "category": {
                        "type": "string",
                        "description": "分类：'user_fact', 'preference', 'goal', 'opinion'",
                        "default": "user_fact"
                    },
                    "importance": {
                        "type": "integer",
                        "description": "重要度 1-10",
                        "default": 7
                    }
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memories",
            "description": "当需要回想过去关于某个特定话题、人物或约定的历史记忆时调用此工具进行检索。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索关键词或问题"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_desktop_documents",
            "description": "扫描并列出用户电脑桌面上现有的文档、论文、Word文件等列表。",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "读取用户电脑桌面或指定路径下的文档、论文（如 Word .docx 文件、.txt、.md 文本）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name_or_path": {
                        "type": "string",
                        "description": "文件名（如 '精神现象学.docx'）或完整文件路径"
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
            "description": "将你修改润色后的论文、文章或报告直接保存到用户的电脑桌面上，支持生成 Word (.docx) 或文本文档 (.txt)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name_or_path": {
                        "type": "string",
                        "description": "生成的文件名，如 '论文修改建议.docx'"
                    },
                    "content": {
                        "type": "string",
                        "description": "要保存的完整文章或润色后的内容"
                    }
                },
                "required": ["file_name_or_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_or_draft",
            "description": "起草并拟定一封正式邮件，并在用户桌面上生成邮件拟稿文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "收件人邮箱地址"
                    },
                    "subject": {
                        "type": "string",
                        "description": "邮件主题"
                    },
                    "body": {
                        "type": "string",
                        "description": "邮件正文详细内容"
                    }
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draw_cad_part",
            "description": "根据工程参数自主绘制 2D CAD 专业机械工程图，并输出为标准 .dxf 文件直接保存到电脑桌面。支持零件类型：'flange'(法兰盘), 'shaft'(阶梯轴), 'plate'(安装板/底座)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_type": {
                        "type": "string",
                        "description": "零件类型：'flange'(法兰盘), 'shaft'(阶梯轴), 'plate'(安装板)"
                    },
                    "params": {
                        "type": "object",
                        "description": "几何尺寸字典。例如法兰盘：{'outer_diameter': 100, 'inner_diameter': 30, 'pcd': 70, 'num_bolts': 4, 'bolt_hole_diameter': 8}；阶梯轴：{'stages': [{'diameter': 25, 'length': 40}, {'diameter': 35, 'length': 60}]}；安装板：{'width': 120, 'height': 80, 'hole_diameter': 8}"
                    },
                    "filename": {
                        "type": "string",
                        "description": "保存的文件名，如 '法兰盘零件图.dxf'"
                    }
                },
                "required": ["part_type", "params"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_solidworks_macro",
            "description": "生成用于在 SolidWorks 中进行 3D 参数化自动建模的 VBA 宏代码脚本 (.bas/.swp)，支持一键自动生成草图、拉伸实体、打孔切除并保存至桌面。",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_name": {
                        "type": "string",
                        "description": "零件名称，如 '电机法兰' 或 '连接支架'"
                    },
                    "part_type": {
                        "type": "string",
                        "description": "零件类型：'flange'(法兰盘) 或 'plate'(安装块/板件)"
                    },
                    "params": {
                        "type": "object",
                        "description": "三维尺寸参数。例如：{'outer_diameter': 120, 'inner_diameter': 35, 'thickness': 15, 'pcd': 80, 'bolt_hole_diameter': 10}"
                    },
                    "filename": {
                        "type": "string",
                        "description": "宏文件名，如 '法兰盘3D建模.bas'"
                    }
                },
                "required": ["part_name", "part_type", "params"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_and_send_file",
            "description": "当用户要求你发送、查找、传过来电脑上的某个文件、文档、书目或论文（如PDF、Word、CAJ、图纸等）时，必须调用此工具在电脑中搜索文件并直接发送给微信端的用户！",
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
    }
]

def chat_loop(model_name: str = "neuro"):
    print("=" * 70)
    print(f"🤖 Neuro 智能体已就绪 (底座模型: {model_name})")
    print("🧠 长期记忆引擎已挂载 | 💻 计算机文档与邮件操作就绪")
    print("📐 工业级 CAD 工程制图 (.dxf) 与 SolidWorks 3D 宏生成就绪！")
    print("💡 输入 'quit' 退出。")
    print("=" * 70)

    messages = []

    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit"]:
                print("👋 Neuro: 下次见！所有新记忆已安全存入本地数据库。")
                break

            # 1. 自动从长期记忆库中检索与当前对话最相关的记忆 (Working Memory Preload)
            memory_context = memory_engine.get_working_memory_context(user_input, max_items=4)
            
            # 构建送给模型的当前轮提示
            current_messages = list(messages)
            if memory_context:
                current_messages.append({
                    "role": "system",
                    "content": f"以下是你的海马体长期记忆库中检索到的相关信息，请结合这些事实与用户交流：\n{memory_context}"
                })
            
            current_messages.append({"role": "user", "content": user_input})

            # 2. 调用模型决策 (附带完整技能库)
            response = client.chat.completions.create(
                model=model_name,
                messages=current_messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )

            response_msg = response.choices[0].message

            # 3. 检查是否触发了 Skill
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

                # 技能执行完毕后，让模型给出最终自然回复
                final_response = client.chat.completions.create(
                    model=model_name,
                    messages=current_messages
                )
                reply = final_response.choices[0].message.content
            else:
                reply = response_msg.content

            print(f"\n🧠 Neuro: {reply}")

            # 维护会话上下文历史 (保留纯净对话历史)
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
