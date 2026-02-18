# AegisOrch v3.0 - Requirements Engineering

## 1. Functional Requirements (OrchBiter Specific)

### 1.1 Kernel-Level Resource Arbitration

* **SR-1.1**: The system MUST implement `HardwareArbiter` to manage CPU/VRAM contention between heavy tools (ClamAV, YARA) and local LLMs (Llama-3, DeepSeek).
* **SR-1.2**: The Arbiter MUST automatically pause (`SIGSTOP`) forensic scans when an LLM inference request is pending and resume (`SIGCONT`) afterwards.
* **SR-1.3**: The system MUST support a "Process Tree" grouping to ensure child processes (e.g., `clamscan` spawned by `python`) are also paused.

### 1.2 Hierarchical Agent Structure

* **SR-2.1**: The system MUST implement a 3-Layer Router:
  * **Layer 1 (Strategic)**: DeepSeek-R1 (Local/API) for high-level planning.
  * **Layer 2 (Tactical)**: Llama-3-8B (Local) for task decomposition.
  * **Layer 3 (Execution)**: Qwen-2.5-Coder (Local) for strict tool execution.
* **SR-2.2**: The system MUST support "Model Hot-Swapping" to unload Layer 1 models if VRAM is insufficient for Layer 2/3 tasks.

### 1.3 "Direct Truth" State Management

* **SR-3.1**: All tool outputs, plans, and decisions MUST be persisted immediately to a local SQLite database (WAL Mode).
* **SR-3.2**: Agents MUST NOT rely on in-memory chat history for long-running state; they must query the `ViewManager` for context.
* **SR-3.3**: The system MUST be crash-recoverable, resuming from the last known state in the database.

### 1.4 Strict Form Execution

* **SR-4.1**: All agent actions (scanning, file deletion) MUST be defined as Pydantic models (`FormExecutor`).
* **SR-4.2**: The system MUST validate all LLM outputs against these schemas *before* execution to prevent hallucinations.

## 2. Non-Functional Requirements

### 2.1 Performance & resource

* **NFR-1**: The system MUST run on consumer hardware (e.g., 16GB VRAM, 32GB RAM) without crashing or system freezing.
* **NFR-2**: Context switching (Pause/Resume) latency MUST be under 500ms.

### 2.2 Security & Safety

* **NFR-3**: The Healer Agent's destructive actions (file deletion, process kill) MUST require a "Human-in-the-Loop" confirmation via the CLI/Dashboard.
* **NFR-4**: The Arbiter MUST NOT pause critical system processes outside of its own child process tree.

## 3. Interfaces

### 3.1 Terminal Dashboard (Textual)

* **UI-1**: The dashboard MUST show real-time resource usage (CPU/GPU/VRAM).
* **UI-2**: The dashboard MUST visualize the Arbiter state (e.g., "Hunter Agent: PAUSED [SIGSTOP]", "Brain Agent: THINKING").
* **UI-3**: The dashboard MUST provide an interactive log of `Direct Truth` entries (database inserts).
