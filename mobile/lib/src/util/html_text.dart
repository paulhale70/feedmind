/// Turn feed HTML into readable plain text, keeping paragraph breaks.
library;

// Closing </li> is deliberately absent: each <li> already starts a new line,
// so breaking on both would double-space list items.
final _blockBreak = RegExp(
  r'<\s*(br|/p|/div|/h[1-6]|/blockquote|/tr)\b[^>]*>',
  caseSensitive: false,
);
final _listItem = RegExp(r'<\s*li\b[^>]*>', caseSensitive: false);
final _dropBlocks = RegExp(
  r'<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>',
  caseSensitive: false,
  dotAll: true,
);
final _tag = RegExp(r'<[^>]+>');
final _entity = RegExp(r'&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z][a-zA-Z0-9]*);');
final _spaces = RegExp(r'[ \t ]+');
final _manyNewlines = RegExp(r'\n\s*\n\s*(\n\s*)+');

const _named = {
  'amp': '&', 'lt': '<', 'gt': '>', 'quot': '"', 'apos': "'", 'nbsp': ' ',
  'ndash': '–', 'mdash': '—', 'hellip': '…', 'lsquo': '‘', 'rsquo': '’',
  'ldquo': '“', 'rdquo': '”', 'laquo': '«', 'raquo': '»', 'bull': '•',
  'middot': '·', 'copy': '©', 'reg': '®', 'trade': '™', 'deg': '°',
  'times': '×', 'eacute': 'é', 'egrave': 'è', 'aacute': 'á', 'oacute': 'ó',
  'uuml': 'ü', 'ouml': 'ö', 'auml': 'ä', 'szlig': 'ß', 'ntilde': 'ñ',
  'ccedil': 'ç', 'euro': '€', 'pound': '£',
};

/// Decode HTML character references (&amp;, &#8217;, &#x2019;, ...).
String decodeEntities(String text) {
  return text.replaceAllMapped(_entity, (m) {
    final ref = m.group(1)!;
    if (ref.startsWith('#')) {
      final code = ref[1] == 'x' || ref[1] == 'X'
          ? int.tryParse(ref.substring(2), radix: 16)
          : int.tryParse(ref.substring(1));
      if (code != null && code > 0 && code <= 0x10FFFF) {
        return String.fromCharCode(code);
      }
      return m.group(0)!;
    }
    return _named[ref] ?? _named[ref.toLowerCase()] ?? m.group(0)!;
  });
}

/// Strip HTML tags, decode entities, and tidy whitespace.
String htmlToText(String? html) {
  if (html == null || html.isEmpty) return '';
  var text = html.replaceAll(_dropBlocks, '');
  text = text.replaceAll(_listItem, '\n• ');
  text = text.replaceAll(_blockBreak, '\n');
  text = text.replaceAll(_tag, '');
  text = decodeEntities(text);
  text = text.replaceAll(_spaces, ' ');
  text = text.split('\n').map((l) => l.trim()).join('\n');
  text = text.replaceAll(_manyNewlines, '\n\n');
  return text.trim();
}
