/// SQLite storage for feeds, articles, podcast downloads, and playback state.
///
/// Mirrors the desktop schema's ideas (rss_database_v2/v3.py): articles are
/// ordered by a normalized published_sort key, podcast episodes are keyed by
/// audio URL with their web page in page_link, and articles removed by
/// clearOldArticles are remembered so a refresh doesn't re-add them as unread.
library;

import 'package:sqflite/sqflite.dart';

import '../models.dart';
import '../util/dates.dart';

class AppDatabase {
  AppDatabase._(this._db);

  final Database _db;

  static const schemaVersion = 1;

  /// How long a cleared-article record is kept after its feed stops listing it.
  static const clearedRecordDays = 90;

  /// Most articles returned for one list.
  static const listLimit = 1000;

  static Future<AppDatabase> open(String path, {DatabaseFactory? factory}) async {
    final db = await (factory ?? databaseFactory).openDatabase(
      path,
      options: OpenDatabaseOptions(
        version: schemaVersion,
        onConfigure: (db) => db.execute('PRAGMA foreign_keys = ON'),
        onCreate: (db, _) => _createSchema(db),
      ),
    );
    return AppDatabase._(db);
  }

  static Future<void> _createSchema(Database db) async {
    final batch = db.batch();
    batch.execute('''
      CREATE TABLE feeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        title TEXT,
        added_date TEXT NOT NULL,
        last_refresh TEXT,
        is_podcast INTEGER NOT NULL DEFAULT 0
      )''');
    batch.execute('''
      CREATE TABLE articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_url TEXT NOT NULL REFERENCES feeds(url) ON DELETE CASCADE,
        title TEXT NOT NULL,
        link TEXT NOT NULL,
        page_link TEXT,
        description TEXT,
        published TEXT,
        published_sort TEXT NOT NULL,
        cached_date TEXT NOT NULL,
        is_read INTEGER NOT NULL DEFAULT 0,
        read_date TEXT,
        is_favorite INTEGER NOT NULL DEFAULT 0,
        audio_url TEXT,
        audio_type TEXT,
        audio_length INTEGER,
        duration_seconds INTEGER NOT NULL DEFAULT 0,
        position_ms INTEGER NOT NULL DEFAULT 0,
        playback_completed INTEGER NOT NULL DEFAULT 0,
        UNIQUE(feed_url, link)
      )''');
    batch.execute(
        'CREATE INDEX idx_articles_sort ON articles(published_sort)');
    batch.execute(
        'CREATE INDEX idx_articles_feed ON articles(feed_url, is_read)');
    batch.execute('''
      CREATE TABLE cleared_articles (
        feed_url TEXT NOT NULL,
        link TEXT NOT NULL,
        cleared_date TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        PRIMARY KEY (feed_url, link)
      )''');
    batch.execute('''
      CREATE TABLE downloads (
        article_id INTEGER PRIMARY KEY REFERENCES articles(id) ON DELETE CASCADE,
        local_path TEXT NOT NULL,
        file_size INTEGER,
        download_date TEXT NOT NULL
      )''');
    await batch.commit(noResult: true);
  }

  Future<void> close() => _db.close();

  String _now() => DateTime.now().toIso8601String();

  // ---------------------------------------------------------------- Feeds

  /// Subscribe to a feed. Returns false if it's already subscribed.
  Future<bool> addFeed(String url, String title) async {
    final id = await _db.insert(
      'feeds',
      {'url': url, 'title': title, 'added_date': _now()},
      conflictAlgorithm: ConflictAlgorithm.ignore,
    );
    return id != 0;
  }

  Future<List<Feed>> getFeeds() async {
    final rows = await _db.rawQuery('''
      SELECT f.*,
             (SELECT COUNT(*) FROM articles a
              WHERE a.feed_url = f.url AND a.is_read = 0) AS unread_count
      FROM feeds f
      ORDER BY f.title COLLATE NOCASE''');
    return rows.map(Feed.fromRow).toList();
  }

  Future<void> renameFeed(String url, String title) =>
      _db.update('feeds', {'title': title}, where: 'url = ?', whereArgs: [url]);

