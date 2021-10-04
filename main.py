from helpers import APISession, urljoin
from pathlib import Path
import requests
import string
import re
import sys
import json
import argparse


def download(url: str, filepath: Path, chunk_size:int=8192):
    JUMP_LEFT_SEQ = '\u001b[100D'
    filesize_dl = 0
    try:
        resp = requests.get(url, stream=True)
        filesize = int(resp.headers['Content-Length'])
        print(f"{filepath.name} - {filesize} bytes")
        with open(filepath, "wb") as handle:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep-alive new chunks
                    handle.write(chunk)
                    filesize_dl = filesize_dl + chunk_size
                    print(JUMP_LEFT_SEQ, end='')
                    print(f'\r{filepath.name}: {filesize_dl*100/filesize:.2f}%', end='',flush=True)
            print()
    except Exception as e:
        print(e, file=sys.stderr)
        return


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', '-u', type=str, help='CTFd URL', required=True)
    ap.add_argument('--token', '-t', type=str, help="Your CTFd personal auth token", required=True)
    ap.add_argument('--output', '-o', type=str, help="Destination folder", default='dump')
    args = ap.parse_args()
    out_path = Path(args.output)
    ctfd = args.url
    s = APISession(prefix_url=ctfd)
    s.headers.update({"Content-Type": "application/json","Authorization": f"Token {args.token}"})

    j_challenges = s.get('/api/v1/challenges').json()
    if j_challenges['success'] == True:
        for ch in j_challenges['data']:
            ch['name'] = re.sub(f'[{string.punctuation}]', '_', ch['name'])
            ch['category'] = re.sub(f'[{string.punctuation}]', '_', ch['category'])
            ch_path = (out_path / ch['category'].strip() / ch['name'].strip())

            ch_path.mkdir(parents=True, exist_ok=True)
            print(str(ch_path))
            ch = s.get(f'/api/v1/challenges/{ch["id"]}').json()

            if ch['success'] == True:
                ch = ch['data']
            with open(str((ch_path / 'Description.md').absolute()),'w', encoding='utf-8') as f:
                f.write(f"{ch['description']}  \n")
                if len(ch['hints']):
                    f.write("\n**Hints**  \n")
                    for hint in ch['hints']:
                        if 'content' in hint:
                            f.write(f"```\n{hint['content']}\n```  \n")
                if len(ch['files']):
                    f.write("\n**Files**  \n")
                    with open(str((ch_path / 'files.txt').absolute()),'w', encoding='utf-8') as filelist:
                        for file in ch['files']:
                            filename = file.split('/')[-1].split('?')[0]
                            url = urljoin(s.prefix_url, file)
                            download(url, ch_path / filename)
                            f.write(f"[{filename}]({url})  \n")
                            filelist.write(f"{url}\n")

            json.dump(ch, open(str((ch_path / 'rawdata.json').absolute()), 'w'))


