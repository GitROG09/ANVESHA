# Models directory

Downloaded/exported model artifacts (Qwen3-VL, Whisper-Small, QNN context
binaries, etc.) go here. This directory is gitignored for binary artifacts
— see `.gitignore` — because model weights don't belong in source control.

Point the Qualcomm backend at files placed here via:
- `QUALCOMM_VISION_MODEL_PATH`
- `QUALCOMM_SPEECH_MODEL_PATH`

See `docs/qualcomm_deployment.md` for how to produce these artifacts.
