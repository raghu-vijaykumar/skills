#!/usr/bin/env node
/**
 * Local music library for Content Studio vlogs.
 *
 * YouTube Audio Library tracks are downloaded manually from YouTube Studio and
 * kept under assets/music/local/<category>/. That folder is gitignored because
 * the library license does not permit redistribution. This script initializes
 * the folders, registers downloads, and generates attribution-ready credits.
 */
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import {
  copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, renameSync,
  statSync, writeFileSync,
} from "node:fs";
import { basename, dirname, extname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "assets", "music");
const AUDIO_EXTENSIONS = new Set([".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"]);
const MANIFEST = "library.json";
const CREDITS = "credits.md";
const LOCAL = "local";

const DEFAULT_CATEGORIES = [
  ["ambient", "Ambient"],
  ["alternative-punk", "Alternative & Punk"],
  ["childrens", "Children's"],
  ["cinematic", "Cinematic"],
  ["classical", "Classical"],
  ["country-folk", "Country & Folk"],
  ["dance-electronic", "Dance & Electronic"],
  ["hip-hop-rap", "Hip-Hop & Rap"],
  ["holiday", "Holiday"],
  ["jazz-blues", "Jazz & Blues"],
  ["pop", "Pop"],
  ["rnb-soul", "R&B & Soul"],
  ["reggae", "Reggae"],
  ["rock", "Rock"],
  ["soundtrack", "Soundtrack"],
  ["world", "World"],
  ["uncategorized", "Uncategorized"],
].map(([slug, label]) => ({ slug, label }));

const LICENSE_LABELS = {
  "youtube-audio-library": "YouTube Audio Library",
  "youtube-audio-library-cc-by": "YouTube Audio Library (CC BY 4.0)",
  "pixabay": "Pixabay Content License",
  "pixabay-cc0": "Pixabay (CC0)",
  "cc-by-4.0": "Creative Commons Attribution 4.0",
  "cc0": "CC0 / public domain",
};

function slugify(value) {
  return String(value).toLowerCase().trim()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function parseArgs(argv) {
  const parsed = { command: null, positional: [], options: {} };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "-h" || token === "--help") {
      parsed.options.help = true;
      continue;
    }
    if (token.startsWith("--")) {
      const key = token.slice(2);
      const next = argv[index + 1];
      if (next === undefined || next.startsWith("--")) {
        parsed.options[key] = true;
      } else {
        parsed.options[key] = next;
        index += 1;
      }
      continue;
    }
    if (!parsed.command) parsed.command = token;
    else parsed.positional.push(token);
  }
  return parsed;
}

function musicPaths(root) {
  return {
    root,
    local: join(root, LOCAL),
    manifest: join(root, MANIFEST),
    credits: join(root, CREDITS),
  };
}

function defaultManifest() {
  return {
    version: 1,
    source: "YouTube Audio Library and Pixabay Music",
    updated: new Date().toISOString().slice(0, 10),
    local_root: LOCAL,
    categories: DEFAULT_CATEGORIES,
    tracks: [],
  };
}

function loadManifest(root) {
  const paths = musicPaths(root);
  if (!existsSync(paths.manifest)) {
    throw new Error(`manifest not found: ${paths.manifest}. Run "init" first.`);
  }
  const manifest = JSON.parse(readFileSync(paths.manifest, "utf8"));
  if (!Array.isArray(manifest.categories) || !Array.isArray(manifest.tracks)) {
    throw new Error(`invalid manifest: ${paths.manifest}`);
  }
  return manifest;
}

