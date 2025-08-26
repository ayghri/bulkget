# Bulkget

Bulkget is a Python-based command-line tool for efficiently downloading a large number of files from a list of URLs. It offers flexibility by supporting two different download managers: the robust and feature-rich `aria2c` for high-performance downloads, and a simple, built-in `urllib` manager for environments where `aria2c` is not available.

## Features

- **Bulk Downloading**: Download a large number of files from a list of URLs specified in a JSON file.
- **Choice of Download Manager**:
  - **`aria2c`**: For fast and reliable downloads, with support for features like parallel downloads and automatic retries. Requires `aria2c` to be installed on your system.
  - **`urllib`**: A lightweight, dependency-free downloader for basic needs. It downloads files to a temporary `*.tmp` file and renames them upon completion to prevent partial downloads.
- **Parallel Downloads**: Download multiple files concurrently to maximize bandwidth usage (configurable with `-n` or `--n-workers`).
- **Checksum Verification**: Ensure file integrity by verifying checksums after download using the `--checksum` flag.
- **Dry Run Mode**: Simulate the download process without actually downloading any files using the `--dry-run` flag.
- **Customizable File Paths**: Use a Python script with a `filepath_hook` function to define custom output paths for downloaded files via the `--filepath-hook` argument.
- **Overwrite Control**: Choose whether to overwrite files that already exist in the destination with the `--overwrite` flag.

## Installation

1.  **Install `aria2c`** (optional, for `aria2c` manager):
    On Debian/Ubuntu:
    ```bash
    sudo apt-get install aria2
    ```
    On macOS:
    ```bash
    brew install aria2
    ```

2.  **Install Bulkget**:
    Clone the repository and install the package using Poetry:
    ```bash
    git clone https://github.com/ayghri/bulkget.git
    cd bulkget
    poetry install
    ```

## Usage

The primary entry point for the tool is the `bulkget` command-line interface.

### Command-Line Interface

```bash
bulkget [OPTIONS] list
```

**Arguments**:

- `list`: Path to the JSON file containing the list of files to download.

**Options**:

- `--path TEXT`: Target directory to download files to. Defaults to the current directory.
- `--manager [aria2c|urllib]`: The download manager to use. Defaults to `aria2c`.
- `-n, --n-workers INTEGER`: Number of parallel download workers. Defaults to 4.
- `--overwrite`: Overwrite existing files.
- `--checksum`: Verify file checksums after download.
- `--dry-run`: Simulate the download without actual file transfers.
- `--port INTEGER`: Port for the `aria2c` RPC server. Defaults to 6800.
- `--filepath-hook TEXT`: Path to a Python file with a 'filepath_hook' function to customize output file paths.
- `--help`: Show the help message and exit.

### JSON File Format

The `list` file should be a JSON object containing a list of file information objects.

```json
{
  "properties": {},
  "files": [
    {
      "name": "file1.txt",
      "url": "http://example.com/file1.txt",
      "checksum": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
      "checksum_type": "sha256"
    },
    {
      "name": "file2.zip",
      "url": "http://example.com/file2.zip",
      "size": 1024
    }
  ]
}
```

- `name`: The name of the file.
- `url`: The URL to download the file from.
- `checksum` (optional): The checksum hash of the file.
- `checksum_type` (optional): The checksum algorithm (e.g., 'md5', 'sha256').
- `size` (optional): The size of the file in bytes.

### Customizing File Paths

You can customize the output directory and filename for each downloaded file by providing a Python script with a `filepath_hook` function. This function receives a [`UrlInfo`](https://github.com/ayghri/bulkget/blob/master/bulkget/utils.py) object and should return the desired relative path for the file.

Use the `--filepath-hook` argument to specify your script.

**Example hook file (`my_hooks.py`):**

```python
from pathlib import Path
from bulkget.utils import UrlInfo

def filepath_hook(file_info: UrlInfo) -> Path:
    # Example: save files into subdirectories based on the first letter of the filename
    first_letter = file_info.name[0].lower()
    return Path(first_letter) / file_info.name
```

**Usage:**

```bash
bulkget --filepath-hook my_hooks.py data/dataset.json
```

This will save files into subdirectories like `a/`, `b/`, etc., inside the target path.

## Examples

### Basic Download

To download the files specified in `dataset.json` to the `downloads` directory:

```bash
bulkget --path downloads data/dataset.json
```

### Using the `urllib` Manager

To use the `urllib` manager with 8 parallel workers:

```bash
bulkget --manager urllib -n 8 data/dataset.json
```

### Dry Run

To see which files would be downloaded without actually downloading them, including their source URLs and target paths:

```bash
bulkget --dry-run data/dataset.json
```

### Verify Checksums

To verify file integrity after download:

```bash
bulkget --checksum data/dataset.json
```

## Use Case: Downloading CESM2 Data

For a detailed guide on how to use `bulkget` to download data from the CESM2 Large Ensemble Project, please see the [CESM2 Download Guide](https://github.com/ayghri/bulkget/blob/master/examples/cesm_download.md).
