# FeedMind Android MVP - Setup Guide

**Phase 1: Android Development Environment Setup**
**Status:** In Progress
**Target:** Production-ready Android RSS reader app

---

## Prerequisites

Before starting Flutter development, ensure you have:
- **Operating System:** Windows, macOS, or Linux
- **Disk Space:** ~10GB free for Flutter, Android Studio, and SDKs
- **RAM:** 8GB minimum (16GB recommended)
- **Internet:** Stable connection for downloading tools

---

## Step 1: Install Flutter SDK

### Download Flutter

**Linux/Mac:**
```bash
cd ~
wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.19.0-stable.tar.xz
tar xf flutter_linux_3.19.0-stable.tar.xz
```

**Or use git (recommended):**
```bash
cd ~
git clone https://github.com/flutter/flutter.git -b stable
```

### Add Flutter to PATH

**Linux/Mac (add to ~/.bashrc or ~/.zshrc):**
```bash
export PATH="$PATH:$HOME/flutter/bin"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Verify Installation

```bash
flutter --version
flutter doctor
```

You'll see warnings about Android Studio - that's expected, we'll fix those next.

---

## Step 2: Install Android Studio

### Download and Install

1. **Download:** https://developer.android.com/studio
2. **Install:** Follow platform-specific instructions
3. **Launch:** Start Android Studio for first-time setup

### Initial Setup Wizard

During first launch:
- Choose **Standard** installation type
- Select UI theme (your preference)
- Wait for SDK components to download (~2-3GB)

### Install Required Components

Android Studio → Settings/Preferences → Appearance & Behavior → System Settings → Android SDK

**SDK Platforms tab:**
- ✅ Android 14.0 (API 34) - Latest
- ✅ Android 13.0 (API 33)
- ✅ Android 8.0 (API 26) - Minimum for FeedMind

**SDK Tools tab:**
- ✅ Android SDK Build-Tools
- ✅ Android SDK Command-line Tools
- ✅ Android Emulator
- ✅ Android SDK Platform-Tools
- ✅ Google Play services

Click **Apply** to download.

---

## Step 3: Install Flutter and Dart Plugins

Android Studio → Settings → Plugins → Marketplace

Search and install:
1. **Flutter** (this will also prompt to install Dart)
2. **Dart**

Restart Android Studio after installation.

---

## Step 4: Configure Android Emulator

### Create Virtual Device

1. Android Studio → Tools → Device Manager (or AVD Manager)
2. Click **Create Device**
3. Select **Phone** → **Pixel 6** (good mid-range device)
4. Download system image: **Android 13 (API 33)** with Google APIs
5. Configure AVD:
   - Name: `Pixel_6_API_33`
   - Startup orientation: Portrait
   - Enable **Hardware - GLES 2.0** for graphics
6. Click **Finish**

### Test Emulator

Launch the emulator to verify it works:
```bash
# Or use Device Manager UI in Android Studio
```

---

## Step 5: Connect Physical Android Device (Optional but Recommended)

### Enable Developer Options

On your Android device:
1. Settings → About Phone
2. Tap **Build Number** 7 times
3. Developer options unlocked!

### Enable USB Debugging

1. Settings → System → Developer Options
2. Enable **USB Debugging**
3. Connect device via USB
4. Accept debugging prompt on device

### Verify Connection

```bash
flutter devices
```

You should see your physical device listed.

---

## Step 6: Run Flutter Doctor

Verify everything is set up:

```bash
flutter doctor -v
```

**Expected output (all ✓):**
```
Doctor summary (to see all details, run flutter doctor -v):
[✓] Flutter (Channel stable, 3.19.0, on Linux, locale en_US.UTF-8)
[✓] Android toolchain - develop for Android devices (Android SDK version 34.0.0)
[✓] Android Studio (version 2023.2)
[✓] Connected device (2 available)
[✓] Network resources
```

**Ignore these warnings for now:**
- ✗ Xcode (not needed for Android-first approach)
- ✗ iOS toolchain (not needed yet)

### Fix Common Issues

**Problem: Android licenses not accepted**
```bash
flutter doctor --android-licenses
# Accept all licenses (type 'y' for each)
```

**Problem: cmdline-tools not found**
- Open Android Studio → SDK Manager → SDK Tools
- Check "Android SDK Command-line Tools"
- Click Apply

---

## Step 7: Create First Flutter App (Validation)

Let's verify Flutter works with a test app:

```bash
cd ~/Wildcat
flutter create flutter_test
cd flutter_test
flutter run
```

Select your Android device or emulator when prompted. You should see the Flutter demo counter app running!

**Press 'q' to quit** when done testing.

---

## Step 8: Test RSS Parsing (Quick Validation)

Before building the full app, let's validate that RSS parsing works in Flutter.

### Create Validation Project

```bash
cd ~/Wildcat
flutter create feedmind_validation
cd feedmind_validation
```

### Add Dependencies

Edit `pubspec.yaml`:
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0
  webfeed: ^1.2.0
  sqflite: ^2.3.0
  path: ^1.8.3
```

