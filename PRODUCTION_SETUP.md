# Production setup

1. Install Python 3.11+, FFmpeg and FFprobe.
2. Create a virtual environment and install requirements.
3. Copy `.env.example` to `.env` and configure credentials. Never commit `.env`.
4. Export environment variables (e.g. `set -a; source .env; set +a`) and start `uvicorn app:app --host 127.0.0.1 --port 8000`.
5. Open the dashboard. Ingest news, review source facts and Taoist quotation, edit the script, render a video, mark verification and approval, and publish.

## Providers

- OpenAI Images: `IMAGE_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_IMAGE_MODEL`.
- OpenAI speech: `VOICE_PROVIDER=openai`, `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`.
- Local test: use preview rendering (placeholder artwork, no narration).
- Optional Runway image-to-video: `ANIMATION_PROVIDER=runway` and `RUNWAYML_API_SECRET`; default `kenburns` animates stills locally.
- FFmpeg creates 720×1280 H.264 MP4, 30 seconds.

## Operational notes

Image and animation providers incur charges. Check provider pricing and supported model names before use. All generated media should be checked for factual accuracy, quote attribution, licensing, visual artifacts and narration quality before publishing. This is a development MVP, not a hardened public service. Secure admin endpoints, configure HTTPS, backups, job queues, rate limits, persistent object storage and monitoring before deploying publicly. YouTube publishing is not yet implemented.
