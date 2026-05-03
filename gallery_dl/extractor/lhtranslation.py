# -*- coding: utf-8 -*-

# Copyright 2025 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://lhtranslation.net/"""

from .madara import MadaraChapterExtractor, MadaraExtractor, MadaraMangaExtractor

BASE_PATTERN = r"(?:https?://)?(?:www\.)?lhtranslation\.net"


class LhtranslationExtractor(MadaraExtractor):
    category = "lhtranslation"
    root = "https://lhtranslation.net"
    use_new_chapter_endpoint = True


class LhtranslationChapterExtractor(LhtranslationExtractor, MadaraChapterExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/([^/?#]+)"
    example = "https://lhtranslation.net/manga/MANGA/CHAPTER/"


class LhtranslationMangaExtractor(LhtranslationExtractor, MadaraMangaExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/?(?:[?#].*)?$"
    example = "https://lhtranslation.net/manga/MANGA/"
    chapter_extractor = LhtranslationChapterExtractor
