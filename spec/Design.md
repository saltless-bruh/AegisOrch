# AegisOrch v3.0 - System Design Specification

## 1. Introduction

AegisOrch v3.0 is a local-first, autonomous malware analysis system built on the **OrchBiter** framework. It is engineered to function as a self-contained "AI Immune System" optimized for resource-constrained consumer hardware (e.g., standard workstations with 12GB VRAM).

Traditional Endpoint Detection and Response (EDR) solutions often rely on cloud telemetry, introducing privacy risks and latency. Conversely, local antivirus solutions rely on static signatures that fail against polymorphic threats. AegisOrch bridges this gap by deploying a team of autonomous AI agents directly on the host machine, capable of reasoning about threats in real-time without sending data to the cloud.

**Core Philosophy:**

1. **Do No Harm (The "Invisible Guardian" Principle):**
    
    The defense system must strictly yield to user activity. If the user is compiling code, rendering 3D scenes, or gaming, AegisOrch must instantly suspend its heavy operations. A security tool that causes frame drops or input lag is a failed tool. The system operates on the principle of "scavenging" idle compute cycles rather than competing for them.
    
2. **Direct Truth (Crash-Resistant Forensics):**
    
    Malware often attempts to crash the host system to wipe volatile evidence. AegisOrch rejects in-memory state management (like Python dictionaries or standard chat history) in favor of **synchronous SQLite persistence (WAL mode)**. Every observation, thought, and planned action is committed to the disk _before_ it is acted upon. If the machine loses power, the "Black Box" remains to tell the story upon reboot.
    
3. **Logical Hierarchy (Persona Swapping):**
    
    Instead of swapping heavy model files (which causes latency), we use a **Single Generalist Model** and swap its "Persona" (System Prompt) to switch between strategic planning and tactical execution. This ensures zero-latency switching between agents.
    

## 2. OrchBiter Integration Strategy

AegisOrch acts as the application layer, while **OrchBiter** serves as the "Operating System" for the agents. We import specific "Superpowers" to handle the physical limitations of the hardware.

### 2.1 The Freeze Ray (`core.arbiter`)

The **Hardware Arbiter** is the most critical component for user acceptance.

- **Mechanism**: It maintains a registry of Process IDs (PIDs) associated with "Heavy Tools" (e.g., ClamAV daemon, YARA scanning threads, Volatility memory dumpers).
    
- **Trigger**: It monitors Human Interface Devices (HID) via `evdev` (Linux) or `pywin32` (Windows).
    
- **Action**: Upon detecting mouse movement or keystrokes, the Arbiter instantly sends `SIGSTOP` signals to the registered PIDs, freezing them at the kernel level. This frees up CPU cycles and memory bus bandwidth immediately. When the user has been idle for >5 seconds, it sends `SIGCONT` to resume operations transparently.
    

### 2.2 The Context Engine (`core.context`)

To minimize latency on consumer hardware, we avoid physical model swapping in favor of **Persona Swapping**.

- **One Model Rule**: A single 7B model stays loaded in VRAM permanently.
    
- **Prompt Injection**: When the system transitions from "Brain" to "Hunter", the Router injects a new System Prompt (e.g., changing from _"You are a Strategist"_ to _"You are a JSON Tool Caller"_).
    
- **Context Pruning**: The Router aggressively summarizes previous steps to keep the context window small and fast.
    

### 2.3 The Safety Net (`core.forms`)

Autonomous remediation is dangerous. A hallucinating AI could delete `System32`.

- **Strict Contracts**: The `Healer` agent is forbidden from outputting free-text commands. It must interact through `FormExecutor`, which binds to Pydantic models.
    
- **Validation**: If the generated JSON does not match the regex patterns (e.g., verifying a target PID exists and is not a kernel process), the action is blocked _before_ execution.
    

### 2.4 The Black Box (`core.db`)

- **Technology**: SQLite with Write-Ahead Logging (WAL).
    
- **Schema Design**: The database stores a "Ledger of Truth" rather than just logs. This includes the raw hash of the file, the exact YARA rule that triggered, the raw chain-of-thought from the AI, and the cryptographic signature of the remediation script.
    

## 3. Agent Roles & Specifications

