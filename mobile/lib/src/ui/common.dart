import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

void showMessage(BuildContext context, String message) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(message)));
}

Future<bool> confirm(
  BuildContext context, {
  required String title,
  required String message,
  required String action,
  bool destructive = false,
}) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel')),
        FilledButton(
          style: destructive
              ? FilledButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.error,
                  foregroundColor: Theme.of(context).colorScheme.onError)
              : null,
          onPressed: () => Navigator.pop(context, true),
          child: Text(action),
        ),
      ],
    ),
  );
  return result ?? false;
}

/// Open an http(s) link in the browser. Feed links are untrusted, so other
/// schemes (file:, intent:, javascript:, ...) are refused.
Future<void> openInBrowser(BuildContext context, String url) async {
  final uri = Uri.tryParse(url.trim());
  if (uri == null || !(uri.scheme == 'http' || uri.scheme == 'https')) {
    showMessage(context, 'This article has no web link');
    return;
  }
  if (!await launchUrl(uri, mode: LaunchMode.externalApplication) &&
      context.mounted) {
    showMessage(context, 'Could not open the link');
  }
}

/// Small rounded count badge.
class CountBadge extends StatelessWidget {
  const CountBadge(this.count, {super.key, this.highlight = true});
  final int count;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    if (count <= 0) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: highlight ? scheme.primaryContainer : scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        count > 9999 ? '9999+' : '$count',
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: highlight ? scheme.onPrimaryContainer : scheme.onSurfaceVariant),
      ),
    );
  }
}
