import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';
import '../services/downloads.dart';
import '../util/dates.dart';
import 'article_screen.dart';
import 'common.dart';
import 'player_bar.dart';

class ArticleListScreen extends StatefulWidget {
  const ArticleListScreen({
    super.key,
    required this.title,
    required this.filter,
    this.singleFeed = false,
  });

  final String title;
  final ArticleFilter filter;

  /// Showing one feed, so the feed name is left off each row.
  final bool singleFeed;

  @override
  State<ArticleListScreen> createState() => _ArticleListScreenState();
}

class _ArticleListScreenState extends State<ArticleListScreen> {
  late bool _unreadOnly = widget.filter.unreadOnly;
  List<Article>? _articles;
  int _loadedRevision = -1;

  ArticleFilter get _filter => ArticleFilter(
        feedUrl: widget.filter.feedUrl,
        unreadOnly: _unreadOnly,
        favoritesOnly: widget.filter.favoritesOnly,
        episodesOnly: widget.filter.episodesOnly,
        downloadedOnly: widget.filter.downloadedOnly,
      );

  Future<void> _load() async {
    final state = context.read<AppState>();
    final revision = state.revision;
    final articles = await state.db.getArticles(_filter);
    if (!mounted) return;
    setState(() {
      _articles = articles;
      _loadedRevision = revision;
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Reload when anything changes articles (refresh, read state, ...).
    // Provider.of (listen: true) is the supported way to depend on a
    // provider outside build.
    final revision = Provider.of<AppState>(context).revision;
    if (revision != _loadedRevision) {
      _loadedRevision = revision;
      _load();
    }
  }

  Future<void> _refresh() async {
    final state = context.read<AppState>();
    final only = widget.filter.feedUrl == null
        ? null
        : state.feeds.where((f) => f.url == widget.filter.feedUrl).toList();
    final result = await state.refresh(only: only);
    if (!mounted) return;
    showMessage(
        context,
        result.errors.isNotEmpty
            ? 'Couldn’t refresh: ${result.errors.values.first}'
            : result.newArticles == 0
                ? 'No new articles'
                : '${result.newArticles} new');
  }

  Future<void> _markAllRead() async {
    final ok = await confirm(context,
        title: 'Mark all as read?',
        message: 'Every article in “${widget.title}” will be marked as read.',
        action: 'Mark read');
    if (!ok || !mounted) return;
    final n = await context.read<AppState>().markAllRead(_filter);
    if (mounted) showMessage(context, 'Marked $n as read');
  }

  @override
  Widget build(BuildContext context) {
    final articles = _articles;
    final canToggleUnread = !widget.filter.unreadOnly;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          if (canToggleUnread)
            IconButton(
              tooltip: _unreadOnly ? 'Show all' : 'Show unread only',
              isSelected: _unreadOnly,
              icon: const Icon(Icons.filter_list),
              selectedIcon: const Icon(Icons.filter_list_off),
              onPressed: () {
                setState(() => _unreadOnly = !_unreadOnly);
                _load();
              },
            ),
          IconButton(
            tooltip: 'Mark all as read',
            icon: const Icon(Icons.done_all),
            onPressed: (articles?.any((a) => !a.isRead) ?? false) ? _markAllRead : null,
          ),
        ],
      ),
      bottomNavigationBar: const PlayerBar(),
      body: articles == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: articles.isEmpty
                  ? ListView(children: [
                      const SizedBox(height: 120),
                      Center(
                        child: Text(
                          _unreadOnly ? 'All caught up' : 'Nothing here yet',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                    ])
                  : ListView.separated(
                      itemCount: articles.length,
                      separatorBuilder: (_, _) => const Divider(height: 1, indent: 16),
                      itemBuilder: (context, i) => _ArticleTile(
                        article: articles[i],
                        showFeed: !widget.singleFeed,
                      ),
                    ),
            ),
    );
  }
}

class _ArticleTile extends StatelessWidget {
  const _ArticleTile({required this.article, required this.showFeed});

  final Article article;
  final bool showFeed;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final state = context.read<AppState>();
    final downloads = context.watch<DownloadManager>();
    final date = formatListDate(article.published);
    final meta = [if (showFeed) article.feedTitle, if (date.isNotEmpty) date].join(' · ');

    Widget? episodeIcon;
    if (article.isEpisode) {
      if (downloads.isDownloading(article.id)) {
        episodeIcon = SizedBox(
          width: 18,
          height: 18,
          child: CircularProgressIndicator(
              strokeWidth: 2, value: downloads.progressOf(article.id)),
        );
      } else {
        episodeIcon = Icon(
          article.isDownloaded ? Icons.download_done : Icons.podcasts,
          size: 18,
          color: scheme.primary,
        );
      }
    }

    return Dismissible(
      key: ValueKey(article.id),
      // Swipe right: read/unread. Swipe left: favorite. The row stays put.
      background: _SwipeBackground(
        alignment: Alignment.centerLeft,
        color: scheme.primaryContainer,
        icon: article.isRead ? Icons.mark_email_unread_outlined : Icons.done,
        label: article.isRead ? 'Unread' : 'Read',
      ),
      secondaryBackground: _SwipeBackground(
        alignment: Alignment.centerRight,
        color: scheme.tertiaryContainer,
        icon: article.isFavorite ? Icons.star_border : Icons.star,
        label: article.isFavorite ? 'Unfavorite' : 'Favorite',
      ),
      confirmDismiss: (direction) async {
        if (direction == DismissDirection.startToEnd) {
          await state.setRead(article, !article.isRead);
        } else {
          await state.setFavorite(article, !article.isFavorite);
        }
        return false;
      },
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        title: Text(
          article.title,
          maxLines: 3,
          overflow: TextOverflow.ellipsis,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: article.isRead ? FontWeight.normal : FontWeight.w600,
            color: article.isRead ? scheme.onSurfaceVariant : scheme.onSurface,
          ),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Row(children: [
            if (!article.isRead) ...[
              Icon(Icons.circle, size: 8, color: scheme.primary),
              const SizedBox(width: 6),
            ],
            Expanded(
              child: Text(meta, maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
            if (article.isFavorite) ...[
              const SizedBox(width: 6),
              Icon(Icons.star, size: 18, color: scheme.tertiary),
            ],
            if (episodeIcon != null) ...[const SizedBox(width: 6), episodeIcon],
          ]),
        ),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => ArticleScreen(articleId: article.id)),
        ),
      ),
    );
  }
}

class _SwipeBackground extends StatelessWidget {
  const _SwipeBackground({
    required this.alignment,
    required this.color,
    required this.icon,
    required this.label,
  });

  final Alignment alignment;
  final Color color;
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) => Container(
        color: color,
        alignment: alignment,
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon),
          const SizedBox(width: 8),
          Text(label),
        ]),
      );
}
