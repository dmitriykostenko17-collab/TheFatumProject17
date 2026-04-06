# VFatumbot Android Production Audit Report

This document identifies potential issues and readiness points for deploying VFatumbot as an Android APK.

## 1. Library Versions (CRITICAL)
- **Status**: Fixed.
- **Issue**: Flet 0.84.0+ introduced breaking changes (Icons, Image, BoxFit).
- **Resolution**: `requirements.txt` is now pinned to `flet==0.28.3`. This ensures the Android build environment matches the stable local environment.

## 2. API Key Management
- **Status**: Needs modification.
- **Issue**: Google Maps API key is currently missing or hardcoded.
- **Resolution**:
    - Injecting `AIzaSyDY2N2VQDGATq0DCwTlEsM2p23Z-ngLSng` into `config.py`.
    - Encouraging use of `.env` for user-specific keys (`W3W_API_KEY`).

## 3. Entropy Sources (Feature Gap)
- **Status**: Integration Planned.
- **Goal**: Support Randonautica's Quantum RNG alongside CamRNG.
- **Plan**:
    - Call `https://qrng.randonautica.app/api/json/randhex?device_id=QWR70154`.
    - Add UI toggle to switch sources.

## 4. Hardware Permissions
- **Status**: Verified.
- **Location**: `ACCESS_FINE_LOCATION` is required for map and point generation.
- **Camera**: `CAMERA` is required for CamRNG (Local Entropy).
- **Action**: Verify `build-apk.yml` handles these flags.

## 5. UI Stability (Android)
- **Themes**: Defaulting to Dark/Light mode based on system.
- **Responsiveness**: Column/Row layouts with `expand=True` to handle different screen sizes.
- **Cleanup**: Removing `flutter.zip` (391MB) and cleaning build artifacts.

## 6. Redundant Files Identification
- `build_apk_automated.py`: Move to `dev_tools/`.
- `resume_download.py`: Move to `dev_tools/`.
- `vfatumbot.db`: Delete local copies from git.
- `flutter.zip`: DELETE.
