import unittest
import hashlib
from pathlib import Path
import json
from datetime import datetime
from dataclasses import replace

from bulkget.utils import verify_checksum, FileInfo, ListInfo

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_utils_data")
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "test_file.txt"
        self.test_content = b"this is a test file for checksum"
        with open(self.test_file, "wb") as f:
            f.write(self.test_content)

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()
        list_file = self.test_dir / "list.json"
        if list_file.exists():
            list_file.unlink()
        self.test_dir.rmdir()

    def test_verify_checksum_valid(self):
        """Tests that verify_checksum returns True for a valid checksum."""
        checksum = hashlib.sha256(self.test_content).hexdigest()
        self.assertTrue(verify_checksum(self.test_file, checksum, "sha256"))

    def test_verify_checksum_invalid(self):
        """Tests that verify_checksum returns False for an invalid checksum."""
        self.assertFalse(verify_checksum(self.test_file, "invalid_checksum", "sha256"))

    def test_file_info_already_downloaded(self):
        """Tests the already_downloaded method of the FileInfo class."""
        checksum = hashlib.sha256(self.test_content).hexdigest()
        file_info = FileInfo(
            name="test_file.txt",
            url="http://example.com/test.txt",
            checksum=checksum,
            checksum_type="sha256",
            size=len(self.test_content),
        )

        # Should be true when file exists and checksum matches
        self.assertTrue(file_info.already_downloaded(self.test_file))

        # Should be false if file doesn't exist
        self.assertFalse(file_info.already_downloaded(Path("non_existent_file.txt")))

        # Should be false if checksum is wrong
        file_info_bad_checksum = replace(file_info, checksum="bad")
        self.assertFalse(file_info_bad_checksum.already_downloaded(self.test_file))

        # Should be true if checksum is skipped and size matches
        self.assertTrue(file_info.already_downloaded(self.test_file, should_checksum=False))

        # Should be false if size is wrong and checksum is skipped
        file_info_bad_size = replace(file_info, size=1)
        self.assertFalse(file_info_bad_size.already_downloaded(self.test_file, should_checksum=False))

    def test_list_info_from_json(self):
        """Tests creating a ListInfo object from a JSON file."""
        list_file = self.test_dir / "list.json"
        json_data = {
            "properties": {"dataset": "test"},
            "files": [
                {
                    "name": "file1.txt",
                    "url": "http://example.com/file1.txt",
                    "checksum": "abc",
                    "checksum_type": "sha256",
                    "size": 123,
                    "mod_time": "2025-08-15T15:00:00",
                }
            ],
        }
        with open(list_file, "w") as f:
            json.dump(json_data, f)

        list_info = ListInfo.from_json(list_file)
        self.assertIsInstance(list_info, ListInfo)
        self.assertEqual(list_info.properties["dataset"], "test")
        self.assertEqual(len(list_info.files), 1)
        self.assertEqual(list_info.files[0].name, "file1.txt")
        self.assertEqual(list_info.files[0].mod_time, datetime(2025, 8, 15, 15, 0, 0))

if __name__ == "__main__":
    unittest.main()
