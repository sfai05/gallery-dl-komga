# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://tritinia.org/"""

from .common import Message
from .madara import MadaraChapterExtractor, MadaraExtractor, MadaraMangaExtractor, _img_url
from .. import text
import re

BASE_PATTERN = r"(?:https?://)?(?:www\.)?tritinia\.org"

_TRITINIA_CHAPTER_RE = re.compile(r"ch-(\d+)(?:-(\d+))?", re.I)


def _parse_chapter_slug(slug):
    m = _TRITINIA_CHAPTER_RE.search(slug)
    if not m:
        return 0, ""
    major = int(m.group(1))
    minor = ("." + m.group(2)) if m.group(2) else ""
    return major, minor


class TritiniaExtractor(MadaraExtractor):
    category = "tritinia"
    root = "https://tritinia.org"
    use_new_chapter_endpoint = True

    def _chapter_images(self, chapter_url):
        page = self.request(chapter_url + "?style=list").text
        urls = []
        for block in re.finditer(
            r'<div[^>]*class="[^"]*page-break[^"]*"[^>]*>(.*?)</div>',
            page,
            re.DOTALL,
        ):
            img_match = re.search(r'<img[^>]+>', block.group(1))
            if not img_match:
                continue
            url = _img_url(img_match.group(0))
            if url:
                urls.append(url.strip())
        return urls


class TritiniaChapterExtractor(TritiniaExtractor, MadaraChapterExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/(ch-[^/?#]+)"
    example = "https://tritinia.org/manga/MANGA/ch-1-welcome-to-the-dungeon/"

    def items(self):
        manga_url = "{}/manga/{}/".format(self.root, self._manga_slug)
        manga_info = self._manga_info(manga_url)
        chapter, minor = _parse_chapter_slug(self._chapter_slug)
        chapter_url, date = self._chapter_info(manga_url, self._chapter_slug)

        data = {
            **manga_info,
            "chapter": chapter,
            "chapter_minor": minor,
            "chapter_id": self._chapter_slug,
            "chapter_url": chapter_url or self.url,
            "date": date,
            "volume": 0,
        }

        images = self._chapter_images(self.url)
        yield Message.Directory, "", data
        for i, url in enumerate(images, 1):
            image_data = text.nameext_from_url(url, {**data, "page": i})
            yield Message.Url, url, image_data


class TritiniaMangaExtractor(TritiniaExtractor, MadaraMangaExtractor):
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/?(?:[?#].*)?$"
    example = "https://tritinia.org/manga/MANGA/"
    chapter_extractor = TritiniaChapterExtractor

    def items(self):
        manga_url = "{}/manga/{}/".format(self.root, self._manga_slug)
        manga_info = self._manga_info(manga_url)
        chapters = self._chapter_list(manga_url)

        for chapter_url, chapter_title, date in reversed(chapters):
            slug = chapter_url.rstrip("/").rsplit("/", 1)[-1]
            chapter, minor = _parse_chapter_slug(slug)
            data = {
                **manga_info,
                "chapter": chapter,
                "chapter_minor": minor,
                "chapter_id": slug,
                "chapter_title": chapter_title,
                "chapter_url": chapter_url,
                "date": date,
                "volume": 0,
                "_extractor": self.chapter_extractor,
            }
            yield Message.Queue, chapter_url, data
