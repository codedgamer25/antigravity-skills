---
name: ai-automation-workflows
description: Design and implement end-to-end AI automation workflows, LLM agents, tool integrations, web scraping, multi-agent pipelines, automated trigger flows, and API integrations using LangChain, CrewAI, AutoGen, Make, and Zapier patterns. Use when user asks to automate business processes, build autonomous agents, or integrate AI into workflows.
---

# AI Automation & Agentic Pipelines

Architectural patterns and operational standards for building autonomous, resilient AI-driven business workflows.

## 1. Multi-Agent & Workflow Orchestration
- **Task Decomposition:** Break monolithic objectives into explicit sequential or parallel sub-tasks with well-defined inputs and expected schemas.
- **State Management & Memory:** Use typed state schemas (e.g., Pydantic models). Persist operational state in external storage to survive pipeline restarts.
- **Human-in-the-Loop (HITL):** Gate high-risk actions (financial charges, external emails, bulk data mutation) behind approval steps.

## 2. Tool Calling & External APIs
- **Tool Schema Rigor:** Provide unambiguous tool descriptions, precise input boundaries, and robust exception catchers.
- **Idempotency & Rollbacks:** Ensure automation webhooks and API calls can be safely retried on network drops without duplicate execution.
- **Rate Limit & Backoff:** Implement exponential jitter backoff for LLM API calls and third-party SaaS rate limits.
