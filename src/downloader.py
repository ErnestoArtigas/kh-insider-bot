"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

import os
import re
from urllib.parse import unquote

import aiofiles
import httpx
from tqdm import tqdm


def remove_invalid_chars(string) -> str:
    return re.sub(pattern=r'[\\\/?:*"<>|]', repl="", string=string)


def extract_decode_filename(url: str) -> str:
    return unquote(string=url.split("/")[-1])


def create_directory(directory_name: str) -> str:
    path = os.path.join(os.getcwd(), directory_name)
    try:
        os.mkdir(path=path)
        return path
    except OSError as error:
        print(error)


async def download_file(path: str, link: str, client: httpx.AsyncClient) -> None:
    file_name = extract_decode_filename(url=link)

    try:
        async with aiofiles.open(file=os.path.join(path, file_name), mode="wb") as file:
            async with client.stream(method="GET", url=link) as response:
                with tqdm(
                    total=float(response.headers["content-length"]),
                    unit="B",
                    unit_scale=True,
                    desc=file_name,
                    initial=0,
                    ascii=False,
                    colour="green",
                ) as progress:
                    async for chunk in response.aiter_bytes():
                        await file.write(chunk)
                        progress.update(len(chunk))
    except Exception as error:
        print(error)


async def download_files(links: list[str], path: str) -> None:
    async with httpx.AsyncClient() as client:
        for link in links:
            await download_file(link=link, path=path, client=client)
