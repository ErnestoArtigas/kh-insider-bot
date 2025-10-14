"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

import asyncio
from optparse import OptionParser, Values
from typing import cast

import httpx
from bs4 import BeautifulSoup, Tag

import downloader
from core.dependencies import rich_console


def extract_name_from_title(link) -> str:
    return link.split("MP3")[0].rstrip()


def is_format_available(song_list_table: Tag, format: str) -> bool:
    table_headers = cast(Tag, song_list_table.find(id="songlist_header")).find_all(
        name="th"
    )

    return any(
        format == cast(str, cast(Tag, cast(Tag, th).contents[0]).string).lower()
        for th in table_headers
    )


async def scrap_links_from_table(
    song_list_table: Tag, format: str, title: str
) -> list[str]:
    song_page_link = []
    song_direct_link = []

    for link in song_list_table.find_all("a"):
        song_page_link.append(f"https://downloads.khinsider.com{link.get('href')}")

    song_page_link = list(dict.fromkeys(song_page_link))

    async with httpx.AsyncClient() as client:
        for link in song_page_link:
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

            song_direct_link.append(cast(Tag, format_music_link.parent).get(key="href"))

    return song_direct_link


def create_parser() -> tuple[OptionParser, Values]:
    parser = OptionParser(usage="main.py -f <format> -l <link/to/the/album>")
    parser.add_option(
        "-f",
        "--format",
        action="store",
        type="string",
        dest="format",
        help="Format of the music",
        metavar="FORMAT",
    )
    parser.add_option(
        "-l",
        "--link",
        action="store",
        type="string",
        dest="link",
        help="Link to the album",
        metavar="LINK",
    )

    (options, _) = parser.parse_args()
    return parser, options


async def main() -> None:
    parser, options = create_parser()
    if options.format is None or options.link is None:
        rich_console.print(
            "Missing arguments, you need to provide the format and the link in the command.",
            style="bold red",
        )
        rich_console.print(parser.usage)
        exit(code=1)

    if options.format.isdigit() or options.link.isdigit():
        rich_console.print(
            "The arguments provided are not string. You need to enter valid arguments",
            style="bold red",
        )
        rich_console.print(parser.usage)
        exit(code=1)

    response = httpx.get(url=options.link)

    soup = BeautifulSoup(markup=response.text, features="html.parser")

    if soup.title is None:
        rich_console.print("The program couldn't process the page.", style="bold red")
        exit(code=1)

    title = downloader.remove_invalid_chars(
        string=extract_name_from_title(link=soup.title.string)
    )

    rich_console.print(f"{title} was loaded.", style="bold green")

    song_list_table = soup.find(id="songlist")

    if song_list_table is None or type(song_list_table) is not Tag:
        rich_console.print(
            "The program cannot find a song table, invalid website.",
            style="bold red",
        )
        exit(code=1)

    if not is_format_available(song_list_table=song_list_table, format=options.format):
        rich_console.print(
            f"The format {options.format} is not available for {title}.",
            style="bold red",
        )
        exit(code=1)

    try:
        # TODO: Convert it to parallelism
        links = await scrap_links_from_table(
            song_list_table=song_list_table, format=options.format, title=title
        )
        rich_console.print(
            f"Scrapped {len(links)} tracks for this album.", style="green"
        )

        directory_name = downloader.create_directory(directory_name=title)

        if not directory_name:
            rich_console.print(
                f"Folder {title} not created, exiting the script.", style="bold red"
            )
            exit(1)

        rich_console.print(
            f"Folder {title} created, downloading the songs.", style="green"
        )

        # TODO: Write functions to use download_file with parallelism
        await downloader.download_files(links=links, path=directory_name)
        rich_console.print("Finished downloading all files.", style="bold green")
    except Exception as error:
        rich_console.print(error, style="bold red")


if __name__ == "__main__":
    asyncio.run(main=main())
