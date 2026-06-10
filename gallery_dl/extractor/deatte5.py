# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.deatte5.com/"""

from .common import Message
from .mangaclash import MangaclashExtractor
from .madara import MadaraChapterExtractor, _parse_chapter_slug, _img_url
from .. import text
import re

BASE_PATTERN = r"(?:https?://)?(?:www\.)?deatte5\.com"


class Deatte5Extractor(MangaclashExtractor):
    category = "deatte5"
    root = "https://www.deatte5.com"
    use_new_chapter_endpoint = True

    def _chapter_images(self, chapter_url):
        page = self.request(chapter_url + "?style=list").text
        urls = []
        for tag in re.finditer(
            r'<img[^>]+class="[^"]*wp-manga-chapter-img[^"]*"[^>]*>',
            page,
        ):
            url = _img_url(tag.group(0))
            if url:
                urls.append(url.strip())
        return urls


class Deatte5ChapterExtractor(Deatte5Extractor, MadaraChapterExtractor):
    pattern = BASE_PATTERN + r"/manga/([a-z0-9-]+?)-(chapter-\d+(?:-\d+)?)/?"
    example = "https://www.deatte5.com/manga/manga-chapter-1/"

    def items(self):
        manga_slug = self._manga_slug
        chapter, minor = _parse_chapter_slug(self._chapter_slug)
        data = {
            "manga"        : manga_slug.replace("-", " ").title(),
            "manga_id"     : manga_slug,
            "manga_url"    : "{}/manga/{}/".format(self.root, manga_slug),
            "lang"         : "en",
            "chapter"      : chapter,
            "chapter_minor": minor,
            "chapter_id"   : self._chapter_slug,
            "chapter_url"  : self.url,
            "volume"       : 0,
        }
        images = self._chapter_images(self.url)
        yield Message.Directory, "", data
        for i, url in enumerate(images, 1):
            image_data = text.nameext_from_url(url, {**data, "page": i})
            yield Message.Url, url, image_data
