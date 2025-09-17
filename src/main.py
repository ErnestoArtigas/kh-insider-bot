"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

from optparse import OptionParser, Values

import colorama
import httpx
import numpy as np
from bs4 import BeautifulSoup

import downloader


def extract_name_from_title(link) -> str:
    return link.split("MP3")[0].rstrip()


def search_for_format(song_list_table):
    th_array = song_list_table.find_all("th")

    format_array = []

    for element in th_array:
        format_array.append(element.get_text().casefold())

    # searching for the index of song name and total (use of casefold() to avoid any string problems)
    start, end = format_array.index("song name"), format_array.index("total:")

    # conversion with numpy just for this option
    format_array = np.array(format_array)

    try:
        format_array = format_array[start + 1 : end - 1].tolist()
        return format_array
    except ValueError:
        print(
            colorama.Fore.RED,
            "The format table is not correct, please report the issue on Github.",
        )
        exit(1)


def scraping_links(song_list_table, format) -> list[str]:
    track_link_array = []
    download_link_array = []

    for request in song_list_table.find_all("a"):
        track_link_array.append("https://downloads.khinsider.com" + request.get("href"))

    track_link_array = list(dict.fromkeys(track_link_array))

    for request in track_link_array:
        response = httpx.get(url=request)
        page_soup = BeautifulSoup(markup=response.text, features="html.parser")
        for element in page_soup.find_all(name="span", class_="songDownloadLink"):
            music_link = element.parent.get(key="href")
            if music_link.split(".")[-1] == format:
                download_link_array.append(music_link)

    if len(download_link_array) == 0:
        print(
            colorama.Fore.RED,
            "No downloadable requests were found. Please report an issue on the github page.",
        )
        exit(code=1)

    return download_link_array


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
            colorama.Fore.RED
            + "The arguments provided are not string. You need to enter valid arguments"
        )
        print(colorama.Style.RESET_ALL, parser.usage)
        exit(code=1)

    response = httpx.get(url=options.link)

    soup = BeautifulSoup(markup=response.text, features="html.parser")

    title = downloader.remove_invalid_chars(
        string=extract_name_from_title(link=soup.title.string)
    )

    print(colorama.Fore.GREEN + title, "was loaded", colorama.Style.RESET_ALL)

    song_list_table = soup.find(id="songlist")

    if song_list_table is None:
        print(
            colorama.Fore.RED, "The program cannot find a song table, invalid website."
        )
        exit(code=1)

    format_array = search_for_format(song_list_table=song_list_table)

    if options.format not in format_array:
        print(
            colorama.Fore.RED,
            "Format is not available for this link. Here are the available formats:",
        )
        print(format_array)
        exit(code=1)

    downloader.download_files(
        directory_name=title,
        link_array=scraping_links(
            song_list_table=song_list_table, format=options.format
        ),
    )


if __name__ == "__main__":
    main()
