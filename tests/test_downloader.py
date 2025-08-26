import unittest
from unittest.mock import patch, call
from pathlib import Path


from bulkget.downloader import Downloader
from bulkget.utils import UrlInfo, UrlList

class TestDownloader(unittest.TestCase):
    def setUp(self):
        self.url_list = UrlList(
            files=[
                UrlInfo(name="file1.txt", url="http://example.com/file1.txt", checksum="abc"),
                UrlInfo(name="file2.txt", url="http://example.com/file2.txt", checksum="def"),
            ]
        )
        self.download_path = Path("test_downloads")
        self.download_path.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.download_path)

    @patch("bulkget.downloader.UrllibManager")
    @patch("bulkget.downloader.Aria2Manager")
    def test_downloader_initialization(self, MockAria2Manager, MockUrllibManager):
        """Tests that the downloader initializes the correct manager."""
        Downloader(
            download_path=self.download_path,
            url_list=self.url_list,
            manager="aria2c",
        )
        MockAria2Manager.assert_called_once()
        MockUrllibManager.assert_not_called()

        MockAria2Manager.reset_mock()
        Downloader(
            download_path=self.download_path,
            url_list=self.url_list,
            manager="urllib",
            n_workers=2,
        )
        MockUrllibManager.assert_called_once_with(n_workers=2)
        MockAria2Manager.assert_not_called()

    @patch("bulkget.utils.UrlInfo.already_downloaded")
    def test_filter_downloaded_files(self, mock_already_downloaded):
        """Tests that already downloaded files are filtered out."""
        mock_already_downloaded.side_effect = [True, False]  # file1 is downloaded, file2 is not

        downloader = Downloader(
            download_path=self.download_path,
            url_list=self.url_list,
            manager="urllib",
        )
        downloader._filter_downloaded_files()

        self.assertEqual(len(downloader.download_queue), 1)
        self.assertEqual(downloader.download_queue[0].name, "file2.txt")

    @patch("bulkget.downloader.Aria2Manager")
    def test_dry_run_aria2(self, MockAria2Manager):
        """Tests dry_run with the aria2c manager."""
        mock_manager_instance = MockAria2Manager.return_value
        downloader = Downloader(
            download_path=self.download_path,
            url_list=self.url_list,
            manager="aria2c",
            dry_run=True,
        )
        downloader.start()
        MockAria2Manager.assert_called_once_with(dry_run=True)
        self.assertEqual(mock_manager_instance.add_file.call_count, 2)
        mock_manager_instance.watch.assert_called_once()

    @patch("bulkget.downloader.UrllibManager")
    def test_dry_run_urllib(self, MockUrllibManager):
        """Tests dry_run with the urllib manager."""
        mock_manager_instance = MockUrllibManager.return_value
        downloader = Downloader(
            download_path=self.download_path,
            url_list=self.url_list,
            manager="urllib",
            dry_run=True,
        )
        downloader.start()
        MockUrllibManager.assert_called_once_with(dry_run=True)
        self.assertEqual(mock_manager_instance.add_file.call_count, 2)
        mock_manager_instance.watch.assert_called_once()

    @patch("bulkget.downloader.UrllibManager")
    def test_download_files_call(self, MockUrllibManager):
        """Tests that the downloader calls the manager correctly."""
        mock_manager_instance = MockUrllibManager.return_value

        downloader = Downloader(
            download_path=self.download_path,
            url_list=self.url_list,
            manager="urllib",
        )
        downloader.download_queue = (
            downloader.url_list.files
        )  # Assume no files are filtered
        downloader._download_files()

        self.assertEqual(mock_manager_instance.add_file.call_count, 2)
        mock_manager_instance.watch.assert_called_once()

    @patch("bulkget.downloader.UrllibManager")
    def test_downloader_with_filepath_hook(self, MockUrllibManager):
        """Tests the Downloader class with a custom filepath_hook."""
        mock_manager_instance = MockUrllibManager.return_value

        def custom_filepath_hook(file_info):
            return Path("custom_dir") / file_info.name

        downloader = Downloader(
            download_path=self.download_path,
            url_list=self.url_list,
            manager="urllib",
            filepath_hook=custom_filepath_hook,
        )
        downloader.download_queue = downloader.url_list.files
        downloader._download_files()

        expected_calls = [
            call(
                url="http://example.com/file1.txt",
                target_dir=str(self.download_path),
                output_name="custom_dir/file1.txt",
            ),
            call(
                url="http://example.com/file2.txt",
                target_dir=str(self.download_path),
                output_name="custom_dir/file2.txt",
            ),
        ]
        mock_manager_instance.add_file.assert_has_calls(expected_calls, any_order=True)


if __name__ == "__main__":
    unittest.main()