The system is composed of specialized agents. Each has a specific resource profile, model assignment, and set of operational constraints.

### 3.1 🦅 Scout (Threat Intelligence)

- **Role**: The "Eyes". Builds the threat map and monitors entry points.
    
- **Type**: `AsyncTool` (Low Resource / I/O Bound).
    
- **Model**: None (Deterministic Python/Regex).
    
- **OrchBiter Integration**: Runs continuously in the background as a daemon. Because it primarily waits on network I/O, it is **ignored** by the Arbiter's "Freeze Ray" to ensure threat intel is always up to date.
    
- **Key Tasks**:
    
    - **Feed Polling**: Checks MalwareBazaar and Abuse.ch every 15 minutes.
        
    - **Bloom Filtering**: Updates a local, memory-efficient Bloom filter with known malicious hashes to minimize expensive database lookups.
        
    - **File Watching**: Monitors high-risk directories (Downloads, Temp, AppData) for new executable creation.
        

### 3.2 🐺 Hunter (Forensics)

- **Role**: The "Hands". Extracts evidence from the file system and memory.
    
- **Type**: `ProcessTool` (High Resource / CPU Bound).
    
- **Model**: **Qwen-2.5-7B-Instruct** (Persona: Digital Forensics Expert).
    
- **OrchBiter Integration**: Registered as a "Heavy Tool". The Arbiter _pauses_ this agent (`SIGSTOP`) when "The Brain" needs to run inference or when user input is detected.
    
- **Implementation Requirement**:
    
    ```
    # aegisorch/agents/hunter.py
    from orchbiter.core.arbiter import ProcessTool
    
    class YaraScanner(ProcessTool):
        def __init__(self):
            super().__init__(
                name="YaraHunter",
                binary_path="/usr/bin/yara",
                resource_profile="heavy_cpu",
                can_suspend=True # Critical for Arbiter control
            )
    ```
    
- **Operational Constraints**:
    
    - **Sandboxing**: File system access is restricted to the specific target directory identified by the Scout.
        
    - **Timeout**: Scans exceeding 5 minutes on a single file are forcefully terminated to prevent "zip bomb" DOS attacks.
        

### 3.3 🧠 Brain (Analysis & Planning)

- **Role**: The "Mind". Interprets raw data and formulates strategy.
    
- **Type**: **Layer 1 Reasoning Persona**.
    
- **Model**: **Qwen-2.5-7B-Instruct** (Persona: Senior Malware Analyst).
    
- **OrchBiter Integration**: Receives priority access to VRAM. When activated, it requests an "Inference Lock", forcing all other agents to sleep.
    
- **Task**:
    
    - **Heuristic Analysis**: Reviews file entropy, PE headers, and imported DLLs.
        
    - **Chain-of-Thought**: We inject a specific prompt ("Think step-by-step about this evidence...") to emulate reasoning capabilities within the generalist model.
        
- **Output**: Generates `Strategy.json`. This model **never** calls tools directly; it only outputs intent.
    

### 3.4 ⚕️ Healer (Remediation)

- **Role**: The "Surgeon". Executes the approved plan.
    
- **Type**: **Layer 3 Execution Persona**.
    
- **Model**: **Qwen-2.5-7B-Instruct** (Persona: Automation Engineer).
    
- **Safety**: Enforced via `FormExecutor` strict JSON schema validation.
    
- **Implementation Requirement**:
    
    ```
    # aegisorch/agents/healer.py
    from pydantic import BaseModel, Field
    
    class RemediationPlan(BaseModel):
        target_pid: int = Field(..., description="The Process ID to kill")
        file_path: str = Field(..., description="Absolute path of malware")
        action: str = Field(..., pattern="^(quarantine|delete)$")
        reasoning: str = Field(..., description="Why is this action safe?")
    ```
    
- **Human-in-the-Loop**: Destructive actions (killing processes, deleting files) require an explicit confirmation code from the user via the UI, unless "Autonomous Mode" is strictly enabled for specific confidence thresholds.
    

## 4. Execution Data Flow (The Unified Pipeline)

The system operates as an event-driven pipeline, utilizing a single model with shifting personas.

