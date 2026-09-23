# Submission Materials — ANVEṢHA AI

This folder contains the competition submission artifacts for the
Snapdragon AI Lab Build & Present Challenge.

| File | Contents |
|---|---|
| `brief_project_description.pdf` | 2-page professional project overview |
| `short_pitch.pptx` | 10-slide pitch deck (editable) |
| `short_pitch.pdf` | Same deck, PDF export |
| `pitch_script.md` | 3-minute and 5-minute spoken pitch scripts |
| `submission_text.md` | Full/500/250/100-word descriptions, tagline, key innovation, tech stack, Qualcomm explanation, problem statement, demo description |
| `README_submission.md` | This file |

## Where to find the actual product

The working application is the rest of this repository, not this folder:

- Source code: `backend/`, `frontend/`
- Automated tests (28, passing): `tests/`, run via `scripts/run_tests.sh`
- Real benchmark numbers: `benchmarks/`
- Full documentation: `docs/` (architecture, problem statement, Qualcomm
  deployment guide, AI models, experiment engine, verification engine,
  benchmarking, demo guide, and a complete, honest limitations doc)
- Top-level `README.md` has full run instructions.

## Honesty note for reviewers

Every claim in these submission materials is cross-checked against
`docs/limitations.md`, which lists exactly what was built and tested versus
what remains a documented-but-unexecuted deployment path (primarily: real
Qualcomm NPU inference, which required Snapdragon hardware not available
during development). Reviewers are encouraged to read that file alongside
the pitch materials.
