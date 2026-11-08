---
name: excel-advanced-analytics
description: Advanced Microsoft Excel and Google Sheets automation, financial modeling, dynamic array formulas (XLOOKUP, FILTER, UNIQUE, LAMBDA), Power Query (M code), Pivot tables, VBA macros, and Python-in-Excel automation. Use when user asks for Excel formulas, spreadsheet models, macro automation, or financial sheet architecture.
---

# Advanced Excel & Spreadsheet Automation

Operational guidance for building bulletproof, audit-ready financial models, reporting templates, and spreadsheet automation workflows.

## 1. Modern Formula Architecture
- **Dynamic Arrays:** Use `FILTER()`, `UNIQUE()`, `SORT()`, and `SORTBY()` to eliminate manual formula copying across rows.
- **Lookup & References:** Discard `VLOOKUP`/`HLOOKUP` in favor of two-way `XLOOKUP()` and `INDEX(..., XMATCH())` with explicit missing-value fallbacks.
- **Custom Functions:** Author reusable `LAMBDA()` helpers and `LET()` blocks to encapsulate complex multi-step computations and enhance readability.

## 2. Power Query (M) & Automation
- **ETL Pipelines:** Load raw CSVs/databases into Power Query; clean headers, unpivot crosstab data, enforce data typing, and merge lookups upstream.
- **Macro & Scripting:** Clean VBA modules with explicit variable declarations (`Option Explicit`), disabled screen updating for bulk tasks (`Application.ScreenUpdating = False`), or Python-in-Excel scripting.
- **Error Handling & Auditability:** Wrap unstable lookups in `IFERROR()` or `IFNA()` with meaningful audit markers. Avoid circular references and hardcoded constants inside calculation formulas.
