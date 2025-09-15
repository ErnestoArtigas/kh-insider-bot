"""
Code written by Ernesto Artigas.
Licence GNU General Public Licence v3.0.
"""

from optparse import OptionParser

import colorama
import numpy as np
import requests
from bs4 import BeautifulSoup

import src.downloader as downloader


def extractNameFromTitle(link):
    return link.split("MP3")[0].rstrip()


def searchForFormat(songListTable):
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
            colorama.Fore.RED
            + "The format table is not correct, please report the issue on Github."
        )
        exit(1)


def scrapingLinks(songListTable, format):
    trackLinkArray = []
    downloadLinkArray = []

    for request in songListTable.find_all("a"):
        trackLinkArray.append("https://downloads.khinsider.com" + request.get("href"))

    trackLinkArray = list(dict.fromkeys(trackLinkArray))

    for request in trackLinkArray:
        requestRequest = requests.get(request)
        pageSoup = BeautifulSoup(requestRequest.text, "html.parser")
        for element in pageSoup.find_all("span", class_="songDownloadLink"):
            musicLink = element.parent.get("href")
            if musicLink.split(".")[-1] == format:
                downloadLinkArray.append(musicLink)

    if len(downloadLinkArray) == 0:
        print(
            colorama.Fore.RED
            + "No downloadable requests were found. Please report an issue on the github page."
        )
        exit(1)

    return downloadLinkArray


def accessLink(format, ostLink):
    request = downloader.getRequestFromLink(ostLink)

    soup = BeautifulSoup(request.text, "html.parser")

    title = downloader.removeInvalidChars(extractNameFromTitle(soup.title.string))

    print(colorama.Fore.GREEN + title, "was loaded" + colorama.Style.RESET_ALL)

    songListTable = soup.find(id="songlist")

    if songListTable == None:
        print(
            colorama.Fore.RED + "The program cannot find a song table, invalid website."
        )
        exit(1)

    formatArray = searchForFormat(songListTable)

    if not format in formatArray:
        print(
            colorama.Fore.RED
            + "Format is not available for this link. Here are the available formats:"
        )
        print(formatArray)
        exit(1)

    downloader.downloadFiles(title, scrapingLinks(songListTable, format))


def main():
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

    if options.format == None or options.link == None:
        print(
            colorama.Fore.RED
            + "Missing arguments, you need to provide the format and the link in the command."
        )
        print(colorama.Style.RESET_ALL + parser.usage)
        exit(1)

    if options.format.isdigit() or options.link.isdigit():
        print(
            colorama.Fore.RED
            + "The arguments provided are not string. You need to enter valid arguments"
        )
        print(colorama.Style.RESET_ALL + parser.usage)
        exit(1)

    accessLink(options.format.casefold(), options.link)


if __name__ == "__main__":
    main()
