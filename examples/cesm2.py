import re

def ncfile_subpath(file_info) -> str:
    """
    Extracts a subpath from a NetCDF filename based on its structure.

    The function expects the filename to the pattern "...[SIM]...[VAR]..[MONTH1]-[MONTH2]"
    the simulation identifier SIM and the start and end months to point to "SIM/MONTH1-MONTH2.nc"

    Parameters:
    nc_filename (str): The NetCDF filename to parse.

    Returns:
    str: A formatted subfolder path in the form 'sim/start_month-end_month.nc'.

    Raises:
    AssertionError: If the filename does not match the expected pattern or if
                    the number of captured groups is not as expected.
    """
    result = re.match(
        r".*-(\d{4}\.\d{3})\..*\.([A-Z]*)\.(\d{6})-(\d{6})\.nc", file_info.name
    )
    assert result is not None
    assert result.lastindex == 4

    sim = result.group(1)
    start_month = int(result.group(3))
    end_month = int(result.group(4))
    subfolder = f"{sim}/{start_month}-{end_month}.nc"
    return subfolder

import argparse
from pathlib import Path
from dataclasses import asdict
import json

from ..examples.xml_parser import extract_dataset
from .downloader import download_dataset



ENDPOINT = "https://tds.ucar.edu/thredds/fileServer/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=str)
    parser.add_argument("--target", type=str)
    parser.add_argument("--token", type=str)
    parser.add_argument("--port", type=int, default=6800)
    parser.add_argument("--checksum", type=bool, default=False)
    parser.add_argument("--dry-run", type=bool, default=False)
    args = parser.parse_args()

    xml_path = args.xml
    target_dir = args.target
    api_token = args.token

    URL_FORMAT = f"{ENDPOINT}{{url}}?api-token={api_token}"
    dataset = extract_dataset(xml_path)

    Path(target_dir).mkdir(parents=True, exist_ok=True)

    with Path(target_dir).joinpath("dataset.json").open("w") as f:
        f.write(json.dumps(asdict(dataset), indent=2, default=str))

    download_dataset(
        target_dir=target_dir,
        dataset=dataset,
        url_format=URL_FORMAT,
        filepath_hook=ncfile_subpath,
        port=args.port,
        dry_run=args.dry_run,
        should_checksum=args.checksum,
    )
