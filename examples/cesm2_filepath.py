import re
from bulkget.utils import UrlInfo

def filepath_hook(file_info: UrlInfo) -> str:
    """
    Extracts a subpath from a NetCDF filename based on its structure.

    The function expects the filename to the pattern "...[SIM]...[VAR]..[MONTH1]-[MONTH2]"
    the simulation identifier SIM and the start and end months to point to "SIM/MONTH1-MONTH2.nc"

    Parameters:
    file_info (FileInfo): The file information object containing the filename to parse.

    Returns:
    str: A formatted subfolder path in the form 'sim/start_month-end_month.nc'.

    Raises:
    AssertionError: If the filename does not match the expected pattern or if
                    the number of captured groups is not as expected.
    """
    match = re.match(
        r".*-(\d{4}\.\d{3})\..*\.([A-Z]*)\.(\d{6})-(\d{6})\.nc", file_info.name
    )
    if not match or match.lastindex != 4:
        # Return a default path if the pattern does not match
        return file_info.name

    sim = match.group(1)
    var_name = match.group(2)
    start_month = int(match.group(3))
    end_month = int(match.group(4))
    subfolder = f"{var_name}/{sim}/{start_month}-{end_month}.nc"
    return subfolder