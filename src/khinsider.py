from typing import cast

import httpx
from bs4 import BeautifulSoup, Tag
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


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


async def get_media_links_from_song_links_tag(
    song_links_tag: Tag, format: str, title: str
) -> list[str]:
    song_links = []
    media_links = []

    for link in song_links_tag.find_all("a"):
        song_links.append(f"https://downloads.khinsider.com{link.get('href')}")

    song_links = list(dict.fromkeys(song_links))

    progress_bar = Progress(
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
    )

    async with httpx.AsyncClient() as client:
        with progress_bar as p:
            for link in p.track(song_links):
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
