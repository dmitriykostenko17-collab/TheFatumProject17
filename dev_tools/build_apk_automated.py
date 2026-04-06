import os
import subprocess
import sys
from resume_download import download_file

# --- Configurations ---
FLUTTER_URL = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.24.1-stable.zip"
ANDROID_SDK_URL = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
JAVA_HOME = r"C:\Program Files\Microsoft\jdk-17.0.18.8-hotspot"

import ctypes

# Constants to prevent sleep
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

def prevent_sleep():
    """Windows-specific call to prevent system from sleeping."""
    try:
        print("--- Preventing system sleep ---")
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    except:
        print("Failed to set sleep prevention.")

def allow_sleep():
    """Reverts system sleep settings."""
    try:
        print("--- Reverting sleep settings ---")
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except:
        pass

def run_cmd(cmd, env=None):
    print(f"Executing: {cmd}")
    process = subprocess.Popen(cmd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    return process.returncode

def setup():
    prevent_sleep()
    try:
        base_dir = os.getcwd()
        tools_dir = os.path.join(base_dir, "build_tools")
        if not os.path.exists(tools_dir):
            os.makedirs(tools_dir)

        # 1. Flutter
        flutter_zip = os.path.join(tools_dir, "flutter.zip")
        flutter_path = os.path.join(tools_dir, "flutter", "bin")
        if not os.path.exists(flutter_path):
            print("--- Downloading Flutter SDK ---")
            download_file(FLUTTER_URL, flutter_zip)
            print("Extracting Flutter (this might take a while)...")
            import zipfile
            with zipfile.ZipFile(flutter_zip, 'r') as zf:
                total = len(zf.namelist())
                for i, member in enumerate(zf.namelist()):
                    try:
                        zf.extract(member, tools_dir)
                    except Exception as ex:
                        print(f"  Warning: skipped {member}: {ex}")
                    if (i + 1) % 500 == 0 or (i + 1) == total:
                        print(f"  Extracted {i+1}/{total} files...")
            print("Flutter extraction complete.")

        # 2. Android SDK Placeholder (Simplified logic)
        # Note: Full Android SDK setup is complex. flet build apk usually handles some of this if flutter is there.
        
        # 3. Environment Variables for the build
        build_env = os.environ.copy()
        build_env["JAVA_HOME"] = JAVA_HOME
        build_env["PATH"] = f"{flutter_path};{JAVA_HOME}\\bin;" + build_env["PATH"]
        
        print("\n--- Running Flet Doctor ---")
        run_cmd("flet doctor", env=build_env)

        print("\n--- Starting APK Build ---")
        build_cmd = (
            "flet build apk "
            "--project \"TheFatumProject\" "
            "--package \"com.dimas.vfatumbot\" "
            "--permissions \"ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,INTERNET,CAMERA\""
        )
        
        result = run_cmd(build_cmd, env=build_env)
        if result == 0:
            print("\n🏆 APK Build Successful! Check the 'build/apk' folder.")
        else:
            print("\n❌ Build failed. Please check the logs above.")
    finally:
        allow_sleep()

if __name__ == "__main__":
    setup()
