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


def extract_name_from_title(link):
    return link.split("MP3")[0].rstrip()


def search_for_format(songListTable):
    thArray = songListTable.find_all("th")

    formatArray = []

    for element in thArray:
        formatArray.append(element.get_text().casefold())

    # searching for the index of song name and total (use of casefold() to avoid any string problems)
    start, end = formatArray.index("song name"), formatArray.index("total:")

    # conversion with numpy just for this option
    formatArray = np.array(formatArray)

    try:
        formatArray = formatArray[start + 1 : end - 1].tolist()
        return formatArray
    except ValueError:
        print(
            colorama.Fore.RED,
            "The format table is not correct, please report the issue on Github.",
        )
        exit(1)


def scraping_links(songListTable, format):
    trackLinkArray = []
    downloadLinkArray = []

    for request in songListTable.find_all("a"):
        trackLinkArray.append("https://downloads.khinsider.com" + request.get("href"))

    trackLinkArray = list(dict.fromkeys(trackLinkArray))

    for request in trackLinkArray:
        response = httpx.get(request)
        pageSoup = BeautifulSoup(response.text, "html.parser")
        for element in pageSoup.find_all("span", class_="songDownloadLink"):
            musicLink = element.parent.get("href")
            if musicLink.split(".")[-1] == format:
                downloadLinkArray.append(musicLink)

    if len(downloadLinkArray) == 0:
        print(
            colorama.Fore.RED,
            "No downloadable requests were found. Please report an issue on the github page.",
        )
        exit(1)

    return downloadLinkArray


def access_link(format, ostLink):
    response = httpx.get(ostLink)

    soup = BeautifulSoup(response.text, "html.parser")

    title = downloader.remove_invalid_chars(extract_name_from_title(soup.title.string))

    print(colorama.Fore.GREEN + title, "was loaded", colorama.Style.RESET_ALL)

    songListTable = soup.find(id="songlist")

    if songListTable is None:
        print(
            colorama.Fore.RED, "The program cannot find a song table, invalid website."
        )
        exit(1)

    formatArray = search_for_format(songListTable)

    if format not in formatArray:
        print(
            colorama.Fore.RED,
            "Format is not available for this link. Here are the available formats:",
        )
        print(formatArray)
        exit(1)

    downloader.download_files(title, scraping_links(songListTable, format))


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
        exit(1)

    if options.format.isdigit() or options.link.isdigit():
        print(
            colorama.Fore.RED
            + "The arguments provided are not string. You need to enter valid arguments"
        )
        print(colorama.Style.RESET_ALL, parser.usage)
        exit(1)

    access_link(options.format.casefold(), options.link)


if __name__ == "__main__":
    main()
