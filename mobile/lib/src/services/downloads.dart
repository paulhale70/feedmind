/// Download podcast episodes for offline listening.
library;

import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../data/database.dart';
import '../models.dart';
import 'feed_fetcher.dart' show FetchException, userAgent;

class DownloadManager extends ChangeNotifier {
  DownloadManager(
    this._db, {
    http.Client? client,
    Future<Directory> Function()? baseDir,
    this.onChanged,
  })  : _client = client ?? http.Client(),
        _baseDir = baseDir ?? getApplicationDocumentsDirectory;

  final AppDatabase _db;
  final http.Client _client;
  final Future<Directory> Function() _baseDir;

  /// Called after a download is added or removed, so lists can refresh.
  final VoidCallback? onChanged;

  /// Hard cap on one episode, to bound disk use.
  static const maxBytes = 2 * 1024 * 1024 * 1024;

  /// Minimum time between progress notifications.
  static const progressInterval = Duration(milliseconds: 250);

  final Map<int, double?> _progress = {};
  final Set<int> _cancelled = {};

  bool isDownloading(int articleId) => _progress.containsKey(articleId);

  /// 0..1, or null if the server didn't say how big the file is.
  double? progressOf(int articleId) => _progress[articleId];

  void cancel(int articleId) => _cancelled.add(articleId);

  Future<File> _fileFor(Article episode) async {
    final dir = Directory(p.join((await _baseDir()).path, 'podcasts'));
    await dir.create(recursive: true);
    var ext = p.extension(Uri.tryParse(episode.audioUrl!)?.path ?? '').toLowerCase();
    if (ext.isEmpty || ext.length > 5) ext = '.mp3';
    return File(p.join(dir.path, 'episode_${episode.id}$ext'));
  }

  /// Download [episode]. Throws [FetchException] on failure; returns quietly
  /// if cancelled.
  Future<void> download(Article episode) async {
    if (!episode.isEpisode || isDownloading(episode.id)) return;
    final uri = Uri.tryParse(episode.audioUrl!);
    if (uri == null || !(uri.scheme == 'http' || uri.scheme == 'https')) {
      throw FetchException('Unsupported audio URL');
    }

    _progress[episode.id] = 0;
    _cancelled.remove(episode.id);
    notifyListeners();

    final file = await _fileFor(episode);
    final partial = File('${file.path}.part');
    IOSink? sink;
    try {
      final response = await _client
          .send(http.Request('GET', uri)..headers['User-Agent'] = userAgent)
          .timeout(const Duration(seconds: 30));
      if (response.statusCode >= 400) {
        throw FetchException('Server returned HTTP ${response.statusCode}');
      }
      final total = response.contentLength;
      if (total != null && total > maxBytes) {
        throw FetchException('Episode is too large to download');
      }

      sink = partial.openWrite();
      var received = 0;
      var lastNotify = DateTime.fromMillisecondsSinceEpoch(0);
      await for (final chunk in response.stream) {
        if (_cancelled.contains(episode.id)) break;
        sink.add(chunk);
        received += chunk.length;
        if (received > maxBytes) {
          throw FetchException('Episode is too large to download');
        }
        final now = DateTime.now();
        if (now.difference(lastNotify) >= progressInterval) {
          lastNotify = now;
          _progress[episode.id] =
              (total != null && total > 0) ? received / total : null;
          notifyListeners();
        }
      }
      await sink.close();
      sink = null;

      if (_cancelled.contains(episode.id)) {
        await _deleteQuietly(partial);
        return;
      }
      await partial.rename(file.path);
      await _db.addDownload(episode.id, file.path, received);
      onChanged?.call();
    } on TimeoutException {
      await _deleteQuietly(partial);
      throw FetchException('Timed out downloading the episode');
    } on http.ClientException catch (e) {
      await _deleteQuietly(partial);
      throw FetchException('Network error: ${e.message}');
    } catch (_) {
      await sink?.close();
      await _deleteQuietly(partial);
      rethrow;
    } finally {
      _progress.remove(episode.id);
      _cancelled.remove(episode.id);
      notifyListeners();
    }
  }

  /// Delete a downloaded episode's file and record.
  Future<void> delete(Article episode) async {
    final path = await _db.removeDownload(episode.id);
    if (path != null) await _deleteQuietly(File(path));
    onChanged?.call();
  }

  /// Delete files left behind by removed feeds.
  Future<void> deleteFiles(Iterable<String> paths) async {
    for (final path in paths) {
      await _deleteQuietly(File(path));
    }
  }

  static Future<void> _deleteQuietly(File f) async {
    try {
      if (await f.exists()) await f.delete();
    } on FileSystemException {
      // Already gone or locked; nothing useful to do.
    }
  }
}
