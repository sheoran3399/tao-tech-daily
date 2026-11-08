"""AI-assisted editorial drafting using ONLY editor-supplied verified article facts."""
import json, os
from urllib.request import Request,urlopen
from urllib.error import HTTPError

def draft(headline,verified_facts,quote,translation,chapter):
    if not verified_facts.strip():
        raise ValueError("Supply a factual summary you verified from the source article.")
    key=os.getenv("OPENAI_API_KEY")
    if not key:raise ValueError("OPENAI_API_KEY missing")
    prompt=(
        "You are a thoughtful, cinematic writer for a 30-second English-language Chinese "
        "cyberpunk donghua micro-film. Make the Taoist wisdom illuminate a REAL dilemma "
        "in the news. Never fabricate facts or imply the news article says more than the "
        "provided verified summary. Avoid clichés such as 'technology changes everything', "
        "'the future needs wisdom', and generic robots. Write ~55-65 spoken words, "
        "natural and poetic, with a clear hook, specific human tension, Taoist insight, "
        "and an emotionally resonant ending. Quote and chapter are editor-supplied and "
        "must be checked by the editor. Respond ONLY as JSON with string fields "
        "'script' and 'insight'. The insight should be one precise sentence describing "
        "the ethical tension and Taoist resolution. "
        f"HEADLINE: {headline}\nVERIFIED FACTS: {verified_facts}\n"
        f"TAOIST QUOTE: {quote}\nTRANSLATION: {translation}\nSOURCE: {chapter}"
    )
    data=json.dumps({"model":os.getenv("OPENAI_SCRIPT_MODEL","gpt-4.1-mini"),
      "messages":[{"role":"user","content":prompt}],
      "temperature":0.7,"response_format":{"type":"json_object"}}).encode()
    req=Request("https://api.openai.com/v1/chat/completions",data=data,
      headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=90) as response:
            result=json.load(response)
        draft=json.loads(result["choices"][0]["message"]["content"])
        if not draft.get("script") or not draft.get("insight"):
            raise ValueError("AI response did not contain script and insight")
        return draft
    except HTTPError as e:
        raise ValueError(f"Script provider HTTP {e.code}; check model access and API key") from e
