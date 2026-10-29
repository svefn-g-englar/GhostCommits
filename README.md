# GhostCommits

> Every abandoned repository has a story. GhostCommits finds the evidence, separates fact from inference, and turns the surviving trail into a safe resurrection plan.

GhostCommits is a competition-ready, open-source AI software archaeologist. It combines deterministic Git/GitHub mining with schema-constrained Gemma inference. Facts never come from the language model; the model may only interpret a validated evidence packet, and unsupported evidence IDs are rejected.

![GhostCommits investigation dashboard](assets/demo.png)

## Standout features

- **The Last Heartbeat** — real GitHub metadata plus bounded Git history mining.
- **Whispers from the Past** — Gemma produces structured, evidence-linked findings.
- **Claim Firewall** — unsupported citations never reach the interface.
- **Resurrection Blueprint** — a safe, contributor-ready recovery sequence.
- **Digital Epitaph** — a shareable PNG memorial generated from verified facts.
- **Adversarial safety** — public GitHub only, bounded clone, no code execution.

## Quick start

Requirements: Python 3.10+, Git, and optionally Ollama for Gemma inference.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama pull gemma3:4b
streamlit run app.py
```

`GITHUB_TOKEN` is optional but recommended to avoid anonymous API rate limits. Without Ollama, the deterministic pipeline still runs and clearly labels its fallback mode.

## Architecture

```text
Repository URL
    ├── GitHubClient ─ metadata, issues, contributors, languages
    └── GitAnalyzer ── bounded clone, commits, TODOs, README
                ↓
EvidenceBuilder ───── immutable records with IDs and source links
                ↓
GemmaEngine ───────── schema-constrained interpretation via Ollama
                ↓
ClaimValidator ────── reject unsupported citations
                ↓
ResurrectionPlanner ─ safe, sequenced recovery actions
                ↓
Streamlit UI ──────── timeline, whispers, roadmap, PNG + JSON
```

## Trust model

- Only public `github.com` repository URLs are accepted.
- Clone depth, blob size, checkout size, scanned file count, and file size are bounded.
- Submodules are not initialized; repository code and scripts are never executed.
- README, issue, commit, and TODO text is untrusted evidence, never instructions.
- Maintainer motive is reported only when explicitly present in a cited source.
- Model findings must cite an existing `E-##` record.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` | empty | Raises GitHub API limits |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama endpoint |
| `GHOSTCOMMITS_MODEL` | `gemma3:4b` | Open-weight interpreter |
| `GHOSTCOMMITS_MAX_REPO_MB` | `250` | Recommended checkout cap |

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall app.py core ui tests
```

Tests cover URL validation, evidence generation, unsupported-claim rejection, confidence normalization, and resurrection planning without network calls.

## Project layout

```text
ghostcommits/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .env.example
├── core/
│   ├── github_client.py
│   ├── git_analyzer.py
│   ├── evidence_builder.py
│   ├── gemma_engine.py
│   ├── claim_validator.py
│   └── resurrection.py
├── ui/
│   ├── components.py
│   ├── charts.py
│   └── styles.css
├── tests/
├── examples/sample_report.json
└── assets/
```

MIT licensed.