Install:
```bash
flutter pub get
```

### Create Simple RSS Test

Create `lib/rss_test.dart`:
```dart
import 'package:http/http.dart' as http;
import 'package:webfeed/webfeed.dart';

Future<void> testRSSParsing() async {
  // Test with TechCrunch feed
  final url = 'https://techcrunch.com/feed/';

  try {
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final feed = RssFeed.parse(response.body);
      print('✓ Feed Title: ${feed.title}');
      print('✓ Articles: ${feed.items?.length ?? 0}');

      if (feed.items != null && feed.items!.isNotEmpty) {
        print('✓ First article: ${feed.items![0].title}');
        print('✓ RSS parsing works!');
      }
    }
  } catch (e) {
    print('✗ Error: $e');
  }
}
```

Update `lib/main.dart`:
```dart
import 'package:flutter/material.dart';
import 'rss_test.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RSS Validation',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _status = 'Press button to test RSS parsing';

  void _testRSS() async {
    setState(() {
      _status = 'Testing RSS parsing...';
    });

    await testRSSParsing();

    setState(() {
      _status = 'RSS test complete! Check console for results.';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('FeedMind Validation'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.rss_feed, size: 100, color: Colors.blue),
            const SizedBox(height: 20),
            Text(_status, textAlign: TextAlign.center),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _testRSS,
              child: const Text('Test RSS Parsing'),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Run Validation App

```bash
flutter run
```

Click the "Test RSS Parsing" button. Check the console - you should see:
```
✓ Feed Title: TechCrunch
✓ Articles: 20
✓ First article: [article title]
✓ RSS parsing works!
```

---

## Step 9: Configure Git Branch for Mobile Development

```bash
cd ~/Wildcat
git checkout -b mobile/android-mvp
git push -u origin mobile/android-mvp
```

---

## Step 10: System Requirements Checklist

Before proceeding to full app development, verify:

- [ ] Flutter SDK installed and in PATH
- [ ] `flutter doctor` shows all green checkmarks (except iOS)
- [ ] Android Studio installed with Flutter/Dart plugins
- [ ] Android SDK API 26, 33, and 34 installed
- [ ] Android emulator created and tested
- [ ] Physical Android device connected (optional)
- [ ] RSS parsing validated with `webfeed` package
- [ ] SQLite package (`sqflite`) installed
- [ ] Git branch `mobile/android-mvp` created

---

## Troubleshooting

### Flutter command not found
```bash
# Add to PATH and reload shell
echo 'export PATH="$PATH:$HOME/flutter/bin"' >> ~/.bashrc
source ~/.bashrc
```

### Android Studio can't find SDK
- Open Android Studio → Settings → Android SDK
- Note the SDK location path
- Set in terminal:
```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

### Emulator won't start
- Check virtualization is enabled in BIOS
- Try creating a new AVD with lower API level (API 29)
- Use physical device instead

### Gradle build errors
```bash
cd your_flutter_project
flutter clean
flutter pub get
flutter run
```

---

## Next Steps

Once this setup is complete, we'll proceed to:

1. **Design Phase:** Create UI mockups and app branding
2. **Project Setup:** Initialize the real FeedMind Flutter project
3. **Database Design:** Plan SQLite schema for mobile
4. **Core Development:** Build RSS reader functionality

---

## Resources

**Flutter Learning:**
- Official Docs: https://docs.flutter.dev/
- Flutter Codelabs: https://docs.flutter.dev/codelabs
- Widget Catalog: https://docs.flutter.dev/ui/widgets

**Packages We'll Use:**
- `webfeed`: https://pub.dev/packages/webfeed
- `sqflite`: https://pub.dev/packages/sqflite
- `http`: https://pub.dev/packages/http
- `provider`: https://pub.dev/packages/provider

**Material Design 3:**
- Guidelines: https://m3.material.io/
- Flutter MD3: https://docs.flutter.dev/ui/design/material

---

**Document Version:** 1.0
**Last Updated:** 2026-01-31
**Status:** Ready for environment setup
