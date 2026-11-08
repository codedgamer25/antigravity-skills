---
name: ui-ux-design-systems
description: Principles for product UI/UX architecture, design systems, ergonomic interaction design, information hierarchy, typography scales, micro-interactions, responsive grids, and Figma-to-code conversions. Use when user asks for UI/UX advice, user experience auditing, design token architecture, or wireframe layouts.
---

# UI/UX Product Design Systems

Standards for shipping modern, refined user interfaces that balance brand expression with cognitive ergonomics.

## 1. Information Architecture & Visual Hierarchy
- **Typography Scale:** Consistent geometric type scales (12, 14, 16, 20, 24, 32, 48, 64), disciplined line heights (`1.1` for headlines, `1.5` for body), and intentional letter-spacing.
- **Surface Elevation:** Layered neutral elevation models using multi-step ambient shadows rather than harsh dark outlines or arbitrary colors.
- **Whitespace & Rhythm:** 4px/8px modular grid alignment. Never crowd high-density controls; group related items with distinct boundary padding.

## 2. Interaction Ergonomics & States
- **State Completeness:** Every interactive component must define default, hover, focus-visible, active/pressed, disabled, loading, and skeleton states.
- **Motion Principles:** Restrained micro-interactions (<200ms) with ease-out or spring transitions. Avoid extraneous animations that delay user intent.
- **Accessibility & Contrast:** WCAG 2.1 AA minimum compliance (4.5:1 text contrast), distinct keyboard focus indicators, and clear semantic labels.
