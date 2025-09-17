"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

import os
import re
from urllib.parse import unquote

import colorama
import requests
from tqdm import tqdm


def remove_invalid_chars(string):
    return re.sub(r'[\\\/?:*"<>|]', "", string)


def get_request_from_link(link):
    request = requests.get(link)
    print("request", request)
    if request.status_code != 200:
        request.raise_for_status()
    return request


def extract_decode_filename(url):
    return unquote(url.split("/")[-1])


def create_directory(directoryName):
    path = os.path.join(os.getcwd(), directoryName)
    try:
        os.mkdir(path)
    except OSError as error:
        raise error


def download_file(path, link):
    request = get_request_from_link(link)
    fileName = extract_decode_filename(link)
    totalSize = int(request.headers.get("content-length"))
    try:
        with open(os.path.join(path, fileName), "wb") as file:
            with tqdm(
                total=totalSize,
                unit="B",
                unit_scale=True,
                desc=fileName,
                initial=0,
                ascii=False,
                colour="green",
            ) as progressBar:
                for chunk in request.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
                        progressBar.update(len(chunk))
    except Exception as error:
        raise (error)


def download_files(directoryName, linkArray):
    try:
        create_directory(directoryName)
        for element in linkArray:
            download_file(os.path.join(os.getcwd(), directoryName), element)
        print(colorama.Fore.GREEN, "Finished downloading all files.")
    except Exception as error:
        print(colorama.Fore.RED)
        print(error)
