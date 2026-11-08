import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import music


def make_track(folder, file, title, artist, category, license_name,
               duration=120, mood="", attribution="", required=False):
    path = folder / "local" / Path(file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"audio:{title}".encode())
    return {
        "file": file,
        "title": title,
        "artist": artist,
        "category": category,
        "mood": mood,
        "duration_seconds": duration,
        "license": license_name,
        "attribution_required": required,
        "attribution_text": attribution,
        "sha256": "0" * 64,
    }


class MusicSelectionTest(unittest.TestCase):
    def make_catalog(self, root):
        tracks = [
            make_track(root, "cinematic/morning.mp3", "Morning Run",
                       "Test Artist", "cinematic", "youtube-audio-library",
                       duration=90, mood="Inspirational"),
            make_track(root, "cinematic/night.mp3", "Night Drive",
                       "Other Artist", "cinematic", "pixabay",
                       duration=240, mood="Dark"),
            make_track(root, "dance-electronic/pulse.mp3", "Pulse",
                       "Beat Maker", "dance-electronic", "youtube-audio-library-cc-by",
                       duration=180, mood="Energetic",
                       attribution="Music: Pulse by Beat Maker", required=True),
            make_track(root, "rnb-soul/velvet.mp3", "Velvet",
                       "Soul Artist", "rnb-soul", "pixabay",
                       duration=150, mood="Romantic"),
        ]
        (root / "library.json").write_text(json.dumps({"tracks": tracks}), encoding="utf-8")
        return tracks

    def test_filters_accept_genre_labels_and_duration(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            self.make_catalog(root)
            _, tracks = music.load_catalog(root)
            selected = music.filter_tracks(tracks, category="Dance & Electronic")
            self.assertEqual([track["title"] for track in selected], ["Pulse"])
            selected = music.filter_tracks(tracks, category="R&B & Soul")
            self.assertEqual([track["title"] for track in selected], ["Velvet"])
            selected = music.filter_tracks(tracks, mood="inspir", max_duration=120)
            self.assertEqual([track["title"] for track in selected], ["Morning Run"])
            selected = music.filter_tracks(tracks, query="other artist")
            self.assertEqual([track["title"] for track in selected], ["Night Drive"])

    def test_missing_audio_is_hidden_unless_requested(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            self.make_catalog(root)
            (root / "local" / "cinematic" / "night.mp3").unlink()
            _, tracks = music.load_catalog(root)
            visible = music.filter_tracks(tracks)
            self.assertNotIn("Night Drive", [track["title"] for track in visible])
            all_tracks = music.filter_tracks(tracks, available_only=False)
            self.assertIn("Night Drive", [track["title"] for track in all_tracks])

    def test_resolve_track_handles_exact_and_ambiguous_titles(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            self.make_catalog(root)
            _, tracks = music.load_catalog(root)
            self.assertEqual(music.resolve_track(tracks, "Morning Run")["title"], "Morning Run")
            self.assertEqual(music.resolve_track(tracks, "cinematic/morning.mp3")["title"],
                             "Morning Run")
            with self.assertRaises(SystemExit):
                music.resolve_track(tracks, "i")

    def test_review_writes_audio_players_and_selection_records_credits(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            draft = root / "draft"
            draft.mkdir()
            self.make_catalog(root)
            _, tracks = music.load_catalog(root)
            selected = music.filter_tracks(tracks, category="cinematic")
            review = music.write_review(draft, selected, root,
                                        draft / "analysis" / "music-review.html")
            page = review.read_text(encoding="utf-8")
            self.assertIn("Morning Run", page)
            self.assertIn("file:///", page)
            self.assertIn("<audio", page)

            track = music.resolve_track(tracks, "Pulse")
            selection, credits = music.write_selection(draft, track, root,
                                                       "out-of-office", "trip")
            payload = json.loads(selection.read_text(encoding="utf-8"))
            self.assertEqual(payload["track"]["title"], "Pulse")
            self.assertEqual(payload["credits"], "Music: Pulse by Beat Maker")
            text = credits.read_text(encoding="utf-8")
            self.assertIn("Attribution: Music: Pulse by Beat Maker", text)
            self.assertIn("License: YouTube Audio Library (CC BY 4.0)", text)

    def test_mix_music_writes_a_new_master_with_ducking(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            video = root / "video.mp4"
            track = root / "music.wav"
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                            "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=30:d=2",
                            "-f", "lavfi", "-i",
                            "sine=frequency=440:sample_rate=48000:duration=2",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                            "-shortest", str(video)], check=True, capture_output=True)
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                            "-f", "lavfi", "-i",
                            "sine=frequency=880:sample_rate=48000:duration=1",
                            "-c:a", "pcm_s16le", str(track)], check=True,
                           capture_output=True)
            output = root / "video-with-music.mp4"
            result = music.mix_music(video, track, output, volume=0.2,
                                     duck=True, fade=0.25)
            self.assertTrue(output.exists())
            duration, audio = music.probe_media(output)
            self.assertAlmostEqual(duration, 2.0, delta=0.2)
            self.assertTrue(audio)
            self.assertTrue(result["duck"])


if __name__ == "__main__":
    unittest.main()
