"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

import os
import re
from urllib.parse import unquote

import requests
from tqdm import tqdm


def remove_invalid_chars(string) -> str:
    return re.sub(pattern=r'[\\\/?:*"<>|]', repl="", string=string)


def get_request_from_link(link) -> requests.Response:
    response = requests.get(link)
    if response.status_code != 200:
        response.raise_for_status()
    return response


def extract_decode_filename(url) -> str:
    return unquote(string=url.split("/")[-1])


def create_directory(directory_name) -> None:
    path = os.path.join(os.getcwd(), directory_name)
    try:
        os.mkdir(path=path)
    except OSError as error:
        raise error


def download_file(path, link) -> None:
    request = get_request_from_link(link=link)
    fileName = extract_decode_filename(url=link)
    totalSize = int(request.headers.get("content-length"))
    try:
        with open(file=os.path.join(path, fileName), mode="wb") as file:
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
