# FeedMind Mobile

FeedMind's phone app: an RSS/Atom reader with podcast playback, written in
Flutter for Android and iOS. It replaces the earlier Kivy prototype.

It's standalone: the phone keeps its own feeds and read state. To move your
subscriptions from the desktop app, use **File → Export OPML** there and
**⋮ → Import OPML** here.

## Features

- RSS 2.0, RSS 1.0 (RDF), and Atom feeds
- All / Unread / Favorites / Podcast episodes / Downloaded views, newest first
- Swipe right to mark read/unread, swipe left to favorite
- Article view with the feed's summary and a link to the full article
- Podcasts: stream or download episodes, background playback with
  lock-screen controls, resume where you left off, 0.8×–2× speed
- OPML import and export
- Old articles (30+ days) are cleared automatically; favorites and downloaded
  episodes are kept, and cleared articles don't come back as unread
- Light and dark theme (follows the system)

## Layout

```
lib/
  main.dart                  app start-up, providers, theme
  src/models.dart            Feed, Article, ParsedFeed, ArticleFilter
  src/app_state.dart         subscriptions, refresh, OPML, counts
  src/data/database.dart     SQLite schema and queries
  src/services/              feed parser/fetcher, OPML, downloads, player
  src/ui/                    screens and the player bar
  src/util/                  date parsing/formatting, HTML-to-text
test/                        unit tests (parser, dates, OPML, database)
```

## Development

Requires the Flutter SDK (stable) and, for Android, the Android SDK.

```sh
cd mobile
flutter pub get
flutter test               # unit tests
flutter analyze            # lints
flutter run                # on a connected phone or running emulator
flutter build apk          # release APK in build/app/outputs/flutter-apk/
```

To start the Android emulator created for this project:
`flutter emulators --launch FeedMind_Pixel`.

### iOS

The code is iOS-ready, but iOS apps can only be built on a Mac with Xcode.
CI (`.github/workflows/mobile.yml`) runs an unsigned iOS build on a macOS
runner for every PR that touches `mobile/`, so breakage shows up early.
Installing on an iPhone needs a Mac (or a cloud Mac / Codemagic) and an
Apple ID; TestFlight/App Store distribution needs an Apple Developer account.
