# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.mgeko.cc/"""

from .common import Extractor, Message
from .madara import _extract_date_near
from .. import text
import re

BASE_PATTERN = r"(?:https?://)?(?:www\.)?mgeko\.cc"

_CHAPTER_RE = re.compile(r"-chapter-(\d+)(?:-(\d+))?-eng-li", re.I)


class MgekoExtractor(Extractor):
    """Base class for mgeko.cc"""
    category = "mgeko"
    root = "https://www.mgeko.cc"
    request_interval = (1.0, 2.0)

    def _manga_info(self, manga_url):
        page = self.request(manga_url).text
        title = text.remove_html(
            text.extr(page, '<h1', "</h1>").split(">", 1)[-1]
        ).strip()
        author = text.remove_html(
            text.extr(page, 'Author</span>', "</div>")
        ).strip() or None
        cover = text.extr(page, 'class="novel-cover"', ">").rsplit('src="', 1)
        cover = cover[-1].split('"', 1)[0] if len(cover) > 1 else None
        manga_slug = manga_url.rstrip("/").rsplit("/", 1)[-1]
        return {
            "manga"    : title or manga_slug.replace("-", " ").title(),
            "manga_id" : manga_slug,
            "manga_url": manga_url,
            "author"   : author,
            "cover"    : cover,
            "lang"     : "en",
        }

    def _chapter_list(self, manga_slug):
        url = "{}/manga/{}/all-chapters/".format(self.root, manga_slug)
        try:
            page = self.request(url).text
        except Exception:
            page = self.request(
                "{}/manga/{}/".format(self.root, manga_slug)
            ).text
        chapters = []
        seen = set()
        href_re = re.compile(
            r'href="((?:https?://[^"]+)?/reader/en/[^"]+-chapter-[^"]+-eng-li/?)"'
        )
        matches = list(href_re.finditer(page))
        for idx, m in enumerate(matches):
            chapter_url = m.group(1)
            if chapter_url.startswith("/"):
                chapter_url = self.root + chapter_url
            if chapter_url in seen:
                continue
            seen.add(chapter_url)
            window_start = m.end()
            window_end = matches[idx + 1].start() if idx + 1 < len(matches) else min(window_start + 600, len(page))
            chapter_date = _extract_date_near(page[window_start:window_end])
            chapters.append((chapter_url, "", chapter_date))
        return chapters

    PAGE_IMG_RE = re.compile(
        r"^https?://[^\s\"']+/cdn_mangaraw/[^\s\"']*/chapter-[^/]+/[^/\s\"']+\.(?:jpg|jpeg|png|webp)$",
        re.I,
    )

    def _chapter_images(self, chapter_url):
        page = self.request(chapter_url).text
        urls = []
        for tag in re.finditer(r"<img[^>]+>", page):
            tag_str = tag.group(0)
            for attr in ("data-src", "data-lazy-src", "src"):
                url = text.extr(tag_str, attr + '="', '"').strip()
                if not url or url.startswith("data:"):
                    continue
                if self.PAGE_IMG_RE.match(url):
                    urls.append(url)
                break
        return urls


class MgekoChapterExtractor(MgekoExtractor):
    """Single chapter on mgeko.cc"""
    subcategory = "chapter"
    directory_fmt = ("{category}", "{manga}",
                     "c{chapter:>03}{chapter_minor}")
    filename_fmt = "{manga}_c{chapter:>03}{chapter_minor}_{page:>03}.{extension}"
    archive_fmt = "{manga_id}_{chapter}_{chapter_minor}_{page}"
    pattern = BASE_PATTERN + r"/reader/en/([^/?#]+-chapter-\d+(?:-\d+)?-eng-li)"
    example = "https://www.mgeko.cc/reader/en/MANGA-chapter-1-eng-li/"

    def _init(self):
        self._chapter_slug = self.groups[0]

    def items(self):
        match = _CHAPTER_RE.search(self._chapter_slug)
        if not match:
            return
        chapter = int(match.group(1))
        minor = ("." + match.group(2)) if match.group(2) else ""
        manga_slug = self._chapter_slug[:match.start()]
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
            "date"         : None,
        }
        images = self._chapter_images(self.url)
        yield Message.Directory, "", data
        for i, url in enumerate(images, 1):
            image_data = text.nameext_from_url(url, {**data, "page": i})
            yield Message.Url, url, image_data


class MgekoMangaExtractor(MgekoExtractor):
    """Full manga (all chapters) on mgeko.cc"""
    subcategory = "manga"
    pattern = BASE_PATTERN + r"/manga/([^/?#]+)/?(?:[?#].*)?$"
    example = "https://www.mgeko.cc/manga/MANGA/"

    def _init(self):
        self._manga_slug = self.groups[0]

    def items(self):
        manga_url = "{}/manga/{}/".format(self.root, self._manga_slug)
        manga_info = self._manga_info(manga_url)
        chapters = self._chapter_list(self._manga_slug)

        for chapter_url, chapter_title, chapter_date in reversed(chapters):
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
                "_extractor"   : MgekoChapterExtractor,
            }
            yield Message.Queue, chapter_url, data
