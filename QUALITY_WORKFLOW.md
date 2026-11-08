# Readable films + a second-agent visual judge

This is an **opt-in private production workflow**, separate from the old `studio.py render` path. The public website remains a read-only gallery of approved films. It has no generation or judge endpoints.

## 1. Playback changes

The supplied four-state example now uses 6, 6, 7 and 14 seconds: 33 seconds total. These are editorial defaults, not a scientific reading-speed claim. Longer copy gets additional time. A five-second total was too short for three captions plus a bilingual quotation.

New GIF exports have no loop extension. The gallery disables looping and pauses on the final encoded frame, with a manual **Replay film** button. The file itself cannot force an unrelated video app to disable that app's repeat setting.

To change the timing of a downloaded four-state GIF without any AI calls:

```bash
cd ~/Documents/tao-tech-daily
git pull --ff-only
source .venv/bin/activate
python quality_studio.py retime \
  --image ~/Downloads/tao_readable_no_loop.gif \
  --out output/readable_example \
  --seconds 6 6 7 14
open output/readable_example/movie.mp4
```

Use the actual downloaded file path. The input is a four-state GIF, NOT a static four-panel PNG or an MP4. The command refuses to overwrite an existing output folder. It creates `movie.mp4`, `preview.gif`, `final_quote.png`, frame PNGs and a playback verification record. No image generation, speech or Runway calls occur.

## 2. Install and configure Agent 2

The new `quality_studio.py` uses Pillow and Pydantic from the existing requirements. No new agent framework is necessary.

```bash
cd ~/Documents/tao-tech-daily
git pull --ff-only
source .venv/bin/activate
python -m pip install -r requirements.txt
set -a
source .env
set +a
python quality_studio.py --help
```

Optional settings in your private `.env`:

```dotenv
OPENAI_JUDGE_MODEL=gpt-4.1-mini
OPENAI_IMAGE_QUALITY=medium
```

Keep your existing `OPENAI_API_KEY` and `OPENAI_IMAGE_MODEL`. The judge model is configurable and must support image inputs and structured JSON output. Current integration uses the OpenAI Responses API for judging and Images API for generation. No Runway key and no TTS calls are involved.

The app does **not** automatically read `.env`; load it as above. Never paste credentials into prompts, briefs, feedback, GitHub, or chat. All images, reports, budget logs and feedback are stored under the existing git-ignored `output/` directory. Images supplied to the judge are sent to the OpenAI API; do not submit private material without authorization.

## 3. Prepare an editorial brief for a real story

```bash
python quality_studio.py init 18 --out output/brief_18.json
nano output/brief_18.json
```

Replace 18 with the actual story ID. This copies the existing headline and quote into an editable JSON file. **It does not certify them as accurate.** The older automatically assigned quote may not fit the article.

Complete these fields:

- `verified_facts`: a short list of facts personally checked against the linked article.
- `source_urls` and `source_reviewed`: actual source links and `true` only after checking.
- `intended_story`: the specific pressure, human choice, and visible consequence.
- `art_prompt`: one continuous scene; smaller off-center protagonist, clear contrast, no panels.
- `captions`: exactly three short English lines: event, dilemma, reframing.
- `quote_zh`, `quote_en`, `quote_source`, `quote_source_url`: exact checked quotation, translation, chapter and source.
- `quote_reviewed`: `true` only after you check the quote.

`kind` is `news` for actual news or `fictional` for an explicitly labeled parable. Fictional examples must not be presented as verified events. The new renderer labels fictional parables on every frame.

Facts and quote checks are human declarations, not automated fact verification. The program refuses to generate a news candidate until the fields are completed.

## 4. Judge an existing image first

This performs **two paid vision-model calls**, and generates no new artwork:

```bash
python quality_studio.py judge \
  --image output/comic_18/four_panel_final.png \
  --brief output/brief_18.json \
  --out output/judge_18.json \
  --allow-paid
```

Use the path to the image you actually want assessed. A saved four-state GIF lets the judge inspect all four caption states. A single still can receive an art review, but is explicitly blocked from a final-sequence pass because the other caption states are unseen. Use `--art path/to/unlettered_art.png` when you have a separate clean illustration for the first pass.

### How Agent 2 works

**Pass A — blind observation:** describes the visible action and consequences without seeing the intended story or creator's prompt. If captions are baked into the only supplied image, the report discloses that it did not have a separate unlettered image.

**Pass B — art-direction review:** sees the brief, the blind observation and all supplied frames. Returns structured, validated scores, visible evidence, uncertainty, what to preserve, and up to three prioritized fixes.

