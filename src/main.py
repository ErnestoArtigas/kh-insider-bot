"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

from optparse import OptionParser, Values
from typing import cast

import colorama
import httpx
from bs4 import BeautifulSoup, Tag

import downloader


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


def scrap_links_from_table(song_list_table: Tag, format: str, title: str) -> list[str]:
    song_page_link = []
    song_direct_link = []

    for link in song_list_table.find_all("a"):
        song_page_link.append(f"https://downloads.khinsider.com{link.get('href')}")

    song_page_link = list(dict.fromkeys(song_page_link))

    for link in song_page_link:
        response = httpx.get(url=link)
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


def main() -> None:
    parser, options = create_parser()

    if options.format is None or options.link is None:
        print(
            colorama.Fore.RED
            + "Missing arguments, you need to provide the format and the link in the command."
        )
        print(colorama.Style.RESET_ALL, parser.usage)
        exit(code=1)

    if options.format.isdigit() or options.link.isdigit():
        print(
            colorama.Fore.RED,
            "The arguments provided are not string. You need to enter valid arguments",
        )
        print(colorama.Style.RESET_ALL, parser.usage)
        exit(code=1)

    response = httpx.get(url=options.link)

    soup = BeautifulSoup(markup=response.text, features="html.parser")

    if soup.title is None:
        print(colorama.Fore.RED, "The program couldn't process the page.")
        exit(code=1)

    title = downloader.remove_invalid_chars(
        string=extract_name_from_title(link=soup.title.string)
    )

    print(colorama.Fore.GREEN, title, "was loaded", colorama.Style.RESET_ALL)

    song_list_table = soup.find(id="songlist")

    if song_list_table is None or type(song_list_table) is not Tag:
        print(
            colorama.Fore.RED, "The program cannot find a song table, invalid website."
        )
        exit(code=1)

    if not is_format_available(song_list_table=song_list_table, format=options.format):
        print(
            colorama.Fore.RED,
            f"The format {options.format} is not available for {title}.",
        )
        exit(code=1)

    try:
        # Convert it to parallelism
        links = scrap_links_from_table(
            song_list_table=song_list_table, format=options.format, title=title
        )
        downloader.create_directory(directory_name=title)
        # Write functions to use download_file with parallelism
        print(colorama.Fore.GREEN, "Finished downloading all files.")
    except Exception as error:
        print(colorama.Fore.RED, error)


if __name__ == "__main__":
    main()
