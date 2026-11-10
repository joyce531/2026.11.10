"""Explicit optional setup: official pinned Windows package, verified hash, user-folder extraction."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import requests

VERSION='5.11.0'
NAME=f'Audiveris-{VERSION}-windowsConsole-x86_64.msi'
SHA256='5f1b4e96a12c53c7da426814b76e599363c4181e291855996e0a6878dda95f71'


def main():
    if os.name!='nt':raise SystemExit('This setup helper is for Windows only.')
    release=requests.get(f'https://api.github.com/repos/Audiveris/audiveris/releases/tags/{VERSION}',timeout=30)
    release.raise_for_status()
    asset=next(a for a in release.json()['assets'] if a['name']==NAME)
    if asset['digest']!='sha256:'+SHA256:raise RuntimeError('Official asset hash changed; inspect manually.')
    target=Path(os.environ['LOCALAPPDATA'])/'NaxiAIStudio/tools'/f'audiveris-{VERSION}'
    download=Path(tempfile.gettempdir())/'naxi-audiveris-download';download.mkdir(exist_ok=True)
    installer=download/NAME
    if not installer.exists() or hashlib.sha256(installer.read_bytes()).hexdigest()!=SHA256:
        # Resolve official GitHub asset redirect; never use a third-party mirror.
        response=requests.get(asset['url']+'?download=1',headers={'Accept':'application/octet-stream'},allow_redirects=False,timeout=30)
        location=response.headers.get('Location','')
        if not location.startswith('https://release-assets.githubusercontent.com/'):
            raise RuntimeError('No official asset redirect; please use the official installer manually.')
        chunk=512*1024;size=asset['size'];count=(size+chunk-1)//chunk
        def fetch(i):
            start=i*chunk;end=min(size,start+chunk)-1;path=download/f'chunk-{i:04d}'
            if path.exists() and path.stat().st_size==end-start+1:return path
            with requests.get(location,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(20,90)) as r:
                if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':
                    raise RuntimeError('Official server did not honor byte range.')
                with path.open('wb') as output:
                    for block in r.iter_content(65536):output.write(block)
            if path.stat().st_size!=end-start+1:raise RuntimeError('Incomplete chunk; rerun to resume.')
            return path
        print('Downloading verified official package in resumable ranges...',flush=True)
        with ThreadPoolExecutor(max_workers=16) as pool:
            paths=list(pool.map(fetch,range(count)))
        with installer.open('wb') as output:
            for path in paths:output.write(path.read_bytes())
    if hashlib.sha256(installer.read_bytes()).hexdigest()!=SHA256:raise RuntimeError('SHA256 mismatch; refusing extraction.')
    print('SHA256 verified. Extracting to user tools directory...',flush=True)
    result=subprocess.run(['msiexec.exe','/a',str(installer),'/qn',f'TARGETDIR={target}'],
                          creationflags=subprocess.CREATE_NO_WINDOW,timeout=180)
    if result.returncode:raise RuntimeError(f'MSI administrative extraction failed: {result.returncode}')
    for path in target.rglob('Audiveris.exe'):print(path,flush=True)


if __name__=='__main__':main()
