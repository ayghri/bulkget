# Climate Models Data Downloader (CESM2/CESM1)

## Requirements

-   Make sure `aria2` is installed. It is used by the script to manage downloads.
-   Create your account on the gateway then on 'Account Home' retrieve your API
    Token and save it.
-   Go to the variable's page, for example CESM2 SSH
    [monthly average](https://www.earthsystemgrid.org/dataset/ucar.cgd.cesm2le.ocn.proc.monthly_ave.SSH.html),
    then click on the "History" tab and download the XML file in the "Source"
    field. Save the file as `SSH_monthly.xml`

The XML file should contain all the information we will need: file URL, size,
name, hash... We will retrieve the download links and send them to the
downloader script.

Installing the package will provide an executable that call
`clim_downloader.main:main`

## Usage by example

We choose CESM2 and CESM1 from the
[models index](https://www.earthsystemgrid.org/project.html). For CESM2:
[dataset](https://www.earthsystemgrid.org/dataset/ucar.cgd.cesm2le.output.html)

Monthly data:

| Field      | link                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------ |
| Ocean      | [link](https://www.earthsystemgrid.org/dataset/ucar.cgd.cesm2le.ocn.proc.monthly_ave.html) |
| Atmosphere | [link](https://www.earthsystemgrid.org/dataset/ucar.cgd.cesm2le.atm.proc.monthly_ave.html) |

The package will extract the files from the XML file. Some files have multiple
versions, it will download the most recent one.

```bash
export TOKEN="put the token here"
clim_download --token $TOKEN \
--xml SSH_monthly.xml \
--target ./SSH \
--checksum true \ #use md5 checksum if available
--dry-run false \ #display information without downloading
--port 7800 \ #use different port for aria2 if another instance is running
```

To monitor the download speed and progress you can call (from within the same
python env):

```
aria2p -p 7800
```

The script will add a `dataset.json` to --target that contains the files
informations for later use.

**Note**: Some dataset have sizes different from the ones reported on the XML
file, so some files will always be re-downloaded whenever the script is
launched.

## Demo

https://github.com/aghriss/clim_downloader/assets/32200675/ba02a545-eab1-4988-81e8-7f5d8a17b852
