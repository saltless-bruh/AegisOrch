# AegisOrch

> **The Autonomous Agentic Reverse Engineering Framework.**

AegisOrch has evolved. Formerly conceived as a local-first antivirus, AegisOrch is now a **fully automated, agent-driven reverse engineering orchestrator**.

Powered by **CrewAI**, **LangChain**, and **`llama.cpp`**, AegisOrch doesn't just quarantine a suspicious file—it automatically decompiles it, reads the pseudocode, identifies Command & Control (C2) callbacks, and generates a comprehensive MITRE ATT&CK intelligence report, all running locally on consumer hardware.

## 🚀 The Vision: From Defense to Decompilation

Traditional AV tells you a file is bad. AegisOrch tells you _why_ it's bad, _how_ it works, and _where_ it's trying to communicate.

By shifting from our custom `OrchBiter` framework to the industry-standard **CrewAI + LangChain** ecosystem, AegisOrch taps into a massive library of agentic tooling. To run heavy AI analysis alongside intensive decompilation tasks (like Radare2 or Ghidra) without freezing the host OS, AegisOrch implements **Sequential Crew Execution** and **Hardware-Aware Tool Locks**.

### 🧠 The LLM Engine: The `llama.cpp` Daemon

AegisOrch is designed to be instantly available from any terminal directory. Instead of loading massive AI models into Python on every run, AegisOrch relies on a background `llama.cpp` server daemon.

**The Target Model:** `unsloth/Nemotron-3-Nano-30B-A3B-GGUF`

- **The Hardware Sweet Spot:** Tailored for systems like an **Nvidia RTX 3060 (12GB VRAM)** paired with **32GB DDR5 RAM** and a strong CPU (Ryzen 7).
    
- **Hybrid Execution:** We offload ~10GB of the model to the GPU, leaving VRAM headroom for the OS, while the remaining layers offload to high-speed DDR5. Because it's an MoE (Mixture of Experts) model, it achieves lightning-fast inference for marathon analysis runs.
    

## 🕵️‍♂️ The Reverse Engineering Crew (CrewAI)

AegisOrch coordinates a specialized team of autonomous AI agents:

1. **🦅 The Scout (Triage & Fingerprinting)**
    
    - _Mission:_ Identifies packed or obfuscated executables via static analysis (PE headers, high entropy calculation).
        
    - _Output:_ Flags high-risk binaries and hands the file path to the decompilation agent.
        
2. **🐺 The Hunter (The Decompiler)**
    
    - _Mission:_ Interacts with RE tools (Radare2 `r2pipe` / PyGhidra MCP Server) to safely unpack, extract strings, and generate C-pseudocode or x86 assembly from the `main()` function.
        
    - _Hardware Control:_ Uses strict LangChain `@tool` mutex locks to ensure CPU-heavy decompilation doesn't compete with GPU-heavy LLM inference.
        
3. **🧠 The Brain (Senior Malware Analyst)**
    
    - _Mission:_ The core reasoning persona. Queries the `llama.cpp` Nemotron daemon to analyze the extracted pseudocode, hunting for persistence hooks, cryptography, and network beacons.
        
4. **📜 The Scribe (Intelligence Reporter)**
    
    - _Mission:_ Consolidates the Brain's JSON findings into a beautiful, human-readable Markdown report mapped to the MITRE ATT&CK framework.
        

## 🏗️ Core Architecture Features

- **Sequential Process Flow:** CrewAI is strictly configured to run agents sequentially. The Scout finishes completely before the Hunter starts, preventing your system from thrashing due to resource contention.
    
- **Hardware-Aware LangChain Tools:** Decompilation tools are wrapped in `threading.Lock` semaphores. If a heavy binary analysis is running, LLM requests queue up patiently.
    
- **Crash-Proof "Direct Truth" Memory:** Reverse engineering is volatile. Through custom LangChain Callbacks, every extracted IOC, pseudocode snippet, and agent thought is instantly committed to a local **SQLite WAL database**. If the system OOMs or crashes, the forensic ledger survives.
    
- **Dynamic Context Hooks (AIDebug Inspired):** Future integration for watching dynamic memory diffs (e.g., `VirtualProtect` calls) and feeding runtime execution traces directly to the Brain agent.
    

## 🛠️ Installation & Setup

### Prerequisites

- Pop!_OS / Linux (Strongly Recommended)
    
- Python 3.12+
    
- 12GB+ VRAM & 32GB+ System RAM
    
- `llama.cpp` compiled with CUDA support
    
- Radare2 or Ghidra (for headless decompilation)
    

### 1. Start the LLM Daemon

Configure a `systemd` service or run the server manually:

