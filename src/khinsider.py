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


def is_format_available(song_links_tag: Tag, format: str) -> bool:
    table_headers = cast(Tag, song_links_tag.find(id="songlist_header")).find_all(
        name="th"
    )

    return any(
        format == cast(str, cast(Tag, cast(Tag, th).contents[0]).string).lower()
        for th in table_headers
    )


# First step
def get_song_links_from_song_links_tag(song_links_tag: Tag) -> list[str]:
    song_links = []

    for link in song_links_tag.find_all("a"):
        song_links.append(
            f"https://downloads.khinsider.com{cast(Tag, link).get('href')}"
        )

    return list(dict.fromkeys(song_links))


# Second step
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


# Third step
def process_chunk_song_links(format: str, song_links: list[str], i: int) -> list[str]:
    async def main(format, song_links):
        async with httpx.AsyncClient() as client:
            return await get_media_link_from_song_links(
                format=format, song_links=song_links, client=client
            )

    return asyncio.run(main(format, song_links))


# Quad step
def scrapping_song_list_table(format: str, song_links_tag: Tag) -> list[str]:
    song_links = get_song_links_from_song_links_tag(song_links_tag=song_links_tag)

    size_chunks = round(
        len(song_links)
        / (len(song_links) if len(song_links) < cpu_count() else cpu_count())
    )

    song_links_chunked = [
        song_links[i : i + size_chunks] for i in range(0, len(song_links), size_chunks)
    ]

    futures = []

    with rich_console.status(
        status=f"[bold cyan]Using {len(song_links_chunked)} cores to scrap song table..."
    ) as _:
        with concurrent.futures.ProcessPoolExecutor(
            len(song_links_chunked)
        ) as executor:
            for i in range(len(song_links_chunked)):
                futures.append(
                    executor.submit(
                        process_chunk_song_links,
                        format=format,
                        song_links=song_links_chunked[i],
                        i=i,
                    )
                )

        concurrent.futures.wait(futures)

    # Get result for each future.
    futures = list(map(lambda x: x.result(), futures))

    # Flatten the result.
    futures = list(chain.from_iterable(futures))

    return futures
