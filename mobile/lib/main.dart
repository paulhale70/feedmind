import 'dart:async';

import 'package:flutter/material.dart';
import 'package:just_audio_background/just_audio_background.dart';
import 'package:path/path.dart' as p;
import 'package:provider/provider.dart';
import 'package:sqflite/sqflite.dart';

import 'src/app_state.dart';
import 'src/data/database.dart';
import 'src/services/downloads.dart';
import 'src/services/player.dart';
import 'src/ui/home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock-screen / notification controls and background playback.
  await JustAudioBackground.init(
    androidNotificationChannelId: 'com.paulhale70.feedmind.audio',
    androidNotificationChannelName: 'Podcast playback',
    androidNotificationOngoing: true,
  );

  final db = await AppDatabase.open(p.join(await getDatabasesPath(), 'feedmind.db'));
  final state = AppState(db);
  await state.load();

  final downloads = DownloadManager(db, onChanged: state.load);
  final player = PlayerController(db, onChanged: state.load);

  // Trim old articles in the background (favorites and downloads are kept).
  unawaited(db.clearOldArticles().then((_) => state.load()));

  runApp(MultiProvider(
    providers: [
      ChangeNotifierProvider.value(value: state),
      ChangeNotifierProvider.value(value: downloads),
      ChangeNotifierProvider.value(value: player),
    ],
    child: const FeedMindApp(),
  ));
}

class FeedMindApp extends StatelessWidget {
  const FeedMindApp({super.key});

  static const _seed = Color(0xFF2E7D6B);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FeedMind',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.system,
      theme: ThemeData(colorSchemeSeed: _seed, brightness: Brightness.light),
      darkTheme: ThemeData(colorSchemeSeed: _seed, brightness: Brightness.dark),
      home: const HomeScreen(),
    );
  }
}
