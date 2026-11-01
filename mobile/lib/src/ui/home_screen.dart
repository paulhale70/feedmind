import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';
import '../services/downloads.dart';
import 'article_list_screen.dart';
import 'common.dart';
import 'player_bar.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  /// Feeds older than this are refreshed when the app opens.
  static const _staleAfter = Duration(minutes: 30);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final state = context.read<AppState>();
      final now = DateTime.now();
      final stale = state.feeds.any((f) =>
          f.lastRefresh == null || now.difference(f.lastRefresh!) > _staleAfter);
      if (stale) _refresh(quiet: true);
    });
  }

  Future<void> _refresh({List<Feed>? only, bool quiet = false}) async {
    final result = await context.read<AppState>().refresh(only: only);
    if (!mounted) return;
    if (result.errors.isNotEmpty) {
      final names = result.errors.keys.take(3).join(', ');
      final more = result.errors.length > 3 ? ' and ${result.errors.length - 3} more' : '';
      showMessage(context, 'Couldn’t refresh $names$more');
    } else if (!quiet) {
      showMessage(
          context,
          result.newArticles == 0
              ? 'No new articles'
              : '${result.newArticles} new article${result.newArticles == 1 ? '' : 's'}');
    }
  }

  void _open(String title, ArticleFilter filter, {bool singleFeed = false}) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ArticleListScreen(
            title: title, filter: filter, singleFeed: singleFeed),
      ),
    );
  }

  Future<void> _addFeed() async {
    final title = await showDialog<String>(
      context: context,
      builder: (_) => const _AddFeedDialog(),
    );
    if (title != null && mounted) showMessage(context, 'Added $title');
  }

  Future<void> _importOpml() async {
    final files = await FilePicker.pickFiles(
      dialogTitle: 'Import OPML',
      type: FileType.any,
    );
    if (files.isEmpty || !mounted) return;
    final state = context.read<AppState>();
    try {
      final text = await files.first.xFile.readAsString();
      final (added, existing, invalid) = await state.importOpml(text);
      if (!mounted) return;
      final parts = [
        '$added added',
        if (existing > 0) '$existing already followed',
        if (invalid > 0) '$invalid skipped',
      ];
      showMessage(context, 'Import: ${parts.join(', ')}');
      if (added > 0) await _refresh(only: state.unfetchedFeeds, quiet: true);
    } on FormatException catch (e) {
      if (mounted) showMessage(context, e.message);
    }
  }

  Future<void> _exportOpml() async {
    final state = context.read<AppState>();
    if (state.feeds.isEmpty) {
      showMessage(context, 'No feeds to export');
      return;
    }
    final saved = await FilePicker.saveFile(
      dialogTitle: 'Export OPML',
      fileName: 'feedmind-subscriptions.opml',
      bytes: Uint8List.fromList(utf8.encode(state.exportOpml())),
      mimeType: 'text/x-opml',
    );
    if (saved != null && mounted) {
      showMessage(context, 'Exported ${state.feeds.length} feeds');
    }
  }

  Future<void> _clearOld() async {
    final ok = await confirm(
      context,
      title: 'Clear old articles?',
      message: 'Removes articles older than 30 days. Favorites and downloaded '
          'episodes are kept.',
      action: 'Clear',
    );
    if (!ok || !mounted) return;
    final n = await context.read<AppState>().clearOldArticles();
    if (mounted) showMessage(context, 'Removed $n old article${n == 1 ? '' : 's'}');
  }

  Future<void> _feedActions(Feed feed) async {
    final action = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          ListTile(
            title: Text(feed.title, style: Theme.of(context).textTheme.titleMedium),
            subtitle: Text(feed.url, maxLines: 1, overflow: TextOverflow.ellipsis),
          ),
          const Divider(),
          ListTile(
              leading: const Icon(Icons.refresh),
              title: const Text('Refresh'),
              onTap: () => Navigator.pop(context, 'refresh')),
          ListTile(
              leading: const Icon(Icons.done_all),
              title: const Text('Mark all as read'),
              onTap: () => Navigator.pop(context, 'read')),
          ListTile(
              leading: const Icon(Icons.edit_outlined),
              title: const Text('Rename'),
              onTap: () => Navigator.pop(context, 'rename')),
          ListTile(
              leading: Icon(Icons.delete_outline,
                  color: Theme.of(context).colorScheme.error),
              title: const Text('Unfollow'),
              onTap: () => Navigator.pop(context, 'remove')),
        ]),
      ),
    );
    if (!mounted || action == null) return;
    final state = context.read<AppState>();
    switch (action) {
      case 'refresh':
        await _refresh(only: [feed]);
      case 'read':
        await state.markAllRead(ArticleFilter(feedUrl: feed.url));
      case 'rename':
        final name = await _askName(feed.title);
        if (name != null) await state.renameFeed(feed, name);
      case 'remove':
        final ok = await confirm(context,
            title: 'Unfollow ${feed.title}?',
            message: 'Its articles and any downloaded episodes will be deleted.',
            action: 'Unfollow',
            destructive: true);
        if (!ok || !mounted) return;
        final downloads = context.read<DownloadManager>();
        final paths = await state.removeFeed(feed);
        await downloads.deleteFiles(paths);
        if (mounted) showMessage(context, 'Unfollowed ${feed.title}');
    }
  }

  Future<String?> _askName(String current) {
    final controller = TextEditingController(text: current);
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rename feed'),
        content: TextField(
          controller: controller,
          autofocus: true,
          textCapitalization: TextCapitalization.sentences,
          onSubmitted: (v) => Navigator.pop(context, v),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
              onPressed: () => Navigator.pop(context, controller.text),
              child: const Text('Save')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final counts = state.counts;
    int count(String key) => counts[key] ?? 0;
    final hasEpisodes = count('episodes') > 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('FeedMind'),
        actions: [
          if (state.refreshing)
            const Padding(
              padding: EdgeInsets.all(14),
              child: SizedBox(
                  width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
            )
          else
            IconButton(
              tooltip: 'Refresh all',
              icon: const Icon(Icons.refresh),
              onPressed: state.feeds.isEmpty ? null : () => _refresh(),
            ),
          PopupMenuButton<String>(
            onSelected: (v) => switch (v) {
              'import' => _importOpml(),
              'export' => _exportOpml(),
              'clear' => _clearOld(),
              _ => null,
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'import', child: Text('Import OPML…')),
              PopupMenuItem(value: 'export', child: Text('Export OPML…')),
              PopupMenuItem(value: 'clear', child: Text('Clear old articles')),
            ],
          ),
        ],
      ),
      // The empty state has its own Add feed button.
      floatingActionButton: state.feeds.isEmpty
          ? null
          : FloatingActionButton.extended(
              onPressed: _addFeed,
              icon: const Icon(Icons.add),
              label: const Text('Add feed'),
            ),
      bottomNavigationBar: const PlayerBar(),
      body: state.feeds.isEmpty
          ? _EmptyState(onAdd: _addFeed, onImport: _importOpml)
          : RefreshIndicator(
              onRefresh: () => _refresh(),
              child: ListView(
                padding: const EdgeInsets.only(bottom: 88),
                children: [
                  _SectionTile(
                    icon: Icons.inbox_outlined,
                    title: 'All articles',
                    count: count('unread'),
                    onTap: () => _open('All articles', ArticleFilter.all),
                  ),
                  _SectionTile(
                    icon: Icons.mark_email_unread_outlined,
                    title: 'Unread',
                    count: count('unread'),
                    onTap: () => _open('Unread', ArticleFilter.unread),
                  ),
                  _SectionTile(
                    icon: Icons.star_outline,
                    title: 'Favorites',
                    count: count('favorites'),
                    highlight: false,
                    onTap: () => _open('Favorites', ArticleFilter.favorites),
                  ),
                  if (hasEpisodes)
                    _SectionTile(
                      icon: Icons.podcasts,
                      title: 'Podcast episodes',
                      count: count('episodes'),
                      highlight: false,
                      onTap: () => _open('Podcast episodes', ArticleFilter.episodes),
                    ),
                  if (count('downloads') > 0)
                    _SectionTile(
                      icon: Icons.download_done,
                      title: 'Downloaded',
                      count: count('downloads'),
                      highlight: false,
                      onTap: () => _open('Downloaded', ArticleFilter.downloads),
                    ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 20, 16, 4),
                    child: Text('Feeds',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            color: Theme.of(context).colorScheme.primary)),
                  ),
                  for (final feed in state.feeds)
                    ListTile(
                      leading: Icon(feed.isPodcast ? Icons.podcasts : Icons.rss_feed),
                      title: Text(feed.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                      subtitle: feed.lastRefresh == null
                          ? const Text('Not fetched yet')
                          : null,
                      trailing: CountBadge(feed.unreadCount),
                      onTap: () => _open(feed.title, ArticleFilter(feedUrl: feed.url),
                          singleFeed: true),
                      onLongPress: () => _feedActions(feed),
                    ),
                ],
              ),
            ),
    );
  }
}

