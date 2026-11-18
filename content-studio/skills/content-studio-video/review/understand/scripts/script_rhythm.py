#!/usr/bin/env python3
"""Report script cadence patterns without rewriting or approving narration."""

from __future__ import annotations

import argparse
import json
import re
import sys


WORD = re.compile(r"[\w]+(?:['’][\w]+)*", re.UNICODE)
SENTENCE_BREAK = re.compile(r"(?<=[.!?।॥])\s+|\n+")
LONG_WORDS = {"voiceover": 11, "narration": 8}


def _words(text):
    return WORD.findall(text)


def _sentences(text):
    return [part.strip() for part in SENTENCE_BREAK.split(text)
            if _words(part)]


def _observation(kind, units, message):
    ids = list(dict.fromkeys(unit["id"] for unit in units))
    starts = [unit["start"] for unit in units if unit["start"] is not None]
    ends = [unit["end"] for unit in units if unit["end"] is not None]
    result = {"kind": kind, "cue_ids": ids, "message": message,
              "sentence_word_counts": [unit["words"] for unit in units]}
    if starts:
        result["start"] = min(starts)
    if ends:
        result["end"] = max(ends)
    return result


def _runs(units, predicate, min_length):
    run = []
    for unit in units:
        if unit["break_before"] or not predicate(unit, run):
            if len(run) >= min_length:
                yield run
            run = []
        if predicate(unit, run):
            run.append(unit)
    if len(run) >= min_length:
        yield run


def analyze(passages, mode="voiceover"):
    """Analyze authored lines in order; findings never alter approval status."""
    if mode not in LONG_WORDS:
        raise ValueError(f"Unknown rhythm mode: {mode}")
    units = []
    observations = []
    previous_end = None
    break_next = False

    for index, passage in enumerate(passages):
        text = str(passage.get("text") or "")
        sentences = _sentences(text)
        start = passage.get("start")
        end = passage.get("end")
        # A deliberate sound-only gap ends a cadence run, even when there is
        # no explicit silence cue in the authored script.
        boundary = break_next or (previous_end is not None and start is not None
                                  and start - previous_end >= 3)
        if not sentences:
            break_next = True
            continue
        break_next = False
        for sentence_index, sentence in enumerate(sentences):
            words = _words(sentence)
            units.append({"id": str(passage.get("id") or f"cue-{index + 1}"),
                          "words": len(words),
                          "opening": tuple(word.casefold() for word in words[:2]),
                          "start": start, "end": end,
                          "break_before": boundary and sentence_index == 0})
        if end is not None:
            previous_end = end
        rate = passage.get("words_per_second")
        if mode == "voiceover" and isinstance(rate, (int, float)) and 3 <= rate <= 3.4:
            observations.append(_observation(
                "tight_cue", units[-len(sentences):],
                "This cue has little room for a natural read; consider shorter wording or more time."))

    for run in _runs(units, lambda unit, _run: unit["words"] >= LONG_WORDS[mode], 3):
        observations.append(_observation(
            "long_run", run,
            "Several long lines run together; consider a short question, turn, or sound break if the story supports it."))
    for run in _runs(units, lambda unit, run: len(unit["opening"]) == 2 and
                     (not run or unit["opening"] == run[0]["opening"]), 3):
        observations.append(_observation(
            "repeated_opening", run,
            "Adjacent lines begin alike; vary the wording where the meaning allows."))

    observations.sort(key=lambda item: (item.get("start", float("inf")),
                                        item["cue_ids"][0], item["kind"]))
    return {"status": "advisory", "mode": mode, "passage_count": len(passages),
            "line_count": len(units), "observations": observations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True,
                        help="read {mode, passages} JSON from standard input")
    args = parser.parse_args()
    if args.stdin:
        payload = json.load(sys.stdin)
        print(json.dumps(analyze(payload["passages"], payload.get("mode", "voiceover")),
                         ensure_ascii=False))


if __name__ == "__main__":
    main()
