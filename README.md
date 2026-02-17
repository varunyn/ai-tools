# ai-tools

This repository will host multiple AI/automation utilities. The first app lives under
`streamlit-summarizer/`, which contains the full Streamlit + OCI Generative AI text
summarizer (docs, Docker setup, tests, etc.).

**Disclaimer:** No apps in this repository are intended for production use. They are for reference and learning only.

## Apps

- [`streamlit-summarizer/`](streamlit-summarizer/) – Streamlit UI for uploading plain-text
  documents and generating summaries using OCI Generative AI. See that folder’s README for
  full setup instructions (Docker, uv, testing, OCI configuration, E2E Playwright suite).

## Contributing

1. Clone the repo and work inside the relevant app directory (e.g., `cd streamlit-summarizer`).
2. Keep shared tooling (e.g., `.gitignore`, common docs) at the repository root when possible.

Future apps can be added under new subdirectories alongside `streamlit-summarizer/`.

This project is licensed under the [MIT License](LICENSE).
