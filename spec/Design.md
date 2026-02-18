# AegisOrch v3.0 - System Design Specification

## 1. Introduction

AegisOrch v3.0 is a local-first, autonomous malware analysis system built on the **OrchBiter** framework. It is designed to operate effectively on resource-constrained consumer hardware (e.g., standard workstations) by leveraging kernel-level resource arbitration to balance heavy forensic tasks with local AI inference.

## 2. Architecture Overview

The system inherits OrchBiter's three core pillars: **Hardware Arbitration**, **Hierarchical Layering**, and **Direct Truth Persistence**.

### 2.1 Core Components (OrchBiter Integration)

* **Hardware Arbiter (`core.arbiter`)**:
  * **Role**: Prevents system freeze/thrashing by pausing heavy forensic tools (e.g., recursive YARA scans, ClamAV) when the Local LLM needs to "think".
  * **Mechanism**: Uses `SIGSTOP`/`SIGCONT` to manage `ProcessTool` lifecycles based on VRAM/CPU pressure.
* **Layered Router (`core.router`)**:
  * **Layer 1 (Strategic)**: DeepSeek-R1 (Local/API) - Decides high-level remediation strategy (e.g., "Isolate host vs Clean file").
  * **Layer 2 (Tactical)**: Llama-3-8B (Local) - Decomposes strategy into tasks (e.g., "Kill PID 1234", "Delete File X").
  * **Layer 3 (Execution)**: Qwen-2.5-Coder (Local) - Generates strict JSON tool calls for the agents.
* **Knowledge Base ("Direct Truth" State)**:
  * **SQLite (WAL Mode)**: Stores every tool output, scan result, and agent decision immediately. No in-memory "chat history" loss on crash.

### 2.2 Agent Roles (The Crew)

The system is composed of specialized agents that map to OrchBiter's "Form Executor" logic.

1. **The Scout (Threat Intelligence)**:
    * **Type**: `AsyncTool` (Low Resource)
    * **Responsibility**: Polls MalwareBazaar/Abuse.ch.
    * **OrchBiter Integration**: Runs continuously in background; minimal resource impact.
2. **The Hunter (Forensics)**:
    * **Type**: `ProcessTool` (High Resource)
    * **Responsibility**: Executes `clamscan`, `yara`, and `volatility` (memory).
    * **OrchBiter Integration**: Registered as a "Heavy Tool". The Arbiter *pauses* this agent when "The Brain" needs to run inference.
3. **The Brain (Analysis)**:
    * **Type**: **Layer 1 / Layer 2 LLM**
    * **Responsibility**: Interprets complex threats.
    * **OrchBiter Integration**: Receives priority access to VRAM.
4. **The Healer (Remediation)**:
    * **Type**: `ProcessTool` (Critical)
    * **Responsibility**: Executes remediation scripts.
    * **Safety**: Enforced via `FormExecutor` strict JSON schema validation.

## 3. Data Flow (OrchBiter Pipeline)

1. **Trigger**: `Watchdog` detects file change OR `Scout` finds new hash.
2. **Context Loading**: `ViewManager` projects relevant DB history into context.
3. **L1 Planning**: DeepSeek-R1 generates a strategic plan (`plan.yaml`).
4. **Arbitration**: Arbiter checks resources. If `Hunter` is scanning, it is PAUSED.
5. **L2/L3 Execution**: Agents execute tasks. Results written to SQLite.
6. **Resumption**: Arbiter RESUMES `Hunter` scan.

## 4. Technology Stack

* **Language**: Python 3.12+ (Asyncio)
* **Framework**: `orchbiter` (Local Package)
* **Persistence**: `SQLAlchemy` + SQLite (WAL)
* **Validation**: `Pydantic v2`
* **UI**: `Textual` (Terminal Dashboard showing Arbiter State)
