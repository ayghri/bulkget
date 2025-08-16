import time

from dataclasses import asdict
from pathlib import Path
from typing import Callable
from typing import Union, Optional
import json
import subprocess

from aria2p import API
from aria2p import Client
from aria2p import Options

from .utils import FileInfo, ListInfo


class Downloader:
    """A class to manage the download of a list of files using aria2.

    Attributes:
        target_dir: The directory where files will be downloaded.
        files_list: A ListInfo object containing the files to download.
        filepath_hook: A function to determine the output file path for a download.
        refresh_interval: The interval in seconds to refresh download status.
        should_checksum: A boolean indicating whether to verify file checksums.
        dry_run: A boolean indicating whether to perform a dry run without downloading.
        server_port: The port for the aria2c RPC server.
        download_queue: A list of FileInfo objects to be downloaded.
        aria2: An Aria2cManager instance.
    """

    def __init__(
        self,
        target_dir: str,
        files_list: ListInfo,
        filepath_hook: Optional[Callable[[FileInfo], Union[str, Path]]] = None,
        refresh_interval: float = 5.0,
        should_checksum=True,
        dry_run=False,
        server_port: int = 6800,
        **server_kwargs,
    ):
        """Initializes the Downloader.

        Args:
            target_dir: The directory where files will be downloaded.
            files_list: A ListInfo object containing the files to download.
            filepath_hook: A function to determine the output file path.
            refresh_interval: The interval in seconds to refresh download status.
            should_checksum: Whether to verify file checksums.
            dry_run: If True, simulates the download without actual file transfers.
            server_port: The port for the aria2c RPC server.
            **server_kwargs: Additional keyword arguments for the Aria2cManager.
        """
        self.target_dir = Path(target_dir)
        self.files_list = files_list
        self.filepath_hook = filepath_hook or (lambda x: x.name)
        self.should_checksum = should_checksum
        self.dry_run = dry_run
        self.refresh_interval = refresh_interval
        self.server_port = server_port

        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.download_queue = []
        self.aria2 = Aria2cManager(port=self.server_port, **server_kwargs)

        print(f"Saving downloaded files to {self.target_dir}")
        print(f"Use 'aria2p -p {self.server_port}' to monitor downloads")

    def _filter_downloaded_files(self):
        """Filters out files that have already been downloaded."""
        print("Filtering out already downloaded files", end=" ")
        if self.should_checksum:
            print("via checksum")
        else:
            print("via size check")

        for file_info in self.files_list.files:
            output_path = self.target_dir.joinpath(
                self.filepath_hook(file_info)
            )
            if not file_info.already_downloaded(
                output_path, should_checksum=self.should_checksum
            ):
                self.download_queue.append(file_info)

    def start(self):
        """Starts the download process."""
        print(f"Starting download of {len(self.files_list)} URLs.")
        self._filter_downloaded_files()

        remaining_downloads = len(self.download_queue)
        total_files = len(self.files_list)
        print(
            f"{total_files - remaining_downloads}/{total_files} URLs already downloaded."
        )
        print(f"{remaining_downloads}/{total_files} URLs to download.")

        if not self.dry_run:
            if remaining_downloads > 0:
                print(
                    f"Starting downloads in {self.refresh_interval} seconds..."
                )
                self._download_files()
            else:
                print("No new files to download.")

        print("Download process finished.")
        self.stop()

    def _download_files(self):
        """Adds files to the download queue and monitors their progress."""
        for download_info in self.download_queue:
            self.aria2.add_file(
                url=download_info.url,
                target_dir=str(self.target_dir),
                output_name=str(self.filepath_hook(download_info)),
            )
        self.aria2.watch(refresh_interval=self.refresh_interval)

    def stop(self):
        """Stops the aria2c server and cleans up resources."""
        print("Stopping aria2c server.")
        self.aria2.stop()