1. **Phase 1: Detection (The Trigger)**
    
    - **Actor**: `Scout` (Network) or `Watchdog` (File System).
        
    - **Action**: Detects `suspicious.exe` (e.g., newly downloaded file with high entropy).
        
    - **Data Write**: Creates a new `Incident` record in `OrchBiter.db` with status `DETECTED`.
        
2. **Phase 2: The "Brain" (Reasoning)**
    
    - **Context Switch**: The `HardwareArbiter` pauses background scans.
        
    - **Persona Load**: System Prompt switches to **"Reasoning Mode"**.
        
    - **Inference**: The model analyzes the incident data.
        
    - **Decision**: Outputs `Strategy.json`.
        
    - **Persist**: The strategy is saved to the DB.
        
3. **Phase 3: The "Hands" (Execution)**
    
    - **Persona Load**: System Prompt switches to **"Tool Execution Mode"**.
        
    - **Translation**: The model reads `Strategy.json` and converts abstract intent into concrete MCP Tool Calls (e.g., `filesystem.move`).
        
    - **Validation**: The `FormExecutor` validates the tool calls.
        
    - **Execution**: The MCP Server performs the disk operation.
        
    - **Resume**: `HardwareArbiter` sends `SIGCONT` to background tasks.
        

## 5. Technology Stack & AI Recommendations

### 5.1 Unified Single-Model Strategy

To eliminate model loading latency and fit comfortably within 12GB VRAM, we use a single, high-performance generalist model.

- **Primary Model**: **Qwen-2.5-7B-Instruct** (GGUF)
    
    - **Quantization**: `Q5_K_M` (~5.5 GB VRAM).
        
    - **Why Qwen?**: It is currently the "Best in Class" for 7B models. It balances **Logic** (Logic benchmarks close to Llama-3) with **Tool Use** (Native function calling capabilities that surpass DeepSeek-R1).
        
    - **VRAM Budget**:
        
        - Model: ~5.5 GB
            
        - Context (8k tokens): ~1.0 GB
            
        - **Total AI Load**: ~6.5 GB
            
        - **Remaining for OS/Games**: ~5.5 GB (Safe margin to prevent lagging).
            

### 5.2 Core Stack

- **Runtime**: Python 3.12+ (Asyncio). Utilizing `TaskGroups` for robust concurrency.
    
- **Orchestration**: `orchbiter` (Local Package). The proprietary engine handling signals and routing.
    
- **Persistence**: `SQLAlchemy` + SQLite (WAL Mode). Chosen for zero-config reliability and high write throughput.
    
- **UI**: `Textual`. A Terminal User Interface (TUI) is preferred over a GUI. In a severe malware infection, the graphical subsystem (Explorer/Gnome) is often compromised or lagging, while the TTY remains responsive.
    

## 6. Project Structure

```
AegisOrch/
├── aegisorch/
│   ├── __init__.py
│   ├── core/                    # The OrchBiter Kernel (Imported)
│   │   ├── arbiter.py           # HardwareArbiter: Manages SIGSTOP/SIGCONT
│   │   ├── router.py            # Model Relay Logic: Handles VRAM swapping
│   │   ├── db.py                # DirectTruthDB: SQLite WAL interface
│   │   └── forms.py             # Pydantic Safety Nets for tool calls
│   ├── agents/                  # The "Crew"
│   │   ├── scout.py             # AsyncTool: Network poller
│   │   ├── hunter.py            # ProcessTool: Wrapped YARA scanner
│   │   ├── brain.py             # Layer 1 Logic: Reasoning prompts
│   │   └── healer.py            # Layer 3 Logic: Remediation schemas
│   ├── tools/                   # MCP Clients
│   │   ├── filesystem.py        # Safe disk operations
│   │   └── memory.py            # Volatility wrappers
│   └── ui/                      # Textual TUI
│       ├── dashboard.py         # Main status screen
│       └── components.py        # Widgets for Arbiter status
├── rules/                       # Detection Logic
│   ├── yara/                    # Custom YARA signatures
│   └── sigma/                   # Behavioral Sigma rules
├── data/                        # SQLite DB (The Black Box)
└── config.yaml                  # Model paths, API keys, and resource limits
```