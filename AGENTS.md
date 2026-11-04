# Expo HAS CHANGED

This project uses Expo SDK 57. Read the exact versioned docs at https://docs.expo.dev/versions/v57.0.0/ before writing any code.

- Do not import `@react-navigation/*`: since SDK 56 expo-router bundles it. Use `expo-router` / `expo-router/react-navigation`.
- The backend lives in `backend/` (FastAPI + SQLite). Run its tests with `backend/.venv/Scripts/python -m pytest` from `backend/`.
