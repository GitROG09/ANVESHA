# LDR Vision Dataset Contract

This directory contains the Objective 2 dataset contract only. No real photographs are included in this repository.

Allowed provenance values are:

- `synthetic`: generated imagery, never a real-world result.
- `test_fixture`: structured inputs used to test parsing, fusion, and verification; these may have no image at all.
- `real`: photographs captured from physical LDR hardware and manually annotated later.

Real-world metrics remain unavailable until `provenance=real` records exist. Related captures must stay in one split/session group to prevent leakage. The held-out real test split must not be used for tuning.
