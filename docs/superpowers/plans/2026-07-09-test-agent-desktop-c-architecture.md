# Test Agent Desktop C Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local PySide6 desktop MVP with the full PRD architecture shape: UI, application service, document pipeline, agent orchestration, RAG, skill runtime, model config, and export service.

**Architecture:** Keep the UI thin and route actions through `ApplicationService`. Core behavior lives in focused service modules with dataclass models. LangGraph, vector DB, and real LLM calls are represented by replaceable adapters so the app can start locally before heavy dependencies are configured.

**Tech Stack:** Python 3.10+, PySide6, PyYAML, python-docx, PyMuPDF, openpyxl, pytest.

---

### Task 1: Project Skeleton And Tests

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `app/__init__.py`
- Create: `app/models/entities.py`
- Create: `tests/test_config_manager.py`
- Create: `tests/test_document_pipeline.py`
- Create: `tests/test_agent_orchestrator.py`
- Create: `tests/test_skill_runtime.py`
- Create: `tests/test_export_service.py`

- [x] Write failing tests for config masking, markdown conversion, rule-based generation, skill loading, and export.
- [x] Run tests and confirm they fail because modules do not exist.

### Task 2: Core Service Implementation

**Files:**
- Create: `app/config/config_manager.py`
- Create: `app/documents/pipeline.py`
- Create: `app/agent/orchestrator.py`
- Create: `app/rag/engine.py`
- Create: `app/skills/runtime.py`
- Create: `app/services/export_service.py`
- Create: `app/services/application_service.py`
- Create: `skills/generate_test_cases/skill.yaml`
- Create: `skills/generate_test_cases/prompt.md`
- Create: `skills/generate_test_cases/handler.py`

- [x] Implement minimal production code to satisfy the tests.
- [x] Run the focused pytest suite and keep it green.

### Task 3: Desktop UI

**Files:**
- Create: `app/desktop/main_window.py`
- Create: `app/desktop/__main__.py`

- [x] Build a PySide6 main window matching the PRD layout: top bar, navigation, upload/config panels, supplemental requirement input, action buttons, result tabs, and RAG sidebar.
- [x] Wire UI actions to `ApplicationService`.
- [x] Keep startup import-safe when PySide6 is not installed.

### Task 4: Verification

**Files:**
- Modify: `README.md`

- [x] Run `python -m pytest`.
- [x] Run a CLI smoke script through `ApplicationService`.
- [x] Run `python -m compileall app`.
- [x] Document local startup commands and dependency notes.
