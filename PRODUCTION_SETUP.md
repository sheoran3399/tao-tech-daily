# Tao Tech Daily v3: Production and gallery

## First-time update on your Mac

1. Stop your running server with Control+C.
2. Run:
   ```bash
   cd ~/Documents/tao-tech-daily
   git pull
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```
3. Start the gallery with `python -m uvicorn app:app --host 127.0.0.1 --port 8000`.
4. Open `http://127.0.0.1:8000`. You will see only published videos.

## Private production

Open a second Terminal window, activate the environment and run `python studio.py --help`.

```bash
python studio.py ingest
python studio.py list
python studio.py show 20
python studio.py render 20 --mode preview
```

Replace 20 with a valid story ID. Preview mode uses placeholder art and no voice. To produce a visually richer AI version:

```bash
export OPENAI_API_KEY='your-private-key'
export RUNWAYML_API_SECRET='your-private-runway-key'
export ANIMATION_PROVIDER=runway
python studio.py render 20 --mode production
```

Do not share or commit your API key. For a longer-term configuration, store it in a local `.env` file and load it into the Terminal before running the command. The application does not automatically load `.env`.

Open the resulting `output/tao_20.mp4` in Finder or QuickTime. Check source facts, quote authenticity, pacing, captions, pronunciation and visual quality.

```bash
python studio.py approve 20
python studio.py publish 20
```

Refresh the gallery page. Only approved/published films are displayed.

## Costs and caveats

OpenAI image and voice calls incur API usage charges. Animated mode requests six images, six Runway clips, and one narration per production run. Confirm current provider models and prices before rendering. It does not yet generate genuine moving anime scenes; it animates stills with camera motion. The Runway pipeline now assembles six genuine 5-second animated clips, but requires live provider testing and incurs costs. It caches finished raw clips for retries. The website is not deployed publicly and YouTube Shorts publishing is not implemented.

For a real public website, configure HTTPS, durable video storage, a production database, backups, and deployment. Keep `studio.py` and secrets off the public server if possible.
