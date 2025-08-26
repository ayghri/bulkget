import unittest
from unittest.mock import patch, call
import shutil
from pathlib import Path

from bulkget.managers import UrllibManager


class TestUrllibManager(unittest.TestCase):
    def setUp(self):
        self.manager = UrllibManager(n_workers=2)
        self.test_dir = Path("test_downloads")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        self.manager.stop()

    @patch("bulkget.managers.urlretrieve")
    def test_download_file_success(self, mock_urlretrieve):
        """Tests that a single file is downloaded successfully."""
        url = "http://example.com/file1.txt"
        file_path = self.test_dir / "file1.txt"
        tmp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

        self.manager._download_file(url, file_path)
        mock_urlretrieve.assert_called_once_with(url, tmp_path)

    @patch("bulkget.managers.urlretrieve")
    def test_download_file_error(self, mock_urlretrieve):
        """Tests that an error during download is handled."""
        url = "http://example.com/file1.txt"
        file_path = self.test_dir / "file1.txt"
        tmp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
        mock_urlretrieve.side_effect = Exception("Test error")

        # Since we are using print instead of logging, we can't use assertLogs.
        # We will just call the function and trust that the exception is caught.
        self.manager._download_file(url, file_path)
        # We can check that urlretrieve was called
        mock_urlretrieve.assert_called_once_with(url, tmp_path)

    def test_add_file(self):
        """Tests that a file is added to the download queue."""
        url = "http://example.com/file1.txt"
        target_dir = str(self.test_dir)
        output_name = "file1.txt"

        self.manager.add_file(url, target_dir, output_name)

        self.assertEqual(len(self.manager.download_queue), 1)
        added_url, added_path = self.manager.download_queue[0]
        self.assertEqual(added_url, url)
        self.assertEqual(added_path, self.test_dir / output_name)

    @patch("bulkget.managers.UrllibManager._download_file")
    def test_watch_downloads_files_in_parallel(self, mock_download_file):
        """Tests that the watch method uses the executor to download files."""
        urls = [
            "http://example.com/file1.txt",
            "http://example.com/file2.txt"
        ]
        target_dir = str(self.test_dir)
        
        self.manager.add_file(urls[0], target_dir, "file1.txt")
        self.manager.add_file(urls[1], target_dir, "file2.txt")

        self.manager.watch()

        self.assertEqual(mock_download_file.call_count, 2)
        
        # Check that it was called with the correct arguments, order doesn't matter
        expected_calls = [
            call(urls[0], self.test_dir / "file1.txt"),
            call(urls[1], self.test_dir / "file2.txt")
        ]
        mock_download_file.assert_has_calls(expected_calls, any_order=True)


if __name__ == "__main__":
    unittest.main()
