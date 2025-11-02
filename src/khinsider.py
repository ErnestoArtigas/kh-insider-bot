import asyncio
import concurrent.futures
from itertools import chain
from multiprocessing import cpu_count
from typing import cast

import httpx
from bs4 import BeautifulSoup, Tag

from core.dependencies import rich_console


def extract_name_from_title(link) -> str:
    return link.split("MP3")[0].rstrip()


def is_format_available(song_table: Tag, format: str) -> bool:
    table_headers = cast(Tag, song_table.find(id="songlist_header")).find_all(name="th")

    return any(
        format == cast(str, cast(Tag, cast(Tag, th).contents[0]).string).lower()
        for th in table_headers
    )


# Function that creates multiple processes to scrap the song table.
def scrapping_song_table(format: str, song_table: Tag) -> list[str]:
    song_links = get_song_links_from_song_table(song_table=song_table)

    """
    To get the right size_chunks, there are two rules:
    - If the array's length is smaller than the cpu_count, then each chunks is 1 element long.
    - Else, we use the cpu_count to divide the array's length.
    """
    size_chunks = round(
        number=len(song_links)
        / (len(song_links) if len(song_links) < cpu_count() else cpu_count())
    )

    # Divides the array into chunks for each processes.
    song_links_chunked = [
        song_links[i : i + size_chunks] for i in range(0, len(song_links), size_chunks)
    ]

    futures = []

    with rich_console.status(
        status=f"[bold cyan]Using {len(song_links_chunked)} cores to scrap song table..."
    ) as _:
        # Running as much workers as chunks in the array (lower or equal to cpu_count).
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=len(song_links_chunked)
        ) as executor:
            for i in range(len(song_links_chunked)):
                futures.append(
                    executor.submit(
                        process_chunk_song_links,
                        format,
                        song_links_chunked[i],
                    )
                )

        concurrent.futures.wait(futures)

    # Gets result for each future.
    futures = list(map(lambda x: x.result(), futures))

    # Flattens the result.
    futures = list(chain.from_iterable(futures))

    return futures


def get_song_links_from_song_table(song_table: Tag) -> list[str]:
    song_links = []

    for link in song_table.find_all("a"):
        song_links.append(
            f"https://downloads.khinsider.com{cast(Tag, link).get('href')}"
        )

    return list(dict.fromkeys(song_links))


# Synchronously runs async chunk processing, function used in processes.
def process_chunk_song_links(format: str, song_links: list[str]) -> list[str]:
    async def async_process_chunk_song_links(
        format: str, song_links: list[str]
    ) -> list[str]:
        async with httpx.AsyncClient() as client:
            return await get_media_link_from_song_links(
                format=format, song_links=song_links, client=client
            )

    return asyncio.run(
        main=async_process_chunk_song_links(format=format, song_links=song_links)
    )


# Extracts from the song link the media link.
async def get_media_link_from_song_links(
    format: str, song_links: list[str], client: httpx.AsyncClient
) -> list[str]:
    media_links = []

    for link in song_links:
        response = await client.get(url=link)
        page_soup = BeautifulSoup(markup=response.text, features="html.parser")
        music_links = page_soup.find_all(
            name="span",
            class_="songDownloadLink",
        )

        # Find the right link element
        format_music_link = [
            link
            for link in music_links
            if format
            in cast(str, cast(Tag, cast(Tag, link).contents[1]).string).lower()
        ][0]

        media_links.append(cast(Tag, format_music_link.parent).get(key="href"))

    return media_links
