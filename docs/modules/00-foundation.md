# Module 0 — Foundation

## 1. Requirements
Establish a production-grade skeleton before any feature code: enforceable
architecture, quality gates, decision records, docs-as-code. Everything later
builds on these rails.

## 2. Architecture
Clean architecture with domain-agnostic kernel and pluggable domains
(ADR-0002). Local-first, Azure-ready runtime strategy (ADR-0003).
Docs-as-code with Mermaid (ADR-0004). See `docs/architecture/c4-level1-context.md`.

## 3. Design rationale
- `src/` layout: forces installed-package imports; prevents accidental
  relative-path hacks that break in containers.
- Kernel/domains split instead of a single `domain/` package: makes the
  "platform, not football app" claim structurally true.
- Ruff (lint+format) over black+flake8+isort: one tool, one config, faster.
- mypy `strict` from day zero: retrofitting strictness is far costlier.
- Makefile as single entry point: humans and CI run the identical gate.

## 4. Implementation
Scaffold packages with responsibility docstrings, `pyproject.toml`
(hatchling, ruff, mypy strict, pytest+coverage), pre-commit hooks,
Makefile, ADRs 0001–0004 + template, module-report template, CONTRIBUTING,
README with architecture diagram. Git repo initialized on `main`.

## 5. Testing
Smoke tests: package version + every layer imports. Verified in-session:
imports, byte-compilation, YAML/TOML validity. `make check` (ruff/mypy/pytest)
must be run on the host — sandbox had no PyPI access this session.

## 6. Future improvements
- import-linter contract to mechanically enforce layer rules (Module 1)
- CI workflow running `make check` (Module 9)
- CODEOWNERS + PR template when collaboration starts

---

## Portfolio annex
- **Skills demonstrated:** clean architecture, ADR practice, Python packaging,
  static analysis tooling, docs-as-code, engineering governance.
- **Interview questions prepared:** "Explain clean architecture / dependency
  rule." "How do you make a codebase reusable across domains?" "How do you
  enforce code quality in a team?" "What is an ADR and why?"
- **Enterprise concepts applied:** separation of concerns, dependency
  inversion, quality gates, Definition of Done, decision governance.
- **Resume bullets:**
  - "Architected a domain-agnostic decision-intelligence platform using clean
    architecture; football analytics as reference implementation, portable to
    manufacturing/finance via pluggable domain packages."
  - "Established enterprise engineering governance: ADRs, strict typing,
    automated quality gates, docs-as-code C4 diagrams."
- **LinkedIn update:** "Kicked off FootballIQ Enterprise — an AI decision-
  intelligence platform. Module 0: clean architecture skeleton with a
  domain-agnostic kernel, ADRs, and fully automated quality gates. Building
  in public; architecture thread to follow."
