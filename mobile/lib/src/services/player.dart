/// Podcast playback with saved/resumed position and background controls.
library;

import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';
import 'package:just_audio_background/just_audio_background.dart';

import '../data/database.dart';
import '../models.dart';

class PlayerController extends ChangeNotifier {
  PlayerController(this._db, {this.onChanged}) {
    _subs.add(_player.playerStateStream.listen(_onPlayerState));
    _subs.add(_player.positionStream.listen(_onPosition));
  }

  final AppDatabase _db;
  final AudioPlayer _player = AudioPlayer();
  final List<StreamSubscription<dynamic>> _subs = [];

  /// Called when an episode finishes (it's marked read), so lists refresh.
  final VoidCallback? onChanged;

  /// How often the position is saved while playing.
  static const saveInterval = Duration(seconds: 5);

  static const speeds = [0.8, 1.0, 1.2, 1.5, 1.75, 2.0];

  Article? _current;
  DateTime _lastSave = DateTime.fromMillisecondsSinceEpoch(0);
  String? _error;

  /// True while a finished episode is being marked complete, so the pause and
  /// rewind it triggers don't save over the "finished" state.
  bool _finishing = false;

  Article? get current => _current;
  AudioPlayer get audio => _player;
  String? get error => _error;
  bool get isPlaying => _player.playing;

  /// Play [episode], resuming where it was left off. Uses the downloaded file
  /// if there is one, otherwise streams.
  Future<void> play(Article episode) async {
    if (_current?.id == episode.id) {
      unawaited(_player.play());
      return;
    }
    await _savePosition();
    final fresh = await _db.getArticle(episode.id) ?? episode;
    _current = fresh;
    _error = null;
    notifyListeners();

    final local = fresh.downloadPath;
    final uri = (local != null && File(local).existsSync())
        ? Uri.file(local)
        : Uri.parse(fresh.audioUrl!);
    final resumeAt = fresh.playbackCompleted
        ? Duration.zero
        : Duration(milliseconds: fresh.positionMs);
    try {
      await _player.setAudioSource(
        AudioSource.uri(
          uri,
          tag: MediaItem(
            id: '${fresh.id}',
            title: fresh.title,
            album: fresh.feedTitle,
          ),
        ),
        initialPosition: resumeAt,
      );
      unawaited(_player.play());
    } on PlayerException catch (e) {
      _error = 'Could not play this episode (${e.message ?? 'error ${e.code}'})';
      notifyListeners();
    } on PlayerInterruptedException {
      // A newer play() call replaced this one.
    }
  }

  Future<void> togglePlayPause() async {
    if (_player.playing) {
      await _player.pause();
      await _savePosition();
    } else if (_current != null) {
      unawaited(_player.play());
    }
  }

  Future<void> seek(Duration position) async {
    await _player.seek(position);
    await _savePosition();
  }

  Future<void> skip(Duration delta) async {
    final duration = _player.duration;
    var target = _player.position + delta;
    if (target < Duration.zero) target = Duration.zero;
    if (duration != null && target > duration) target = duration;
    await seek(target);
  }

  Future<void> setSpeed(double speed) async {
    await _player.setSpeed(speed);
    notifyListeners();
  }

  /// Stop and close the player bar.
  Future<void> stop() async {
    await _savePosition();
    await _player.stop();
    _current = null;
    notifyListeners();
  }

  void _onPlayerState(PlayerState state) {
    if (state.processingState == ProcessingState.completed) {
      unawaited(_onCompleted());
    } else if (!state.playing) {
      unawaited(_savePosition());
    }
    notifyListeners();
  }

  void _onPosition(Duration position) {
    if (_player.playing && DateTime.now().difference(_lastSave) >= saveInterval) {
      unawaited(_savePosition());
    }
  }

  Future<void> _savePosition() async {
    final episode = _current;
    if (episode == null || _finishing) return;
    _lastSave = DateTime.now();
    final ms = _player.position.inMilliseconds;
    // Progress into a finished episode means it's being replayed; position 0
    // (e.g. the rewind after finishing) leaves the finished flag alone.
    await _db.savePlayback(episode.id, positionMs: ms, completed: ms > 0 ? false : null);
  }

  Future<void> _onCompleted() async {
    final episode = _current;
    if (episode == null || _finishing) return;
    _finishing = true;
    try {
      await _player.pause();
      await _player.seek(Duration.zero);
      await _db.savePlayback(episode.id, positionMs: 0, completed: true);
      await _db.setRead(episode.id, true);
    } finally {
      _finishing = false;
    }
    onChanged?.call();
  }

  @override
  void dispose() {
    for (final s in _subs) {
      s.cancel();
    }
    _player.dispose();
    super.dispose();
  }
}
