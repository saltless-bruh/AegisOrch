# AegisOrch (formerly AegisOrch)

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
