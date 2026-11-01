/// Download feeds over HTTP(S) with a timeout and a size cap.
library;

import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models.dart';
import 'feed_parser.dart';

class FetchException implements Exception {
  FetchException(this.message);
  final String message;
  @override
  String toString() => message;
}

const userAgent = 'FeedMind/1.0 (+https://github.com/paulhale70/feedmind)';

/// Largest feed document accepted, so a hostile or broken server can't
/// exhaust memory.
const maxFeedBytes = 10 * 1024 * 1024;

/// Only http(s) feeds are fetched (no file:, content:, data:, ...).
Uri validateFeedUrl(String input) {
  var text = input.trim();
  if (text.isEmpty) throw FetchException('Enter a feed URL');
  if (!text.contains('://')) text = 'https://$text';
  final uri = Uri.tryParse(text);
  if (uri == null || !(uri.scheme == 'http' || uri.scheme == 'https') ||
      uri.host.isEmpty) {
    throw FetchException('Only http:// and https:// feed URLs are supported');
  }
  return uri;
}

class FeedFetcher {
  FeedFetcher({http.Client? client, this.timeout = const Duration(seconds: 20)})
      : _client = client ?? http.Client();

  final http.Client _client;
  final Duration timeout;

  Future<ParsedFeed> fetch(String url) async {
    final uri = validateFeedUrl(url);
    final request = http.Request('GET', uri)
      ..headers['User-Agent'] = userAgent
      ..headers['Accept'] =
          'application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5';

    final List<int> bytes;
    try {
      final response = await _client.send(request).timeout(timeout);
      if (response.statusCode >= 400) {
        throw FetchException('Server returned HTTP ${response.statusCode}');
      }
      bytes = await _readCapped(response.stream).timeout(timeout);
    } on TimeoutException {
      throw FetchException('Timed out contacting ${uri.host}');
    } on http.ClientException catch (e) {
      throw FetchException('Network error: ${e.message}');
    }
    return parseFeed(decodeFeedBytes(bytes), feedUrl: url);
  }

  Future<List<int>> _readCapped(Stream<List<int>> stream) async {
    final out = <int>[];
    await for (final chunk in stream) {
      out.addAll(chunk);
      if (out.length > maxFeedBytes) {
        throw FetchException('Feed is larger than ${maxFeedBytes ~/ (1024 * 1024)} MB');
      }
    }
    return out;
  }

  void close() => _client.close();
}

final _encodingDecl = RegExp(r'''encoding\s*=\s*["']([A-Za-z0-9._-]+)["']''');

/// Decode feed bytes using the encoding in the XML declaration (UTF-8 by
/// default; Latin-1/Windows-1252 feeds still exist). Strips a UTF-8 BOM.
String decodeFeedBytes(List<int> bytes) {
  final head = latin1.decode(bytes.take(200).toList(), allowInvalid: true);
  final declared = _encodingDecl.firstMatch(head)?.group(1)?.toLowerCase();
  if (declared == 'iso-8859-1' || declared == 'latin1' || declared == 'windows-1252') {
    return latin1.decode(bytes, allowInvalid: true);
  }
  var text = utf8.decode(bytes, allowMalformed: true);
  if (text.startsWith('﻿')) text = text.substring(1);
  return text;
}
