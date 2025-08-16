import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import shutil


from bulkget.downloader import Downloader, Aria2cManager
from bulkget.utils import FileInfo, ListInfo

class TestAria2cManager(unittest.TestCase):
    @patch("subprocess.Popen")
    def test_start_server_success(self, mock_popen):
        """Tests that the aria2c server starts successfully."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        manager = Aria2cManager()
        self.assertIsNotNone(manager.process)
        mock_popen.assert_called_once()
        manager.stop()

    @patch("subprocess.Popen")
    def test_start_server_failure(self, mock_popen):
        """Tests that a RuntimeError is raised when aria2c fails to start."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1
        mock_process.communicate.return_value = (b"", b"error")
        mock_popen.return_value = mock_process

        with self.assertRaises(RuntimeError):
            Aria2cManager()

    @patch("subprocess.Popen")
    def test_stop_server(self, mock_popen):
        """Tests that the aria2c server is terminated correctly."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        manager = Aria2cManager()
        manager.stop()
        mock_process.terminate.assert_called_once()


class TestDownloader(unittest.TestCase):
    def setUp(self):
        self.files_list = ListInfo(
            files=[
                FileInfo(name="file1.txt", url="http://example.com/file1.txt"),
                FileInfo(name="file2.txt", url="http://example.com/file2.txt"),
            ]
        )

    @patch("bulkget.downloader.Aria2cManager")
    def test_filter_downloaded_files(self, MockAria2cManager):
        """Tests that already downloaded files are filtered out."""
        with patch.object(FileInfo, "already_downloaded") as mock_already_downloaded:
            mock_already_downloaded.side_effect = [True, False]  # file1 is downloaded, file2 is not

            downloader = Downloader(target_dir="fake_dir", files_list=self.files_list)
            downloader._filter_downloaded_files()

            self.assertEqual(len(downloader.download_queue), 1)
            self.assertEqual(downloader.download_queue[0].name, "file2.txt")

    @patch("bulkget.downloader.Aria2cManager")
    def test_dry_run(self, MockAria2cManager):
        """Tests that no downloads are started in dry_run mode."""
        mock_aria2_manager_instance = MockAria2cManager.return_value
        
        downloader = Downloader(target_dir="fake_dir", files_list=self.files_list, dry_run=True)
        downloader.start()

        mock_aria2_manager_instance.add_file.assert_not_called()
        mock_aria2_manager_instance.watch.assert_not_called()

    @patch("bulkget.downloader.Aria2cManager")
    def test_download_files_call(self, MockAria2cManager):
        """Tests that the downloader calls the aria2 manager correctly."""
        mock_aria2_manager_instance = MockAria2cManager.return_value
        
        downloader = Downloader(target_dir="fake_dir", files_list=self.files_list)
        downloader.download_queue = downloader.files_list.files  # Assume no files are filtered
        downloader._download_files()

        self.assertEqual(mock_aria2_manager_instance.add_file.call_count, 2)
        mock_aria2_manager_instance.watch.assert_called_once()

    @patch("bulkget.downloader.Aria2cManager")
    def test_filepath_hook(self, MockAria2cManager):
        """Tests that the filepath_hook is used to determine the output path."""
        mock_aria2_manager_instance = MockAria2cManager.return_value

        def custom_hook(file_info):
            return f"custom/{file_info.name}"

        downloader = Downloader(
            target_dir="fake_dir",
            files_list=self.files_list,
            filepath_hook=custom_hook,
        )
        downloader.download_queue = downloader.files_list.files
        downloader._download_files()

        expected_calls = [
            call(url='http://example.com/file1.txt', target_dir='fake_dir', output_name='custom/file1.txt'),
            call(url='http://example.com/file2.txt', target_dir='fake_dir', output_name='custom/file2.txt'),
        ]
        mock_aria2_manager_instance.add_file.assert_has_calls(expected_calls, any_order=True)

    def tearDown(self):
        
        if Path("fake_dir").exists():
            shutil.rmtree(Path("fake_dir"))


if __name__ == "__main__":
    unittest.main()
