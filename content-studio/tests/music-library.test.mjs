import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(ROOT, "content-studio", "scripts", "music-library.mjs");

function run(root, args) {
  return spawnSync(process.execPath, [SCRIPT, "--root", root, ...args], {
    encoding: "utf8",
  });
}

function readManifest(root) {
  return JSON.parse(readFileSync(join(root, "library.json"), "utf8"));
}

test("initializes categories and registers a downloaded track", () => {
  const root = mkdtempSync(join(tmpdir(), "cs-music-"));
  try {
    assert.equal(run(root, ["init"]).status, 0);
    assert.ok(existsSync(join(root, "local", "cinematic")));
    assert.ok(existsSync(join(root, "credits.md")));

    const source = join(root, "download.mp3");
    writeFileSync(source, "camera-safe music bytes");
    const added = run(root, ["add", source, "--category", "cinematic",
      "--title", "Morning Run", "--artist", "Test Artist",
      "--license", "youtube-audio-library-cc-by",
      "--attribution", "Music: Morning Run by Test Artist"]);
    assert.equal(added.status, 0, added.stderr);
    assert.ok(existsSync(join(root, "local", "cinematic", "download.mp3")));

    const manifest = readManifest(root);
    assert.equal(manifest.tracks.length, 1);
    assert.equal(manifest.tracks[0].title, "Morning Run");
    assert.equal(manifest.tracks[0].category, "cinematic");
    assert.equal(manifest.tracks[0].license, "youtube-audio-library-cc-by");
    assert.equal(manifest.tracks[0].attribution_required, true);

    const credits = readFileSync(join(root, "credits.md"), "utf8");
    assert.match(credits, /Music: Morning Run by Test Artist/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("rejects a duplicate by content hash", () => {
  const root = mkdtempSync(join(tmpdir(), "cs-music-"));
  try {
    run(root, ["init"]);
    const source = join(root, "one.mp3");
    writeFileSync(source, "same bytes");
    assert.equal(run(root, ["add", source, "--category", "pop"]).status, 0);
    const duplicate = run(root, ["add", source, "--category", "rock"]);
    assert.notEqual(duplicate.status, 0);
    assert.match(duplicate.stderr, /already registered/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("scans manually placed category folders and verifies hashes", () => {
  const root = mkdtempSync(join(tmpdir(), "cs-music-"));
  try {
    run(root, ["init"]);
    mkdirSync(join(root, "local", "ambient"), { recursive: true });
    const file = join(root, "local", "ambient", "Slow Air.mp3");
    writeFileSync(file, "ambient bytes");

    const scanned = run(root, ["scan"]);
    assert.equal(scanned.status, 0, scanned.stderr);
    const manifest = readManifest(root);
    assert.equal(manifest.tracks.length, 1);
    assert.equal(manifest.tracks[0].title, "Slow Air");
    assert.equal(manifest.tracks[0].category, "ambient");
    assert.equal(run(root, ["verify"]).status, 0);

    writeFileSync(file, "changed bytes");
    assert.notEqual(run(root, ["verify"]).status, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
