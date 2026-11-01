/// OPML import/export, compatible with the desktop app and other readers.
library;

import 'package:xml/xml.dart';

class OpmlFeed {
  const OpmlFeed({required this.url, required this.title});
  final String url;
  final String title;
}

/// All feeds (outlines with an xmlUrl) at any depth, de-duplicated by URL.
List<OpmlFeed> parseOpml(String text) {
  final XmlDocument doc;
  try {
    doc = XmlDocument.parse(text);
  } on XmlException catch (e) {
    throw FormatException('Not a valid OPML file: ${e.message}');
  }
  final seen = <String>{};
  final feeds = <OpmlFeed>[];
  for (final outline in doc.findAllElements('outline', namespaceUri: '*')) {
    final url = outline.getAttribute('xmlUrl')?.trim() ?? '';
    if (url.isEmpty || !seen.add(url)) continue;
    final title = (outline.getAttribute('title') ??
            outline.getAttribute('text') ??
            url)
        .trim();
    feeds.add(OpmlFeed(url: url, title: title.isEmpty ? url : title));
  }
  return feeds;
}

String buildOpml(List<OpmlFeed> feeds, {DateTime? now}) {
  final builder = XmlBuilder()..processing('xml', 'version="1.0" encoding="UTF-8"');
  builder.element('opml', attributes: {'version': '2.0'}, nest: () {
    builder.element('head', nest: () {
      builder.element('title', nest: 'FeedMind subscriptions');
      builder.element('dateCreated',
          nest: (now ?? DateTime.now()).toUtc().toIso8601String());
    });
    builder.element('body', nest: () {
      for (final f in feeds) {
        builder.element('outline', attributes: {
          'type': 'rss',
          'text': f.title,
          'title': f.title,
          'xmlUrl': f.url,
        });
      }
    });
  });
  return builder.buildDocument().toXmlString(pretty: true);
}
