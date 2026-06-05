# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://manhwatop.com/"""

from .mangaclash import MangaclashExtractor
from .madara import MadaraChapterExtractor, MadaraMangaExtractor

BASE_PATTERN = r"(?:https?://)?(?:www\.)?manhwatop\.com"


class ManhwatopExtractor(MangaclashExtractor):
    category = "manhwatop"
    root = "https://manhwatop.com"
    use_new_chapter_endpoint = True


class ManhwatopChapterExtractor(ManhwatopExtractor, MadaraChapterExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/(chapter-[^/?#]+)"
    example = "https://manhwatop.com/manga/MANGA/chapter-1/"


class ManhwatopMangaExtractor(ManhwatopExtractor, MadaraMangaExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/?(?:[?#].*)?$"
    example = "https://manhwatop.com/manga/MANGA/"
    chapter_extractor = ManhwatopChapterExtractor
