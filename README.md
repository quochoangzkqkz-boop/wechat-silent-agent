# WeChat-Silent-Agent (微信 4.x 静默双向智能体网关)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20~%203.15-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/WeChat-4.0%20%7C%204.1-07C160.svg" alt="WeChat">
  <img src="https://img.shields.io/badge/Base%20Model-DeepSeek--R1--8B-purple.svg" alt="DeepSeek">
  <img src="https://img.shields.io/badge/Inference-AMD%20ROCm%20%7C%20Ollama-red.svg" alt="AMD ROCm">
  <img src="https://img.shields.io/badge/Security-Zero%20Injection%20(Anti--Ban)-brightgreen.svg" alt="Security">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

> **A Zero-Injection, Non-Intrusive WeChat 4.x Remote AI Gateway powered by DeepSeek-R1 & Native Windows OCR.**  
> 针对微信 4.x（Qt/自绘硬件渲染架构）彻底重构的全新双向静默交互框架。**0 注入、0 封号风险、轮询期间 0 鼠标移动与 0 抢占**，支持手机端与电脑端本地 DeepSeek-R1 智能体实时联动，自主读取学术论文、生成 2D CAD 工程图纸并双向回传大文件。

---

## 💡 为什么需要本项目？(Background & Motivation)

随着微信桌面端全面升级至 **微信 4.0 / 4.1**，底层架构完全抛弃了传统的 Win32 / UIAutomation 控件树，改用 **Qt5 + 硬件加速渲染（`MMUIRenderSubWindowHW`）**：
1. **现有开源自动化全部失效**：像 `wxauto`、`pywinauto` 等基于原生句柄查找的库在微信 4.x 上完全无法读取消息气泡与聊天列表。
2. **Hook 内存注入极易封号**：传统的 DLL 内存注入或逆向 Hook 严重违反安全协议，导致微信账号被高频封禁。
3. **传统 GUI 自动化严重抢占光标**：传统的点击自动化会不断把用户的物理光标拉走并弹出右键菜单，用户在打游戏、写代码或看论文时无法正常使用电脑。

**WeChat-Silent-Agent** 提出了全新的系统级解决方案：
* **全静默内存屏幕差分（Differential Visual Hashing）**：轮询仅需 5ms 内存比对，闲时 **0% CPU、0 物理光标移动、0 键盘输入、0 弹窗**。
* **微秒级原子光标复原（Microsecond Cursor Restoration）**：在发送消息的瞬间缓存物理鼠标坐标并在 `< 15ms` 内瞬时归位，用户完全无感。
* **Windows 原生离线 OCR**：基于系统内置 `Windows.Media.Ocr`，无需联网、无需任何付费 API，毫秒级识别气泡文字。
* **全双工文件管道（CF_HDROP File Piping）**：打通 Windows 系统级剪贴板文件对象，实现 PDF 论文、Word 文档、CAD 图纸的手机端与 PC 端双向秒级传输。

---

## 🏗️ 系统架构图 (Architecture)

