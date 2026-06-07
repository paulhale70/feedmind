# FeedMind — Project Overview

**AI-powered RSS / Atom reader with first-class podcast & video support.**
Version **3.8.0** · Desktop (Windows-first) · Python + Tkinter + SQLite · MIT licensed

---

## 1. What it is

FeedMind is a local-first desktop feed reader that goes beyond aggregation: it
adds AI summaries, full-text extraction, and built-in podcast/video playback on
top of a conventional RSS/Atom reader. All data lives in a local SQLite
database — no accounts, no cloud, no telemetry. The core app runs with **zero
pip installs** (standard library + Tkinter + SQLite); every richer feature
(AI, PDF export, notifications, audio metadata) is an optional dependency that
degrades gracefully when absent.

- **Audience:** news readers, researchers, podcast listeners, professionals.
- **Platform:** Windows is the primary target (built-in MCI audio backend);
  macOS/Linux work with `pygame-ce`. A separate Kivy mobile app exists as an
  early MVP under `mobile/`.

---

## 2. Status & recent work

`v3.8.0` was a security, stability, and UI release (no new feature surface):

- **Security hardening:** SSRF protection (private/loopback/metadata IP
  blocking + redirect re-checks), response-size and download caps, safe podcast
  filenames, MCI command-injection guard, http(s)-only link opening, escaped
  PDF links, delimited AI prompts, bounded OPML depth.
- **Stability:** per-thread SQLite connections (WAL) fixing cross-thread
  corruption; one-time (not every-startup) destructive migration; thread-safe
  audio position updates; graceful shutdown.
- **UI:** live filter counts, active-filter highlight, empty states, full-width
  status bar, working audio seek bar.
- **Project:** added LICENSE, made tests runnable directly/under pytest,
  buildozer cleanup, Windows `.exe` release artifact.

An incremental **god-object refactor** is in progress (decoupling the UI from
the database schema first; see open PRs).

---

## 3. Architecture

A single Tkinter app coordinates a set of focused, mostly independent modules.

### Module map

| Module | Responsibility |
|---|---|
| `feedmind.py` | Main application & all UI (the large coordinator class) |
| `rss_core.py` | Feed fetch + RSS/Atom parsing; the shared `safe_urlopen` SSRF/egress layer |
| `rss_database_v2.py` / `_v3` | Data layer. **V3 is the live class**, inheriting V2 |
| `rss_api_config.py` | API-key management (keyring-first, env-var aware) |
| `rss_ai_summarizer.py` | AI summaries / TL;DR / key points (Claude, OpenAI, auto) |
| `rss_article_extractor.py` | Full-text extraction (newspaper3k / trafilatura) |
| `rss_feed_finder.py` | Feed auto-discovery from a website URL |
| `rss_opml.py` | OPML import/export |
| `rss_audio_player.py` (+ `_ui`) | Audio playback (Windows MCI / pygame backends) |
| `rss_video_player_ui.py` | Video playback via the system player |
| `rss_podcast_downloader.py` | Episode downloads with progress + size caps |
| `rss_auto_refresh.py` | Background refresh scheduling helpers |
| `rss_notifications.py` | Desktop notifications (plyer) |
| `rss_pdf_exporter.py` | PDF export (reportlab) |
| `rss_themes.py` | Light/dark theme color definitions |
| `mobile/` | Kivy mobile app (early MVP) |

### Data layer

- SQLite, **one connection per thread** (WAL + busy timeout) for safe concurrent
  refresh/download workers alongside the Tk main thread.
- Schema is migrated in-place via `PRAGMA table_info` + idempotent `ALTER`s,
  with a `PRAGMA user_version` gate for destructive one-time migrations.
- Tables: `feeds`, `articles`, `categories`, `settings`, `reading_stats`,
  `podcast_downloads`.

### Threading model

- Network/refresh/download work runs on daemon threads.
- UI updates are marshaled back to the Tk main thread (`root.after` or a
  queue-drained poller for audio position).

---

## 4. Current feature set

**Reading**
- RSS & Atom parsing, article caching / offline reading, read/unread tracking,
  favorites, full-text search.
- Sort (date / title / feed), "Last 7 days" filter, feed bookmarks (pinned).

**Organization**
- Categories/folders, OPML import/export, dark/light themes, reading
  statistics, keyboard shortcuts (`j/k`, `o`, `r`, `f`, `b`, `Ctrl+…`).

**AI** (optional, Claude/OpenAI)
- TL;DR, comprehensive summary, key-point extraction; smart caching so articles
  are never re-processed; free full-text extraction.

**Podcast / video**
- Auto-detection of podcast feeds, built-in audio player, episode downloads for
  offline listening, video playback via the system player, smart auto-refresh.

**Output & alerts**
- PDF export, desktop notifications.

---

## 5. Tech stack

- **Core (zero-install):** Python 3.9+ · Tkinter · SQLite · Windows MCI audio.
- **Optional:** `defusedxml`, `keyring` (security); `reportlab` (PDF);
  `plyer` (notifications); `anthropic` / `openai` (AI);
  `newspaper3k` / `trafilatura` (extraction); `pygame-ce`, `mutagen` (audio);
  `kivy`/`kivymd` (mobile).
- **Packaging:** PyInstaller (`feedmind.spec`, `build_exe.bat`) → `FeedMind.exe`;
  Buildozer (`buildozer.spec`) for Android.

### Run

