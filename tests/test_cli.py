import unittest
import json
from pathlib import Path
import subprocess
import shutil
import time

from bulkget.downloader import Downloader
from bulkget.utils import ListInfo


class TestBulkget(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_data")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.list_file = self.test_dir / "files.json"
        self.download_dir = self.test_dir / "downloads"
        self.download_dir.mkdir(exist_ok=True)

        # Create a dummy file on a simple http server
        self.dummy_file_content = "This is a test file."
        self.dummy_file_name = "test_file.txt"
        self.dummy_file_path = self.test_dir / self.dummy_file_name
        with open(self.dummy_file_path, "w") as f:
            f.write(self.dummy_file_content)

        # Start a simple http server
        self.server_process = subprocess.Popen(
            [
                "python",
                "-m",
                "http.server",
                "8000",
                "--directory",
                str(self.test_dir),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Create the list file
        file_info = {
            "properties": {},
            "files": [
                {
                    "name": self.dummy_file_name,
                    "url": f"http://localhost:8000/{self.dummy_file_name}",
                    "checksum": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
                    "checksum_type": "sha256",
                    "size": len(self.dummy_file_content),
                }
            ],
        }
        with open(self.list_file, "w") as f:
            json.dump(file_info, f)

    def tearDown(self):
        self.server_process.terminate()
        self.server_process.wait()
        
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_download_cli(self):
        """Tests the command-line interface of the bulkget package."""
        result = subprocess.run(
            [
                "bulkget",
                str(self.list_file),
                "--target",
                str(self.download_dir),
                "--checksum",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
        self.assertEqual(result.returncode, 0)
        downloaded_file = self.download_dir / self.dummy_file_name
        self.assertTrue(downloaded_file.exists())
        with open(downloaded_file, "r") as f:
            content = f.read()
        self.assertEqual(content, self.dummy_file_content)

    def test_downloader_with_filepath_hook(self):
        """Tests the Downloader class with a custom filepath_hook."""

        def custom_filepath_hook(file_info):
            return Path("custom_dir") / file_info.name

        list_info = ListInfo.from_json(self.list_file)
        downloader = Downloader(
            target_dir=str(self.download_dir),
            files_list=list_info,
            filepath_hook=custom_filepath_hook,
            should_checksum=True,
        )
        time.sleep(5)
        downloader.start()

        expected_file = self.download_dir / "custom_dir" / self.dummy_file_name
        self.assertTrue(expected_file.exists())
        with open(expected_file, "r") as f:
            content = f.read()
        self.assertEqual(content, self.dummy_file_content)


if __name__ == "__main__":
    unittest.main()
