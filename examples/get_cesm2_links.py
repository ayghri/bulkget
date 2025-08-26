"""
This script crawls the NCAR Research Data Archive to find and list download links
for NetCDF (.nc) files for a specific dataset, file list, and variable.
It is designed to be used with datasets like CESM2, as demonstrated in the example usage.

The script takes a dataset ID, a file list ID, and a variable name as input,
and generates a JSON file containing the URLs of the found .nc files. This
JSON file can then be used with other tools (like bulkget) to download the files.

Example:
    python examples/get_cesm2_links.py \
        --dataset d651056 \
        --filelist 22 \
        --var-name SSH \
        --target ./data
"""
import argparse
import requests
from pathlib import Path
from typing import Union, Set

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    print(
        "Beautiful Soup is not installed. Please install it with 'pip install beautifulsoup4'"
    )
    exit(1)

from bulkget.utils import UrlInfo, UrlList

BASE_URL = "https://rda.ucar.edu/datasets"


def _fetch_and_parse_page(session: requests.Session, url: str) -> BeautifulSoup:
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        response = session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Failed to fetch page {url}: {e}")
        raise


def _extract_nc_links(soup: BeautifulSoup) -> Set[str]:
    """Extracts unique .nc file links from a BeautifulSoup object."""
    links = soup.find_all(
        "a", href=lambda href: href and href.strip().endswith(".nc")  # type: ignore
    )
    return {link["href"].strip() for link in links} # type: ignore


def crawl_for_nc_files(
    dataset: str, filelist: Union[str, int], var_name: str
) -> UrlList:
    """
    Crawls paginated web pages to find unique .nc file links for a given variable.

    Args:
        dataset: The dataset ID (e.g., 'd651056').
        filelist: The file list ID within the dataset.
        var_name: The variable name to filter by (e.g., 'SSH').

    Returns:
        A UrlList object containing the found file URLs and metadata.
    """
    print(f"Starting crawl for variable '{var_name}' in dataset '{dataset}'.")
    page_num = 0
    found_files: Set[str] = set()
    session = requests.Session()
    list_link = f"{BASE_URL}/{dataset}/filelist/{filelist}/"

    while True:
        page_url = f"{list_link}?filter_wfile={var_name}.&page={page_num}"
        print(f"Crawling page: {page_url}")

        try:
            soup = _fetch_and_parse_page(session, page_url)
        except requests.RequestException:
            break

        new_links = _extract_nc_links(soup)

        if not new_links:
            print(f"No .nc files found on page {page_num}. Stopping crawl.")
            break

        newly_discovered_files = new_links - found_files
        if not newly_discovered_files:
            print(f"No new .nc files found on page {page_num}. Stopping crawl.")
            break

        found_files.update(newly_discovered_files)
        print(
            f"Found {len(newly_discovered_files)} new file(s) on page {page_num}."
        )
        page_num += 1

    print(f"Crawl finished. Found a total of {len(found_files)} unique files.")

    file_infos = [
        UrlInfo(name=url.split("/")[-1], url=url)
        for url in sorted(list(found_files))
    ]
    return UrlList(
        files=file_infos, properties={"url": list_link, "filter": var_name}
    )


def main():
    """Parses command-line arguments and runs the crawler."""
    parser = argparse.ArgumentParser(
        description="Crawl the NCAR RDA for NetCDF file links.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example Usage:
  python examples/get_cesm2_links.py --dataset d651056 --filelist 22 --var-name SSH --target ./data
""",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Dataset ID, e.g., 'd651056' for CESM2.",
    )
    parser.add_argument(
        "--filelist",
        type=str,
        required=True,
        help="File list ID for the dataset, e.g., '22'.",
    )
    parser.add_argument(
        "--var-name",
        type=str,
        required=True,
        help="Variable name to filter for, e.g., 'SSH'.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Target directory to save the output JSON file.",
    )

    args = parser.parse_args()

    args.target.mkdir(parents=True, exist_ok=True)

    url_list = crawl_for_nc_files(args.dataset, args.filelist, args.var_name)

    output_file = args.target / f"{args.var_name}_{args.dataset}.json"
    url_list.to_json(output_file, indent=2)
    print(f"Successfully saved link list to {output_file}")


if __name__ == "__main__":
    main()
