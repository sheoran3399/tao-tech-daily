# Tao Tech Daily — Film Gallery + Private Production

**The website is now a public-facing gallery, not a video-generation dashboard.** The video pipeline runs privately from your Mac's Terminal. Only approved, published films appear on the site.

## What changed

- `/` and `/watch`: cinematic gallery of completed videos
- `/api/videos`: read-only list of published films
- `/videos/tao_N.mp4`: accessible only for published films
- `studio.py`: private command-line production and review workflow
- `production.py`: 30-second portrait storyboard or AI artwork + English narration
- No public video generation, editorial actions, or admin token fields

## Run locally (Mac)

```bash
cd ~/Documents/tao-tech-daily
git pull
source .venv/bin/activate
python -m pip install -r requirements.txt
python studio.py list
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 to see your gallery. Keep the server running. **The existing local database `tao.db` and output videos are preserved by `git pull`.**

## Create a film privately

In a **second Terminal window**, while the gallery server is running:

```bash
cd ~/Documents/tao-tech-daily
source .venv/bin/activate
python studio.py ingest
python studio.py list
python studio.py show 20
python studio.py render 20 --mode preview
```

Replace `20` with your chosen story ID. The preview is a silent storyboard with placeholder art. It is not the final aesthetic. To create real animated scenes, configure `OPENAI_API_KEY`, `RUNWAYML_API_SECRET`, and `ANIMATION_PROVIDER=runway`, then run:

```bash
python studio.py render 20 --mode production
```

Check the video in `output/tao_20.mp4`. Then:

```bash
python studio.py approve 20
python studio.py publish 20
```

Approval requires explicit confirmation after you check the source article, quote attribution, script, and finished film. Refresh the gallery to see the published film.

To edit a script, use `python studio.py edit 20 --script "Your revised narration"`. Editing or re-rendering revokes prior approval.

## Providers and limitations

- OpenAI image generation: `OPENAI_API_KEY`, `OPENAI_IMAGE_MODEL`
- OpenAI text-to-speech: `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`
- FFmpeg: video assembly and motion from still images
- `ANIMATION_PROVIDER=kenburns` (default): animated camera movement over stills
- **Real motion-video mode:** set `ANIMATION_PROVIDER=runway`, `RUNWAYML_API_SECRET`, and `OPENAI_API_KEY`. Six 5-second Runway clips are composited into the final 30-second film, with captions and English voice. Provider calls incur costs; the SDK/model parameters need a live integration test. Completed raw clips are cached for assembly retries.
- The quote selection is deterministic, not AI-researched. Verify the quote and actual article before publishing.
- The final video still needs artistic quality testing; code changes alone do not guarantee an appealing result. Provider calls have not been live-tested. Use a small spending budget before production.

## Important deployment note

This gallery is **local only** until you deploy it. A public host will need persistent SQLite storage and a durable location for MP4s, or a separate storage service/CDN. The current local `output/` files are not uploaded to GitHub. Do not expose the production CLI, local database, or API keys to the public.

See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md).
