# HR Screening frontend

The frontend is a Vite + React 19 + TypeScript workbench for the existing
FastAPI screening service. It keeps the three phases intact:

1. Ingest a resume and job description, by upload or pasted text.
2. Review and correct extracted skills and fields.
3. Run deterministic screening rules and inspect the result, interview guide,
   and draft-only communication.

## Setup

From this directory:

```bash
npm install
npm run dev
```

The UI uses Tailwind CSS v4 through the Vite plugin and local shadcn/ui-style
components configured in `components.json`. The visual system uses shadcn CSS
variables with a dark, dense analyst-workbench theme.

## API configuration

By default, requests go to `http://localhost:8000`. To point the UI at another
FastAPI deployment, create `frontend/.env.local`:

```bash
VITE_API_URL=https://your-api.example.com
```

The existing API contract is unchanged:

- `POST /parse-document` with multipart field `file`
- `POST /extract` with `resume_text`, `jd_text`, and `mandatory_rule_notes`
- `POST /screen` with the reviewed screening request

## Checks

```bash
npm run build
npm run lint
```

The frontend does not mock the backend, send email, add authentication, or
persist screening state. All edits are immutable React state updates and are
sent in the `/screen` JSON body when scoring is run.
