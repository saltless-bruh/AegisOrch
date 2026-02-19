# **Project Proposal: OrchBiter (Orchestration Arbiter)**

**Date**: February 2026  
**Status**: Proposal for Open Source Release  
**Project Name**: OrchBiter (formerly "Orches AI")  
**Tagline**: The Operating System for Local Agents. A hardware-aware orchestration engine for autonomous systems.

## **1. Executive Summary**

**OrchBiter** is a proposed open-source Python framework designed to orchestrate hierarchical AI agents on resource-constrained hardware, specifically targeting high-performance consumer workstations (e.g., Ryzen/RTX configurations).

Existing agentic frameworks such as LangChain, CrewAI, and AutoGen operate under the assumption of unlimited, elastic cloud compute. They spawn processes and make API calls asynchronously, ignorant of the host machine's physical limitations. **OrchBiter** fundamentally rejects this "cloud assumption." It introduces **kernel-level resource arbitration**, allowing heavy local LLMs (like DeepSeek-R1) to coexist with intensive computational tasks—such as video encoding, large-scale compilation, or security scanning—without causing system instability or VRAM thrashing.

>**Origin & Validation**: The core components of OrchBiter are not theoretical. They were designed, stress-tested, and validated inside **AAPt (AI Auto Penetration Testing)**, a production autonomous security research tool developed on Linux (Pop\_OS!). AAPt required running a local LLM alongside CPU-intensive hacking tools (`nuclei`, `ffmpeg`, custom scanners) on a single consumer GPU (RTX 3060 12GB) without crashing or thrashing. The orchestration engine that solved that problem *is* OrchBiter. This project extracts and generalizes that battle-tested skeleton, decoupling it from offensive security logic to provide a robust foundation for any high-stakes, local-first agentic workflow.

## **2. Problem Statement: The "Cloud Assumption" Gap**

The current landscape of AI orchestration frameworks suffers from three critical limitations when deployed on local, single-node hardware:

1. **Resource Ignorance (The "Thrashing" Problem)**:  
    Standard frameworks treat tool execution as "fire-and-forget." They will happily launch a CPU-intensive subprocess (e.g., `ffmpeg`, `nuclei`, `make -j`) while simultaneously trying to load a 32GB LLM into VRAM. On local hardware, this leads to immediate resource contention. The OS pages the model to system RAM, causing inference latency to spike from seconds to minutes (thrashing), or the system freezes entirely due to bus saturation.
2. **State Fragility & Race Conditions**:  
    Most frameworks rely on ephemeral "context windows" or in-memory chat history to maintain state. In long-running autonomous operations, this is fragile. If the Python process crashes, the agent's "brain" is wiped. Furthermore, asynchronous agents reading/writing to purely in-memory structures often encounter race conditions.
3. **Lack of Determinism in Control Flow**:  
    Many multi-agent frameworks rely on "conversational" loops where agents chat to resolve tasks. While flexible, this is non-deterministic and prone to infinite "chat loops." For systems engineering, security, and data science tasks, this lack of rigor is unacceptable.

**Market Analysis:**

* *LangChain/CrewAI*: Excellent for cloud-native/SAAS applications where asyncio is the only constraint.
* *AutoPentester/Academic Research*: Often focus on high-level strategy but lack rigorous software engineering standards (e.g., Pydantic validation, error handling).
* *OrchBiter*: Fills the gap for **Local, Resource-Constrained, High-Reliability** orchestration—essentially acting as an "Operating System for Agents."

## **3. Core Solution: The OrchBiter Architecture**

OrchBiter is defined by three architectural pillars designed to enforce stability and predictability on local hardware.

### **3.1. Kernel-Level Hardware Arbiter**

The framework acts as a specialized scheduler (Arbiter) for AI workloads, managing the contention between "Thinking" (Inference) and "Doing" (Tool Execution).

