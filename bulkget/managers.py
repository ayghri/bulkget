import time
import subprocess


from pathlib import Path
from urllib.request import urlretrieve
from threading import Lock
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


class Aria2Manager:
    """Manages the lifecycle of an aria2c download manager instance.

    This class can be used as a context manager to ensure that the aria2c
    process is properly started and terminated.
    """

    def __init__(
        self,
        port: int = 6800,
        n_workers=4,
        num_splits=8,
        overwrite=True,
        file_renaming=False,
        dry_run=False,
        **kwargs,
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
        self.num_splits = num_splits
        self.n_workers = n_workers
        self.overwrite = overwrite
        self.file_renaming = file_renaming
        self.process = None
        self.api = None
        self.queue_size = 0
        self.lock = Lock()

        self.dry_run = dry_run
        if not self.dry_run:
            self._start_server()

    def _start_server(self, max_retries: int = 3):
        """Starts the aria2c download manager as a subprocess.

        Args:
            max_retries: The maximum number of times to retry starting the server.

        Raises:
            RuntimeError: If aria2c fails to start or if the port is in use.
        """

        from aria2p import API
        from aria2p import Client

        if self.process and self.process.poll() is None:
            print(f"aria2c is already running on port {self.port}")
            return

        for attempt in range(max_retries):
            try:
                port = self.port + attempt
                aria2_command = [
                    "aria2c",
                    f"--max-connection-per-server={self.n_workers}",
                    f"--split={self.num_splits}",
                    f"--allow-overwrite={str(self.overwrite).lower()}",
                    f"--auto-file-renaming={str(self.file_renaming).lower()}",
                    "--optimize-concurrent-downloads=true",
                    "--file-allocation=none",
                    "--enable-rpc",
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
        if self.dry_run:
            print(
                f"[Dry Run] Would download: {url} to {target_dir}/{output_name}"
            )
            return

        if not self.api:
            raise RuntimeError("Aria2c server is not running.")

        from aria2p import Options

        options = Options(self.api, struct={})
        options.set("dir", target_dir)
        options.set("out", output_name)
        options.set("follow-http-redirect", "true")
        with self.lock:
            self.api.add(url, options=options)
            self.queue_size += 1

    def watch(self, refresh_interval=5.0):
        """Monitors the download queue until all files are downloaded."""
        if self.dry_run:
            print("[Dry Run] Skipping download monitoring.")
            return
        if not self.api:
            raise RuntimeError("Aria2c server is not running.")
        while True:
            downloads = self.api.get_downloads()
            if not downloads:
                if self.queue_size > 0:
                    # All downloads are complete and have been removed
                    print(f"{self.queue_size}/{self.queue_size} downloads completed.")
                    break
                time.sleep(refresh_interval)
                continue

            completed_downloads = [d for d in downloads if d.is_complete]
            for d in completed_downloads:
                d.remove()

            done_count = self.queue_size - len(self.api.get_downloads())
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


class UrllibManager:
    """Manages downloads using Python's urllib."""

    def __init__(
        self,
        n_workers: int = 4,
        overwrite: bool = True,
        dry_run: bool = False,
        **kwargs,
    ):
        self.n_workers = n_workers
        self.overwrite = overwrite
        self.dry_run = dry_run
        self.download_queue: List[Tuple[str, Path]] = []
        self.lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=self.n_workers)

    def _download_file(self, url: str, full_path: Path):
        tmp_path = full_path.with_suffix(f"{full_path.suffix}.tmp")
        try:
            urlretrieve(url, tmp_path)
            tmp_path.rename(full_path)
            print(f"Finished downloading {full_path.name}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            if tmp_path.exists():
                tmp_path.unlink()

    def add_file(self, url: str, target_dir: str, output_name: str):
        """Adds a file to the download queue."""
        full_path = Path(target_dir) / output_name
        if self.dry_run:
            print(f"[Dry Run] Would download: {url} to {full_path}")
            return

        if full_path.exists() and not self.overwrite:
            print(f"File {full_path.name} already exists. Skipping.")
            return
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock:
            self.download_queue.append((url, full_path))

    def watch(self, refresh_interval=1.0):
        """Monitors the download queue until all files are downloaded."""
        if self.dry_run:
            print("[Dry Run] Skipping download monitoring.")
            return
        print("Started watching downloads.")

        if not self.download_queue:
            print("No files to download.")
            return

        futures = [
            self.executor.submit(self._download_file, url, path)
            for url, path in self.download_queue
        ]

        total_downloads = len(self.download_queue)
        completed_downloads = 0

        for future in as_completed(futures):
            completed_downloads += 1
            print(
                f"{completed_downloads}/{total_downloads} downloads completed."
            )

        print("All downloads completed.")

    def stop(self):
        """Stops the download manager."""
        print("Stopping UrllibManager.")
        self.executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
