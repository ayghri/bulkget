import argparse
from pathlib import Path

from .downloader import download_dataset
from .utils import ListInfo


def main():
    """Main function to run the bulk downloader."""
    parser = argparse.ArgumentParser(description="Bulk file downloader using aria2.")
    parser.add_argument(
        "list_json",
        type=str,
        help="Path to the JSON file containing the list of files to download.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Target directory to download files to. Defaults to current directory.",
    )
    parser.add_argument(
        "--port", type=int, default=6800, help="Port for the aria2c RPC server."
    )
    parser.add_argument(
        "--checksum", action="store_true", help="Verify file checksums after download."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the download without actual file transfers.",
    )

    args = parser.parse_args()

    list_info_path = Path(args.list_json)
    if not list_info_path.exists():
        raise FileNotFoundError(
            f"The specified file list '{list_info_path}' does not exist."
        )

    target_dir = args.target
    list_info = ListInfo.from_json(list_info_path)

    Path(target_dir).mkdir(parents=True, exist_ok=True)

    download_dataset(
        target_dir=target_dir,
        list_info=list_info,
        dry_run=args.dry_run,
        should_checksum=args.checksum,
        port=args.port,
    )
