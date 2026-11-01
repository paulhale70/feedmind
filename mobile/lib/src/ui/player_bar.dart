import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import 'package:provider/provider.dart';

import '../services/player.dart';
import '../util/dates.dart';

/// Mini player shown at the bottom of every screen while an episode is
/// loaded. Tap to open the full player.
class PlayerBar extends StatelessWidget {
  const PlayerBar({super.key});

  @override
  Widget build(BuildContext context) {
    final player = context.watch<PlayerController>();
    final episode = player.current;
    if (episode == null) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;

    return Material(
      color: scheme.surfaceContainerHigh,
      child: SafeArea(
        top: false,
        child: InkWell(
          onTap: () => showModalBottomSheet<void>(
            context: context,
            isScrollControlled: true,
            showDragHandle: true,
            builder: (_) => const _PlayerSheet(),
          ),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            StreamBuilder<Duration>(
              stream: player.audio.positionStream,
              builder: (context, snap) {
                final total = player.audio.duration;
                final pos = snap.data ?? Duration.zero;
                final value = (total == null || total.inMilliseconds == 0)
                    ? 0.0
                    : (pos.inMilliseconds / total.inMilliseconds).clamp(0.0, 1.0);
                return LinearProgressIndicator(value: value, minHeight: 2);
              },
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 4, 4),
              child: Row(children: [
                Icon(Icons.podcasts, color: scheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(episode.title, maxLines: 1, overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleSmall),
                    Text(episode.feedTitle, maxLines: 1, overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall),
                  ]),
                ),
                _PlayPauseButton(player: player),
                IconButton(
                  tooltip: 'Close player',
                  icon: const Icon(Icons.close),
                  onPressed: player.stop,
                ),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}

class _PlayPauseButton extends StatelessWidget {
  const _PlayPauseButton({required this.player, this.size = 24});
  final PlayerController player;
  final double size;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<PlayerState>(
      stream: player.audio.playerStateStream,
      builder: (context, snap) {
        final state = snap.data;
        final loading = state?.processingState == ProcessingState.loading ||
            state?.processingState == ProcessingState.buffering;
        if (loading) {
          return SizedBox(
            width: size + 24,
            height: size + 24,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: const CircularProgressIndicator(strokeWidth: 2),
            ),
          );
        }
        final playing = state?.playing ?? false;
        return IconButton(
          iconSize: size,
          tooltip: playing ? 'Pause' : 'Play',
          icon: Icon(playing ? Icons.pause : Icons.play_arrow),
          onPressed: player.togglePlayPause,
        );
      },
    );
  }
}

class _PlayerSheet extends StatelessWidget {
  const _PlayerSheet();

  @override
  Widget build(BuildContext context) {
    final player = context.watch<PlayerController>();
    final episode = player.current;
    final theme = Theme.of(context);
    if (episode == null) return const SizedBox(height: 120);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(episode.title, textAlign: TextAlign.center, maxLines: 3,
              overflow: TextOverflow.ellipsis, style: theme.textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(episode.feedTitle, style: theme.textTheme.bodyMedium),
          const SizedBox(height: 16),
          StreamBuilder<Duration>(
            stream: player.audio.positionStream,
            builder: (context, snap) {
              final total = player.audio.duration ?? Duration.zero;
              var pos = snap.data ?? Duration.zero;
              if (pos > total) pos = total;
              final max = total.inMilliseconds.toDouble();
              return Column(children: [
                Slider(
                  value: max == 0 ? 0 : pos.inMilliseconds.toDouble().clamp(0, max),
                  max: max == 0 ? 1 : max,
                  onChanged: max == 0
                      ? null
                      : (v) => player.seek(Duration(milliseconds: v.round())),
                ),
                Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                  Text(formatDuration(pos)),
                  Text('-${formatDuration(total - pos)}'),
                ]),
              ]);
            },
          ),
          const SizedBox(height: 8),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            IconButton(
              iconSize: 32,
              tooltip: 'Back 10 seconds',
              icon: const Icon(Icons.replay_10),
              onPressed: () => player.skip(const Duration(seconds: -10)),
            ),
            const SizedBox(width: 16),
            _PlayPauseButton(player: player, size: 48),
            const SizedBox(width: 16),
            IconButton(
              iconSize: 32,
              tooltip: 'Forward 30 seconds',
              icon: const Icon(Icons.forward_30),
              onPressed: () => player.skip(const Duration(seconds: 30)),
            ),
          ]),
          const SizedBox(height: 8),
          StreamBuilder<double>(
            stream: player.audio.speedStream,
            builder: (context, snap) {
              final speed = snap.data ?? 1.0;
              return SegmentedButton<double>(
                showSelectedIcon: false,
                segments: [
                  for (final s in PlayerController.speeds)
                    ButtonSegment(value: s, label: Text('${_trim(s)}×')),
                ],
                selected: {PlayerController.speeds.contains(speed) ? speed : 1.0},
                onSelectionChanged: (v) => player.setSpeed(v.first),
              );
            },
          ),
        ]),
      ),
    );
  }

  static String _trim(double v) =>
      v == v.roundToDouble() ? v.toStringAsFixed(0) : v.toString();
}
