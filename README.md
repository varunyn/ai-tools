# ai-tools

A collection of small AI and automation apps built for learning, experimentation, and reference.
Each app lives in its own folder with its own README, setup steps, and test commands.

> **Disclaimer**
> Projects in this repository are not intended for production use.

## Apps

| App                                                                              | Description                                                                                                                                                              | Primary Stack                            |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| [`streamlit-summarizer/`](streamlit-summarizer/)                                 | Upload plain-text documents and generate summaries using OCI Generative AI. Includes Docker setup, uv workflow, and tests.                                               | OCI GEN AI + Streamlit + Python          |
| [`nextjs-oci-openai-chat/`](nextjs-oci-openai-chat/)                             | OpenAI-style chat app powered by OCI Generative AI with a Next.js frontend and FastAPI backend. Includes local/dev setup, Docker, and backend/frontend testing guidance. | OCI GEN AI + Next.js + FastAPI           |
| [`nextjs-streamlit-oci-realtime-speech/`](nextjs-streamlit-oci-realtime-speech/) | Real-time speech transcription with Streamlit or Next.js, backed by Oracle AI Speech. Includes Python + Node setup and env docs.                                         | Streamlit + Next.js + OCI Speech Service |

## Getting Started

1. Clone this repository.
2. Enter the app directory you want to run (for example: `cd nextjs-oci-openai-chat`).
3. Follow that app’s README for dependencies, environment variables, and run/test commands.

## Contributing

- Keep changes scoped to the relevant app directory when possible.
- Keep shared assets and repository-level docs at the root.

## License

This project is licensed under the [MIT License](LICENSE).
