---
name: modern-web-dev-stack
description: Full-stack web development principles across modern HTML5, CSS3, JavaScript/TypeScript, React, Next.js, Node.js, REST/GraphQL APIs, responsive design, bundle optimization, and web performance (Core Web Vitals). Use when user asks for web app development, frontend architecture, backend API building, or performance tuning.
---

# Modern Full-Stack Web Development

Engineering standards for building scalable, responsive, accessible, and high-performance web applications.

## 1. Frontend Architecture & React / Next.js
- **Component Design:** Atomic component structuring, clear separation between presentation and data hooks, and strictly typed props with TypeScript.
- **State Management:** Local state (`useState`, `useReducer`) where possible; URL state for shareable filters/pagination; lightweight global stores (Zustand) for application-wide states.
- **Performance & Core Web Vitals:** Optimize LCP (image priorities, WebP/AVIF formats), minimize CLS (reserved dimensions), and reduce INP (debounced handlers, lazy loading).

## 2. API Design & Backend Resilience
- **RESTful Standards:** Predictable HTTP verbs, standard status codes (200, 201, 400, 401, 403, 404, 500), and consistent JSON error envelopes.
- **Database Query Efficiency:** Avoid N+1 query patterns; use indexing on filtered columns, connection pooling, and transaction isolation where required.
- **Security:** CSRF tokens, sanitization against XSS, parameterized queries for SQL, and rate limiting on sensitive routes.
