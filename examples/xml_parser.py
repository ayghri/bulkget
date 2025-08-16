from typing import Dict
from bulkget.downloader import FileInfo
from ..bulkget.downloader import ListInfo
import xml.etree.ElementTree as ET
import datetime


def parse_xml(xml_path: str):
    iter = ET.iterparse(xml_path)
    for _, el in iter:
        el.tag = el.tag.split("}")[1]
    root = iter.root
    return root.findall("dataset")[0]


def get_properties(node) -> Dict:
    data = {}
    properties = node.findall("property")
    for prop in properties:
        data[prop.attrib["name"]] = prop.attrib["value"]
    return data


def get_file_info(file_tree) -> FileInfo:
    properties = get_properties(file_tree)
    file_info = FileInfo(
        name=file_tree.attrib["name"],
        url=file_tree.attrib["urlPath"],
        checksum=properties.get("checksum", ""),
        checksum_type=properties.get("checksum_type", ""),
        size=int(properties["size"]),
        mod_time=datetime.datetime.strptime(
            properties["mod_time"], "%Y-%m-%d %H:%M:%S"
        ),
    )
    return file_info


def extract_dataset(xml_path) -> ListInfo:
    # got the dataset tree
    dataset_tree = parse_xml(xml_path)
    # retrieve all files nodes
    file_nodes = dataset_tree.findall("dataset")
    # START: some files are duplicate, we get the most recent one
    files_hash: Dict[str, FileInfo] = {}
    for node in file_nodes:
        file_info = get_file_info(node)
        if file_info.name in files_hash:
            if files_hash[file_info.name].mod_time > file_info.mod_time:
                file_info = files_hash[file_info.name]
        files_hash[file_info.name] = file_info
    # END

    return ListInfo(
        properties=get_properties(dataset_tree),
        files=list(files_hash.values()),
    )