| Criterion | Weight |
|---|---:|
| Story clarity: visible cause, choice, consequence | 25% |
| Artfulness: composition, lighting, coherence and originality | 20% |
| Visual contrast: problem versus benefit is unmistakable | 15% |
| Human resonance: relatable stakes | 10% |
| Taoist connection: action embodies the teaching | 15% |
| Readability: captions, Chinese/English quote and timing | 15% |

Default acceptance: 80/100, plus at least 8/10 on story clarity, Taoist connection and readability; no blocking issues; adequate confidence; human factual/quote checks. Passing means **ready for your review**, never approved or published.

These thresholds are a starting rubric, not an objective measure of beauty. Model confidence is self-reported, not statistically calibrated. Vision can miss text errors, especially small or non-English text. Inspect the Chinese yourself.

A crucial rule: a bright tower is not evidence that it caused another neighborhood's darkness. The judge must not invent a missing causal connection merely because the caption implies it.

## 5. Run the creator → judge → revision loop

Start with one candidate:

```bash
python quality_studio.py improve \
  --brief output/brief_18.json \
  --attempts 1 \
  --allow-paid
```

After reviewing that result, allow a bounded loop:

```bash
python quality_studio.py improve \
  --brief output/brief_18.json \
  --attempts 3 \
  --allow-paid
```

Flow:

```text
Your checked brief
    → Agent 1 generates ONE coherent illustration
    → deterministic renderer adds three caption states + bilingual closing quote
    → Agent 2 observes and judges the actual pixels
    → controller checks score, blockers and remaining attempts
         ├─ pass → save for YOUR approval
         ├─ art-only fixes → send specific feedback to Agent 1
         ├─ facts / quotes / captions / timing issue → stop for editor
         └─ error, attempt limit or no progress → stop, preserve best candidate
```

Each candidate uses at most **one image request and two judge requests**. Three candidates means at most **three image calls + six judge calls per run**. Calls are counted before dispatch, including failed attempts. There are no automatic network retries. This is a **call-count cap, not a dollar cap**: actual cost varies by configured model, image quality and tokens; requests that time out may still incur a charge. Rerunning starts a new budget.

Revisions generate new candidates from the revised prompt; they are not guaranteed to preserve the exact same pixels or character. Every attempt is saved separately. The controller retains the best score rather than blindly choosing the last attempt, and stops after two non-improving revisions. Errors preserve existing output.

The loop does not change quotes, rewrite factual claims, edit its own code or deploy anything. It does not run on a schedule.

## 6. Review, stage, then publish manually

The console prints the best candidate folder. Open its `movie.mp4`, `final_quote.png`, and `judge.json`. Its `creator_request.json` records the exact art prompt. The parent folder contains the brief, all candidates, `run.json`, and the API-call/usage log.

To stage a passing candidate for the existing approval workflow, replace the example folder below with the exact printed path:

```bash
python quality_studio.py stage 18 --candidate output/quality/YOUR_RUN/candidate_01
python studio.py approve 18
python studio.py publish 18
```

**Staging withdraws an existing published version of this story, clears its approvals, archives its old MP4, and installs the new video as a draft.** It checks that the movie bytes still match the judged candidate. It never publishes. The gallery continues to hide drafts.

Do not stage the fictional example under an unrelated real headline. The existing `studio.py render` command is unchanged and still uses the older pipeline; use this new workflow explicitly.

## 7. Record your taste so the next run can use it

```bash
python quality_studio.py feedback \
  --candidate output/quality/YOUR_RUN/candidate_01 \
  --rating dislike \
  --note "Beautiful colors, but the valve is not visibly connected to the homes. Make the cause and result obvious."
```

Feedback is appended to `output/quality_feedback.jsonl`. The next creator request includes the latest eight human notes. This is prompt/context memory, **not model retraining or guaranteed improvement**. Curate the notes and calibrate the judge against your approvals over time. Use held-out examples to detect a judge that rewards polished visuals but misses story clarity.

## 8. What is tested, and what is not

Tested locally: syntax/imports, deterministic rubric gates, refusal of calls without explicit paid opt-in, call limits, early stopping, best-candidate retention, frame extraction, typography composition, and actual FFmpeg/GIF export. The supplied example was verified as a 33-second silent MP4 and a GIF without a loop extension.

Not tested: paid image generation or live judge calls with your account, behavior on your specific Mac, or cross-browser playback. Review one candidate before enabling three. No live judge score for the supplied artwork is claimed.

## Further subagents (architecture proposal, not implemented)

Later, a coordinator could dispatch a news researcher, source/quote checker, story editor, artist, judge, and packager. Keep source verification separate from aesthetic approval; store source snapshots and chosen quotes. Freeze editorial meaning before visual iteration. Route only the failing part back to the responsible subagent. Keep human publication approval, cost limits, saved candidates and a manual stop.

Official API references:
- https://developers.openai.com/api/docs/guides/images-vision
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/guides/image-generation
- https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
- https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/ended_event
