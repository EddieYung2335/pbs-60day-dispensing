"""
Fetch PBS Date-of-Supply CSVs. 

Cached: delete a file in data/raw to refetch. 
"""
import shutil
import urllib.request
from pathlib import Path

from src.config import BASE_URL, RAW, MAP_FILE, SUPPLY_FILES


def download_one(name, dest_dir=RAW, opener=urllib.request.urlopen):
    """
    Make sure one named file exists on disk, and tell the caller whether it had to go get it.
    It does not know there is several files.
    It only takes filename, ensure that file is sitting in a folder, reports back. 

    Args:
        name: filename, no default, caller must say which file
        dest_dir: folder to put the file in. Defaults to RAW so real runs need no arguments. Test pass `tmp_path`. 
        opener: the thing that fetches a URL. Defaults to the real urllib.request.urlopen. Test pass fake one. 
    
    Returns:
        path - a Path object pointing at the finished file
        was_fetched - True if it downloaded, False if the file is already there. 
    """ 
    dest = Path(dest_dir) / name
    if dest.exists():
        return dest, False
    # parents=True -> create data/ if it is missing
    # exist_ok=True -> don't complain if data/ already exists
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Create a temporary file name 
    tmp = dest.with_suffix(dest.suffix + ".part")

    with opener(BASE_URL + name) as response, open(tmp, "wb") as out:
        # Data transfer
        shutil.copyfileobj(response, out)
    # Move the temporary file to the final destination.
    tmp.replace(dest)
    return dest, True



def main():
    """
    Loops over every file, prints a receipt line each time.
    It is what runs when you run `python src/download.py` from the command line.
    """
    for name in SUPPLY_FILES + [MAP_FILE]:
        path, fetched = download_one(name)
        size_md = path.stat().st_size / 1e6
        print(f"{'downloaded' if fetched else 'cached' :>10} {size_md:6.2f} MB {path.name}")

if __name__ == "__main__":
    main()