import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';

import '../app_state.dart';
import '../models.dart';
import '../services/downloads.dart';
import '../services/player.dart';
import '../util/dates.dart';
import 'common.dart';
import 'player_bar.dart';

/// One article or podcast episode. Opening it marks it as read.
class ArticleScreen extends StatefulWidget {
  const ArticleScreen({super.key, required this.articleId});
  final int articleId;

  @override
  State<ArticleScreen> createState() => _ArticleScreenState();
}

class _ArticleScreenState extends State<ArticleScreen> {
  Article? _article;
  int _loadedRevision = -1;
  bool _markedRead = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Provider.of (listen: true) is the supported way to depend on a
    // provider outside build.
    final revision = Provider.of<AppState>(context).revision;
    if (revision != _loadedRevision) {
      _loadedRevision = revision;
      _load();
    }
  }

  Future<void> _load() async {
    final state = context.read<AppState>();
    final article = await state.db.getArticle(widget.articleId);
    if (!mounted) return;
    setState(() => _article = article);
    if (article != null && !article.isRead && !_markedRead) {
      _markedRead = true;
      await state.setRead(article, true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final article = _article;
    if (article == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final state = context.read<AppState>();
    final theme = Theme.of(context);
    final date = formatListDate(article.published);
    final hasLink = article.webUrl.startsWith('http');

    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
            tooltip: article.isFavorite ? 'Remove from favorites' : 'Add to favorites',
            icon: Icon(article.isFavorite ? Icons.star : Icons.star_border),
            onPressed: () => state.setFavorite(article, !article.isFavorite),
          ),
          IconButton(
            tooltip: article.isRead ? 'Mark as unread' : 'Mark as read',
            icon: Icon(article.isRead
                ? Icons.mark_email_unread_outlined
                : Icons.mark_email_read_outlined),
            onPressed: () => state.setRead(article, !article.isRead),
          ),
          if (hasLink)
            IconButton(
              tooltip: 'Share',
              icon: const Icon(Icons.share_outlined),
              onPressed: () => SharePlus.instance.share(
                  ShareParams(uri: Uri.parse(article.webUrl), subject: article.title)),
            ),
        ],
      ),
      bottomNavigationBar: const PlayerBar(),
      body: SelectionArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
          children: [
            Text(article.title, style: theme.textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(
              [article.feedTitle, if (date.isNotEmpty) date].join(' · '),
              style: theme.textTheme.bodyMedium
                  ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
            ),
            if (article.isEpisode) ...[
              const SizedBox(height: 16),
              _EpisodeControls(article: article),
            ],
            const SizedBox(height: 20),
            if (article.description.isNotEmpty)
              Text(article.description,
                  style: theme.textTheme.bodyLarge?.copyWith(height: 1.5))
            else
              Text('No summary in the feed.',
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            if (hasLink) ...[
              const SizedBox(height: 24),
              OutlinedButton.icon(
                onPressed: () => openInBrowser(context, article.webUrl),
                icon: const Icon(Icons.open_in_browser),
                label: Text(article.isEpisode ? 'Open episode page' : 'Read full article'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _EpisodeControls extends StatelessWidget {
  const _EpisodeControls({required this.article});
  final Article article;

  @override
  Widget build(BuildContext context) {
    final player = context.watch<PlayerController>();
    final downloads = context.watch<DownloadManager>();
    final isCurrent = player.current?.id == article.id;
    final playing = isCurrent && player.isPlaying;

    final resumeAt = Duration(milliseconds: article.positionMs);
    final total = Duration(seconds: article.durationSeconds);
    String playLabel;
    if (playing) {
      playLabel = 'Pause';
    } else if (!article.playbackCompleted && resumeAt > const Duration(seconds: 5)) {
      playLabel = 'Resume from ${formatDuration(resumeAt)}';
    } else {
      playLabel = 'Play';
    }

    final downloading = downloads.isDownloading(article.id);
    final progress = downloads.progressOf(article.id);

    Future<void> download() async {
      try {
        await downloads.download(article);
      } catch (e) {
        if (context.mounted) showMessage(context, 'Download failed: $e');
      }
    }

    return Card.filled(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Row(children: [
            const Icon(Icons.podcasts),
            const SizedBox(width: 8),
            Expanded(
              child: Text([
                if (article.durationSeconds > 0) formatDuration(total),
                if (article.playbackCompleted) 'Played',
                if (article.isDownloaded) 'Downloaded',
              ].join(' · ')),
            ),
          ]),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: FilledButton.icon(
                onPressed: () => playing ? player.togglePlayPause() : player.play(article),
                icon: Icon(playing ? Icons.pause : Icons.play_arrow),
                label: Text(playLabel, overflow: TextOverflow.ellipsis),
              ),
            ),
            const SizedBox(width: 8),
            if (downloading)
              OutlinedButton.icon(
                onPressed: () => downloads.cancel(article.id),
                icon: SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2, value: progress),
                ),
                label: Text(progress == null ? 'Cancel' : '${(progress * 100).round()}%'),
              )
            else if (article.isDownloaded)
              OutlinedButton.icon(
                onPressed: () async {
                  if (isCurrent) await player.stop();
                  await downloads.delete(article);
                },
                icon: const Icon(Icons.delete_outline),
                label: const Text('Delete'),
              )
            else
              OutlinedButton.icon(
                onPressed: download,
                icon: const Icon(Icons.download),
                label: const Text('Download'),
              ),
          ]),
          if (isCurrent && player.error != null) ...[
            const SizedBox(height: 8),
            Text(player.error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ],
        ]),
      ),
    );
  }
}
