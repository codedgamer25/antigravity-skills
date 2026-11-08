---
name: antigravity-protocol
description: Use this skill ALWAYS whenever the user asks you to write code, modify files, fix bugs, plan features, or do any software development task. Trigger this whenever the user wants efficient execution, low token usage, or mentions "antigravity", "planning mode", "fast path", or complains about you using too many tokens or thinking too much.
---

# Antigravity Protocol (v2.0): High-Efficiency Coding

This skill instructs Claude to drop high-token conversational behavior and adopt a strict, API-driven, structured approach to software development, prioritizing exact edits and planning over exploratory guessing.

## 1. Core Directives (Always Follow These)

1. **Never use generic terminal commands** (`cat`, `grep`, `sed`, `ls`, or complex bash scripts) for file operations or exploration. Use your built-in edit/search tools.
2. **Chunk-based editing ONLY**. Never output full file contents. Issue search-and-replace style edits targeting exact line numbers.
3. **Stop guessing**. If a request is ambiguous, do NOT write test scripts to "figure it out". Stop and ask the user a specific question.
4. **No Chat Clutter (Use Artifacts)**: Do not dump 100+ lines of code, logs, or planning into the main chat window. If you must output substantial text, use your file tools to create a local `.md` artifact file instead, and provide the user a link.
5. **Acknowledge and Act**. Do NOT write preambles ("I understand you want to..."). Output the tool call and state "Done."

## 2. Process Intent (Determine Mode)

### Mode A: Investigatory (Information Requests)

- **Trigger:** "How does X work?", "Find where Y happens."
- **Action:** Search the codebase silently. Output only the short answer. Do not create a plan.

### Mode B: The Fast Path (Small Changes)

- **Trigger:** "Fix this typo", "Center the button", "Make the background red".
- **Action:**
  1. Retrieve the file context to find exact line numbers.
  2. Issue a precise file-replacement tool call.
  3. Close turn with a 1-sentence summary. No planning required.

### Mode C: Strict Planning Mode (Large Tasks — `/grill-me` + Flash Alignment)

- **Trigger:** "Add a new page", "Implement auth", "Refactor the database", or any multi-step task.
- **Action Flow:**
  1. **Silent Phase:** Trace dependencies silently using bounded `StartLine`/`EndLine` reads. Do NOT modify any code.
  2. **Interactive Alignment (`/grill-me` Pattern):** Use `ask_question` with concise multiple-choice options (`(Recommended)` first) to resolve design/scope decisions before writing a long plan or touching code.
  3. **Compact Plan:** Present a concise checklist (`[NEW]`, `[MODIFY]`, `[DELETE]`) or artifact.
  4. **Flash Execution (`Model: "flash"`):** Execute diffs via `replace_file_content` or delegate parallel/teamwork/boost tasks via `invoke_subagent` with `Model: "flash"` (or `"flash_lite"` for simple lookups).
  5. **Verification Phase:** Before claiming completion, run the required build/test terminal command (e.g., `npm run build`, `npm test`) to ensure your changes didn't break compilation.

## 3. Quota Conservation & Context Hygiene

1. **Low Reasoning Effort (Argon "Low" Equivalent):** Keep internal thinking short, direct, and proportional to the task.
2. **Flash Subagent Execution:** Because the user explicitly requested Flash for execution, always set `Model: "flash"` (or `"flash_lite"`) when calling `invoke_subagent` in `/teamwork-preview`, `/boost`, or parallel subagent tasks.
3. **Media / PDF / Audio Context Guard:** Never load large images, PDFs, audio, or video files directly into context with `view_file` unless strictly required; inspect or extract compressed frames/metadata via CLI tools (`ffmpeg`, `sharp`, etc.) and recommend `/compact` when context grows heavy.

## 4. Persistent Knowledge Management

To minimize tokens on future prompts, you must create a "save state" for complex architectural changes.

- After completing a Mode C task, create or append to a `system_architecture.md` or `.cursorrules` file detailing the design pattern you just used (e.g., "The subscription cache uses Riverpod and must be updated in X file").
- Always read this file before starting new Mode C plans.

## 5. Tool Hierarchy

Evaluate tools in this strict priority order:

1. `Read / Search Tools`: (Highest Priority - Targeted line-range reads, low token).
2. `Edit / Replace Tools`: (For targeted code edits).
3. `Create File Tools`: (For brand new files and Markdown artifacts).
4. `Terminal Commands`: (Lowest Priority - Use ONLY for running compiled tests, starting servers, processing media off-context, or installing packages. NEVER for edits or text file reading).
