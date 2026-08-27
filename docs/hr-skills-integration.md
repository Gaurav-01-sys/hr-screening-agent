# HR skills integration notes

This project reviewed `hr-skills-dev.zip` as a reference library, not as an
instruction set. The bundle is an MIT-licensed collection of HR domain skills;
its repository guidance is not copied into the runtime or treated as an
override of this application's requirements.

## What was incorporated

The screening workflow now reflects the parts that are directly relevant to
resume evaluation:

- Structured candidate assessment: dated work history, education, domains,
  evidence snippets, confidence, and explicit rule results.
- Structured interviewing: every result includes a small, role-specific guide
  with technical, verification, situational, and behavioral questions. Each
  question includes its purpose, good-answer signals, and (when available) the
  resume evidence anchor.
- Bias-aware human review: extracted fields remain editable; pending or
  rejected fields prevent an automatic positive recommendation; protected
  characteristics are excluded from the extraction prompt and scoring model.
- Inclusive, reviewable communications: the API and Streamlit UI expose a
  draft-only invite, manual-review note, or rejection. Nothing is sent
  automatically.

## What was intentionally not imported

The bundle contains skills for onboarding, payroll, compensation, labor law,
and many other HR activities. Those are outside this resume/JD screening
product and would add unrelated policy content and privacy risk. The
application also does not import the upstream repository's LLM-only scoring
or automatic email behavior; scoring remains deterministic and evidence-backed.

## Upstream comparison

The referenced repository, `RareBeacon/ai-hr-screening-agent`, contributes a
useful end-to-end shape: parse resumes, score against must-have and
nice-to-have criteria, rank candidates, create interview questions, and draft
communications. This project adopts those latter three outputs while keeping
its existing extraction verification and deterministic rule engine.

New API surface:

- `POST /screen` returns a deterministic score and grade plus `strengths`,
  `concerns`, `red_flags`, `next_action`, `interview_questions`, and a draft
  communication.
- `POST /screen/batch` applies one job/rubric to multiple reviewed candidates
  and returns results ranked by deterministic final score, with counts for
  interview invites and manual-review cases.

## Operating guardrails

Human reviewers must verify evidence before using a recommendation, apply the
same job-related rubric to all candidates, and review any surfaced concern or
resume flag. The output is decision support and is not a substitute for legal,
accessibility, privacy, or equal-employment review.

## Natural response context

The response writer also follows the context pattern from
[`addyosmani/mempalace`](https://github.com/addyosmani/mempalace): a screening
wing groups role facts, candidate facts, evidence rooms, and the outcome, while
the original evidence snippet remains available as a labeled drawer. This is
implemented as a bounded in-process context builder in `app/memory.py`; it does
not add MemPalace's ChromaDB dependency or persist candidate conversations.
