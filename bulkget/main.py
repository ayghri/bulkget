import argparse
from pathlib import Path
import importlib.util
import sys
from typing import Callable, Optional, Union

from bulkget.utils import UrlList, UrlInfo
from bulkget import Downloader


def download_dataset(
    download_path: Union[str, Path],
    url_list: UrlList,
    manager: str = "aria2c",
    n_workers: int = 4,
    filepath_hook: Optional[Callable[[UrlInfo], Union[str, Path]]] = None,
    should_checksum: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
    port: int = 6800,
):
    """Initiates the download process for a specified dataset.

    Args:
        download_path: The directory where downloaded files will be stored.
        url_list: An object containing metadata and list of UrlInfos to be downloaded.
        port: The port number for the aria2 download server.
        filepath_hook: A function to determine the file location.
        dry_run: If True, simulates the download without actual file transfers.
        should_checksum: If True, enables checksum verification for downloaded files.
        manager: The download manager to use ("aria2c" or "urllib").
        n_workers: The number of workers for the download manager.
    """
    download_path = Path(download_path)
    download_path.mkdir(parents=True, exist_ok=True)

    downloader = Downloader(
        download_path=str(download_path),
        url_list=url_list,
        filepath_hook=filepath_hook,
        should_checksum=should_checksum,
        manager=manager,
        refresh_interval=0.5,
        n_workers=n_workers,
        overwrite=overwrite,
        dry_run=dry_run,
        port=port,
    )
    try:
        downloader.start()
    except Exception as e:
        print(f"An error occurred during the download process: {e}")
        downloader.stop()
        raise


def main():
    """Main function to run the bulk downloader."""
    parser = argparse.ArgumentParser(description="Bulk file downloader.")
    parser.add_argument(
        "list",
        type=str,
        help="Path to the JSON file containing the list of files to download.",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Target directory to download files to. Defaults to current directory.",
    )

    parser.add_argument(
        "--manager",
        type=str,
        default="aria2c",
        choices=["aria2c", "urllib"],
        help="Download manager to use.",
    )
    parser.add_argument(
        "--filepath-hook",
        type=str,
        help="Path to a Python file with a 'filepath_hook' function to customize output file paths.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=6800,
        help="Port for the aria2c RPC server.",
    )

    parser.add_argument(
        "--checksum",
        action="store_true",
        help="Verify file checksums after download.",
    )
    parser.add_argument(
        "-n",
        "--n-workers",
        type=int,
        default=4,
        help="Number of parallel download workers.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the download without actual file transfers.",
    )

    args = parser.parse_args()

    filepath_hook: Optional[Callable[[UrlInfo], Union[str, Path]]] = None
    if args.filepath_hook:
        try:
            file_path = Path(args.filepath_hook)
            if not file_path.is_file():
                raise FileNotFoundError(
                    f"The specified hook file does not exist: {file_path}"
                )

            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(
                module_name, file_path
            )
            if not spec or not spec.loader:
                raise ImportError(f"Cannot load spec from file {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            filepath_hook = getattr(module, "filepath_hook", None)
            if not filepath_hook or not callable(filepath_hook):
                raise AttributeError(
                    f"The file {file_path} does not contain a callable 'filepath_hook' function."
                )
        except (FileNotFoundError, ImportError, AttributeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    url_list_path = Path(args.list)
    if not url_list_path.exists():
        raise FileNotFoundError(
            f"The specified file list '{url_list_path}' does not exist."
        )

    download_path = Path(args.path)
    url_list = UrlList.from_json(url_list_path)

    download_path.mkdir(parents=True, exist_ok=True)

    download_dataset(
        download_path=download_path,
        url_list=url_list,
        manager=args.manager,
        filepath_hook=filepath_hook,
        should_checksum=args.checksum,
        port=args.port,
        n_workers=args.n_workers,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )
