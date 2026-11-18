# Data model

- **Passage:** stable `id`, `text`, optional `start` and `end` seconds, optional `words_per_second`. Passages remain in authored order.
- **Observation:** `kind`, `cue_ids`, optional `start` and `end`, `message`, and measured `sentence_word_counts`. An observation suggests review and never changes validation status.
- **Rhythm report:** input passage count, analyzed line counts, and ordered observations. No source audio or media is stored.
