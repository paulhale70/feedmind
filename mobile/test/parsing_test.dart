import 'dart:convert';

import 'package:feedmind/src/services/feed_fetcher.dart';
import 'package:feedmind/src/services/feed_parser.dart';
import 'package:feedmind/src/services/opml.dart';
import 'package:feedmind/src/util/dates.dart';
import 'package:feedmind/src/util/html_text.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const feedUrl = 'https://example.com/feed';

void main() {
  group('dates', () {
    test('parses RFC 822 with named and numeric zones', () {
      expect(parsePublishedDate('Tue, 27 Oct 2026 10:30:00 GMT'),
          DateTime.utc(2026, 10, 27, 10, 30));
      expect(parsePublishedDate('Tue, 27 Oct 2026 03:30:00 -0700'),
          DateTime.utc(2026, 10, 27, 10, 30));
      expect(parsePublishedDate('27 Oct 2026 02:30:00 PST'),
          DateTime.utc(2026, 10, 27, 10, 30));
    });

    test('parses ISO 8601 and bare dates', () {
      expect(parsePublishedDate('2026-10-27T10:30:00Z'), DateTime.utc(2026, 10, 27, 10, 30));
      expect(parsePublishedDate('2026-10-27T12:30:00+02:00'),
          DateTime.utc(2026, 10, 27, 10, 30));
      expect(parsePublishedDate('2026-10-27T10:30:00'), DateTime.utc(2026, 10, 27, 10, 30));
      expect(parsePublishedDate('2026-10-27'), DateTime.utc(2026, 10, 27));
    });

    test('returns null for garbage', () {
      for (final s in [null, '', 'not a date', 'Someday soon']) {
        expect(parsePublishedDate(s), isNull, reason: '$s');
      }
    });

    test('sort key orders by real date, not string', () {
      final now = DateTime.utc(2026, 11, 1);
      final older = publishedSortKey('Wed, 01 Jan 2020 00:00:00 GMT', now);
      final newer = publishedSortKey('Tue, 27 Oct 2026 00:00:00 GMT', now);
      expect(newer.compareTo(older), greaterThan(0));
      expect(publishedSortKey('garbage', now), '2026-11-01T00:00:00');
    });

    test('list date formats', () {
      final now = DateTime(2026, 11, 1, 12);
      expect(formatListDate('2026-10-27', now: now), 'Oct 27');
      expect(formatListDate('2025-03-04', now: now), 'Mar 4, 2025');
      expect(formatListDate('', now: now), '');
      expect(formatListDate('sometime last week, probably', now: now), 'sometime last we');
    });

    test('duration format', () {
      expect(formatDuration(const Duration(seconds: 75)), '1:15');
      expect(formatDuration(const Duration(hours: 1, minutes: 2, seconds: 3)), '1:02:03');
    });
  });

  group('html to text', () {
    test('keeps paragraphs, decodes entities, drops scripts', () {
      const html = '<p>Hello &amp; welcome</p><script>alert(1)</script>'
          '<p>It&#8217;s <b>fine</b>&nbsp;&hellip;</p><ul><li>one</li><li>two</li></ul>';
      // A paragraph followed by a list leaves one blank line between them.
      expect(htmlToText(html), 'Hello & welcome\nIt’s fine …\n\n• one\n• two');
    });
  });

  group('feed parser', () {
    test('RSS 2.0 with podcast enclosure and itunes duration', () {
      const xml = '''<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
          xmlns:atom="http://www.w3.org/2005/Atom"><channel>
        <title>Show</title>
        <atom:link rel="self" href="https://example.com/feed"/>
        <item>
          <title>Episode 1</title>
          <atom:link rel="self" href="https://example.com/wrong"/>
          <link>https://example.com/ep1</link>
          <description><![CDATA[<p>Notes</p>]]></description>
          <pubDate>Tue, 27 Oct 2026 10:30:00 GMT</pubDate>
          <enclosure url="https://cdn.example.com/ep1.mp3" type="audio/mpeg" length="1234"/>
          <itunes:duration>1:02:03</itunes:duration>
        </item>
      </channel></rss>''';
      final feed = parseFeed(xml, feedUrl: feedUrl);
      expect(feed.title, 'Show');
      final item = feed.items.single;
      expect(item.link, 'https://example.com/ep1');
      expect(item.description, 'Notes');
      expect(item.audioUrl, 'https://cdn.example.com/ep1.mp3');
      expect(item.audioLength, 1234);
      expect(item.durationSeconds, 3723);
    });

    test('RSS 1.0 (RDF) with dc:date', () {
      const xml = '''<?xml version="1.0"?>
      <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
               xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <channel rdf:about="https://example.com/"><title>RDF Example</title></channel>
        <item rdf:about="https://example.com/a">
          <title>First</title><link>https://example.com/a</link>
          <dc:date>2026-10-27T10:30:00Z</dc:date>
        </item>
        <item rdf:about="https://example.com/b"><title>Second</title>
          <link>
            https://example.com/b
          </link></item>
      </rdf:RDF>''';
      final feed = parseFeed(xml, feedUrl: feedUrl);
      expect(feed.title, 'RDF Example');
      expect(feed.items.map((i) => i.link), ['https://example.com/a', 'https://example.com/b']);
      expect(feed.items.first.published, '2026-10-27T10:30:00Z');
    });

    test('Atom picks the article page link and finds enclosures', () {
      const xml = '''<feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:media="http://search.yahoo.com/mrss/">
        <title>Atom Example</title>
        <entry>
          <title>Entry</title>
          <media:title>Wrong title</media:title>
          <link rel="self" href="https://example.com/feed/e"/>
          <link rel="enclosure" type="audio/mpeg" href="https://example.com/e.mp3"/>
          <link rel="alternate" type="text/html" href="https://example.com/e"/>
          <updated>2026-10-27T10:30:00Z</updated>
          <content type="html">&lt;p&gt;Body&lt;/p&gt;</content>
        </entry>
      </feed>''';
      final item = parseFeed(xml, feedUrl: feedUrl).items.single;
      expect(item.title, 'Entry');
      expect(item.link, 'https://example.com/e');
      expect(item.audioUrl, 'https://example.com/e.mp3');
      expect(item.description, 'Body');
      expect(item.published, '2026-10-27T10:30:00Z');
    });

    test('rejects non-feeds', () {
      expect(() => parseFeed('<html><body/></html>', feedUrl: feedUrl),
          throwsA(isA<FeedFormatException>()));
      expect(() => parseFeed('not xml <', feedUrl: feedUrl),
          throwsA(isA<FeedFormatException>()));
    });

    test('itunes duration formats', () {
      expect(parseItunesDuration('90'), 90);
      expect(parseItunesDuration('01:30'), 90);
      expect(parseItunesDuration('1:00:00'), 3600);
      expect(parseItunesDuration('soon'), 0);
    });
  });

  group('fetcher', () {
    test('only http(s) URLs; adds https:// when missing', () {
      expect(validateFeedUrl('example.com/feed').toString(), 'https://example.com/feed');
      for (final bad in ['file:///etc/passwd', 'javascript:alert(1)', '', 'ftp://x/y']) {
        expect(() => validateFeedUrl(bad), throwsA(isA<FetchException>()), reason: bad);
      }
    });

    test('fetches and parses', () async {
      final client = MockClient((req) async {
        expect(req.headers['User-Agent'], userAgent);
        return http.Response(
            '<rss><channel><title>T</title><item><title>A</title>'
            '<link>https://example.com/a</link></item></channel></rss>',
            200);
      });
      final feed = await FeedFetcher(client: client).fetch(feedUrl);
      expect(feed.items.single.title, 'A');
    });

    test('reports HTTP errors', () async {
      final client = MockClient((_) async => http.Response('nope', 404));
      expect(FeedFetcher(client: client).fetch(feedUrl),
          throwsA(isA<FetchException>().having((e) => e.message, 'message', contains('404'))));
    });

    test('rejects oversized feeds', () async {
      final client = MockClient.streaming((_, _) async => http.StreamedResponse(
          Stream.fromIterable(List.generate(11, (_) => List.filled(1024 * 1024, 32))),
          200));
      expect(FeedFetcher(client: client).fetch(feedUrl), throwsA(isA<FetchException>()));
    });

    test('decodes Latin-1 feeds and strips a UTF-8 BOM', () {
      final latin = latin1.encode('<?xml version="1.0" encoding="ISO-8859-1"?><x>café</x>');
      expect(decodeFeedBytes(latin), contains('café'));
      expect(decodeFeedBytes([0xEF, 0xBB, 0xBF, ...utf8.encode('<x/>')]), '<x/>');
    });
  });

  group('OPML', () {
    test('round-trips and de-duplicates nested outlines', () {
      const opml = '''<opml version="2.0"><body>
        <outline text="News">
          <outline text="BBC" xmlUrl="https://feeds.bbci.co.uk/news/rss.xml"/>
          <outline title="Dup" xmlUrl="https://feeds.bbci.co.uk/news/rss.xml"/>
        </outline>
        <outline text="No URL"/>
        <outline xmlUrl="https://example.com/pod.xml"/>
      </body></opml>''';
      final feeds = parseOpml(opml);
      expect(feeds.map((f) => f.title), ['BBC', 'https://example.com/pod.xml']);

      final again = parseOpml(buildOpml(feeds));
      expect(again.map((f) => f.url), feeds.map((f) => f.url));
      expect(again.map((f) => f.title), feeds.map((f) => f.title));
    });

    test('invalid OPML is a FormatException', () {
      expect(() => parseOpml('<<<'), throwsFormatException);
    });
  });
}
