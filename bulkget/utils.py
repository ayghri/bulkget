from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib


from dataclasses import dataclass, field, asdict
import json


def verify_checksum(file_path: Path, checksum: str, checksum_type: str) -> bool:
    """
    Compares the checksum of a file with a provided checksum value.

    Parameters:
    file_path (str): The path to the file to be checked.
    checksum (str): The expected checksum value to compare against.
    checksum_type (str): The type of checksum algorithm to use (e.g., 'md5', 'sha256').

    Returns:
    bool: True if the computed checksum matches the provided checksum, False otherwise.

    Raises:
    ValueError: If the provided checksum_type is not recognized by hashlib.
    """
    if checksum_type not in hashlib.algorithms_available:
        raise ValueError(
            f"Unrecognized checksum type {checksum_type}. "
            f"Supported: {hashlib.algorithms_available}"
        )
    hash_obj = hashlib.new(checksum_type)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest().lower() == checksum.lower()


@dataclass
class UrlInfo:
    name: str
    url: str
    checksum: str = ""
    checksum_type: str = ""
    size: int = -1
    mod_time: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

    def already_downloaded(
        self,
        path: Path,
        should_checksum: bool = True,
    ) -> bool:
        """
        Checks if a file has already been downloaded.

        Parameters:
        path (Path): The file path to check for existence and download status.
        should_checksum (bool): Flag indicating whether to perform checksum verification. Defaults to True.
            If false, we check using filesize if > 0 or if *.aria2 exists (unfinished download)

        Returns:
        bool: True if the file is considered already downloaded, False otherwise.
        """
        if not path.exists():
            return False
        if path.with_suffix(".aria2").exists():
            return False
        if should_checksum and self.checksum != "":
            return verify_checksum(
                path,
                checksum=self.checksum,
                checksum_type=self.checksum_type,
            )
        if self.size > 0:
            return self.size == path.stat().st_size
        return True


@dataclass
class UrlList:
    properties: Dict = field(default_factory=dict)
    files: List[UrlInfo] = field(default_factory=list)

    def __len__(self):
        return len(self.files)

    def to_json(self, path: Path, **kwargs):
        """Saves the ListInfo object to a JSON file."""

        def default_serializer(o):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError(
                f"Object of type {o.__class__.__name__} is not JSON serializable"
            )

        with open(path, "w") as f:
            json.dump(asdict(self), f, default=default_serializer, **kwargs)

    @classmethod
    def from_json(cls, path: Path) -> "UrlList":
        """Creates a ListInfo object from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        files_data = data.get("files", [])
        for file_data in files_data:
            if "mod_time" in file_data and isinstance(
                file_data["mod_time"], str
            ):
                file_data["mod_time"] = datetime.fromisoformat(
                    file_data["mod_time"]
                )

        return cls(
            properties=data.get("properties", {}),
            files=[UrlInfo(**f) for f in files_data],
        )