```
./llama-server -m models/Nemotron-3-Nano-30B-A3B.Q4_K_M.gguf -ngl 33 --host 127.0.0.1 --port 8080
```

### 2. Setup AegisOrch

```
git clone [https://github.com/your-repo/AegisOrch.git](https://github.com/your-repo/AegisOrch.git)
cd AegisOrch
pip install -r requirements.txt
```

### 3. Trigger an Autonomous Hunt

```
# Run AegisOrch on a specific suspicious binary
python3 -m aegisorch analyze --target ./suspicious_sample.exe
```

## 📜 Roadmap

- [x] **Phase 1**: Pivot architecture to CrewAI + LangChain.
    
- [x] **Phase 2**: Implement Static Analysis (Entropy/PE) Scout Agent.
    
- [ ] **Phase 3**: Integrate `r2pipe` LangChain tools for automated assembly extraction.
    
- [ ] **Phase 4**: Implement PyGhidra MCP Server connection for deep C-pseudocode analysis.
    
- [ ] **Phase 5**: Dynamic execution hooking and registry snapshots.
    

## License

MIT License# AegisOrch (formerly PyMalScan)

> **The Autonomous AI Immune System for Your Local Machine.**

**AegisOrch** is a next-generation forensic orchestration system powered by the **OrchBiter** framework. Unlike traditional antivirus tools that rely on static signatures and cloud APIs, AegisOrch operates as a **Hardware-Aware, Agentic Defense System**. It orchestrates a team of autonomous AI agents—Scouts, Hunters, and Healers—to proactively defend your workstation without freezing your system.

---

## 🚀 Key Differences

| Feature | Legacy Antivirus | AegisOrch |
| :--- | :--- | :--- |
| **Logic** | Static Signatures | **Autonomous AI Agents** (OrchBiter) |
| **Resource Usage** | Hogs CPU/Disk | **Hardware Arbitration** (Pauses scans during AI inference) |
| **Intelligence** | Daily Updates | **Real-Time Threat Intel** (Abuse.ch / MalwareBazaar) |
| **Recovery** | Quarantine File | **Direct Truth Persistence** (SQLite WAL History) |
| **Analysis** | "Threat Found" | **DeepSeek/Llama Powered Explanations** |

---

## 🧠 The Agent Crew

AegisOrch creates a local "Security Operations Center" (SOC) inside your RAM:

1.  **🦅 The Scout (Threat Intel)**
    *   *Mission*: Polls global threat feeds (MalwareBazaar, Abuse.ch) for new IOCs.
    *   *Tech*: Asyncio poller, minimal footprint.
2.  **🐺 The Hunter (Forensics)**
    *   *Mission*: Hunts for threats in Filesystem, Memory (PIDs), and Persistence hooks (Cron/Registry).
    *   *Tech*: ClamAV, YARA (Disk + Memory), Volatility concepts.
    *   *Behavior*: **Pauses automatically** when you need your PC for other heavy tasks.
3.  **🧠 The Brain (Analysis)**
    *   *Mission*: Analyzes suspicious findings using Local LLMs (Llama-3, DeepSeek).
    *   *Tech*: Heuristic Scoring (Entropy, PE Headers) + AI Explanation.
4.  **⚕️ The Healer (Remediation)**
    *   *Mission*: Generates surgical remediation scripts.
    *   *Safety*: Requires your explicit "Yes" via CLI to execute destructive actions.

---

## 🏗️ Architecture: OrchBiter Inside

This project serves as the flagship implementation of the **OrchBiter Framework**:
*   **Kernel-Level Arbitration**: Uses `SIGSTOP`/`SIGCONT` to manage resource contention between AI inference and forensic scanning.
*   **Direct Truth**: Every action is saved to SQLite immediately. No data loss on crash.
*   **Strict Forms**: All AI actions are validated against Pydantic schemas to prevent hallucinations.

---

## 🛠️ Installation & Usage

### Prerequisites
*   Python 3.12+
*   Linux (Preferred) or WSL2
*   ClamAV & YARA

### Setup
```bash
git clone https://github.com/your-repo/AegisOrch.git
cd AegisOrch
pip install -r requirements.txt
```

### Running the Orchestrator
```bash
# Start the autonomous defense system
sudo python3 -m aegisorch start
```

### Manual Deep Scan
```bash
# Trigger a manual hunt
sudo python3 -m aegisorch hunt --target /home/user --analyze
```

---

## 📜 Roadmap
*   [x] **Phase 1**: Core OrchBiter Integration (Hardware Arbiter, SQLite)
*   [ ] **Phase 2**: Agent "Crew" Implementation (Scout, Hunter, Brain)
*   [ ] **Phase 3**: Local LLM Integration (DeepSeek/Llama for analysis)

## License
MIT License
