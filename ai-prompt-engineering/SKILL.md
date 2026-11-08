---
name: ai-prompt-engineering
description: Systematic prompt engineering frameworks (ReAct, Chain of Thought, Few-Shot, System Metaprompts), model-specific parameter tuning (temperature, top_p), guardrail validation, structured JSON outputs, and LLM steering. Use when user asks to craft, optimize, evaluate, or debug LLM prompts and agent instructions.
---

# Advanced Prompt Engineering & Steering

Protocols for crafting deterministic, high-efficiency, hallucination-resistant prompts for frontier LLMs.

## 1. Prompt Architecture & Structure
- **Role & Persona:** Establish precise behavioral boundaries and technical competencies upfront.
- **Context & Constraints:** Declare explicit constraints (e.g., negative constraints, formatting rules, token conservation) before the main instruction.
- **Few-Shot Demonstrations:** Provide 2-3 canonical input/output pairs covering normal operation and edge cases.
- **Delimiters:** Use XML tags (`<context>`, `<instructions>`, `<input>`) or Markdown fences to separate system directives from untrusted user inputs.

## 2. Reasoning & Reliability Techniques
- **Chain of Thought (CoT):** Direct the model to generate its reasoning step-by-step prior to outputting its final conclusion.
- **Structured Schema Enforcement:** Enforce strict JSON or Pydantic output schemas with explicit validation rules.
- **Evaluation & Red-Teaming:** Test prompts against prompt injection,jailbreaks, role confusion, and ambiguous phrasing.
