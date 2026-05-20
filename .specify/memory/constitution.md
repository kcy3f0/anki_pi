<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0
- List of modified principles:
  - VI. Data Continuity & Backward Compatibility (Added)
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md (✅ updated)
- Follow-up TODOs: None
-->

# Anki Pi Constitution

## Core Principles

### I. Functional Integrity
Ensure no existing functionality is broken or missing during the refactoring process. Any behavioral change must be explicitly justified, documented, and approved. Preservation of existing features is the highest priority.

### II. Clean Code & Maintainability
Code must pursue high readability and maintainability, strictly following DRY (Don't Repeat Yourself) and SOLID principles. Favor composition over inheritance, keep functions focused (Single Responsibility), and ensure interfaces are stable.

### III. Testing Discipline
Refactored code must be accompanied by complete unit tests. Strive for high test coverage to ensure long-term stability and prevent regressions. Tests must verify both positive scenarios and edge cases.

### IV. Lightweight & Minimalist Architecture
Maintain a clean and lightweight architecture suitable for resource-constrained environments like Raspberry Pi. Strictly forbid the introduction of unexplained third-party dependency libraries. Every dependency must have a clear, documented rationale.

### V. Incremental Refactoring
Refactor in small, manageable increments. Validate each step with existing and new tests before proceeding to the next phase. Avoid massive, all-at-once changes that are difficult to review and debug.

### VI. Data Continuity & Backward Compatibility
The existing `flashcards.db` SQLite database must be seamlessly reusable by the refactored application. If schema changes are absolutely necessary, an automated, non-destructive migration script must be provided to update the existing database without data loss.

## Technology Stack & Constraints
- **Backend**: Python 3.x, Flask
- **Frontend**: Vanilla HTML/CSS/JavaScript (Strictly no build step or complex frameworks)
- **Database**: SQLite
- **Scheduling**: FSRS (Free Spaced Repetition Scheduler) Algorithm
- **Environment**: Optimized for Raspberry Pi and Intranet usage.

## Quality Gates & Review
- **Regression Check**: All existing tests must pass before and after refactoring.
- **Test Mandatory**: New unit tests are required for all refactored or added modules.
- **SOLID/DRY Review**: Code reviews must specifically check for adherence to these principles.
- **Dependency Audit**: Any new dependency must be justified in the implementation plan.
- **Data Migration**: Any database schema change must be accompanied by a non-destructive migration script.

## Governance
- This Constitution supersedes all other development practices within the Anki Pi project.
- Amendments require a formal rationale and must be documented in the version history.
- All Pull Requests and Implementation Plans must be verified against these principles.
- Use `README.md` and `GEMINI.md` for project-specific runtime development guidance.
- All PRs/reviews must verify compliance with the Core Principles.
- Technical debt or complexity must be justified and tracked.
- Use .specify templates to maintain consistency across the project.

**Version**: 1.1.0 | **Ratified**: 2026-05-19 | **Last Amended**: 2026-05-19
