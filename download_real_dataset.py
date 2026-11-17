import os
import sys
import zipfile
import urllib.request
DATASET_DIR = os.path.join(os.path.dirname(__file__), 'dataset', 'real_clinical_slides')
ZENODO_URL = 'https://zenodo.org/records/16971046/files/ABO-BTI%20ABO%20Blood%20Typing.zip?download=1'

def download_zenodo_dataset():
    os.makedirs(DATASET_DIR, exist_ok=True)
    zip_path = os.path.join(DATASET_DIR, 'ABO_BTI_clinical_dataset.zip')
    print('=' * 80)
    print('   DOWNLOADING REAL CLINICAL BLOOD TYPING DATASET (ZENODO ABO-BTI)')
    print('   DOI: 10.5281/zenodo.16971046 | Real Clinical Agglutination Benchmark')
    print('=' * 80)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        req = urllib.request.Request(ZENODO_URL, headers=headers)
        print(f'[+] Connecting to Zenodo Open Repository...')
        with urllib.request.urlopen(req, timeout=60) as response, open(zip_path, 'wb') as out_file:
            total_size = int(response.info().get('Content-Length', -1))
            block_size = 1024 * 64
            downloaded = 0
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)
                downloaded += len(buffer)
                if total_size > 0:
                    pct = min(100.0, downloaded * 100.0 / total_size)
                    sys.stdout.write(f'\r  -> Downloading: {pct:.1f}% ({downloaded / (1024 * 1024):.1f} MB / {total_size / (1024 * 1024):.1f} MB)')
                else:
                    sys.stdout.write(f'\r  -> Downloading: {downloaded / (1024 * 1024):.1f} MB')
                sys.stdout.flush()
        print(f'\n[+] Download complete ({downloaded / (1024 * 1024):.1f} MB)! Extracting archive...')
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DATASET_DIR)
        print(f'[+] Extraction complete in: {DATASET_DIR}')
    except Exception as e:
        print(f'\n[-] Download failed: {e}')
if __name__ == '__main__':
    download_zenodo_dataset()
