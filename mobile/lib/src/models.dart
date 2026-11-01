/// Data models shared by the parser, database, and UI.
library;

/// One item as parsed from a feed, before it is stored.
class ParsedItem {
  const ParsedItem({
    required this.title,
    required this.link,
    this.description = '',
    this.published = '',
    this.audioUrl,
    this.audioType,
    this.audioLength,
    this.durationSeconds = 0,
  });

  final String title;

  /// The item's web page.
  final String link;
  final String description;

  /// The date string exactly as the feed gave it.
  final String published;
  final String? audioUrl;
  final String? audioType;
  final int? audioLength;
  final int durationSeconds;
}

/// A parsed feed document.
class ParsedFeed {
  const ParsedFeed({required this.title, required this.items});
  final String title;
  final List<ParsedItem> items;
}

/// A subscribed feed.
class Feed {
  const Feed({
    required this.id,
    required this.url,
    required this.title,
    this.isPodcast = false,
    this.lastRefresh,
    this.unreadCount = 0,
  });

  final int id;
  final String url;
  final String title;
  final bool isPodcast;
  final DateTime? lastRefresh;
  final int unreadCount;

  factory Feed.fromRow(Map<String, Object?> row) => Feed(
        id: row['id'] as int,
        url: row['url'] as String,
        title: (row['title'] as String?) ?? (row['url'] as String),
        isPodcast: (row['is_podcast'] as int? ?? 0) == 1,
        lastRefresh: DateTime.tryParse((row['last_refresh'] as String?) ?? ''),
        unreadCount: (row['unread_count'] as int?) ?? 0,
      );
}

/// A cached article or podcast episode.
class Article {
  const Article({
    required this.id,
    required this.feedUrl,
    required this.title,
    required this.link,
    this.pageLink,
    this.feedTitle = '',
    this.description = '',
    this.published = '',
    this.isRead = false,
    this.isFavorite = false,
    this.audioUrl,
    this.audioType,
    this.durationSeconds = 0,
    this.downloadPath,
    this.positionMs = 0,
    this.playbackCompleted = false,
  });

  final int id;
  final String feedUrl;
  final String feedTitle;
  final String title;

  /// Unique key within the feed. For podcast episodes this is the audio URL,
  /// because many podcasts give every episode the same show-page link.
  final String link;

  /// The web page for the article/episode (see [webUrl]).
  final String? pageLink;
  final String description;
  final String published;
  final bool isRead;
  final bool isFavorite;
  final String? audioUrl;
  final String? audioType;
  final int durationSeconds;

  /// Local file path if the episode has been downloaded.
  final String? downloadPath;

  /// Saved playback position.
  final int positionMs;
  final bool playbackCompleted;

  bool get isEpisode => audioUrl != null && audioUrl!.isNotEmpty;
  bool get isDownloaded => downloadPath != null;

  /// The page to open in a browser or share.
  String get webUrl {
    final page = pageLink?.trim() ?? '';
    return page.isNotEmpty ? page : link;
  }

  factory Article.fromRow(Map<String, Object?> row) => Article(
        id: row['id'] as int,
        feedUrl: row['feed_url'] as String,
        feedTitle: (row['feed_title'] as String?) ?? '',
        title: row['title'] as String,
        link: row['link'] as String,
        pageLink: row['page_link'] as String?,
        description: (row['description'] as String?) ?? '',
        published: (row['published'] as String?) ?? '',
        isRead: (row['is_read'] as int? ?? 0) == 1,
        isFavorite: (row['is_favorite'] as int? ?? 0) == 1,
        audioUrl: row['audio_url'] as String?,
        audioType: row['audio_type'] as String?,
        durationSeconds: (row['duration_seconds'] as int?) ?? 0,
        downloadPath: row['local_path'] as String?,
        positionMs: (row['position_ms'] as int?) ?? 0,
        playbackCompleted: (row['playback_completed'] as int? ?? 0) == 1,
      );
}

/// Which articles a list shows.
class ArticleFilter {
  const ArticleFilter({
    this.feedUrl,
    this.unreadOnly = false,
    this.favoritesOnly = false,
    this.episodesOnly = false,
    this.downloadedOnly = false,
  });

  final String? feedUrl;
  final bool unreadOnly;
  final bool favoritesOnly;
  final bool episodesOnly;
  final bool downloadedOnly;

  static const all = ArticleFilter();
  static const unread = ArticleFilter(unreadOnly: true);
  static const favorites = ArticleFilter(favoritesOnly: true);
  static const episodes = ArticleFilter(episodesOnly: true);
  static const downloads = ArticleFilter(episodesOnly: true, downloadedOnly: true);
}
