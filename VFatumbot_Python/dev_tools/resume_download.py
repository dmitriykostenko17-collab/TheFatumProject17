import requests
import os
import sys
import time

def download_file(url, filename=None):
    if not filename:
        filename = url.split('/')[-1]
    
    # Check if file exists to resume
    resume_header = {}
    if os.path.exists(filename):
        existing_size = os.path.getsize(filename)
        resume_header = {'Range': f'bytes={existing_size}-'}
        print(f"Resuming download from {existing_size} bytes...")
        mode = 'ab'
    else:
        existing_size = 0
        mode = 'wb'

    try:
        response = requests.get(url, headers=resume_header, stream=True, timeout=30)
        
        # Check if server supports Range (206 Partial Content)
        if response.status_code == 416:
            print("File already completely downloaded.")
            return True
        elif response.status_code != 206 and existing_size > 0:
            print("Server doesn't support resume. Starting from scratch.")
            mode = 'wb'
            existing_size = 0
            response = requests.get(url, stream=True, timeout=30)

        total_size = int(response.headers.get('content-length', 0)) + existing_size
        
        with open(filename, mode) as f:
            downloaded = existing_size
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        done = int(50 * downloaded / total_size)
                        # Format: [####      ] 25.4% (15.5/60.0 MB)
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        sys.stdout.write(f"\r[{'#' * done}{'-' * (50-done)}] {percent:5.1f}% ({mb_downloaded:0.1f}/{mb_total:0.1f} MB)")
                    else:
                        mb_downloaded = downloaded / (1024 * 1024)
                        sys.stdout.write(f"\rDownloaded: {mb_downloaded:0.1f} MB")
                    sys.stdout.flush()
        print("\nDownload complete.")
        # Verify integrity if it's a zip
        if filename.endswith('.zip'):
            import zipfile
            if zipfile.is_zipfile(filename):
                print("✅ ZIP integrity check passed.")
            else:
                print("❌ ZIP file is corrupted! Deleting and retrying...")
                os.remove(filename)
                return download_file(url, filename)
        return True
    except (requests.exceptions.RequestException, ConnectionError) as e:
        print(f"\nConnection lost: {e}")
        print("Waiting 10 seconds before retrying...")
        time.sleep(10)
        return download_file(url, filename)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resume_download.py <URL> [filename]")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    download_file(url, filename)
