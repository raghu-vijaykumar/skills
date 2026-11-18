# Three rendered Blender showcases

These are original procedural scenes rendered headlessly with Blender 5.3 at 1280×720, 24 fps, for 96 frames each. The editable `.blend`, full MP4, and JSON reports were generated in the ignored `tmp/` directory. The committed GIFs are 480×270, 8 fps, 32-frame copies of those exact MP4s. They are evidence for these three authored examples only.

| Scene | Encoded MP4 SHA-256 | GIF SHA-256 | Visual review of exact MP4 frames |
| --- | --- | --- | --- |
| [Clamp](examples/clamp.py) | `00ad2a3dfaef8f72879e4cfb20ec5f5b128660037d709ab5dc16f387b18a5782` | `3499afc701f2b9e79014e5fc2006ab03eebd6a4c9e0fc960a093fc860edaa682` | Start: screw and pad below demonstration block. Middle: screw rotates and rises. End: pad approaches block; both remain framed. |
| [Character](examples/character.py) | `8fce5e61d3a240a82e0c7cf467db84c9be92300f03dbe446fc80c29349daf849` | `7cde92b15bd64936ba4b278b5225172432bb7cca281cfdd3a688bffb67367353` | Start: whole courier visible. Middle: head turns and arm lifts. End: arm returns; head and feet remain inside frame. |
| [Corridor](examples/corridor.py) | `5df9cb20b74004481f1ad74cb332fa7da72111fa75f291bf244e6b13d9085260` | `923893f0c7944da867d42ab6d95ba1282ccb02323fb0f5af470dabc3d7a5c4a4` | Start, middle, end: central door and side bays remain legible as the camera pushes forward. Practical lights and cool/warm contrast remain visible. |

Each MP4 passed FFprobe frame count and 1280×720 dimension checks. Each GIF decoded to 32 frames at 480×270. Sample frames came from the encoded MP4 at 0.25, 2.0, and 3.75 seconds and were visually inspected. The clamp mechanism is illustrative, not an engineering model. The character and corridor are original stylized examples, not generic implementations of every related upstream style. A project using these shots still needs narrated-context and exact-master review.

The required object names in each [JSON specification](README.md#rebuild-the-showcases) were checked in the saved `.blend` scenes; all passed. The current builder, specification, and shared helper hashes match the inputs recorded for these renders.