* **Mechanism**: The `HardwareArbiter` class utilizes `SIGSTOP` and `SIGCONT` signals to manage process life-cycles at the kernel level. It explicitly handles **Process Trees** (using process groups) to ensure that pausing a parent tool also pauses its resource-hungry children.
* **Arbitration Logic**:
  * **Inference Priority**: When a Local LLM (e.g., DeepSeek-R1) needs to perform reasoning, the Arbiter checks for active "Heavy Tools."
  * **Preemption**: If a heavy tool is running, the Arbiter pauses it (`SIGSTOP`), granting the LLM exclusive access to VRAM and memory bandwidth. Once inference is complete, the tool is resumed (`SIGCONT`).
  * **Deadlock Prevention**: The Arbiter includes logic to detect dependency chains (e.g., if the LLM is waiting for the tool's output stream, it must NOT pause the tool).
* **Result**: Prevents VRAM eviction and system freezing. A user can run a background task consuming 100% of the CPU, and the agent can seamlessly interrupt it to "think," then resume it.

**Arbiter in Action — Example Log:**

```text
[Arbiter] LLM inference requested.  Active heavy tools: [ffmpeg PID 4821]
[Arbiter] Dependency check passed — LLM not waiting on tool output stream.
[Arbiter] Sending SIGSTOP to process group 4821... OK
[VRAM]    Usage: 9.8 GB → 6.1 GB (headroom restored)
[LLM]     Inference complete in 2.4s. Output: Strategy.json
[Arbiter] Sending SIGCONT to process group 4821. Resuming heavy tools.
[ffmpeg]  ...encoding resumed at frame 2103/5400 (38%)
```

*A user running a 4K video encode in the background experiences zero interruption. The encoder silently pauses for 2.4 seconds and resumes — invisible to the user.*

### **3.2. Hierarchical "Layered" Routing**

OrchBiter enforces a strict military-style command hierarchy. The **default and primary configuration is Fully Local** — no cloud dependency, no external API calls, complete data sovereignty. A Hybrid configuration is available as an optional performance enhancement.

#### **Configuration A: The Fully Local Stack (Default — Privacy/Offline/Sovereign)**

> *This is the core identity of OrchBiter. Designed and validated on a single RTX 3060 12GB.*

* **Layer 1 (Strategic Planning)**: DeepSeek-R1-Distill-32B (Local). High reasoning capability, high VRAM cost — only activated when needed.
* **Layer 2 (Tactical Decomposition)**: Llama-3-8B-Instruct (Local). Fast task breakdown; loaded while L1 is offloaded.
* **Layer 3 (Execution)**: Qwen-2.5-Coder-7B or Gemma-2-2B (Local). Optimized for function calling; minimal VRAM footprint.

#### **Configuration B: The Hybrid Stack (Optional — Performance)**

* **Layer 1 (Strategic Planning)**: DeepSeek-R1 (Local or API). Analyzes scope, generates `plan.yaml`.
* **Layer 2 (Tactical Decomposition)**: Gemini Flash (API). Fast, cost-efficient breakdown of objectives.
* **Layer 3 (Execution)**: Claude Haiku (API). "Doers, not thinkers." Executes strict JSON schemas via MCP.

**Complexity-Based Escape Hatch**: If Layer 3 fails repeatedly or encounters an unknown state, it escalates to Layer 2. If Layer 2 cannot replan, it escalates to Layer 1 for a strategic pivot. **Model Hot-Swapping**: The Arbiter manages VRAM by offloading the current layer's model to system RAM before loading the next, preventing out-of-memory errors on constrained hardware.

### **3.3. "Direct Truth" State Management**

OrchBiter abandons the probabilistic nature of vector stores for the deterministic reliability of SQL.

* **Architecture**: **"Direct Truth"** strategy. No "write-behind" buffering. Every tool result and plan update is persisted immediately to **SQLite (WAL Mode)**.
* **Context Projection (ViewManager)**: The agent does not read the raw database. A `ViewManager` class query-optimizes and heuristic-ranks data (e.g., "Top 5 critical findings") to project a relevant "View" into the context window.
* **Benefit**: Zero data loss on crash. The database remains the single source of truth.

## **4. Technical Specifications**

### **4.1 Component Architecture**

The framework will be released as a modular PyPI package (`src/orchbiter`).

| Module | Function | Status |
| :---- | :---- | :---- |
| `core.arbiter` | The `HardwareArbiter` class. Manages thread locks, process signaling (`psutil`), and VRAM monitoring. Distinguishes between `ProcessTool` (Arbiter-managed) and `AsyncTool` (standard async). | **Ready for Extraction** |
| `core.router` | The `LayeredRouter` logic. Implements L1/L2/L3 selection and supports Model Hot-Swapping (unloading L1 to load L2 if VRAM is tight). | **Ready for Extraction** |
| `core.forms` | `FormExecutor` logic. Uses Pydantic models to generate JSON schemas for LLMs, enforcing strict type-checking *before* execution. | **Ready for Extraction** |
| `core.graph` | `TaskDAG` and `WorkflowEngine`. Manages dependency resolution and allows for dynamic phase injection ("Intervention Protocol"). | **Ready for Extraction** |
| `interfaces.mcp` | A robust client implementation for the Model Context Protocol (MCP), enabling standard integration with external tools (Databases, Git, Filesystem). | **Ready for Extraction** |

### **4.2 Tech Stack Choices**

* **Language**: **Python 3.12+**. Native `asyncio` support is critical for high-concurrency orchestration.
* **OS Support**: **Linux First** (Pop\_OS!, Ubuntu, Arch). macOS is secondary. Windows support is planned for v2.0 (native `SIGSTOP`/`SIGCONT` do not exist on Win32; WSL2 is the recommended workaround in the interim).
* **Validation**: **Pydantic v2**. Strict data validation for all tool inputs/outputs.
* **Persistence**: **SQLAlchemy + SQLite (WAL mode)**. Serverless, zero-config, concurrent-safe.
* **UI**: **Textual**. Terminal-based dashboard to visualize agent thought processes and Arbiter state.
* **Process & Resource Monitoring**: **`psutil`**. Cross-platform library for querying CPU, RAM, VRAM utilization and managing process lifecycles (required by `HardwareArbiter`).
* **User Activity Detection**: **`evdev`** (Linux). Monitors Human Interface Devices (keyboard/mouse) to detect user activity and trigger the Arbiter's Freeze/Resume cycle. This is what allows the system to yield to the user transparently.

## **5. Comparison vs. Industry Standards**

| Feature | Standard (LangChain/CrewAI) | OrchBiter | Why It Matters |
| :---- | :---- | :---- | :---- |
| **Compute Assumption** | Cloud / Unlimited API | **Local / Constrained** | Prevents crashes on consumer hardware. |
| **Resource Control** | None (Async fire-and-forget) | **Kernel-Level Arbitration** | Allows concurrent running of Heavy AI + Heavy Tools. |
| **State Persistence** | In-Memory / Vector Store | **SQL "Direct Truth"** | Guarantees recovery after crashes; auditable history. |
| **Control Flow** | Conversational / Chat Loops | **Hierarchical Form Execution** | Deterministic behavior; easier to debug. |
| **Agent Persona** | Fixed Roleplay / Assistant | **Configurable via `PromptManager`** | Domain-agnostic; adapts to any technical workflow. |
| **Tool Types** | APIs Only | **Process & API Hybrid** | Manages actual OS processes (compilers, scanners). |

## **6. Implementation Plan**

### **Phase 1: The "Skeleton" Extraction (Weeks 1-2)**

* **Objective**: Isolate the generic orchestration logic.
* **Tasks**:
    1. Extract `HardwareArbiter`: Implement `ProcessTool` vs `AsyncTool` distinction. Ensure generic `requires_resource_lock` attribute works.
    2. Extract `LayeredRouter`: Implement the "Fully Local" vs "Hybrid" configuration toggle.
    3. Create `BaseTool`: Pydantic-based abstract base class.
    4. Establish Repository: `src/orchbiter` layout.

### **Phase 2: Sanitization & Generalization (Week 3)**

* **Objective**: Ensure the framework is domain-agnostic and safe.
* **Tasks**:
    1. **Prompt Abstraction**: Replace hardcoded security personas with a configurable `PromptManager`.
    2. **Demonstration**: Create a "Hello World" example:
        * *Scenario*: Agent transcodes a video (High CPU `ffmpeg`) and summarizes a large text corpus (High VRAM `LLM`) simultaneously.
        * *Outcome*: Logs show video encoder pausing for inference and resuming automatically.
    3. **Testing**: Unit tests for router fallbacks, arbiter locks, and process group signaling.

### **Phase 3: Open Source Release (Week 4)**

* **Objective**: Public launch.
* **Tasks**:
    1. **Documentation**: Draft `README.md` containing a **GIF of `htop`** showing the Arbiter in action (CPU spiking, pausing, resuming). This is the key "Visual Proof."
    2. **Licensing**: Apache 2.0 License.
    3. **Distribution**: PyPI package `orchbiter` and GitHub release.

## **7. Strategic Positioning**

**Value Proposition**:  
"OrchBiter is the only orchestration framework that treats your local hardware as a finite resource. It doesn't just run agents; it *schedules* them like an Operating System."

**Target Audience**:

1. **Systems & DevOps Engineers**: Builders of automation tools that require "break-glass" intervention and strict state management.
2. **Edge AI Developers**: Running agents on Jetson/Raspberry Pi where resources are scarce.
3. **Local LLM Researchers**: Users experimenting with local models (DeepSeek, Llama 3) who need to manage VRAM contention effectively.

## **8. Conclusion**

OrchBiter transforms a proprietary, high-risk security tool into a general-purpose public utility. By solving the "local resource contention" problem, it carves out a unique niche that major cloud-native frameworks have ignored. It effectively bridges the gap between high-level AI reasoning and low-level kernel resource management to enable true local autonomy.
