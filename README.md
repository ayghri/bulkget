# bulkget

A simple and efficient bulk file downloader powered by `aria2c` and its python wrapper [aria2p](https://github.com/pawamoy/aria2p).

`bulkget` is designed to download a large number of files from a list specified in a JSON file. It uses `aria2c` for parallel downloads, checksum verification, and error handling.

## Features

-   **Parallel Downloads**: Leverages `aria2c` to download multiple files at once.
-   **Checksum Verification**: Automatically verifies file integrity using SHA-256 or other hash algorithms.
-   **Resumable Downloads**: Can resume interrupted downloads.
-   **Customizable File Paths**: Use hooks to define a custom directory structure for your downloads.
-   **Dry Run Mode**: Simulate a download process without downloading any files.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

1.  **Install Poetry**:
    Follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).

2.  **Install Dependencies**:
    From the root of the project directory, run:
    ```bash
    poetry install
    ```

This will create a virtual environment and install all the necessary dependencies.

## Usage

The primary command-line interface is `bulkget`.

```bash
bulkget [OPTIONS] list_json.json
```

**Arguments**:

- `list_json.json`: (Required) Path to the JSON file containing the list of files to download.

**Options**:
- `--target <directory>`: (Required) The directory where files will be downloaded. Defaults to the current directory.
- `--port <port>`: The port for the aria2c RPC server. Defaults to 6800.
- `--checksum`: If set, verifies the checksum of each file after download, if checksum not in json, it uses file size.
- `--dry-run`: If set, simulates the download process without actually downloading any files.

**JSON File Format**:

The `list_json.json` file should have the following structure:

```json
{
  "properties": {
  },
  "files": [
    {
      "name": "file1.zip",
      "url": "http://example.com/file1.zip",
      "checksum": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
      "checksum_type": "sha256",
      "size": 1024,
      "mod_time": "2025-08-15T15:00:00"
    },
    {
      "name": "file2.tar.gz",
      "url": "http://example.com/file2.tar.gz",
      "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "checksum_type": "sha256"
    }

    {
      "name": "file3.tar.gz",
      "url": "http://example.com/file3.tar.gz",
    }
  ]
}
```

**Monitor Downloads**:

```sh
aria2p -p <port>
```


# Climate Models Bulk downloader library

I've created this package to manage downloading the datasets of the climate
models from the Earth System Grid.

Provided as is. It requires >=Python 3.9, depends mainly on [aria2p](https://github.com/pawamoy/aria2p).

## Requirements

-   Ensure that `aria2` is installed on your system, as it is used by the script
    to manage downloads.

## Installation

```
pip install git+https://github.com/aghriss/bulk-download
```

## Usage by example

The key component for using this library is the `FileInfo` class defined in
`downloader.py`

```python
from bulk_download.downloader import launch_download
from bulk_download.downloader import FileInfo
from bulk_download.downloader import DatasetInfo


URL = "https://raw.githubusercontent.com/aghriss/bulk-download/master/bulk_download/{url}"
f1 = FileInfo(name="file1.py", url="downloader.py")
f2 = FileInfo(name="file2.py", url="utils.py")
f3 = FileInfo(name="file3.py", url="__init__.py", metadata={"hidden": True})
dataset = DatasetInfo(files=[f1, f2, f3])

# it will save "files_list.json" to target_dir
launch_download(target_dir="/tmp/bulk_test", url_format=URL, dataset=dataset, port=6800)

# ls /tmp/bulk_test
## ❯ ls /tmp/bulk_test
## total 16K
##    0   120  .
##    0   860  ..
## 8.0K  6.5K  file1.py
## 4.0K  1.8K  file2.py
##    0     0  file3.py
## 4.0K   431  files_list.json
```

We can provide a `locate_files_func` to specify the sub-path of `target_dir` for
each file:

```python

URL = "https://raw.githubusercontent.com/aghriss/bulk-download/master/bulk_download/{url}"
f1 = FileInfo(name="file1.py", url="downloader.py")
f2 = FileInfo(name="file2.py", url="utils.py")
f3 = FileInfo(name="file3.py", url="__init__.py", metadata={"hidden": True})
dataset = DatasetInfo(files=[f1, f2, f3])


# let's say we want to put the files in subfolders depending on their type
def locate_file(f: FileInfo):
    if f.metadata.get("hidden", False):
        return f".sub/{f.name}"
    return f"main/{f.name}"


launch_download(
    target_dir="/tmp/bulk_test",
    url_format=URL,
    dataset=dataset,
    port=6800,
    locate_files_func=locate_file,
)

## ❯ find /tmp/bulk_test -type f -name "*.py"
## /tmp/bulk_test/main/file1.py
## /tmp/bulk_test/main/file2.py
## /tmp/bulk_test/.sub/file3.py
```

The script will add a `files_list.json` in the `target_dir` that contains the
file information for later use.

## Demo

This is a demo that uses the library to download CESM2 data.
[More details here](docs/cesm_download.md)
https://github.com/aghriss/clim_downloader/assets/32200675/ba02a545-eab1-4988-81e8-7f5d8a17b852
