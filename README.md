# KH Insider Bot

## Description

The project is a simple downloader written in Python. You need to provide a link and a format when using the command and it will donwload in the current directory. If the album folder already exists it won't overwrite it and just raise an error. If the format you entered isn't available it will list to you availables format before exiting the program.

This project isn't to diminish the khinsider project, the amount of work for preserving so much soundtrack is massive. It was a simple project to understand the scraping in python. Go donate to his [website](https://downloads.khinsider.com/forums/index.php?account/upgrades).

## Roots

The first version of the project was written in NodeJS, as a side project for using the [Pupeteer](https://pptr.dev) library and the [node-downloader-helper](https://www.npmjs.com/package/node-downloader-helper) package, respectively for accessing the various link and download each files. It was very rough on the edges, that is why I have changed the language and used scraping instead of a headless chrome window.


## Dependencies

- bs4 : Used to scrape the website.
- numpy : Used to slice the format array with the most efficiency.
- tqdm : Used to generate loading bar for each download.


## Installation

```sh
poetry install
```


## Usage

For using the program you have to specify the album page link on khinsider and specify the format you want to use. This program won't convert the songs for you, you have to specify one format available for this specific album. If the format you use doesn't exist for this album the program will print to you available formats before exiting.

```sh
# To run in a poetry shell you need to install the plugin
poetry shell && python main.py -f <format> -l <link/to/the/album>

# To run without a poetry shell instance
poetry run python main.py -f <format> -l <link/to/the/album>
```

The downloaded files will be stored into a specific folder for each album.


## Issues

- A GUI could be neat, it could be a cool idea for a future update.