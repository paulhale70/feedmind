/// Date helpers for feed dates.
///
/// Feeds publish dates as free-form strings: RFC 822 in RSS ("Tue, 27 Oct 2026
/// 10:30:00 GMT"), ISO 8601 in Atom ("2026-10-27T10:30:00Z"). Sorting those
/// strings directly is wrong, so each article also stores a normalized UTC
/// sort key. Mirrors rss_dates.py in the desktop app.
library;

import 'package:intl/intl.dart';

const _months = {
  'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
  'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
};

// RFC 822 named zones, as hours offset from UTC.
const _zones = {
  'GMT': 0, 'UT': 0, 'UTC': 0, 'Z': 0,
  'EST': -5, 'EDT': -4, 'CST': -6, 'CDT': -5,
  'MST': -7, 'MDT': -6, 'PST': -8, 'PDT': -7,
};

final _rfc822 = RegExp(
  r'^(?:[A-Za-z]{3,},?\s*)?(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\s+(\d{2,4})'
  r'(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*([A-Za-z]+|[+-]\d{4})?',
);
final _isoZone = RegExp(r'(Z|[+-]\d{2}:?\d{2})$', caseSensitive: false);
final _bareDate = RegExp(r'^\d{4}-\d{2}-\d{2}$');

/// Parse a feed date (RFC 822, ISO 8601, or YYYY-MM-DD) to a UTC DateTime.
/// Returns null if the string can't be parsed. Dates without a zone are
/// treated as UTC.
DateTime? parsePublishedDate(String? text) {
  if (text == null) return null;
  final s = text.trim();
  if (s.isEmpty) return null;

  final m = _rfc822.firstMatch(s);
  if (m != null) {
    final month = _months[m.group(2)!.toLowerCase()];
    if (month != null) {
      var year = int.parse(m.group(3)!);
      if (year < 100) year += year < 50 ? 2000 : 1900;
      var dt = DateTime.utc(
        year,
        month,
        int.parse(m.group(1)!),
        int.parse(m.group(4) ?? '0'),
        int.parse(m.group(5) ?? '0'),
        int.parse(m.group(6) ?? '0'),
      );
      final zone = m.group(7);
      if (zone != null) {
        if (zone.startsWith('+') || zone.startsWith('-')) {
          final sign = zone.startsWith('-') ? -1 : 1;
          final minutes =
              int.parse(zone.substring(1, 3)) * 60 + int.parse(zone.substring(3, 5));
          dt = dt.subtract(Duration(minutes: sign * minutes));
        } else {
          final hours = _zones[zone.toUpperCase()];
          if (hours != null) dt = dt.subtract(Duration(hours: hours));
        }
      }
      return dt;
    }
  }

  final iso = DateTime.tryParse(s);
  if (iso != null) {
    if (_isoZone.hasMatch(s)) return iso.toUtc();
    // No zone given: take the wall-clock values as UTC.
    return DateTime.utc(iso.year, iso.month, iso.day, iso.hour, iso.minute,
        iso.second);
  }

  if (s.length >= 10) {
    final prefix = DateTime.tryParse(s.substring(0, 10));
    if (prefix != null) {
      return DateTime.utc(prefix.year, prefix.month, prefix.day);
    }
  }
  return null;
}

/// Sortable UTC key ("2026-10-27T10:30:00") for an article. Falls back to
/// [fallback] (normally the time it was cached) when the date can't be parsed.
String publishedSortKey(String? published, DateTime fallback) {
  final dt = parsePublishedDate(published) ?? fallback.toUtc();
  return dt.toIso8601String().substring(0, 19);
}

/// Short, friendly date for article lists, in the device's local time:
/// "14:05" for today, "Oct 27" for this year, "Oct 27, 2025" otherwise.
/// A bare date ("2026-10-27") has no time to convert and is never shown as a
/// clock time. Unparseable strings are shown truncated rather than hidden.
String formatListDate(String? published, {DateTime? now}) {
  if (published == null || published.trim().isEmpty) return '';
  final text = published.trim();
  final utc = parsePublishedDate(text);
  if (utc == null) return text.length > 16 ? text.substring(0, 16) : text;

  final isBareDate = _bareDate.hasMatch(text);
  final local = isBareDate
      ? DateTime(utc.year, utc.month, utc.day)
      : utc.toLocal();
  final today = now ?? DateTime.now();

  if (!isBareDate &&
      local.year == today.year &&
      local.month == today.month &&
      local.day == today.day) {
    return DateFormat.Hm().format(local);
  }
  if (local.year == today.year) return DateFormat.MMMd().format(local);
  return DateFormat.yMMMd().format(local);
}

/// Format a duration as H:MM:SS or M:SS.
String formatDuration(Duration d) {
  final h = d.inHours;
  final m = d.inMinutes.remainder(60).toString().padLeft(h > 0 ? 2 : 1, '0');
  final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
  return h > 0 ? '$h:$m:$s' : '$m:$s';
}
