from pathlib import Path

import pytest

from foundation.utils import atomic_write


def writer_creator(stuff_to_write):
    def writer(f):
        f.write(stuff_to_write)
    return writer

def test_writes_text(tmp_path):
    path = tmp_path / "test.txt"

    atomic_write(path, writer_creator("hello"))

    assert path.read_text() == "hello"


def test_writes_binary(tmp_path):
    path = tmp_path / "test.bin"

    atomic_write(path, writer_creator(b"\x00\x01\xff"), encoding=None)

    assert path.read_bytes() == b"\x00\x01\xff"


def test_supports_custom_encoding(tmp_path):
    path = tmp_path / "test.txt"

    atomic_write(
        path,
        writer_creator("Jürgen"),
        encoding="latin-1",
    )

    assert path.read_bytes() == "Jürgen".encode("latin-1")


def test_creates_parent_directories(tmp_path):
    path = tmp_path / "foo" / "bar" / "test.txt"

    atomic_write(path, writer_creator("hello"))

    assert path.read_text() == "hello"


def test_overwrites_existing_file(tmp_path):
    path = tmp_path / "test.txt"
    path.write_text("old")

    atomic_write(path, writer_creator("new"))

    assert path.read_text() == "new"


def test_empty_file(tmp_path):
    path = tmp_path / "test.txt"

    atomic_write(path, lambda f: None)

    assert path.read_text() == ""


def test_writer_exception_does_not_replace_existing_file(tmp_path):
    path = tmp_path / "test.txt"
    path.write_text("old")

    def writer(f):
        f.write("new")
        raise RuntimeError("something went wrong")

    with pytest.raises(RuntimeError, match="something went wrong"):
        atomic_write(path, writer)

    assert path.read_text() == "old"


def test_writer_exception_cleans_up_temp_file(tmp_path):
    path = tmp_path / "test.txt"

    def writer(f):
        f.write("partial")
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        atomic_write(path, writer)

    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


def test_unicode_text(tmp_path):
    path = tmp_path / "test.txt"
    content = "Hällo 世界 🌍"

    atomic_write(path, writer_creator(content))

    assert path.read_text(encoding="utf-8") == content
