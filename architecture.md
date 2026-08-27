# Implementation Blueprint

## Core bounded agents

Use a small number of narrowly-scoped agents:

- `Parsing agent`: reads Docling output and prepares document chunks with provenance
- `Extraction agent`: extracts candidate and JD facts into JSON
- `Review assistant`: explains extracted values to the human reviewer and highlights low-confidence fields
- `Recommendation agent`: converts deterministic results into HR-facing rationale

Do not let any agent directly decide hiring eligibility without rules and scoring output.

## State machine

```text
uploaded
-> parsed
-> extracted
-> pending_human_review
-> normalized
-> scored
-> recommended
-> closed
```

## Human-in-the-loop checkpoints

### Checkpoint 1: Extraction verification

Reviewer validates:

- name
- education
- employment periods
- skill durations
- certifications
- unexplained gaps

### Checkpoint 2: Final decision review

Reviewer validates:

- hard-rule failures
- score breakdown
- AI explanation
- final disposition

## API contract

### `POST /screen`

Input:

- candidate profile with evidence-backed extracted fields
- JD requirements
- mandatory rules

Output:

- rule results
- score breakdown
- recommendation
- explanation

## Storage model

You will likely want these tables:

- `documents`
- `document_blocks`
- `candidate_profiles`
- `job_requirements`
- `extracted_fields`
- `review_actions`
- `rulesets`
- `screening_runs`
- `rule_results`
- `score_breakdowns`

## Rule types to support first

- `skill_min_months`
- `skill_required`
- `total_experience_min_months`
- `education_required`
- `location_required`
- `notice_period_max_days`
- `work_authorization_required`
- `domain_required`

## RAG guidance

Use retrieval only for reference corpora such as:

- skill synonym dictionary
- title normalization map
- company/domain taxonomy
- internal hiring rubric library

Do not use retrieval to decide numeric thresholds if they are already provided in the JD or rule set.

## Downstream outputs

The recommendation response contains bounded downstream artifacts: ranked
strengths, concerns, and factual resume flags; structured interview questions
anchored to matched skills and failed rules; and a draft-only communication
that requires human verification before sending.

`POST /screen/batch` reuses the same reviewed candidate schema and rubric for
multi-candidate workflows, then sorts by deterministic final score. It does not
call an LLM to rank candidates and does not send communications.