  /// Unsubscribe. Articles, downloads, and cleared records go with it.
  /// Returns downloaded file paths so the caller can delete the files.
  Future<List<String>> removeFeed(String url) async {
    return _db.transaction((txn) async {
      final rows = await txn.rawQuery('''
        SELECT d.local_path FROM downloads d
        JOIN articles a ON a.id = d.article_id
        WHERE a.feed_url = ?''', [url]);
      await txn.delete('feeds', where: 'url = ?', whereArgs: [url]);
      await txn.delete('cleared_articles', where: 'feed_url = ?', whereArgs: [url]);
      return rows.map((r) => r['local_path'] as String).toList();
    });
  }

  // ------------------------------------------------------------- Articles

  /// Store a feed's items. Returns how many were new.
  ///
  /// Existing keys and cleared records are loaded up front and the writes go
  /// out as one batch: on Android each sqflite call crosses the platform
  /// channel, so per-item queries made a 350-episode podcast take ~25 s.
  Future<int> cacheItems(String feedUrl, List<ParsedItem> items) async {
    return _db.transaction((txn) async {
      final now = DateTime.now();
      final stamp = now.toIso8601String();

      final existingRows = await txn.query('articles',
          columns: ['link', 'audio_url'], where: 'feed_url = ?', whereArgs: [feedUrl]);
      final existingLinks = {for (final r in existingRows) r['link'] as String};
      final existingAudio = {
        for (final r in existingRows)
          if (r['audio_url'] != null) r['audio_url'] as String,
      };
      final cleared = {
        for (final r in await txn.query('cleared_articles',
            columns: ['link'], where: 'feed_url = ?', whereArgs: [feedUrl]))
          r['link'] as String,
      };

      final batch = txn.batch();
      final stillListed = <String>[];
      var added = 0;
      var hasAudio = false;

      for (final item in items) {
        final audio = item.audioUrl;
        // Episodes are keyed by audio URL: many podcasts give every episode
        // the same show-page link.
        final key = audio ?? item.link;
        if (audio != null) hasAudio = true;
        if (key.isEmpty) continue;
        if (audio != null && existingAudio.contains(audio)) continue;
        if (existingLinks.contains(key)) continue;
        if (cleared.contains(key)) {
          // Removed by clearOldArticles: don't re-add, but note that the
          // feed still lists it so the record isn't pruned.
          stillListed.add(key);
          continue;
        }
        existingLinks.add(key);
        if (audio != null) existingAudio.add(audio);

        batch.insert(
          'articles',
          {
            'feed_url': feedUrl,
            'title': item.title,
            'link': key,
            'page_link': item.link.isEmpty ? null : item.link,
            'description': item.description,
            'published': item.published,
            'published_sort': publishedSortKey(item.published, now),
            'cached_date': stamp,
            'audio_url': audio,
            'audio_type': item.audioType,
            'audio_length': item.audioLength,
            'duration_seconds': item.durationSeconds,
          },
          conflictAlgorithm: ConflictAlgorithm.ignore,
        );
        added++;
      }

      for (final link in stillListed) {
        batch.update('cleared_articles', {'last_seen': stamp},
            where: 'feed_url = ? AND link = ?', whereArgs: [feedUrl, link]);
      }
      batch.update(
        'feeds',
        {'last_refresh': stamp, if (hasAudio) 'is_podcast': 1},
        where: 'url = ?',
        whereArgs: [feedUrl],
      );
      await batch.commit(noResult: true);
      return added;
    });
  }

  static const _articleSelect = '''
    SELECT a.*, f.title AS feed_title, d.local_path
    FROM articles a
    JOIN feeds f ON f.url = a.feed_url
    LEFT JOIN downloads d ON d.article_id = a.id''';

  Future<List<Article>> getArticles(ArticleFilter filter,
      {int limit = listLimit}) async {
    final where = <String>[];
    final args = <Object?>[];
    if (filter.feedUrl != null) {
      where.add('a.feed_url = ?');
      args.add(filter.feedUrl);
    }
    if (filter.unreadOnly) where.add('a.is_read = 0');
    if (filter.favoritesOnly) where.add('a.is_favorite = 1');
    if (filter.episodesOnly) where.add("a.audio_url IS NOT NULL AND a.audio_url != ''");
    if (filter.downloadedOnly) where.add('d.local_path IS NOT NULL');

    final rows = await _db.rawQuery('''
      $_articleSelect
      ${where.isEmpty ? '' : 'WHERE ${where.join(' AND ')}'}
      ORDER BY a.published_sort DESC, a.id DESC
      LIMIT ?''', [...args, limit]);
    return rows.map(Article.fromRow).toList();
  }

