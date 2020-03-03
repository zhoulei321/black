import json
import tarfile
import tempfile
import zipfile
from argparse import ArgumentParser
from pathlib import Path
from typing import Union
from urllib.request import urlopen, urlretrieve

PYPI_INSTANCE = "https://pypi.org/pypi"
ArchiveKind = Union[tarfile.TarFile, zipfile.ZipFile]


def get_package_source(package: str) -> None:
    with urlopen(PYPI_INSTANCE + f"/{package}/json") as page:
        metadata = json.load(page)

    for source in metadata["urls"]:
        if source["python_version"] == "source":
            break
    else:
        raise ValueError(f"Couldn't find any sources for {package}")
    return source["url"]


def get_archive_manager(local_file: Path) -> ArchiveKind:
    if tarfile.is_tarfile(local_file):
        return tarfile.open(local_file)
    elif zipfile.is_zipfile(local_file):
        return zipfile.ZipFile(local_file)
    else:
        raise ValueError("Unknown archive kind.")


def get_first_archive_member(archive: ArchiveKind) -> str:
    if isinstance(archive, tarfile.TarFile):
        return archive.getnames()[0]
    elif isinstance(archive, zipfile.ZipFile):
        return archive.namelist()[0]


def download_and_extract(package: str, directory: Path) -> Path:
    source = get_package_source(package)

    local_file, _ = urlretrieve(source, directory / f"{package}-src")
    with get_archive_manager(local_file) as archive:
        archive.extractall(path=directory)
        result_dir = get_first_archive_member(archive)
    return directory / result_dir


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("-p", "--pypi-package", help="PyPI package to download")
    parser.add_argument(
        "-o",
        "--output",
        default=Path("output/"),
        help="Output directory to download packages",
    )

    options = parser.parse_args()
    options.output.mkdir(exist_ok=True)

    source_directory = download_and_extract(options.pypi_package, options.output)
    print(source_directory)


if __name__ == "__main__":
    main()
