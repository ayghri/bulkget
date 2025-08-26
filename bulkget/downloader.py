from pathlib import Path
from typing import Callable
from typing import Union, Optional

from .utils import UrlInfo, UrlList
from .managers import Aria2Manager, UrllibManager


class Downloader:
    """A class to manage the download of a list of files."""

    def __init__(
        self,
        download_path: Union[str, Path],
        url_list: UrlList,
        manager: str = "aria2c",
        filepath_hook: Optional[Callable[[UrlInfo], Union[str, Path]]] = None,
        refresh_interval: float = 5.0,
        should_checksum=True,
        **manager_kwargs,
    ):
        """Initializes the Downloader.

        Args:
            download_path: The directory where files will be downloaded.
            url_list: A UrlList object containing the files to download.
            manager: The download manager to use ("aria2c" or "urllib").
            filepath_hook: A function to determine the output file path.
            refresh_interval: The interval in seconds to refresh download status.
            should_checksum: Whether to verify file checksums.
            dry_run: If True, simulates the download without actual file transfers.
            server_port: The port for the aria2c RPC server.
            n_workers: Number of worker threads for downloading files.
            **manager_kwargs: Additional keyword arguments for the download manager.
        """
        self.download_path = Path(download_path)
        self.url_list = url_list
        self.manager_name = manager
        self.filepath_hook = filepath_hook or (lambda x: x.name)
        self.should_checksum = should_checksum
        self.refresh_interval = refresh_interval

        self.download_path.mkdir(parents=True, exist_ok=True)
        self.download_queue: list[UrlInfo] = []

        if manager == "aria2c":
            self.manager = Aria2Manager(**manager_kwargs)
        elif manager == "urllib":
            self.manager = UrllibManager(**manager_kwargs)
        else:
            raise ValueError(f"Unknown manager: {manager}")

        print(f"Using {manager} to download files.")
        print(f"Saving downloaded files to {self.download_path}")

    def _filter_downloaded_files(self):
        """Filters out files that have already been downloaded."""
        print("Filtering out already downloaded files", end=" ")
        if self.should_checksum:
            print("via checksum")
        else:
            print("via size check")

        for file_info in self.url_list.files:
            output_path = self.download_path.joinpath(
                self.filepath_hook(file_info)
            )
            if not file_info.already_downloaded(
                output_path, should_checksum=self.should_checksum
            ):
                self.download_queue.append(file_info)

    def start(self):
        """Starts the download process."""
        print(f"Starting download of {len(self.url_list)} URLs.")
        self._filter_downloaded_files()

        remaining_downloads = len(self.download_queue)
        total_files = len(self.url_list)
        print(
            f"{total_files - remaining_downloads}/{total_files} URLs already downloaded."
        )
        print(f"{remaining_downloads}/{total_files} URLs to download.")

        if remaining_downloads > 0:
            print(f"Starting downloads in {self.refresh_interval} seconds...")
            self._download_files()
        else:
            print("No new files to download.")

        print("Download process finished.")
        self.stop()

    def _download_files(self):
        """Adds files to the download queue and monitors their progress."""
        for file_info in self.download_queue:
            output_path = self.filepath_hook(file_info)
            self.manager.add_file(
                url=file_info.url,
                target_dir=str(self.download_path),
                output_name=str(output_path),
            )
        self.manager.watch(refresh_interval=self.refresh_interval)

    def stop(self):
        """Stops the download manager and cleans up resources."""
        print("Stopping download manager.")
        self.manager.stop()