class Aria2cManager:
    """Manages the lifecycle of an aria2c download manager instance.

    This class can be used as a context manager to ensure that the aria2c
    process is properly started and terminated.
    """

    def __init__(
        self,
        port: int = 6800,
        max_connections=16,
        num_splits=16,
        overwrite=True,
        file_renaming=False,
    ):
        """Initializes the Aria2cManager with specified configurations.

        Args:
            port: The port for the aria2c RPC server.
            max_connections: Maximum connections per server.
            num_splits: Number of splits for downloads.
            overwrite: Whether to allow overwriting existing files.
            file_renaming: Whether to enable automatic file renaming.
        """
        self.port = port
        self.max_connections = max_connections
        self.num_splits = num_splits
        self.overwrite = overwrite
        self.file_renaming = file_renaming
        self.process = None
        self.api: Optional[API] = None
        self.queue_size = 0
        self._start_server()

    def _start_server(self, max_retries: int = 3):
        """Starts the aria2c download manager as a subprocess.

        Args:
            max_retries: The maximum number of times to retry starting the server.

        Raises:
            RuntimeError: If aria2c fails to start or if the port is in use.
        """
        if self.process and self.process.poll() is None:
            print(f"aria2c is already running on port {self.port}")
            return

        for attempt in range(max_retries):
            try:
                port = self.port + attempt
                aria2_command = [
                    "aria2c",
                    "--enable-rpc",
                    f"--max-connection-per-server={self.max_connections}",
                    f"--split={self.num_splits}",
                    f"--allow-overwrite={str(self.overwrite).lower()}",
                    f"--auto-file-renaming={str(self.file_renaming).lower()}",
                    "--optimize-concurrent-downloads=true",
                    "--file-allocation=none",
                    "--rpc-listen-port",
                    str(port),
                ]
                self.process = subprocess.Popen(
                    aria2_command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                time.sleep(0.5)
                if self.process.poll() is None:
                    self.port = port
                    self.api = API(
                        Client(
                            host="http://localhost", port=self.port, secret=""
                        )
                    )
                    if self.process.stderr:
                        self.process.stderr.close()
                    return
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")

        if self.process:
            _, stderr = self.process.communicate()
            raise RuntimeError(
                f"Failed to start aria2c after {max_retries} attempts. "
                f"Error: {stderr.decode().strip()}"
            )
        else:
            raise RuntimeError(
                f"Failed to start aria2c after {max_retries} attempts."
            )

    def add_file(self, url: str, target_dir: str, output_name: str):
        """Submits a download request to the aria2 download manager.

        Args:
            url: The URL of the file to download.
            target_dir: The directory where the file will be saved.
            output_name: The name of the output file.
        """
        if not self.api:
            raise RuntimeError("Aria2c server is not running.")
        options = Options(self.api, struct={})
        options.set("dir", target_dir)
        options.set("out", output_name)
        self.api.add(url, options=options)
        self.queue_size += 1

    def watch(self, refresh_interval=5.0):
        """Monitors the download queue until all files are downloaded."""
        if not self.api:
            raise RuntimeError("Aria2c server is not running.")
        while True:
            downloads = self.api.get_downloads()
            completed_downloads = [d for d in downloads if d.is_complete]

            for d in completed_downloads:
                d.remove()

            done_count = len(completed_downloads)
            print(f"{done_count}/{self.queue_size} downloads completed.")

            if done_count == self.queue_size:
                break

            time.sleep(refresh_interval)

    def stop(self):
        """Stops the aria2c process if it is running."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("aria2c process terminated.")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print(
                    "aria2c process killed as it did not terminate gracefully."
                )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def download_dataset(
    target_dir: Union[str, Path],
    list_info: ListInfo,
    port: int,
    filepath_hook: Optional[Callable[[FileInfo], Union[str, Path]]] = None,
    dry_run: bool = False,
    should_checksum: bool = False,
):
    """Initiates the download process for a specified dataset.

    Args:
        target_dir: The directory where downloaded files will be stored.
        list_info: An object containing metadata and list of FileInfos to be downloaded.
        port: The port number for the aria2 download server.
        filepath_hook: A function to determine the file location.
        dry_run: If True, simulates the download without actual file transfers.
        should_checksum: If True, enables checksum verification for downloaded files.
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    with target_dir.joinpath("files_list.json").open("w") as f:
        json.dump(asdict(list_info), f, indent=2, default=str)

    downloader = Downloader(
        target_dir=str(target_dir),
        files_list=list_info,
        filepath_hook=filepath_hook,
        server_port=port,
        dry_run=dry_run,
        should_checksum=should_checksum,
        refresh_interval=0.5,
    )
    try:
        downloader.start()
    except Exception as e:
        print(f"An error occurred during the download process: {e}")
        downloader.stop()
        raise
