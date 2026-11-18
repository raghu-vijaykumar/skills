# Blender-to-videogen handoff review

On 2026-11-18, the synthetic Remotion project used the 96-frame, 24 fps [clamp Blender shot](review.md) and a generated offline test narration saying, “The screw rises and closes the clamp.” The package copied the MP4 and WAV into project-relative assets, pinned both SHA-256 values, and placed both at `cue-clamp`, frame 0. The existing videogen validator accepted the plan and two hashes; changing the registered media or removing the video from the scene is covered by a rejection test.

| Candidate | Exact composed MP4 SHA-256 | Picture/audio | Editorial score | Result |
| --- | --- | --- | ---: | --- |
| Small frame with label | `1676b1faefeafd00da9f4b0f8bdc3f07e57d22b7004a432a5230f5a4bc2bf4bb` | 120 frames, 640×360, AAC | 73/100 | Rejected: the label and smaller frame reduce mechanism detail. GIF hash retained in [scores.json](scores.json), GIF kept in ignored `tmp/`. |
| Full resolution | `ae9554ec2fea319b0c881aa03069389d1e45767f2bfab11723f7d86aead20d76` | 120 frames, 1280×720, AAC | 77/100 | Selected: [optimized GIF](previews/handoff.gif), 480×270, 32 frames. |

The full-resolution MP4 decoded to exactly 120 frames. The video stream lasts 4.000 seconds; AAC extends the container to 4.053 seconds. Silence detection found speech activity from about 0.17 to 2.10 seconds, starting with the animated shot. The exact encoded frames at 0.25, 2.0, and 3.75 seconds were inspected: the clamp stays fully framed, its screw and pad move toward the top block, and the final state remains visible. The physical mechanism and contact geometry are illustrative. This review proves the synthetic code-driven handoff, not a production draft approval or an edited-video timeline adapter.

The [scorebook](scores.json) retains both full-render candidates and selects the higher-scoring technically valid result. The committed GIF is a visual summary of the composed output; narration evidence comes from the exact MP4 audio stream and cue checks.
