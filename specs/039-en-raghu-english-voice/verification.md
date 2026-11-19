# Verification: en-raghu English Voice

The owner reviewed the initial take 2 and take 3 clone previews and asked to
keep both. Their two 9.7-second references are bundled with recorded hashes.
The older `raghu` and `rakshitha` profiles were not changed.

## Commands and results

- Focused voice suite: 51 tests passed.
- `npm run check:docs`: 187 maintained files and 1104 links passed.
- `npm run check:capabilities`: 53 skills, 165 methods passed.
- Relevant Node skill-discovery and capability tests: 6 passed, 2 skipped.
- `voice.py status --profile en-raghu`: resolved bundled profile and listed
  `take2` and `take3`, with no missing samples.
- `voice.py synthesize --dry-run --reference-variant take3`: bound take 3's
  exact SHA-256 and reported a planned render without loading model weights.
- Real local `voice.py synthesize` runs with the official Chatterbox Turbo
  checkpoint rendered both selected variants. Each exact output was probed and
  round-trip transcribed locally.
- The checkpoint and Python environment were moved into private local Content
  Studio folders; a new take 3 render from those durable paths produced the
  same SHA-256 as the verified test WAV.
- The staged diff contains the two authorized reference WAVs as Git LFS
  pointers. It contains no model weights or generated preview WAVs.

| Variant | Output | Peak | SHA-256 | Local transcription |
| --- | ---: | ---: | --- | --- |
| take2 | 6.22 s, 24 kHz mono PCM16 | -7.7 dBFS | `efb0eb87845a79fb0432835d548cab829e6a2d62b1fa2cdb126cdb8037f4d183` | Intended English line recovered. |
| take3 | 5.86 s, 24 kHz mono PCM16 | -5.5 dBFS | `5f4376717576fc93d15ab06613ec5b1f30c45e5014630075b54b7e8e114f4002` | Intended English line recovered. |

An initial take 2 render used a different seed and transcribed “English-wise
clone.” The final profile's first-cue seed was changed to the reviewed
comparison seed and the exact rerender transcribed “English voice clone.”
The real test WAVs and model weights are local review evidence outside Git.
Future scripts still need their own word and listening review before use in a
production video.
