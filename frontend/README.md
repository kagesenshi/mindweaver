# Mindweaver Frontend

This is the Flutter-based frontend for Mindweaver. It replaces the legacy Reflex-based UI with a modern, responsive, and cross-platform experience.

## Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) (stable channel)
- A running Mindweaver backend (default: `http://localhost:8000`)

## Getting Started

### 1. Install Dependencies

Fetch all required packages:

```bash
flutter pub get
```

### 2. Generate Serializers

The project uses `json_serializable` for API data models. Generate the necessary code:

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### 3. Run the Application

#### Web (Recommended for development)
```bash
flutter run -d chrome
```

#### Linux Desktop
```bash
flutter run -d linux
```

## Configuration

The frontend connects to the backend at `http://localhost:8000` by default. You can modify this in `lib/config/settings.dart` or override it during execution via Dart defines:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://your-api:8000
```

## Project Structure

- `lib/models/`: Data entities mirroring the backend.
- `lib/providers/`: State management using Riverpod.
- `lib/pages//`: Individual UI views.
- `lib/services/`: API clients and core logic.
- `lib/widgets/`: Reusable UI components.
