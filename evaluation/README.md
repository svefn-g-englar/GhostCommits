# GhostCommits evaluation

This evaluation measures the behavior of the complete pipeline on three deliberately different public repositories. It records observations; it does not assume that inactivity proves abandonment or infer private maintainer intent.

## Cases

| Expected lifecycle | Repository | Selection rule |
| --- | --- | --- |
| Archived | `jquery-archive/jquery-mobile` | GitHub's repository metadata explicitly sets `archived: true`. |
| Inactive | `nvbn/thefuck` | Not archived, with at least 365 days since the last recorded push at evaluation time. |
| Active | `pallets/flask` | Not archived, with fewer than 365 days since the last recorded push at evaluation time. |

These are operational labels for this evaluation, not claims about maintainers' intentions.

## Metrics

- **Evidence validity:** source URLs returning an HTTP status below 400 divided by all evidence source URLs checked.
- **Claim support:** validated findings whose cited evidence IDs all exist in the generated packet divided by all rendered findings.
- **Classification accuracy:** repositories whose observed lifecycle label matches the documented selection rule divided by all cases.
- **Recommendation actionability:** roadmap steps containing an action, effort estimate, and only valid evidence IDs divided by all roadmap steps.
- **Performance:** wall-clock seconds for GitHub ingestion, bounded Git mining, Gemma inference, validation, planning, and source-link checks.
- **AI usage:** true only when Ollama/Gemma produced the analysis. The default evaluation rejects fallback output.

## Run

Start Ollama and make the configured model available, then run from the project root:

```bash
ollama pull gemma3:1b
python -m evaluation.run_evaluation
```

The generated `results.json` contains aggregate metrics plus the evidence, findings, warnings, and resurrection plan for every case. Use `--allow-fallback` only for pipeline smoke tests, never for reporting Gemma performance.

## Latest measured run

Observed October 30, 2026 with `gemma3:1b`, clone depth 120, and fallback disabled:

| Metric | Result |
| --- | ---: |
| Lifecycle classification | 3 / 3 (100%) |
| Reachable evidence sources | 50 / 50 (100%) |
| Evidence-supported findings | 3 / 3 (100%) |
| Actionable roadmap steps | 18 / 18 (100%) |
| Runs using Gemma | 3 / 3 |
| Mean end-to-end duration | 60.60 seconds |

These are the actual observations stored in [`results.json`](results.json), not benchmark targets.

## Limitations

- GitHub metadata, issues, and source URLs can change after the observation time.
- Commit mining is intentionally bounded to the configured clone depth; it is not a complete census of repository history.
- A reachable source link does not by itself prove that a natural-language interpretation is correct. The evidence IDs make that interpretation auditable.
- The 365-day inactive threshold is a transparent evaluation convention, not a universal definition of abandonment.
- Local model output can vary slightly across Ollama and model versions even with a low temperature.
- GhostCommits never executes repository code, so it does not claim that suggested fixes compile or pass upstream tests.
