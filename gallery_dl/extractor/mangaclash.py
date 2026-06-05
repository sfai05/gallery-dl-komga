# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://mangaclash.com/"""

from .madara import MadaraChapterExtractor, MadaraExtractor, MadaraMangaExtractor, _img_url
from .. import text
import re

BASE_PATTERN = r"(?:https?://)?(?:www\.)?mangaclash\.com"


class MangaclashExtractor(MadaraExtractor):
    category = "mangaclash"
    root = "https://mangaclash.com"
    use_new_chapter_endpoint = True

    def _chapter_images(self, chapter_url):
        # MangaClash has a `reading-content-wrap` wrapper div that would be
        # matched as a prefix by the default Madara container selector and
        # truncate too early. Match the actual class with closing quote, then
        # pull every `<img class="wp-manga-chapter-img...">` from it.
        page = self.request(chapter_url + "?style=list").text
        container = text.extr(page, 'class="reading-content"', "</div></div>")
        urls = []
        for tag in re.finditer(
            r'<img[^>]+class="[^"]*wp-manga-chapter-img[^"]*"[^>]*>',
            container,
        ):
            url = _img_url(tag.group(0))
            if url:
                urls.append(url.strip())
        return urls


class MangaclashChapterExtractor(MangaclashExtractor, MadaraChapterExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/(chapter-[^/?#]+)"
    example = "https://mangaclash.com/manga/MANGA/chapter-1/"


class MangaclashMangaExtractor(MangaclashExtractor, MadaraMangaExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/?(?:[?#].*)?$"
    example = "https://mangaclash.com/manga/MANGA/"
    chapter_extractor = MangaclashChapterExtractor