function saveManifest(root, manifest) {
  const paths = musicPaths(root);
  manifest.updated = new Date().toISOString().slice(0, 10);
  manifest.tracks.sort((left, right) =>
    left.category.localeCompare(right.category) || left.title.localeCompare(right.title));
  writeFileSync(paths.manifest, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  writeCredits(root, manifest);
}

function categoryFor(manifest, value) {
  const wanted = slugify(value);
  const category = manifest.categories.find((item) =>
    item.slug === wanted || slugify(item.label) === wanted);
  if (!category) {
    const names = manifest.categories.map((item) => item.label).join(", ");
    throw new Error(`unknown category "${value}". Use one of: ${names}`);
  }
  return category;
}

function safeFileName(name) {
  return basename(name).replace(/[<>:"/\\|?*\x00-\x1f]/g, "-").trim() || "track";
}

function sha256(path) {
  const digest = createHash("sha256");
  digest.update(readFileSync(path));
  return digest.digest("hex");
}

function durationSeconds(path) {
  try {
    const output = execFileSync("ffprobe", [
      "-v", "error", "-show_entries", "format=duration",
      "-of", "default=nw=1:nk=1", path,
    ], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    const value = Number.parseFloat(output);
    return Number.isFinite(value) && value > 0 ? Math.round(value * 1000) / 1000 : null;
  } catch {
    return null;
  }
}

function walkAudio(folder) {
  if (!existsSync(folder)) return [];
  const results = [];
  for (const entry of readdirSync(folder, { withFileTypes: true })) {
    const full = join(folder, entry.name);
    if (entry.isDirectory()) results.push(...walkAudio(full));
    else if (AUDIO_EXTENSIONS.has(extname(entry.name).toLowerCase())) results.push(full);
  }
  return results;
}

function relativeTrackPath(root, path) {
  return relative(musicPaths(root).local, path).split(sep).join("/");
}

function addTrack(root, input, options) {
  const paths = musicPaths(root);
  const manifest = loadManifest(root);
  const source = resolve(input);
  if (!existsSync(source)) throw new Error(`file not found: ${source}`);
  if (!AUDIO_EXTENSIONS.has(extname(source).toLowerCase())) {
    throw new Error(`unsupported audio type: ${extname(source) || "no extension"}`);
  }
  if (!options.category) throw new Error("--category is required");

  const category = categoryFor(manifest, options.category);
  const digest = sha256(source);
  const duplicate = manifest.tracks.find((track) => track.sha256 === digest);
  if (duplicate) {
    throw new Error(`already registered as "${duplicate.title}" (${duplicate.file})`);
  }

  const folder = join(paths.local, category.slug);
  mkdirSync(folder, { recursive: true });
  let target = join(folder, safeFileName(source));
  if (existsSync(target)) {
    const suffix = extname(target);
    target = join(folder, `${basename(target, suffix)}-${digest.slice(0, 8)}${suffix}`);
  }

  if (options.move) renameSync(source, target);
  else copyFileSync(source, target);

  const license = options.license || "youtube-audio-library";
  const attribution = String(options.attribution || "");
  const track = {
    file: relativeTrackPath(root, target),
    title: String(options.title || basename(target, extname(target))),
    artist: String(options.artist || "Unknown artist"),
    category: category.slug,
    mood: String(options.mood || ""),
    duration_seconds: durationSeconds(target),
    license,
    attribution_required: Boolean(attribution) || Boolean(options["attribution-required"])
      || license.includes("cc-by"),
    attribution_text: attribution,
    source_url: String(options["source-url"] || ""),
    downloaded: String(options.downloaded || new Date().toISOString().slice(0, 10)),
    sha256: digest,
  };
  manifest.tracks.push(track);
  saveManifest(root, manifest);
  return { track, path: target };
}

function scanTracks(root, options) {
  const paths = musicPaths(root);
  const manifest = loadManifest(root);
  const known = new Set(manifest.tracks.map((track) => track.file));
  const added = [];
  for (const file of walkAudio(paths.local)) {
    const filePath = relativeTrackPath(root, file);
    if (known.has(filePath)) continue;
    const firstFolder = filePath.includes("/") ? filePath.split("/")[0] : "uncategorized";
    let category = manifest.categories.find((item) => item.slug === slugify(firstFolder));
    if (!category) {
      category = { slug: slugify(firstFolder), label: firstFolder };
      manifest.categories.push(category);
    }
    const digest = sha256(file);
    const duplicate = manifest.tracks.find((track) => track.sha256 === digest);
    if (duplicate) {
      console.warn(`skip duplicate: ${filePath} matches ${duplicate.file}`);
      continue;
    }
    const track = {
      file: filePath,
      title: basename(file, extname(file)),
      artist: String(options.artist || "Unknown artist"),
      category: category.slug,
      mood: "",
      duration_seconds: durationSeconds(file),
      license: options.license || "youtube-audio-library",
      attribution_required: false,
      attribution_text: "",
      source_url: "",
      downloaded: new Date().toISOString().slice(0, 10),
      sha256: digest,
    };
    manifest.tracks.push(track);
    added.push(track);
  }
  if (added.length) saveManifest(root, manifest);
  return added;
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return "unknown";
  const total = Math.round(seconds);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

function labelFor(manifest, slug) {
  return manifest.categories.find((item) => item.slug === slug)?.label || slug;
}

function writeCredits(root, manifest) {
  const paths = musicPaths(root);
  const lines = [
    "# Music credits",
    "",
    "Source: YouTube Audio Library and Pixabay Music. Audio files are kept locally under `local/`",
    "and are not committed or redistributed.",
    "",
  ];
  if (!manifest.tracks.length) {
    lines.push("_No tracks registered yet._", "");
  } else {
    for (const category of manifest.categories) {
      const tracks = manifest.tracks.filter((track) => track.category === category.slug);
      if (!tracks.length) continue;
      lines.push(`## ${category.label}`, "");
      for (const track of tracks) {
        const license = LICENSE_LABELS[track.license] || track.license;
        lines.push(`- **${track.title}** — ${track.artist} · ${formatDuration(track.duration_seconds)} · ${license}`);
      }
      lines.push("");
    }
  }
  const attribution = manifest.tracks.filter((track) => track.attribution_required);
  lines.push("## Attribution required", "");
  if (!attribution.length) {
    lines.push("_No attribution-required tracks registered._", "");
  } else {
    lines.push("Paste the exact line into the video description:", "");
    for (const track of attribution) {
      const fallback = `Music: \"${track.title}\" by ${track.artist} (${LICENSE_LABELS[track.license] || track.license})`;
      lines.push(`- **${track.title}** — ${track.artist}`, `  \`${track.attribution_text || fallback}\``);
    }
    lines.push("");
  }
  writeFileSync(paths.credits, `${lines.join("\n")}`, "utf8");
}

function init(root) {
  const paths = musicPaths(root);
  mkdirSync(paths.root, { recursive: true });
  if (!existsSync(paths.manifest)) {
    writeFileSync(paths.manifest,
      `${JSON.stringify(defaultManifest(), null, 2)}\n`, "utf8");
  }
  const manifest = loadManifest(root);
  for (const category of manifest.categories) {
    mkdirSync(join(paths.local, category.slug), { recursive: true });
  }
  writeCredits(root, manifest);
  console.log(`initialized ${paths.root}`);
  console.log(`audio folder: ${paths.local} (gitignored)`);
  console.log("next: open the YouTube Audio Library, download MP3s, then run \"add\" or \"scan\"");
}

function openLibrary(source = "youtube") {
  const name = String(source).toLowerCase();
  const url = name.startsWith("pixabay")
    ? "https://pixabay.com/music/"
    : "https://www.youtube.com/audiolibrary";
  if (process.platform === "win32") {
    execFileSync("cmd", ["/c", "start", "", url], { stdio: "ignore" });
  } else if (process.platform === "darwin") {
    execFileSync("open", [url], { stdio: "ignore" });
  } else {
    execFileSync("xdg-open", [url], { stdio: "ignore" });
  }
  console.log(`opened ${url}`);
  if (name.startsWith("pixabay")) {
    console.log("download manually and check each track page for the Content ID shield");
  } else {
    console.log("sign in, filter by category, and use each track's DOWNLOAD button");
  }
}

function verify(root) {
  const paths = musicPaths(root);
  const manifest = loadManifest(root);
  const problems = [];
  for (const track of manifest.tracks) {
    const file = join(paths.local, ...track.file.split("/"));
    if (!existsSync(file)) {
      problems.push(`missing: ${track.file}`);
    } else if (sha256(file) !== track.sha256) {
      problems.push(`changed: ${track.file}`);
    }
  }
  if (problems.length) {
    for (const problem of problems) console.error(problem);
    return false;
  }
  console.log(`${manifest.tracks.length} track(s) verified`);
  return true;
}

function list(root) {
  const manifest = loadManifest(root);
  if (!manifest.tracks.length) {
    console.log("no tracks registered");
    return;
  }
  for (const category of manifest.categories) {
    const tracks = manifest.tracks.filter((track) => track.category === category.slug);
    if (!tracks.length) continue;
    console.log(`\n${category.label}`);
    for (const track of tracks) {
      console.log(`  ${track.title} — ${track.artist} (${formatDuration(track.duration_seconds)})`);
    }
  }
}

function usage() {
  return `Usage:
  node content-studio/scripts/music-library.mjs init
  node content-studio/scripts/music-library.mjs open [--source youtube|pixabay]
  node content-studio/scripts/music-library.mjs add <file> --category <name> [options]
  node content-studio/scripts/music-library.mjs scan
  node content-studio/scripts/music-library.mjs list
  node content-studio/scripts/music-library.mjs verify
  node content-studio/scripts/music-library.mjs credits

Global option:
  --root <dir>   music library root (default: content-studio/assets/music)

Add options:
  --title <text>          track title
  --artist <text>         artist
  --mood <text>           optional mood label
  --license <name>        youtube-audio-library (default),
                          youtube-audio-library-cc-by, pixabay,
                          pixabay-cc0, cc-by-4.0, cc0
  --attribution <text>    exact credit required by the license
  --source-url <url>      track page or source reference
  --downloaded <date>     YYYY-MM-DD
  --move                  move instead of copy

The script does not download from YouTube. Download MP3s manually from the
Audio Library, then add them here. Audio is stored under local/ and is
gitignored; only the manifest and credits are committed.`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.options.help || !args.command) {
    console.log(usage());
    return 0;
  }
  const root = resolve(String(args.options.root || DEFAULT_ROOT));
  switch (args.command) {
    case "init":
      init(root);
      return 0;
    case "open":
      openLibrary(args.options.source || args.positional[0] || "youtube");
      return 0;
    case "add": {
      if (!args.positional[0]) throw new Error("add requires an audio file");
      const { track, path } = addTrack(root, args.positional[0], args.options);
      console.log(`added ${track.title} -> ${path}`);
      return 0;
    }
    case "scan": {
      const added = scanTracks(root, args.options);
      console.log(added.length ? `added ${added.length} track(s)` : "no new tracks");
      return 0;
    }
    case "list":
      list(root);
      return 0;
    case "verify":
      return verify(root) ? 0 : 1;
    case "credits":
      writeCredits(root, loadManifest(root));
      console.log(`wrote ${musicPaths(root).credits}`);
      return 0;
    default:
      throw new Error(`unknown command "${args.command}"`);
  }
}

try {
  process.exitCode = main();
} catch (error) {
  console.error(`music-library: ${error.message}`);
  process.exitCode = 1;
}
