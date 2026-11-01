/// Parse RSS 2.0, RSS 1.0 (RDF), and Atom feeds.
///
/// Element names are matched by local name in any namespace, so RSS 1.0
/// (which puts item/title/link in the http://purl.org/rss/1.0/ namespace) and
/// default-namespaced Atom are handled by the same lookups. The xml package
/// does not resolve external entities, so XXE is not a concern.
library;

import 'package:xml/xml.dart';

import '../models.dart';
import '../util/html_text.dart';

class FeedFormatException implements Exception {
  FeedFormatException(this.message);
  final String message;
  @override
  String toString() => message;
}

const _itunesNs = 'http://www.itunes.com/dtds/podcast-1.0.dtd';

/// Atom link relations that never point at the article's web page.
const _nonArticleRels = {'self', 'enclosure', 'edit', 'replies', 'license'};

ParsedFeed parseFeed(String xmlText, {required String feedUrl}) {
  final XmlDocument doc;
  try {
    doc = XmlDocument.parse(xmlText);
  } on XmlException catch (e) {
    throw FeedFormatException('Not a valid feed (XML error: ${e.message})');
  }
  final root = doc.rootElement;
  switch (root.name.local.toLowerCase()) {
    case 'feed':
      return _parseAtom(root, feedUrl);
    case 'rss':
    case 'rdf':
      return _parseRss(root, feedUrl);
    default:
      throw FeedFormatException(
          'Not an RSS or Atom feed (root element <${root.name.qualified}>)');
  }
}

XmlElement? _child(XmlElement e, String local) =>
    e.findElements(local, namespaceUri: '*').firstOrNull;

String? _childText(XmlElement e, String local) => _child(e, local)?.innerText;

const _rss1Ns = 'http://purl.org/rss/1.0/';

/// Text of an RSS core element (no namespace in RSS 2.0, the RSS 1.0
/// namespace in RDF feeds). Ignores same-named elements from other
/// namespaces, e.g. an <atom:link> that comes before an item's <link>.
String? _rssText(XmlElement e, String local) => e
    .findElements(local, namespaceUri: '*')
    .where((c) => c.name.namespaceUri == null || c.name.namespaceUri == _rss1Ns)
    .firstOrNull
    ?.innerText;

ParsedFeed _parseRss(XmlElement root, String feedUrl) {
  final channel = root.findAllElements('channel', namespaceUri: '*').firstOrNull;
  final feedTitle = _clean(channel == null ? null : _rssText(channel, 'title'));

  final items = <ParsedItem>[];
  for (final item in root.findAllElements('item', namespaceUri: '*')) {
    final enclosure = _child(item, 'enclosure');
    final duration = item
        .findElements('duration', namespaceUri: _itunesNs)
        .firstOrNull
        ?.innerText;
    final audioUrl = enclosure?.getAttribute('url')?.trim();

    items.add(ParsedItem(
      title: _clean(_rssText(item, 'title'), fallback: 'No Title'),
      link: (_rssText(item, 'link') ?? '').trim(),
      description: htmlToText(
          _rssText(item, 'description') ?? _childText(item, 'encoded')),
      published:
          (_rssText(item, 'pubDate') ?? _childText(item, 'date') ?? '').trim(),
      audioUrl: (audioUrl == null || audioUrl.isEmpty) ? null : audioUrl,
      audioType: enclosure?.getAttribute('type'),
      audioLength: int.tryParse(enclosure?.getAttribute('length') ?? ''),
      durationSeconds: parseItunesDuration(duration),
    ));
  }
  return ParsedFeed(title: feedTitle.isEmpty ? feedUrl : feedTitle, items: items);
}

const _atomNs = 'http://www.w3.org/2005/Atom';

/// Atom elements: the Atom namespace (or none, for sloppy feeds). Ignores
/// same-named elements from extensions such as media:title.
Iterable<XmlElement> _atomChildren(XmlElement e, String local) => e
    .findElements(local, namespaceUri: '*')
    .where((c) => c.name.namespaceUri == null || c.name.namespaceUri == _atomNs);

String? _atomText(XmlElement e, String local) =>
    _atomChildren(e, local).firstOrNull?.innerText;

ParsedFeed _parseAtom(XmlElement root, String feedUrl) {
  final feedTitle = _clean(_atomText(root, 'title'));
  final items = <ParsedItem>[];

  for (final entry in _atomChildren(root, 'entry')) {
    final links = _atomChildren(entry, 'link').toList();
    final enclosure = links
        .where((l) => l.getAttribute('rel') == 'enclosure')
        .firstOrNull;
    final audioUrl = enclosure?.getAttribute('href')?.trim();

    items.add(ParsedItem(
      title: _clean(_atomText(entry, 'title'), fallback: 'No Title'),
      link: atomArticleLink(links),
      description:
          htmlToText(_atomText(entry, 'content') ?? _atomText(entry, 'summary')),
      published:
          (_atomText(entry, 'published') ?? _atomText(entry, 'updated') ?? '')
              .trim(),
      audioUrl: (audioUrl == null || audioUrl.isEmpty) ? null : audioUrl,
      audioType: enclosure?.getAttribute('type'),
      audioLength: int.tryParse(enclosure?.getAttribute('length') ?? ''),
    ));
  }
  return ParsedFeed(title: feedTitle.isEmpty ? feedUrl : feedTitle, items: items);
}

/// Pick an Atom entry's web-page link: rel="alternate" (the default when rel
/// is absent) with an HTML type first, then any alternate, then any link that
/// isn't clearly non-article (self, enclosure, replies, ...).
String atomArticleLink(List<XmlElement> links) {
  String? alternate;
  String? fallback;
  for (final link in links) {
    final href = link.getAttribute('href')?.trim() ?? '';
    if (href.isEmpty) continue;
    final rel = link.getAttribute('rel') ?? 'alternate';
    if (rel == 'alternate') {
      final type = link.getAttribute('type') ?? 'text/html';
      if (type == 'text/html' || type == 'application/xhtml+xml') return href;
      alternate ??= href;
    } else if (!_nonArticleRels.contains(rel)) {
      fallback ??= href;
    }
  }
  return alternate ?? fallback ?? '';
}

/// Parse an itunes:duration value: seconds, MM:SS, or HH:MM:SS.
int parseItunesDuration(String? value) {
  if (value == null) return 0;
  final parts = value.trim().split(':');
  if (parts.isEmpty || parts.length > 3) return 0;
  var total = 0;
  for (final part in parts) {
    final n = int.tryParse(part.trim());
    if (n == null) return 0;
    total = total * 60 + n;
  }
  return total;
}

String _clean(String? text, {String fallback = ''}) {
  if (text == null) return fallback;
  final cleaned = htmlToText(text).replaceAll('\n', ' ').trim();
  return cleaned.isEmpty ? fallback : cleaned;
}
