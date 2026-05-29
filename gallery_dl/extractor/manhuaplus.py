# -*- coding: utf-8 -*-

# Copyright 2025 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://manhuaplus.com/"""

from .madara import MadaraChapterExtractor, MadaraExtractor, MadaraMangaExtractor

BASE_PATTERN = r"(?:https?://)?(?:www\.)?manhuaplus\.com"


class ManhuaplusExtractor(MadaraExtractor):
    category = "manhuaplus"
    root = "https://manhuaplus.com"


class ManhuaplusChapterExtractor(ManhuaplusExtractor, MadaraChapterExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/([^/?#]+)"
    example = "https://manhuaplus.com/manga/MANGA/CHAPTER/"


class ManhuaplusMangaExtractor(ManhuaplusExtractor, MadaraMangaExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/?(?:[?#].*)?$"
    example = "https://manhuaplus.com/manga/MANGA/"
    chapter_extractor = ManhuaplusChapterExtractor