```text
[手机端微信 (文件传输助手)] 
         │  (云端同步)
         ▼
[PC 微信 4.1 窗口]  <──────────────────────────┐
         │ (内存屏幕缓冲)                        │  (<15ms 瞬时物理光标恢复 & CF_HDROP)
         ▼                                     │
[差分哈希检测器 (ImageGrab + MD5)]               │
         │  (仅屏幕变化时触发)                   │
         ▼                                     │
[Windows.Media.Ocr 本地引擎]                    │
         │  (提取新指令文本)                     │
         ▼                                     │
┌──────────────────────────────────────────────┴───────────────────────────┐
│                    🧠 Cognitive Brain (DeepSeek-R1)                      │
│                                                                          │
│  - 长思维链思考 (Chain-of-Thought)                                        │
│  - 斯坦福 Generative Agents 长期海马体记忆 (SQLite + 衰减检索)               │
│  - 物理技能库 (Tool-Calling / Function Calling):                          │
│     ├─ search_and_send_file: 模糊全盘深度文件寻道 (.pdf, .docx, .caj)     │
│     ├─ draw_cad_part: 2D 工业机械制图 (.dxf 标准图纸)                     │
│     ├─ generate_solidworks_macro: 3D 参数化建模宏脚本 (.bas)             │
│     └─ save_document: 论文润色与 Word 成果落地                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ 核心特性 (Key Features)

| 特性 | 传统方案 (Hook / wxauto) | WeChat-Silent-Agent (本项目) |
| :--- | :--- | :--- |
| **微信 4.x 兼容性** | ❌ 彻底失效 (无法获取控件) | ✅ **原生完美适配** (Qt/DirectComposition) |
| **账号安全性** | ❌ 极高风险 (DLL 注入秒封号) | ✅ **100% 绝对安全** (纯系统级交互，零侵入) |
| **前台抢鼠标** | ❌ 严重 (频繁抖动、乱弹右键) | ✅ **完全无感** (微秒级瞬时归位，光标自由) |
| **OCR 成本** | 需配置第三方收费 API | ✅ **纯本地零成本** (Windows 原生 OCR) |
| **大附件双向回传** | ❌ 仅支持纯文本聊天 | ✅ **支持全格式大文件** (PDF, Word, DXF, CAJ) |
| **端侧算力加速** | 仅依赖云端大模型 | ✅ **AMD ROCm / NVIDIA CUDA 端侧纯本地运行** |

---

## 🚀 快速启动指南 (Quick Start)

### 1. 环境要求
* **操作系统**：Windows 10 / Windows 11 (64-bit)
* **Python 版本**：Python 3.10 ~ 3.15
* **微信版本**：微信 PC 客户端 4.0 或 4.1
* **本地大模型运行环境**：[Ollama](https://ollama.com/) (支持 AMD ROCm 或 NVIDIA GPU 加速)

### 2. 克隆与依赖安装
```bash
git clone https://github.com/quochoangzkqkz-boop/wechat-silent-agent.git
cd wechat-silent-agent

# 安装精简依赖 (纯 Python，无需编译环境)
pip install -r requirements.txt
```

### 3. 本地大模型准备 (以 DeepSeek-R1 为例)
你可以直接使用 Ollama 加载 DeepSeek-R1 系列模型：
```bash
# 构建智能体模型
ollama create neuro -f Modelfile
```

### 4. 一键运行
打开电脑微信，确保【文件传输助手】置于会话窗口中，直接双击运行：
```bash
start.bat
# 或执行: python -m src.gateway
```

现在，你可以用手机向电脑上的微信【文件传输助手】发送任意指令：
* `帮我把黑格尔的精神现象学论文发过来` ➡️ 自动搜索电脑并传回文件原件。
* `帮我画一个外径120内径40的法兰盘并导出CAD` ➡️ 自动生成标准 `.dxf` 工程图纸并作为附件回传。

---

## 📂 项目目录结构 (Repository Structure)

```text
wechat-silent-agent/
├── .gitignore               # Git 忽略配置（已过滤大权重与敏感临时文件）
├── LICENSE                  # MIT 开源许可证
├── README.md                # 详细项目技术白皮书
├── requirements.txt         # 核心运行环境依赖
├── Modelfile                # DeepSeek-R1 / Qwen3 推理参数与行动规范
├── start.bat                # Windows 一键无痛启动脚本
└── src/
    ├── __init__.py
    ├── gateway.py           # 核心：微信 4.x 全静默视觉双向网关
    ├── agent.py             # 认知中枢：思维链、工具调度与大模型通信
    ├── memory.py            # 海马体：Generative Agents 长期持久化记忆
    ├── tools/
    │   ├── __init__.py
    │   ├── computer_tools.py # 深度文件检索、论文精读、Word 保存
    │   └── cad_tools.py      # 2D CAD (.dxf) 绘图与 SolidWorks 宏生成
    └── scripts/
        └── ps_ocr.ps1        # 纯离线 Windows.Media.Ocr 驱动引擎
```

---

## 📜 许可证 (License)

本项目基于 [MIT License](LICENSE) 开源发布，欢迎学术研究、开源社区交流及商业化参考！
