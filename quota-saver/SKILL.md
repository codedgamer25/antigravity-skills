---
name: quota-saver
description: >-
  Quota-conservation workflow combining low-effort reasoning, Flash subagent execution
  (for /teamwork-preview, /boost, and parallel tasks), strict media/PDF/audio context hygiene,
  and interactive /grill-me plan alignment using ask_question before code execution.
  Invoke with /quota-saver or whenever the user wants to stretch quota, plan with Flash, or run a low-token workflow.
---

# Quota-Saver & Flash Alignment Workflow (`/quota-saver`)

Follow this 4-pillar workflow to make Antigravity quota last significantly longer while keeping code quality high.

---

## Pillar 1: Low-Effort Reasoning Discipline (Argon "Low" Equivalent)
- Keep chain-of-thought brief, decisive, and action-oriented.
- Do not re-read files already in context or run exploratory shell scripts when a single targeted `view_file` (with `StartLine`/`EndLine`) suffices.
- Skip conversational filler; state actions and results concisely.

---

## Pillar 2: `/grill-me` Interactive Plan Alignment (Flash-First Planning)
Before writing code on any non-trivial or multi-step request:
1. **Quick Context Check**: Read only the relevant file headers or line ranges (`view_file` with `StartLine`/`EndLine`).
2. **Grill the Requirements (`ask_question`)**:
   - Call `ask_question` with 1–3 focused multiple-choice questions covering any architectural, UX, or scope trade-offs.
   - Always place the best option first, prefixed with `(Recommended)`.
3. **Lock the Compact Plan**:
   - Once the user answers, output a concise checklist (`[MODIFY]`, `[NEW]`, `[VERIFY]`) under 25 lines.

---

## Pillar 3: Flash Execution (`Model: "flash"`) for Subagents, `/boost`, and `/teamwork-preview`
- The user has explicitly authorized and requested `Model: "flash"` for subagents.
- Whenever invoking `invoke_subagent`:
  - Pass `Model: "flash"` for code execution, parallel edits, test runs, or multi-agent teamwork (`/teamwork-preview` / `/boost`).
  - Pass `Model: "flash_lite"` for lightweight file lookups or quick searches.
- For direct single-file edits, use `replace_file_content` on exact line ranges rather than rewriting whole files.

---

## Pillar 4: Strict Input Context Hygiene (Images, PDFs, Audio, Video)
- **Avoid Raw Binary Ingestion**: Never call `view_file` on large PDFs, audio files, videos, or uncompressed images unless visual inspection is explicitly required.
- **Process Media via CLI**: Use `ffprobe`/`ffmpeg` or lightweight scripts to inspect metadata, crop, resize, or extract single JPEG frames before viewing.
- **Slice Text Reads**: Always bound `view_file` calls with `StartLine` and `EndLine` (max 100–200 lines per call).
- **Context Compaction**: Recommend `/compact` whenever the session accumulates multiple completed tasks or media attachments.