class _SectionTile extends StatelessWidget {
  const _SectionTile({
    required this.icon,
    required this.title,
    required this.count,
    required this.onTap,
    this.highlight = true,
  });

  final IconData icon;
  final String title;
  final int count;
  final bool highlight;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
        leading: Icon(icon),
        title: Text(title),
        trailing: CountBadge(count, highlight: highlight),
        onTap: onTap,
      );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onAdd, required this.onImport});
  final VoidCallback onAdd;
  final VoidCallback onImport;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.rss_feed, size: 64, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 16),
          Text('No feeds yet', style: text.headlineSmall),
          const SizedBox(height: 8),
          Text(
            'Add a news site, blog, or podcast feed URL, or import the OPML '
            'file exported from FeedMind on your computer.',
            textAlign: TextAlign.center,
            style: text.bodyMedium,
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
              onPressed: onAdd, icon: const Icon(Icons.add), label: const Text('Add feed')),
          const SizedBox(height: 8),
          TextButton.icon(
              onPressed: onImport,
              icon: const Icon(Icons.file_open_outlined),
              label: const Text('Import OPML')),
        ]),
      ),
    );
  }
}

class _AddFeedDialog extends StatefulWidget {
  const _AddFeedDialog();

  @override
  State<_AddFeedDialog> createState() => _AddFeedDialogState();
}

class _AddFeedDialogState extends State<_AddFeedDialog> {
  final _controller = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final title = await context.read<AppState>().addFeed(_controller.text);
      if (mounted) Navigator.pop(context, title);
    } catch (e) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add feed'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        enabled: !_busy,
        keyboardType: TextInputType.url,
        autocorrect: false,
        decoration: InputDecoration(
          labelText: 'Feed URL',
          hintText: 'https://example.com/feed.xml',
          errorText: _error,
          errorMaxLines: 3,
        ),
        onSubmitted: (_) => _submit(),
      ),
      actions: [
        TextButton(
            onPressed: _busy ? null : () => Navigator.pop(context),
            child: const Text('Cancel')),
        FilledButton(
          onPressed: _busy ? null : _submit,
          child: _busy
              ? const SizedBox(
                  width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Add'),
        ),
      ],
    );
  }
}
