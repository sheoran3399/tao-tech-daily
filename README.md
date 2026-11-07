# Tao Tech Daily

A daily tech-news-to-Taoist-wisdom video studio. Phase 1 publishes reviewed 30-second, 9:16 videos to a local website. Phase 2 (planned): YouTube Shorts.

**Settings:** English narration, Chinese donghua × futuristic technology, manual editorial approval.

## Quick start

Requires Python 3.11+, FFmpeg and FFprobe.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to set your keys
set -a; source .env; set +a
uvicorn app:app --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000 . Set STUDIO_ADMIN_TOKEN and supply it in the dashboard to run editorial actions. The server must remain local until authentication, HTTPS and persistent hosting are configured.

Workflow: ingest RSS headlines → edit script/quote → generate preview or AI artwork + narration → verify article facts and Taoist quote → approve → publish to gallery.

**Do not commit .env, API keys, generated media, or tao.db.** RSS headlines are editorial leads, not verified article summaries. Generated video output and provider calls have not been tested end-to-end in this repository.

See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) for provider configuration.
