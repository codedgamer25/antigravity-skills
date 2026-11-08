---
name: cybersecurity-expert
description: Perform cybersecurity audits, vulnerability scanning, security posture reviews, penetration testing guidance, OWASP Top 10 mitigation, secure coding audits, and threat modeling. Use whenever the user asks for cybersecurity advice, hardening, security assessments, or vulnerability checks.
---

# Cybersecurity & Threat Assessment Skill

Expert toolkit and systematic methodology for evaluating, auditing, and hardening software systems, infrastructure, and web applications.

## 1. Application Security (AppSec) & Secure Coding
- **OWASP Top 10 Mitigation:** Check for SQLi, XSS, CSRF, SSRF, Broken Access Control, Security Misconfiguration, Insecure Deserialization, Cryptographic Failures, and Vulnerable Components.
- **Dependency Auditing:** Inspect `package.json`, `requirements.txt`, `pom.xml`, and lockfiles for known CVEs.
- **Secrets Management:** Ensure zero hardcoded API keys, tokens, SSH keys, or connection strings in code or version control.

## 2. Infrastructure & Network Defense
- **Hardening Protocols:** Enforce TLS 1.3, strict CORS policies, CSP (Content Security Policy), HSTS, and X-Content-Type-Options.
- **Authentication & RBAC:** Implement least-privilege principles, secure JWT storage (HttpOnly/Secure cookies), and multi-factor auth strategies.
- **Input Validation & Sanitization:** Strict whitelisting, parametrized queries, and context-aware output encoding.

## 3. Incident Response & Threat Modeling
- STRIDE Threat Modeling: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege.
- Audit logging: Tamper-evident logging without recording sensitive PII.
