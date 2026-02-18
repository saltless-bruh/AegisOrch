# AegisOrch v3.0 - Development Roadmap (Tasks)

This document outlines the actionable tasks derived from the System Design and Requirements.

## Phase 1: Core Framework (OrchBiter Foundation) <!-- id: 0 -->

### 1.1 Project Structure & Async Setup <!-- id: 1 -->

- [ ] Initialize `aegisorch/orchestrator/` module structure.
- [ ] Define `Agent` protocol/base class using `pydantic` and `asyncio` (`agent.py`).
- [ ] Implement the `Orchestrator` main loop (`core.py`) with message routing.
- [ ] Create basic `main.py` entry point launching the Orchestrator with a dummy `EchoAgent`.

### 1.2 Knowledge Base (Data Layer) <!-- id: 2 -->

- [ ] Define `pydantic` models for:
  - `ThreatIntel` (IOCs, hashes).
  - `ScanResult` (file path, threat score).
  - `AgentMessage` (sender, content, type).
- [ ] Implement `DatabaseManager` using `sqlite3` (or `aiosqlite` if async required).
- [ ] Write migration script to initialize the SQLite DB schema.

## Phase 2: The Crew (Agent Implementation) <!-- id: 3 -->

### 2.1 The Scout Agent (Threat Intel) <!-- id: 4 -->

- [ ] Create `ScoutAgent` class inheriting from `Agent`.
- [ ] Implement `fetch_malware_bazaar` tool using `aiohttp` or `requests`.
- [ ] Add logic to update local DB with fetched hashes/IOCs.
- [ ] **Test**: Verify `Scout` successfully writes dummy IOCs to DB.

### 2.2 The Hunter Agent (Detection) <!-- id: 5 -->

- [ ] Create `HunterAgent` class.
- [ ] Port existing `AegisOrch` scanners (ClamAV, YARA) into `Hunter` tools.
- [ ] Implement **Memory Scanning** tool using `yara-python` on PIDs.
- [ ] Implement **Wait Logic**: Listen for `NewThreat` events from `Scout` to trigger scans.

### 2.3 The Brain Agent (Analysis) <!-- id: 6 -->

- [ ] Create `BrainAgent` class.
- [ ] Implement `heuristic_analysis` tool (Entropy, PE Header checks).
- [ ] (Optional) Add dummy LLM integration point for future expansion.
- [ ] Implement `generate_remediation_plan(scan_result)` logic.

## Phase 3: Loop & UI Integration <!-- id: 7 -->

### 3.1 Advanced CLI Dashboard <!-- id: 8 -->

- [ ] Create `rich` layout with panels for:
  - Active Agents status.
  - Live Logs / Alerts.
  - System Stats (CPU/RAM).
- [ ] Wire `Orchestrator` events to update the UI in real-time.

### 3.2 The Healer Agent (Remediation) <!-- id: 9 -->

- [ ] Create `HealerAgent` class.
- [ ] Implement `execute_plan` tool (e.g., `os.uunlink`, `psutil.Process.kill`).
- [ ] **Crucial**: Add interactive confirmation prompt in CLI before execution.

## Phase 4: Testing & Documentation <!-- id: 10 -->

- [ ] Write integration test: `Scout` fetches hash -> `Hunter` scans file -> `Brain` analyzes -> `Healer` suggests fix.
- [ ] Update `README.md` with new architecture details.
