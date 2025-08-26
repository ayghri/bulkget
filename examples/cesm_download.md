# Downloading CESM2 Data with Bulkget

This guide provides a step-by-step walkthrough on how to download CESM2 (Community Earth System Model 2) data from the NCAR Research Data Archive using `bulkget` and the provided example scripts.

## 1. Finding the Dataset and Filelist IDs

Before you can start downloading, you need to identify two key pieces of information from the NCAR Research Data Archive website:

-   **Dataset ID**: This is a unique identifier for the dataset you want to access. For example, the dataset ID for "CESM2 Large Ensemble Project" is `d651056`.
-   **Filelist ID**: Within a dataset, there can be multiple file lists. You need to find the ID for the specific collection of files you are interested in.

You can typically find these IDs in the URL when browsing the dataset on the [NCAR RDA website](https://rda.ucar.edu/). For instance, if the URL is `https://rda.ucar.edu/datasets/d651056/filelist/22/`, the dataset ID is `d651056` and the filelist ID is `22`.

Alternatively, you can find the `filelist` number by inspecting the "Web File Listing" element on the dataset page. The `onclick` attribute will contain the necessary information. For example:
`onclick="$.get('/datasets/d651056/filelist/22/', replace_ds_content)"`
In this case, the filelist ID is `22`.

## 2. Generating the Download Links

Once you have the dataset and filelist IDs, you can use the `examples/get_cesm2_links.py` script to crawl the website and generate a JSON file containing all the download links for a specific variable.

In this example, we will download the links for the `TAUY` variable:

```bash
python examples/get_cesm2_links.py --dataset d651056 --filelist 22 --var-name TAUY --target data/
```

This command will produce the following output and create a `data/TAUY_d651056.json` file:

```
Starting crawl for variable 'TAUY' in dataset 'd651056'.
Crawling page: https://rda.ucar.edu/datasets/d651056/filelist/22/?filter_wfile=TAUY.&page=0
Found 2000 new file(s) on page 0.
Crawling page: https://rda.ucar.edu/datasets/d651056/filelist/22/?filter_wfile=TAUY.&page=1
Found 600 new file(s) on page 1.
Crawling page: https://rda.ucar.edu/datasets/d651056/filelist/22/?filter_wfile=TAUY.&page=2
No .nc files found on page 2. Stopping crawl.
Crawl finished. Found a total of 2600 unique files.
Successfully saved link list to data/TAUY_d651056.json
```

## 3. Downloading the Files with Bulkget

Now that you have the JSON file with all the download links, you can use `bulkget` to download the files.

### Important Note on Download Manager

The NCAR Research Data Archive may not be compatible with `aria2c` due to how it handles redirects or authentication. For this reason, it is recommended to use the `urllib` manager, which is more resilient in these cases.

### Running the Download

The following command will download the files using the `urllib` manager, 8 parallel workers, and a custom filepath hook to organize the downloaded files.

```bash
bulkget --path /buckets/datasets/ssh/simulations/cesm2/monthly/ \
        -n 8 \
        --manager urllib \
        --filepath-hook examples/cesm2_filepath.py \
        data/TAUY_d651056.json
```

The `examples/cesm2_filepath.py` hook is designed to parse the CESM2 filenames and organize them into a structured directory hierarchy `VAR_NAME/SIMULATION/START_MONTH-END_MONTH.nc`.  This helps in keeping the downloaded data organized.
