# -*- coding: utf-8 -*-

# Copyright 2025 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Base extractor classes for sites using the Madara WordPress manga theme"""

from .common import Extractor, Message
from .. import text
import re

# Chapter number from URL slug, e.g. "chapter-12", "chapter-12-5"
_CHAPTER_RE = re.compile(r"chapter-(\d+)(?:-(\d+))?", re.I)
# Lazy-loaded image attributes in priority order
_IMG_ATTRS = ("data-src", "data-lazy-src", "data-cfsrc", "src")


def _img_url(tag):
    """Return the best image URL from an <img> tag string."""
    for attr in _IMG_ATTRS:
        url = text.extr(tag, attr + '="', '"').strip()
        if url and not url.startswith("data:"):
            return url
    srcset = text.extr(tag, 'srcset="', '"')
    if srcset:
        return srcset.strip().rsplit(",", 1)[-1].split()[0]
    return None


def _parse_chapter_slug(slug):
    """Return (chapter_int, chapter_minor_str) from a chapter URL slug."""
    m = _CHAPTER_RE.search(slug)
    if not m:
        return 0, ""
    major = int(m.group(1))
    minor = ("." + m.group(2)) if m.group(2) else ""
    return major, minor


class MadaraExtractor(Extractor):
    """Base extractor for Madara WordPress manga sites"""
    basecategory = "madara"
    request_interval = (1.0, 2.0)

    # Override in subclasses
    # CSS-like description of where page images are found
    page_img_container = "reading-content"
    # Whether to always use the new /ajax/chapters/ endpoint
    use_new_chapter_endpoint = False

    def _manga_info(self, manga_url):
        page = self.request(manga_url).text

        title = text.remove_html(
            text.extr(page, 'class="post-title">', "</div>") or
            text.extr(page, 'id="manga-title">', "</h1>")
        ).strip()

        author = text.remove_html(
            text.extr(page, 'class="author-content">', "</div>")
        ).strip()

        artist = text.remove_html(
            text.extr(page, 'class="artist-content">', "</div>")
        ).strip()

        description = text.remove_html(
            text.extr(page, 'class="summary__content', "</div>") or
            text.extr(page, 'class="post-content_item">', "</div>")
        ).strip()

        status = text.remove_html(
            text.extr(page, 'class="summary-content">', "</div>")
        ).strip()

        cover_block = text.extr(page, 'class="summary_image"', "</div>")
        cover = None
        for attr in _IMG_ATTRS:
            cover = text.extr(cover_block, attr + '="', '"').strip()
            if cover and not cover.startswith("data:"):
                break

        genres = re.findall(
            r'<a[^>]+>([^<]+)</a>',
            text.extr(page, 'class="genres-content">', "</div>"),
        )
        tags = re.findall(
            r'<a[^>]+>([^<]+)</a>',
            text.extr(page, 'class="tags-content">', "</div>"),
        )

        manga_slug = manga_url.rstrip("/").rsplit("/", 1)[-1]

        return {
            "manga"      : title,
            "manga_id"   : manga_slug,
            "manga_url"  : manga_url,
            "author"     : author or None,
            "artist"     : artist or None,
            "description": description or None,
            "status"     : status or None,
            "cover"      : cover or None,
            "genres"     : genres,
            "tags"       : tags,
            "lang"       : "en",
        }

    def _chapter_list(self, manga_url):
        """Return list of (chapter_url, chapter_title) newest-first."""
        manga_url_clean = manga_url.rstrip("/") + "/"

        if not self.use_new_chapter_endpoint:
            page = self.request(manga_url_clean).text
            chapters_html = text.extr(page, 'class="main version-chap', "</ul>")
            if chapters_html:
                return self._parse_chapter_list(chapters_html)

        # POST to /ajax/chapters/ (new endpoint)
        try:
            response = self.request(
                manga_url_clean + "ajax/chapters/",
                method="POST",
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            return self._parse_chapter_list(response.text)
        except Exception:
            return []

    def _parse_chapter_list(self, html):
        chapters = []
        for li in text.extract_iter(html, '<li class="wp-manga-chapter', "</li>"):
            url = text.extr(li, 'href="', '"')
            title = text.remove_html(text.extr(li, ">", "</a>")).strip()
            if url:
                chapters.append((url, title))
        return chapters

    def _chapter_images(self, chapter_url):
        """Return ordered list of image URLs for a chapter page."""
        page = self.request(chapter_url + "?style=list").text
        container = text.extr(page, 'class="' + self.page_img_container, "</div>")
        urls = []
        for tag in re.finditer(r"<img[^>]+>", container):
            url = _img_url(tag.group(0))
            if url:
                urls.append(url)
        return urls


class MadaraChapterExtractor(MadaraExtractor):
    """Generic chapter extractor for Madara sites"""
    subcategory = "chapter"
    directory_fmt = ("{category}", "{manga}",
                     "{volume:?v/ />02}c{chapter:>03}{chapter_minor}")
    filename_fmt = "{manga}_c{chapter:>03}{chapter_minor}_{page:>03}.{extension}"
    archive_fmt = "{manga_id}_{chapter}_{chapter_minor}_{page}"

    def _init(self):
        self._manga_slug = self.groups[0]
        self._chapter_slug = self.groups[1]

    def items(self):
        manga_url = "{}/manga/{}/".format(self.root, self._manga_slug)
        manga_info = self._manga_info(manga_url)
        chapter, minor = _parse_chapter_slug(self._chapter_slug)

        data = {
            **manga_info,
            "chapter"      : chapter,
            "chapter_minor": minor,
            "chapter_id"   : self._chapter_slug,
            "volume"       : 0,
        }

        images = self._chapter_images(self.url)
        yield Message.Directory, data
        for i, url in enumerate(images, 1):
            image_data = text.nameext_from_url(url, {**data, "page": i})
            yield Message.Url, url, image_data


class MadaraMangaExtractor(MadaraExtractor):
    """Generic manga extractor for Madara sites"""
    subcategory = "manga"

    def _init(self):
        self._manga_slug = self.groups[0]

    def items(self):
        manga_url = "{}/manga/{}/".format(self.root, self._manga_slug)
        manga_info = self._manga_info(manga_url)
        chapters = self._chapter_list(manga_url)

        for chapter_url, chapter_title in reversed(chapters):
            slug = chapter_url.rstrip("/").rsplit("/", 1)[-1]
            chapter, minor = _parse_chapter_slug(slug)
            data = {
                **manga_info,
                "chapter"      : chapter,
                "chapter_minor": minor,
                "chapter_id"   : slug,
                "chapter_title": chapter_title,
                "volume"       : 0,
                "_extractor"   : self.chapter_extractor,
            }
            yield Message.Queue, chapter_url, data
