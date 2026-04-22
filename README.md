# AegisOrch

> **The Autonomous Agentic Reverse Engineering Framework.**

AegisOrch has evolved. Formerly conceived as a local-first antivirus, AegisOrch is now a **fully automated, multi-agent reverse engineering orchestrator**.

Powered by **CrewAI**, **LangChain**, and a local **`llama.cpp` router daemon**, AegisOrch automatically decompiles suspicious binaries, reasons through highly obfuscated assembly, identifies Command & Control (C2) callbacks, and generates comprehensive MITRE ATT&CK intelligence reports—all running locally on consumer hardware.

## 🚀 The Vision: An Enterprise RE Lab on Your Desktop

Traditional AV tells you a file is bad. AegisOrch tells you _why_ it's bad, _how_ it works, and _where_ it's trying to communicate, surviving marathon analysis runs without context degradation.

AegisOrch is specifically tailored for local execution (Target Hardware: **Nvidia RTX 3060 12GB VRAM + 32GB System RAM**). To achieve this without melting the host OS, it utilizes a carefully curated stack of Mixture of Experts (MoE), Distilled Reasoning, and embedding models managed by a single background daemon.

### 🧠 The AegisOrch AI Stack (Daemon Models)

We utilize `llama.cpp`'s router mode to dynamically switch between four specialized models, perfectly threading the 44GB memory pool (~27.5GB total footprint), leaving ample room for background RE tools like Radare2 and Ghidra.

1. **The Scout (`unsloth/functiongemma-270m-it-GGUF`)**
    
    - _Role:_ Lightning-fast triage. Analyzes PE headers and entropy in milliseconds to decide if a file warrants deep analysis.
        
2. **The Brain (`unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF`)**
    
    - _Role:_ The Manager / Macro-Reasoner. Uses deep `<think>` blocks to strategize the reverse engineering process, delegating specific decompilation tasks to the Worker without losing the overarching threat-intel plot.
        
3. **The Hunter & Scribe (`unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`)**
    
    - _Role:_ The Tool Worker. Wakes up to execute LangChain tools (e.g., Ghidra MCP server, `r2pipe`), parses raw x86 assembly, and outputs strict JSON.
        
    - _The Synergy:_ Because it shares the exact same tokenizer vocabulary as the DeepSeek-R1-Qwen Brain, `llama.cpp` swaps between the Thinker and Worker instantly without flushing the KV cache.
        
4. **The LLM-Wiki (`unsloth/embeddinggemma-300m-GGUF`)**
    
    - _Role:_ The Memory Engine. Powers AegisOrch's local ChromaDB, allowing the agents to instantly recall Windows API structures and previous findings during 5-hour marathon analysis runs.
        

## 🏗️ Core Architecture Features

- **Hierarchical Crew Execution:** The R1 Thinker acts as the manager, while the Qwen3-Coder acts as the worker. This prevents the reasoning model from breaking JSON schemas and keeps tool execution flawless.
    
- **The LLM-Wiki (RAG Memory):** Agents maintain a continuous dynamic memory. If the Worker decrypts an XOR loop in function 1, the Thinker will remember that exact XOR key 4 hours later when analyzing function 50.
    
- **Hardware-Aware LangChain Tools:** CPU-heavy decompilation tools are wrapped in `threading.Lock` mutexes, ensuring reversing tools and LLM inference never compete for system resources simultaneously.
    
- **Crash-Proof "Direct Truth":** Every extracted IOC, pseudocode snippet, and agent thought is instantly committed to a local **SQLite WAL database**.
    

## 🛠️ Installation & Setup

### Prerequisites

- Pop!_OS / Linux (Strongly Recommended)
    
- Python 3.12+
    
- 12GB+ VRAM & 32GB+ System RAM
    
- Radare2 or Ghidra (for headless decompilation)
    
- `llama.cpp` compiled with CUDA support
    

### 1. Setup the Model Directory

Create a folder named `aegis_models` and place the four `.gguf` files (listed above) inside.

### 2. Start the LLM Router Daemon

AegisOrch expects the AI engine to be running in the background. Start `llama.cpp` pointing to the directory:

```
./llama-server --model-dir ./aegis_models --host 127.0.0.1 --port 8080 -ngl 99 --ctx-size 32768
```

### 3. Setup AegisOrch

```
git clone [https://github.com/your-repo/AegisOrch.git](https://github.com/your-repo/AegisOrch.git)
cd AegisOrch
pip install -r requirements.txt
```

### 4. Trigger an Autonomous Hunt

```
# Run AegisOrch on a specific suspicious binary
python3 -m aegisorch analyze --target ./suspicious_sample.exe
```

## 📜 Roadmap

- [x] **Phase 1**: Pivot architecture to CrewAI + LangChain + `llama.cpp` Router.
    
- [x] **Phase 2**: Define the Quad-Model (Scout, Thinker, Worker, Memory) hardware-optimized stack.
    
- [ ] **Phase 3**: Implement the LLM-Wiki ChromaDB memory system using EmbeddingGemma.
    
- [ ] **Phase 4**: Integrate `r2pipe` and PyGhidra MCP Server as strict LangChain tools for the Worker agent.
    
- [ ] **Phase 5**: Dynamic execution hooking (AIDebug style) and registry snapshots integration.
    

## License

MIT License
