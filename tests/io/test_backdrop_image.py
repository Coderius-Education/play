import pytest
import os
import play
from play.globals import globals_list


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_set_backdrop_image_invalid_path():
    """set_backdrop_image() with a nonexistent file should raise an error."""
    with pytest.raises(FileNotFoundError):
        play.set_backdrop_image("nonexistent_image.png")


def test_set_backdrop_image_sets_type():
    """set_backdrop_image() should set backdrop_type to 'image'."""
    # Create a minimal valid PNG file
    import tempfile
    import struct
    import zlib

    fd, path = tempfile.mkstemp(suffix=".png")
    try:
        # Minimal 1x1 PNG
        def make_png():
            signature = b"\x89PNG\r\n\x1a\n"

            def chunk(chunk_type, data):
                c = chunk_type + data
                crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
                return struct.pack(">I", len(data)) + c + crc

            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            raw = b"\x00\xff\x00\x00"  # filter byte + 1 RGB pixel
            idat = zlib.compress(raw)
            return (
                signature
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", idat)
                + chunk(b"IEND", b"")
            )

        with os.fdopen(fd, "wb") as f:
            f.write(make_png())

        play.set_backdrop_image(path)
        assert globals_list.backdrop_type == "image"
        assert globals_list.backdrop is not None
    finally:
        os.remove(path)
