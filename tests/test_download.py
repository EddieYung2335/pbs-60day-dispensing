"""
A simple test file for "fetch a file".

The purpose for this test is simply to ensure that cached files are not refetched, missing files are. 
"""

import pytest
from src.download import download_one

def test_existing_file_is_not_refetched(tmp_path):
    """
    1. Make a temp folder
    2. Put a file named "already.csv" in it with text "cached"
    3. Define a fake opener that RAISES if called 
    4. call download_one
    5. assert: returned fetched flag is False
    6. assert: file text is still "cached"
    """
    (tmp_path / "already.csv").write_text("cached")

    def explode(url):
        raise AssertionError(f"should not have fetched {url}")

    path, fetched = download_one("already.csv", dest_dir=tmp_path, opener=explode)
    assert fetched is False
    assert path.read_text() == "cached"

def test_missing_file_is_fetched(tmp_path):
    """
    1.  Make a temp folder
    2. define a fake opnener that records the url it was given and returns a fake file-like object holding b"col\n1\n"
    3. call download_one
    4. assert: returned fetched flag is True
    5. assert: file text is "col\n1\n"
    6. assert: the url passed to the opener ends with "new.csv"
    """
    class FakeResponse:
        def read(self, *a):
            return b""
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
    
    calls = []

    def fake_opener(url):
        calls.append(url)
        import io
        return io.BytesIO(b"col\n1\n")

    path, fetched = download_one("new.csv", dest_dir=tmp_path, opener=fake_opener)
    assert fetched is True
    assert path.read_bytes() == b"col\n1\n"
    assert calls[0].endswith("new.csv")