  Future<Article?> getArticle(int id) async {
    final rows = await _db.rawQuery('$_articleSelect WHERE a.id = ?', [id]);
    return rows.isEmpty ? null : Article.fromRow(rows.first);
  }

  Future<void> setRead(int id, bool read) => _db.update(
        'articles',
        {'is_read': read ? 1 : 0, 'read_date': read ? _now() : null},
        where: 'id = ?',
        whereArgs: [id],
      );

  Future<void> setFavorite(int id, bool favorite) => _db.update(
      'articles', {'is_favorite': favorite ? 1 : 0},
      where: 'id = ?', whereArgs: [id]);

  /// Mark everything matching [filter] as read. Returns how many changed.
  Future<int> markAllRead(ArticleFilter filter) async {
    final where = <String>['is_read = 0'];
    final args = <Object?>[];
    if (filter.feedUrl != null) {
      where.add('feed_url = ?');
      args.add(filter.feedUrl);
    }
    if (filter.favoritesOnly) where.add('is_favorite = 1');
    if (filter.episodesOnly) where.add("audio_url IS NOT NULL AND audio_url != ''");
    if (filter.downloadedOnly) {
      where.add('id IN (SELECT article_id FROM downloads)');
    }
    return _db.update('articles', {'is_read': 1, 'read_date': _now()},
        where: where.join(' AND '), whereArgs: args);
  }

  /// Counts for the home screen (not capped by [listLimit]).
  Future<Map<String, int>> getCounts() async {
    final row = (await _db.rawQuery('''
      SELECT COUNT(*) AS total,
             COALESCE(SUM(is_read = 0), 0) AS unread,
             COALESCE(SUM(is_favorite = 1), 0) AS favorites,
             COALESCE(SUM(audio_url IS NOT NULL AND audio_url != ''), 0) AS episodes,
             (SELECT COUNT(*) FROM downloads) AS downloads
      FROM articles''')).first;
    return row.map((k, v) => MapEntry(k, (v as int?) ?? 0));
  }

  // ------------------------------------------------------ Podcast support

  /// Save the playback position. [completed] is only changed when given.
  Future<void> savePlayback(int id, {required int positionMs, bool? completed}) =>
      _db.update(
        'articles',
        {
          'position_ms': positionMs,
          if (completed != null) 'playback_completed': completed ? 1 : 0,
        },
        where: 'id = ?',
        whereArgs: [id],
      );

  Future<void> addDownload(int articleId, String path, int size) => _db.insert(
        'downloads',
        {
          'article_id': articleId,
          'local_path': path,
          'file_size': size,
          'download_date': _now(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );

  /// Forget a download. Returns its file path so the caller can delete it.
  Future<String?> removeDownload(int articleId) async {
    final rows = await _db.query('downloads',
        columns: ['local_path'], where: 'article_id = ?', whereArgs: [articleId]);
    await _db.delete('downloads', where: 'article_id = ?', whereArgs: [articleId]);
    return rows.isEmpty ? null : rows.first['local_path'] as String;
  }

  // -------------------------------------------------------------- Cleanup

  /// Remove articles cached more than [days] ago. Favorites and downloaded
  /// episodes are kept; removed articles are remembered so a refresh doesn't
  /// re-add them as unread. Returns how many were removed.
  Future<int> clearOldArticles({int days = 30, DateTime? now}) async {
    final at = now ?? DateTime.now();
    final cutoff = at.subtract(Duration(days: days)).toIso8601String();
    final stamp = at.toIso8601String();
    const where = '''cached_date < ? AND is_favorite = 0
        AND id NOT IN (SELECT article_id FROM downloads)''';

    return _db.transaction((txn) async {
      await txn.rawInsert('''
        INSERT OR REPLACE INTO cleared_articles (feed_url, link, cleared_date, last_seen)
        SELECT feed_url, link, ?, ? FROM articles WHERE $where''',
          [stamp, stamp, cutoff]);
      final removed = await txn.rawDelete(
          'DELETE FROM articles WHERE $where', [cutoff]);

      // Forget records the feed has stopped listing: not seen for
      // clearedRecordDays although the feed was refreshed since then.
      final stale =
          at.subtract(const Duration(days: clearedRecordDays)).toIso8601String();
      await txn.rawDelete('''
        DELETE FROM cleared_articles
        WHERE last_seen < ?
          AND feed_url IN (SELECT url FROM feeds WHERE last_refresh >= ?)''',
          [stale, stale]);
      return removed;
    });
  }
}
