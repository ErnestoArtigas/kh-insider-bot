"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

import asyncio
import time
from optparse import OptionParser, Values

import httpx
from bs4 import BeautifulSoup, Tag

import downloader
from core.dependencies import rich_console
from khinsider import (
    extract_name_from_title,
    is_format_available,
    test,
)


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

    # 1 - Arguments verification.
    if options.format is None or options.link is None:
        rich_console.print(
            "Missing arguments, you need to provide the format and the link in the command.",
            style="bold red",
        )
        rich_console.print(parser.usage)
        exit(code=1)

    if options.format.isdigit() or options.link.isdigit():
        rich_console.print(
            "The arguments provided are not string. You need to enter valid arguments.",
            style="bold red",
        )
        rich_console.print(parser.usage)
        exit(code=1)

    # 2 - Get BeautifulSoup from link.
    response = httpx.get(url=options.link)

    soup = BeautifulSoup(markup=response.text, features="html.parser")

    if soup.title is None:
        rich_console.print("The program couldn't process the page.", style="bold red")
        exit(code=1)

    # 3 - Remove invalid characters from title.
    title = downloader.remove_invalid_chars(
        string=extract_name_from_title(link=soup.title.string)
    )

    rich_console.print(f"{title} was loaded.", style="bold green")

    # 4 - Verify if songlistg table exists.
    song_table = soup.find(id="songlist")

    if song_table is None or type(song_table) is not Tag:
        rich_console.print(
            "The program cannot find a song table, invalid website.",
            style="bold red",
        )
        exit(code=1)

    if not is_format_available(song_table=song_table, format=options.format):
        rich_console.print(
            f"The format {options.format} is not available for {title}.",
            style="bold red",
        )
        exit(code=1)

    # 5 - Get downloadable media links from songlist.
    rich_console.print(f"Scrapping {title} song list table.", style="green")
    start = time.time()
    media_links = test(song_table=song_table, format=options.format)
    end = time.time()
    rich_console.print(
        f"Scrapped {len(media_links)} tracks for this album in {round(number=end - start, ndigits=2)} seconds.",
        style="green",
    )

    # 6 - Create directory if not present.
    directory_name = downloader.create_directory(directory_name=title)

    if not directory_name:
        rich_console.print(
            f"Folder {title} not created, exiting the script.", style="bold red"
        )
        exit(1)

    rich_console.print(f"Folder {title} created, downloading the songs.", style="green")

    # 7 - Download songs.
    await downloader.download_files(links=media_links, path=directory_name)

    rich_console.print("Finished downloading all files.", style="bold green")


if __name__ == "__main__":
    from rich.traceback import install

    install(show_locals=True)
    asyncio.run(main=main())
