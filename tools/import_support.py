"""Restore files required by the Keil project from the original Milandr ZIP."""

import argparse
from pathlib import Path, PureWindowsPath
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "dac_music.uvprojx"
EXTRA_FILES = ('arraymusic.h',)


def support_paths():
    tree = ElementTree.parse(ROOT / PROJECT)
    paths = {Path(file) for file in EXTRA_FILES}
    for instance in tree.findall("./RTE/files/file/instance"):
        if instance.get("removed") != "1":
            paths.add(Path(*PureWindowsPath(instance.text).parts))
    return sorted(paths)


def import_support(archive_path):
    # Only copy files named in the Keil project, plus the original audio if used.
    with ZipFile(archive_path) as archive:
        if PROJECT not in archive.namelist():
            raise ValueError(f"Use the original archive containing {PROJECT}.")
        paths = support_paths()
        missing = {path.as_posix() for path in paths}.difference(archive.namelist())
        if missing:
            raise ValueError("Files missing from the Milandr archive: " + ", ".join(sorted(missing)))
        payload = [(ROOT / path, archive.read(path.as_posix())) for path in paths]

    for destination, contents in payload:
        if destination.exists() and destination.read_bytes() != contents:
            raise ValueError(f"Existing file differs: {destination.relative_to(ROOT)}")
    for destination, contents in payload:
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)
    return len(payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Original example ZIP from the Milandr support portal")
    args = parser.parse_args()
    try:
        restored = import_support(args.archive)
    except (BadZipFile, OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Ready: {restored} project support files.")
