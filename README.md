# GhostCommits

GhostCommits is an evidence-grounded software archaeology experience for public GitHub repositories. It reads public metadata and a recent commit sample, clearly separates observations from interpretation, builds a bounded resurrection plan, and exports a shareable digital epitaph.

## Run locally

No build step or dependencies are required.

```bash
python3 -m http.server 4173 --directory dist
```

Then open `http://localhost:4173`.

## Safety and accuracy

- Public GitHub repositories only.
- Repository code is never cloned or executed.
- Every synthesized finding cites evidence records in the case file.
- Inactivity is not presented as proof of abandonment.
- GitHub's anonymous API rate limit applies; a labeled demo case remains available offline.

## Structure

The deployable static application lives in `dist/`. `.openai/hosting.json` configures private Sites hosting.
