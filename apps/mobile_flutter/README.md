# CivicGrid Flutter Mobile

This folder contains the Flutter client shell for CivicGrid NYC.

## Initialize platform folders

If this folder does not yet have platform directories (`android`, `ios`, `web`, etc.), run:

```bash
cd apps/mobile_flutter
flutter create .
```

This keeps existing `lib/` and `pubspec.yaml` and generates missing Flutter scaffolding.

## Run

```bash
cd apps/mobile_flutter
flutter pub get
flutter run
```

## API base URL

Set API URL in the app header field:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://127.0.0.1:8000`
- Physical device: `http://<your-laptop-lan-ip>:8000`
