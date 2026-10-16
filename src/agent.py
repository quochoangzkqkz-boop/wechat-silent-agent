"""
Cognitive Agent Controller & Tool Schema
Compatible with:
- Local Ollama (DeepSeek-R1, Qwen2.5, Llama-3) via OpenAI-standard API
- Tool calling / Function calling execution loop
"""

import os
import json
import re
from openai import OpenAI
import httpx2 as httpx

from .memory import memory_engine
from .tools import (
    list_desktop_documents,
    read_document,
    save_document,
    send_email_or_draft,
    search_and_send_file,
    draw_cad_part,
    generate_solidworks_macro
)

# Bypass system proxies for local Ollama daemon
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# Initialize local OpenAI-compatible client
OLLAMA_BASE_URL = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434/v1")
MODEL_NAME = os.environ.get("AGENT_MODEL_NAME", "neuro")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama",
    http_client=httpx.Client(trust_env=False)
)

AVAILABLE_TOOLS = {
    "list_desktop_documents": list_desktop_documents,
    "read_document": read_document,
    "save_document": save_document,
    "send_email_or_draft": send_email_or_draft,
    "search_and_send_file": search_and_send_file,
    "draw_cad_part": draw_cad_part,
    "generate_solidworks_macro": generate_solidworks_macro,
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_and_send_file",
            "description": "Searches for existing documents, papers, CAD drawings, or books across the user's computer (Desktop, Downloads, Documents) and returns the file path for transmission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword or filename to search, e.g. 'Burckhardt', 'MachineDesign', 'Thesis'"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draw_cad_part",
            "description": "Generates a 2D engineering CAD drawing (.dxf) based on dimensional parameters and saves it to Desktop. Supported: 'flange', 'shaft', 'plate'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_type": {
                        "type": "string",
                        "description": "'flange', 'shaft', or 'plate'"
                    },
                    "params": {
                        "type": "object",
                        "description": "Dimensions in mm, e.g. {'outer_diameter': 120, 'inner_diameter': 35, 'pcd': 80, 'bolt_hole_diameter': 10}"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Output filename (e.g. 'flange_part.dxf')"
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
            "description": "Generates a SolidWorks 3D parametric modeling VBA macro script (.bas) to automate sketch extrusion, cutouts, and hole placement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_name": {"type": "string"},
                    "part_type": {"type": "string"},
                    "params": {"type": "object"},
                    "filename": {"type": "string"}
                },
                "required": ["part_name", "part_type", "params"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Reads full contents of a Word paper (.docx) or text document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name_or_path": {"type": "string"},
                    "max_chars": {"type": "integer", "default": 3500}
                },
                "required": ["file_name_or_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_document",
            "description": "Saves written or revised text directly to user's Desktop as a Word document (.docx).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name_or_path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["file_name_or_path", "content"]
            }
        }
    }
]

def think_and_execute(user_text: str):
    """
    Main reasoning entrypoint: Injects long-term memory, invokes DeepSeek-R1 / local LLM,
    executes requested tools, and gathers output files.
    """
    memory_context = memory_engine.get_working_memory_context(user_text, max_items=4)
    system_instruction = (
        "You are an autonomous AI Agent companion running directly on the user's local operating system.\n"
        "【Action Principles】\n"
        "1. When the user asks for a file, paper, book, or drawing, immediately call search_and_send_file.\n"
        "2. When the user requests mechanical drafting or 3D modeling, call draw_cad_part or generate_solidworks_macro.\n"
        "3. Prioritize concise, pragmatic action over abstract conversation."
    )
    if memory_context:
        system_instruction += f"\n\n【Long-Term Memory Context】\n{memory_context}"

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_text}
    ]
    generated_files = []

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        response_msg = response.choices[0].message

        if response_msg.tool_calls:
            messages.append(response_msg)
            for tool_call in response_msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"⚡ [Tool Call] {fn_name}({fn_args})")

                if fn_name in AVAILABLE_TOOLS:
                    tool_result = AVAILABLE_TOOLS[fn_name](**fn_args)
                else:
                    tool_result = f"Error: Unknown tool {fn_name}"

                found_paths = re.findall(r"['\"]([A-Za-z]:\\[^'\"<>\n]+\.(?:dxf|docx|txt|bas|pdf|caj|zip|doc|xlsx|pptx))['\"]", str(tool_result))
                for fp in found_paths:
                    if os.path.isfile(fp) and fp not in generated_files:
                        generated_files.append(fp)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })

            final_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages
            )
            reply = final_response.choices[0].message.content
        else:
            reply = response_msg.content

        # Clean CoT think tags for chat display
        if "</think>" in reply:
            reply = reply.split("</think>")[-1].strip()

        return reply, generated_files

    except Exception as e:
        return f"Agent execution error: {str(e)}", []
