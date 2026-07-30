#!/bin/bash
set -euo pipefail

# Activate the local virtual environment if it exists.
if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# API keys are read from your shell environment - never hardcode them here.
# Set them once in ~/.zshrc, or create a .env file (git-ignored) and source it:
#
#   export GEMINI_API_KEY="..."
#   export OPENROUTER_API_KEY="..."
#
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

if [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "Note: no GEMINI_API_KEY or OPENROUTER_API_KEY found in the environment."
    echo "The app will start and fall back to its offline parser/tailor engines."
    echo "You can also paste a key into the app sidebar at runtime."
fi

streamlit run app.py