```bash
python feedmind.py                 # source (zero installs for core)
# or download FeedMind.exe from the GitHub release (Windows, no Python)
```

---

## 6. Known limitations & tech debt

- **`FeedMind` is a god object** (~1,900 lines mixing UI, threading, business
  logic). Refactor underway.
- **Tests are smoke scripts**, some hitting live network; no CI, no GUI/mobile
  coverage.
- **V1 database module is dead code** (kept only for legacy tests).
- **Audio:** playback-speed control is a non-functional placeholder; a single
  global MCI alias/mixer prevents concurrent playback; pygame position tracking
  drifts across pauses.
- **Mobile app** is an early MVP, far behind the desktop feature set.
- No code signing on the Windows `.exe` (SmartScreen prompt on first run).

---

## 7. Possible new feature sets

Grouped by theme, with rough **value** and **effort** so they can be triaged.
Items marked 🔗 build directly on code that already exists.

### A. Intelligence (AI/ML)
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Local/offline AI** via Ollama (no API cost/keys) | High | Med | 🔗 Slots behind the existing `AIProvider` abstraction as a third provider |
| **Auto-tagging & AI categorization** of incoming articles | High | Med | 🔗 Reuses summarizer; writes to a new `tags` table |
| **Semantic search** (embeddings) across cached articles | High | Med-High | Local embeddings + a vector column; big UX win over keyword search |
| **Daily/weekly AI digest** (in-app + optional email) | High | Med | 🔗 Combines summarizer + notifications/PDF |
| **"Ask this feed/article"** Q&A chat | Med | Med | RAG over cached full-text |
| **Duplicate / near-duplicate detection** across feeds | Med | Low-Med | Hash/embedding compare on insert |
| **Sentiment & topic clustering** dashboards | Med | Med | Visualize what your feeds are talking about |

### B. Reading experience
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Text-to-speech** ("listen to this article") | High | Med | 🔗 Reuses the audio backend; pairs well with TTS engines |
| **Read-it-later / save-for-later queue** | High | Low | New flag + view; low-risk |
| **Highlights & annotations** with export | Med | Med | Per-article notes table |
| **On-device translation** of foreign-language feeds | Med | Med | Local or API translation before display |
| **Distraction-free reader mode** (typography, width, font size) | Med | Low | 🔗 Extends the extractor + detail pane |

### C. Podcast / media
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Episode transcription** (Whisper) + searchable transcripts | High | High | 🔗 Builds on downloads; unlocks transcript search & chapters |
| **Working playback-speed control** (currently a placeholder) | Med | Low-Med | Replace MCI with a backend that supports rate (e.g. miniaudio/ffmpeg) |
| **Playback queue, sleep timer, resume-position** | Med | Med | 🔗 Audio player already tracks position |
| **Embedded video playback** (vs. handing to system player) | Med | High | `python-vlc`/libmpv embed |

### D. Organization & automation
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Rules engine** (auto-mark read, auto-tag, mute, star by keyword/regex) | High | Med | Differentiator; runs on refresh |
| **Saved searches / smart folders** | Med | Low-Med | 🔗 Search already exists |
| **Keyword & per-feed notification rules + quiet hours** | Med | Low-Med | 🔗 Extends notifications |

### E. Sync, sharing & integrations
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Optional cloud / self-hosted sync** of subscriptions & read-state | High | High | On the roadmap; design for opt-in/E2E |
| **Read-later integrations** (Pocket, Instapaper, Readwise) | Med | Low-Med | Share-out from an article |
| **Share to Slack / email / Notion**, webhooks/IFTTT | Med | Low-Med | 🔗 Slots next to existing actions |
| **Browser extension** "Subscribe in FeedMind" + send-to-app | Med | Med | Drives discovery |

### F. Platform & reach
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Bring the mobile (Kivy) app to feature parity** | High | High | 🔗 Scaffolding exists in `mobile/` |
| **System tray / background service** with badge counts | Med | Low-Med | Keep refreshing while minimized |
| **Web version** (read anywhere) | Med | High | Larger architectural lift |
| **Localization / i18n & accessibility** (screen-reader, keyboard-only) | Med | Med | Broadens audience |

### G. Privacy & security extras
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Encrypted local database** (at-rest) | Med | Med | SQLCipher; complements local-first ethos |
| **Per-feed proxy / Tor fetching** | Low-Med | Med | 🔗 Extends `safe_urlopen` |

### H. Quality & developer experience (enablers)
| Idea | Value | Effort | Notes |
|---|---|---|---|
| **Real pytest suite + CI** (mocked network, GUI smoke) | High | Med | Unblocks safe iteration on everything above |
| **Finish the god-object refactor** | High | Med-High | In progress; improves every future feature |
| **Plugin architecture** (third-party feed handlers/actions) | Med | High | Long-term extensibility |
| **Code-sign the Windows build** | Med | Low | Removes SmartScreen friction |

---

## 8. Suggested near-term roadmap

A pragmatic ordering that front-loads enablers and high-value/low-effort wins:

1. **Enablers first:** real test suite + CI; finish the UI refactor. *(makes
   everything else safe and fast)*
2. **Quick wins:** read-it-later queue, saved searches, distraction-free reader
   mode, working playback speed.
3. **Flagship differentiators:** local/offline AI (Ollama), rules engine,
   AI daily digest, semantic search.
4. **Reach:** mobile parity, optional sync, browser extension.

---

*Generated as a living overview — update alongside `CHANGELOG.md` as features land.*
