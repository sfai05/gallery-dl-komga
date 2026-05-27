# -*- coding: utf-8 -*-

# Copyright 2016-2025 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://hentai2read.com/"""

from .common import ChapterExtractor, MangaExtractor
from .. import text, util


class Hentai2readBase():
    """Base class for hentai2read extractors"""
    category = "hentai2read"
    root = "https://hentai2read.com"

    def _extract_info(self, page):
        block = text.extr(page, 'class="list list-simple-mini">', '</ul>')

        manga_alt_raw = text.extr(block, '<li class="text-muted">', '<')
        manga_alt = []
        if manga_alt_raw:
            alt = text.unescape(manga_alt_raw.strip())
            if alt and alt != '-':
                manga_alt = [alt]

        def _field(label):
            li = text.extr(block, '<b>{}</b>'.format(label), '</li>')
            return text.remove_html(li).strip()

        def _taglist(label):
            li_block = text.extr(block, '<b>{}</b>'.format(label), '</li>')
            return [
                t.strip()
                for t in text.re(
                    r'class="tagButton"[^>]*>([^<]+)</a>'
                ).findall(li_block)
                if t.strip() and t.strip() != '-'
            ]

        status = _field('Status')
        if status == '-':
            status = ""

        year_raw = _field('Release Year')
        year = text.parse_int(year_raw) if year_raw and year_raw != '-' else None

        page_info = ' '.join(_field('Page').split())
        if page_info == '-':
            page_info = ""

        author = _field('Author')
        if author == '-':
            author = ""

        artist = _field('Artist')
        if artist == '-':
            artist = ""

        # Category (broad: Adult, Oneshot, Big Breasts, …) + Content (Ahegao, Creampie, …)
        # merged into a single tags list (Komga writes everything into <Genre>)
        tags = _taglist('Category') + _taglist('Content')

        storyline = text.extr(block, '<b>Storyline</b>', '</li>')
        description = text.unescape(text.remove_html(storyline)).strip()
        if description in ('Nothing yet!', '-', ''):
            description = ""

        if page_info:
            description = (description + "\n\n" + page_info if description else page_info)

        return {
            "manga_alt"  : manga_alt,
            "author"     : author,
            "artist"     : artist,
            "tags"       : tags,
            "description": description,
            "status"     : status,
            "year"       : year,
        }


class Hentai2readChapterExtractor(Hentai2readBase, ChapterExtractor):
    """Extractor for a single manga chapter from hentai2read.com"""
    archive_fmt = "{chapter_id}_{page}"
    pattern = r"(?:https?://)?(?:www\.)?hentai2read\.com(/[^/?#]+/([^/?#]+))"
    example = "https://hentai2read.com/TITLE/1/"

    def metadata(self, page):
        page_title, pos = text.extract(page, "<title>", "</title>")
        manga_id, pos = text.extract(page, 'data-mid="', '"', pos)
        chapter_id, pos = text.extract(page, 'data-cid="', '"', pos)
        chapter, sep, minor = self.groups[1].partition(".")

        match = text.re(
            r"Reading (.+) \(([^)]+)\) Hentai(?: by (.*))? - "
            r"([^:]+): (.+) . Page 1 ").match(page_title)
        if match:
            manga, mtype, author, _, title = match.groups()
        else:
            self.log.warning("Failed to extract 'manga', 'type', 'author', "
                             "and 'title' metadata")
            manga = mtype = author = title = ""

        try:
            manga_path = self.groups[0].rsplit("/", 1)[0]
            manga_page = self.request(self.root + manga_path + "/").text
            info = self._extract_info(manga_page)
        except Exception:
            info = {
                "manga_alt"  : [],
                "author"     : "",
                "artist"     : "",
                "tags"       : [],
                "description": "",
                "status"     : "",
                "year"       : None,
            }

        return {
            "manga"        : manga,
            "manga_id"     : text.parse_int(manga_id),
            "manga_alt"    : info["manga_alt"],
            "chapter"      : text.parse_int(chapter),
            "chapter_minor": sep + minor,
            "chapter_id"   : text.parse_int(chapter_id),
            "type"         : mtype,
            "author"       : author or info["author"],
            "artist"       : info["artist"],
            "title"        : title,
            "tags"         : info["tags"],
            "description"  : info["description"],
            "status"       : info["status"],
            "lang"         : "en",
            "language"     : "English",
        }

    def images(self, page):
        images = text.extract(page, "'images' : ", ",\n")[0]
        return [
            ("https://hentaicdn.com/hentai" + part, None)
            for part in util.json_loads(images)
        ]


class Hentai2readMangaExtractor(Hentai2readBase, MangaExtractor):
    """Extractor for hmanga from hentai2read.com"""
    chapterclass = Hentai2readChapterExtractor
    pattern = r"(?:https?://)?(?:www\.)?hentai2read\.com(/[^/?#]+)/?$"
    example = "https://hentai2read.com/TITLE/"

    def chapters(self, page):
        results = []

        pos = page.find('itemscope itemtype="http://schema.org/Book') + 1
        manga, pos = text.extract(
            page, '<span itemprop="name">', '</span>', pos)
        mtype, pos = text.extract(
            page, '<small class="text-danger">[', ']</small>', pos)
        manga_id = text.parse_int(text.extract(
            page, 'data-mid="', '"', pos)[0])

        info = self._extract_info(page)

        while True:
            chapter_id, pos = text.extract(page, ' data-cid="', '"', pos)
            if not chapter_id:
                return results
            _  , pos = text.extract(page, ' href="', '"', pos)
            url, pos = text.extract(page, ' href="', '"', pos)

            chapter, pos = text.extract(page, '>', '<', pos)
            chapter, _, title = text.unescape(chapter).strip().partition(" - ")
            chapter, sep, minor = chapter.partition(".")

            results.append((url, {
                "manga"        : manga,
                "manga_id"     : manga_id,
                "manga_alt"    : info["manga_alt"],
                "chapter"      : text.parse_int(chapter),
                "chapter_minor": sep + minor,
                "chapter_id"   : text.parse_int(chapter_id),
                "type"         : mtype,
                "author"       : info["author"],
                "artist"       : info["artist"],
                "title"        : title,
                "tags"         : info["tags"],
                "description"  : info["description"],
                "status"       : info["status"],
                "lang"         : "en",
                "language"     : "English",
            }))
