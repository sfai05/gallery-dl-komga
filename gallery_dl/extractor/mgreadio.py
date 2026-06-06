# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://mgread.io/"""

from .common import Extractor, Message
from .madara import _extract_date_near
from .. import text
import re

BASE_PATTERN = r"(?:https?://)?(?:www\.)?mgread\.io"

_CHAPTER_RE = re.compile(r"chapter-(\d+)(?:-(\d+))?/?$", re.I)
_PAGE_IMG_RE = re.compile(
    r"https?://mg\.mgread\.io/\d+/\d+/[^\s\"']+?\.(?:jpg|jpeg|png|webp)",
    re.I,
)


class MgreadioExtractor(Extractor):
    """Base class for mgread.io"""
    category = "mgreadio"
    root = "https://mgread.io"
    request_interval = (1.0, 2.0)

    def _manga_info(self, manga_url):
        page = self.request(manga_url).text
        title = text.extr(page, '<title>', '</title>').strip()
        if " [Ch." in title:
            title = title.split(" [Ch.", 1)[0].strip()
        if " – Mgread.io" in title:
            title = title.split(" – Mgread.io", 1)[0].strip()
        cover = text.extr(page, 'property="og:image" content="', '"').strip() or None
        manga_slug = manga_url.rstrip("/").rsplit("/", 1)[-1]
        return {
            "manga"    : title or manga_slug.replace("-", " ").title(),
            "manga_id" : manga_slug,
            "manga_url": manga_url,
            "author"   : None,
            "cover"    : cover,
            "lang"     : "en",
        }

    def _chapter_list(self, manga_slug):
        chapters = []
        seen = set()
        href_re = re.compile(
            r'href=["\']?(' + re.escape(self.root) +
            r'/manga/' + re.escape(manga_slug) +
            r'/chapter-[a-z0-9-]+/?)["\']?',
            re.I,
        )
        for p in range(1, 100):
            url = "{}/manga/{}/chapter/page/{}/".format(self.root, manga_slug, p)
            try:
                page = self.request(url).text
            except Exception:
                break
            page_chapters = []
            matches = list(href_re.finditer(page))
            for idx, m in enumerate(matches):
                chapter_url = m.group(1)
                if chapter_url in seen:
                    continue
                seen.add(chapter_url)
                window_start = m.end()
                window_end = matches[idx + 1].start() if idx + 1 < len(matches) else min(window_start + 600, len(page))
                chapter_date = _extract_date_near(page[window_start:window_end])
                page_chapters.append((chapter_url, "", chapter_date))
            if not page_chapters:
                break
            chapters.extend(page_chapters)
        return chapters

    def _chapter_images(self, chapter_url):
        page = self.request(chapter_url).text
        urls = []
        seen = set()
        for m in _PAGE_IMG_RE.finditer(page):
            url = m.group(0)
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
        return urls


class MgreadioChapterExtractor(MgreadioExtractor):
    """Single chapter on mgread.io"""
    subcategory = "chapter"
    directory_fmt = ("{category}", "{manga}",
                     "c{chapter:>03}{chapter_minor}")
    filename_fmt = "{manga}_c{chapter:>03}{chapter_minor}_{page:>03}.{extension}"
    archive_fmt = "{manga_id}_{chapter}_{chapter_minor}_{page}"
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/(chapter-\d+(?:-\d+)?)/?"
    example = "https://mgread.io/manga/MANGA/chapter-1/"

    def _init(self):
        self._manga_slug = self.groups[0]
        self._chapter_slug = self.groups[1]

    def items(self):
        match = _CHAPTER_RE.search(self._chapter_slug)
        if not match:
            return
        chapter = int(match.group(1))
        minor = ("." + match.group(2)) if match.group(2) else ""
        data = {
            "manga"        : self._manga_slug.replace("-", " ").title(),
            "manga_id"     : self._manga_slug,
            "manga_url"    : "{}/manga/{}/".format(self.root, self._manga_slug),
            "lang"         : "en",
            "chapter"      : chapter,
            "chapter_minor": minor,
            "chapter_id"   : self._chapter_slug,
            "chapter_url"  : self.url,
            "volume"       : 0,
            "date"         : None,
        }
        images = self._chapter_images(self.url)
        yield Message.Directory, "", data
        for i, url in enumerate(images, 1):
            image_data = text.nameext_from_url(url, {**data, "page": i})
            yield Message.Url, url, image_data


class MgreadioMangaExtractor(MgreadioExtractor):
    """Full manga (all chapters) on mgread.io"""
    subcategory = "manga"
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/?(?:[?#].*)?$"
    example = "https://mgread.io/manga/MANGA/"

    def _init(self):
        self._manga_slug = self.groups[0]

    def items(self):
        manga_url = "{}/manga/{}/".format(self.root, self._manga_slug)
        manga_info = self._manga_info(manga_url)
        chapters = self._chapter_list(self._manga_slug)

        def _sort_key(entry):
            slug = entry[0].rstrip("/").rsplit("/", 1)[-1]
            m = _CHAPTER_RE.search(slug)
            if not m:
                return (0, 0)
            return (int(m.group(1)), int(m.group(2)) if m.group(2) else 0)

        chapters_sorted = sorted(chapters, key=_sort_key)

        for chapter_url, chapter_title, chapter_date in chapters_sorted:
            slug = chapter_url.rstrip("/").rsplit("/", 1)[-1]
            match = _CHAPTER_RE.search(slug)
            chapter = int(match.group(1)) if match else 0
            minor = ("." + match.group(2)) if (match and match.group(2)) else ""
            data = {
                **manga_info,
                "chapter"      : chapter,
                "chapter_minor": minor,
                "chapter_id"   : slug,
                "chapter_title": chapter_title,
                "chapter_url"  : chapter_url,
                "volume"       : 0,
                "date"         : chapter_date,
                "_extractor"   : MgreadioChapterExtractor,
            }
            yield Message.Queue, chapter_url, data
