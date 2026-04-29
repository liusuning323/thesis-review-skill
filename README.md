# Academic Thesis Multi-Round Review Framework

A production-tested automation workflow for reviewing and revising academic theses (especially systematic literature reviews) using multi-agent collaboration.

## What This Is

A 5-round review framework that orchestrates multiple AI agents to review, critique, and revise an academic thesis from initial draft to submission-ready final manuscript. Developed and validated on a 36,400-word Master's thesis in education at a New Zealand university.

## Key Results (From Production Use)

| Metric | Value |
|--------|-------|
| Thesis length | ~36,400 words, 114 pages |
| Review rounds | 5 |
| Issues found & fixed | 100+ |
| Total agent-hours | ~28 |
| Compilation status | 0 errors, 0 undefined refs |
| Final verdict | READY FOR SUBMISSION |

## What's Included

- **`skill_thesis_review.md`** — Complete workflow: Phase 0→5, Agent prompt templates, checklists, token optimization strategies
- **`retrospective.md`** — 12 real problems encountered and solved, 19 lessons learned, applicable to any LLM-assisted academic writing project

## Quick Start

```bash
# 1. Read the skill document
cat skill_thesis_review.md

# 2. Apply to your thesis by replacing:
#    - File paths
#    - Theoretical framework (Biesta → yours)
#    - Review scholar perspectives (Sturm, Ng → your field's scholars)
#    - Citation format (APA 7th → yours)

# 3. Run Phase 0 (preparation)
# 4. Launch Round 1 reviews (3 parallel agents)
# 5. Iterate through Rounds 2→5
```

## Prerequisites

- Claude Code or compatible multi-agent LLM environment
- LaTeX distribution (xelatex for CJK support)
- Python 3.x (for assembly/conversion scripts)
- macOS Mail.app (for email delivery — optional)

## License

MIT
