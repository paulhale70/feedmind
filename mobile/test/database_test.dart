import 'package:feedmind/src/data/database.dart';
import 'package:feedmind/src/models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

const feed = 'https://example.com/feed';

ParsedItem article(String id, String published) =>
    ParsedItem(title: id, link: 'https://example.com/$id', published: published);

ParsedItem episode(int n, {String page = 'https://example.com/show'}) => ParsedItem(
      title: 'Ep $n',
      link: page,
      published: '2026-10-2${n}T00:00:00Z',
      audioUrl: 'https://cdn.example.com/ep$n.mp3',
      audioType: 'audio/mpeg',
      durationSeconds: 60,
    );

void main() {
  sqfliteFfiInit();
  late AppDatabase db;

  setUp(() async {
    db = await AppDatabase.open(inMemoryDatabasePath, factory: databaseFactoryFfiNoIsolate);
    await db.addFeed(feed, 'Example');
  });
  tearDown(() => db.close());

  test('addFeed rejects duplicates', () async {
    expect(await db.addFeed(feed, 'Again'), isFalse);
    expect((await db.getFeeds()).single.title, 'Example');
  });

  test('articles are ordered by real date, newest first', () async {
    await db.cacheItems(feed, [
      article('old', 'Wed, 01 Jan 2020 00:00:00 GMT'),
      article('new', 'Tue, 27 Oct 2026 00:00:00 GMT'),
      article('mid', '2024-06-01T00:00:00Z'),
    ]);
    final titles = (await db.getArticles(ArticleFilter.all)).map((a) => a.title);
    expect(titles, ['new', 'mid', 'old']);
  });

  test('refresh only adds new items and counts them', () async {
    expect(await db.cacheItems(feed, [article('a', ''), article('b', '')]), 2);
    expect(await db.cacheItems(feed, [article('a', ''), article('c', '')]), 1);
    expect((await db.getFeeds()).single.unreadCount, 3);
  });

  test('episodes keyed by audio URL keep their page link', () async {
    await db.cacheItems(feed, [episode(1, page: 'https://example.com/ep1'), episode(2)]);
    // Same show-page link for both: still two episodes.
    final eps = await db.getArticles(ArticleFilter.episodes);
    expect(eps, hasLength(2));
    final ep1 = eps.firstWhere((e) => e.title == 'Ep 1');
    expect(ep1.link, 'https://cdn.example.com/ep1.mp3');
    expect(ep1.webUrl, 'https://example.com/ep1');
    expect((await db.getFeeds()).single.isPodcast, isTrue);
  });

  test('read, favorite, mark all read, and counts', () async {
    await db.cacheItems(feed, [article('a', ''), article('b', ''), episode(1)]);
    final all = await db.getArticles(ArticleFilter.all);
    await db.setRead(all[0].id, true);
    await db.setFavorite(all[1].id, true);
    expect(await db.getCounts(),
        {'total': 3, 'unread': 2, 'favorites': 1, 'episodes': 1, 'downloads': 0});
    expect(await db.getArticles(ArticleFilter.unread), hasLength(2));
    expect(await db.getArticles(ArticleFilter.favorites), hasLength(1));

    expect(await db.markAllRead(ArticleFilter.episodes), 1);
    expect(await db.markAllRead(const ArticleFilter(feedUrl: feed)), 1);
    expect((await db.getCounts())['unread'], 0);
  });

  test('downloads and playback position', () async {
    await db.cacheItems(feed, [episode(1)]);
    final ep = (await db.getArticles(ArticleFilter.episodes)).single;

    await db.addDownload(ep.id, '/data/episode_1.mp3', 1000);
    expect((await db.getArticle(ep.id))!.downloadPath, '/data/episode_1.mp3');
    expect(await db.getArticles(ArticleFilter.downloads), hasLength(1));

    await db.savePlayback(ep.id, positionMs: 42000);
    expect((await db.getArticle(ep.id))!.positionMs, 42000);
    await db.savePlayback(ep.id, positionMs: 0, completed: true);
    // A later save without `completed` leaves the finished flag alone.
    await db.savePlayback(ep.id, positionMs: 0);
    expect((await db.getArticle(ep.id))!.playbackCompleted, isTrue);

    expect(await db.removeDownload(ep.id), '/data/episode_1.mp3');
    expect((await db.getArticle(ep.id))!.downloadPath, isNull);
  });

  test('removing a feed deletes its articles and returns download paths', () async {
    await db.cacheItems(feed, [episode(1), article('a', '')]);
    final ep = (await db.getArticles(ArticleFilter.episodes)).single;
    await db.addDownload(ep.id, '/data/episode_1.mp3', 1000);

    expect(await db.removeFeed(feed), ['/data/episode_1.mp3']);
    expect(await db.getFeeds(), isEmpty);
    expect(await db.getArticles(ArticleFilter.all), isEmpty);
    expect((await db.getCounts())['downloads'], 0);
  });

  group('clearOldArticles', () {
    test('keeps favorites and downloads; cleared items do not come back', () async {
      final items = [article('fav', ''), article('plain', ''), episode(1)];
      await db.cacheItems(feed, items);
      final all = await db.getArticles(ArticleFilter.all);
      await db.setFavorite(all.firstWhere((a) => a.title == 'fav').id, true);
      await db.addDownload(all.firstWhere((a) => a.title == 'Ep 1').id, '/x.mp3', 1);
      // Run the cleanup as if it were 40 days from now.
      final later = DateTime.now().add(const Duration(days: 40));
      expect(await db.clearOldArticles(days: 30, now: later), 1);
      final left = (await db.getArticles(ArticleFilter.all)).map((a) => a.title);
      expect(left, unorderedEquals(['fav', 'Ep 1']));

      // The feed still lists the cleared article: it must not return.
      expect(await db.cacheItems(feed, items), 0);
      expect(await db.getArticles(ArticleFilter.all), hasLength(2));
    });

    test('nothing recent is removed', () async {
      await db.cacheItems(feed, [article('a', '')]);
      expect(await db.clearOldArticles(days: 30), 0);
    });
  });
}
