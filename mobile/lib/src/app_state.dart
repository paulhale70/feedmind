/// App-wide state: subscriptions, counts, and actions the screens call.
library;

import 'package:flutter/foundation.dart';

import 'data/database.dart';
import 'models.dart';
import 'services/feed_fetcher.dart';
import 'services/opml.dart';

class RefreshResult {
  const RefreshResult({required this.newArticles, required this.errors});
  final int newArticles;

  /// Feed title -> error message for feeds that failed.
  final Map<String, String> errors;
}

class AppState extends ChangeNotifier {
  AppState(this.db, {FeedFetcher? fetcher}) : fetcher = fetcher ?? FeedFetcher();

  final AppDatabase db;
  final FeedFetcher fetcher;

  List<Feed> _feeds = [];
  Map<String, int> _counts = const {};
  bool _refreshing = false;
  int _revision = 0;

  List<Feed> get feeds => _feeds;
  Map<String, int> get counts => _counts;
  bool get refreshing => _refreshing;

  /// Bumped whenever articles change, so open lists know to reload.
  int get revision => _revision;

  /// How many feeds are refreshed at once.
  static const refreshConcurrency = 4;

  Future<void> load() async {
    _feeds = await db.getFeeds();
    _counts = await db.getCounts();
    _revision++;
    notifyListeners();
  }

  /// Subscribe to [url]: fetch it first so bad URLs fail before saving.
  /// Returns the feed's title. Throws on failure or if already subscribed.
  Future<String> addFeed(String url) async {
    final uri = validateFeedUrl(url);
    final normalized = uri.toString();
    if (_feeds.any((f) => f.url == normalized)) {
      throw FetchException('You already follow this feed');
    }
    final parsed = await fetcher.fetch(normalized);
    if (!await db.addFeed(normalized, parsed.title)) {
      throw FetchException('You already follow this feed');
    }
    await db.cacheItems(normalized, parsed.items);
    await load();
    return parsed.title;
  }

  /// Unsubscribe. Returns paths of downloaded episodes to delete.
  Future<List<String>> removeFeed(Feed feed) async {
    final paths = await db.removeFeed(feed.url);
    await load();
    return paths;
  }

  Future<void> renameFeed(Feed feed, String title) async {
    final trimmed = title.trim();
    if (trimmed.isEmpty) return;
    await db.renameFeed(feed.url, trimmed);
    await load();
  }

  /// Refresh [only] these feeds, or all of them.
  Future<RefreshResult> refresh({List<Feed>? only}) async {
    if (_refreshing) return const RefreshResult(newArticles: 0, errors: {});
    _refreshing = true;
    notifyListeners();

    final targets = List<Feed>.of(only ?? _feeds);
    var added = 0;
    final errors = <String, String>{};
    try {
      // A few at a time: fast, without opening dozens of connections.
      for (var i = 0; i < targets.length; i += refreshConcurrency) {
        final batch = targets.skip(i).take(refreshConcurrency);
        await Future.wait(batch.map((feed) async {
          try {
            final parsed = await fetcher.fetch(feed.url);
            added += await db.cacheItems(feed.url, parsed.items);
          } catch (e) {
            errors[feed.title] = e.toString();
          }
        }));
      }
    } finally {
      _refreshing = false;
      await load();
    }
    return RefreshResult(newArticles: added, errors: errors);
  }

  Future<void> setRead(Article a, bool read) async {
    await db.setRead(a.id, read);
    await load();
  }

  Future<void> setFavorite(Article a, bool favorite) async {
    await db.setFavorite(a.id, favorite);
    await load();
  }

  Future<int> markAllRead(ArticleFilter filter) async {
    final n = await db.markAllRead(filter);
    await load();
    return n;
  }

  Future<int> clearOldArticles({int days = 30}) async {
    final n = await db.clearOldArticles(days: days);
    await load();
    return n;
  }

  /// Import feeds from OPML text. New feeds are saved right away and fetched
  /// in the background by the caller's follow-up [refresh].
  /// Returns (added, alreadyFollowed, invalid).
  Future<(int, int, int)> importOpml(String text) async {
    final entries = parseOpml(text);
    var added = 0, existing = 0, invalid = 0;
    for (final entry in entries) {
      final String url;
      try {
        url = validateFeedUrl(entry.url).toString();
      } on FetchException {
        invalid++;
        continue;
      }
      if (await db.addFeed(url, entry.title)) {
        added++;
      } else {
        existing++;
      }
    }
    await load();
    return (added, existing, invalid);
  }

  String exportOpml() => buildOpml(
      [for (final f in _feeds) OpmlFeed(url: f.url, title: f.title)]);

  /// Feeds that have never been fetched (e.g. just imported).
  List<Feed> get unfetchedFeeds =>
      _feeds.where((f) => f.lastRefresh == null).toList();
}
