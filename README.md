## v7: Captioned four-scene comic (no narration)

The default `ANIMATION_PROVIDER=comic` mode now generates **one four-panel image**, splits it into four illustrations, and places **a readable English caption to the right of each**. The final panel displays the original Chinese Taoist quote, its English translation, and chapter attribution. The 30-second MP4 is **silent**: there is no text-to-speech request and no Runway charge.

```bash
cd ~/Documents/tao-tech-daily
git pull
source .venv/bin/activate
set -a; source .env; set +a
python studio.py render 18 --mode production
open output/tao_18.mp4
```

Replace 18 with the story you want. The prompt is cached: if the underlying story and insight haven't changed, the existing illustration is reused, but the final composition is rebuilt. Review the quote and translation carefully before approving. The output is still one static page shown for 30 seconds, not four successive scenes.

## v6: Story-first editorial improvements

The main issue in v5 was generic storytelling. New `editorial.py` can draft a more specific, emotionally engaging English script from **facts you personally verified**. It will not retrieve or verify full articles automatically.

```bash
cd ~/Documents/tao-tech-daily
git pull
source .venv/bin/activate
set -a; source .env; set +a
python studio.py show 18
python studio.py draft 18 --facts "Write a short factual summary you verified from the linked article here"
```

Review the generated script and insight before typing `SAVE`. Verify the Taoist quotation and attribution too; the old automatic quote pairing may be unrelated. If necessary, edit with `python studio.py edit 18 --quote "..." --translation "..." --chapter "..." --insight "..."`.

For a different English narration voice, set `OPENAI_TTS_VOICE=nova` in `.env` and reload it. This is a voice preference, not a guarantee of natural delivery.

```bash
python studio.py render 18 --mode production
```

The comic prompt now uses your actual editorial tension and quote, rather than a generic machine confrontation and sunrise. When the story or voice changes, cached assets are regenerated where necessary. Image and speech generation incur API costs. **Code changes have not been live-rendered or visually reviewed.**

## Recommended beginner mode: one four-panel comic image

No Runway needed. Set `ANIMATION_PROVIDER=comic` (or leave it unset), and provide only an OpenAI API key. Each 30-second episode uses **one** AI-generated four-panel cyberpunk illustration and **one** English narration track, assembled into a static-image MP4 with FFmpeg. The website stays a read-only gallery.

```bash
python studio.py list
python studio.py render 20 --mode production
python studio.py approve 20
python studio.py publish 20
```

Replace `20` with your story ID. Review the illustration and narration before approval. Note: AI artwork can misinterpret the four-panel layout. If you want to regenerate, remove `output/comic_20/four_panel_art.png` and `output/comic_20/narration.mp3` only when you deliberately want to rerun paid generation.

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

Replace `20` with your chosen story ID. The preview is a silent storyboard with placeholder art. It is not the final aesthetic. To create the default four-panel comic, configure `OPENAI_API_KEY` and `ANIMATION_PROVIDER=comic`, then run:

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
