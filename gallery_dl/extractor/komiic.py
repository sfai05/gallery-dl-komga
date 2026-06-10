# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://komiic.com/ (Komiic / 漫画)"""

from .common import ChapterExtractor, MangaExtractor
from .. import text

BASE_PATTERN = r"(?:https?://)?komiic\.com"
_API        = "https://komiic.com/api/query"

_GQL_COMIC = """
query comicById($comicId: ID!) {
  comicById(comicId: $comicId) {
    id title status year imageUrl
    authors   { id name }
    categories { id name }
  }
}
"""

_GQL_CHAPTERS = """
query chapterByComicId($comicId: ID!) {
  chaptersByComicId(comicId: $comicId) {
    id serial type dateUpdated size
  }
}
"""

_GQL_IMAGES = """
query imagesByChapterId($chapterId: ID!) {
  imagesByChapterId(chapterId: $chapterId) {
    id kid height width
  }
}
"""


class KomiicBase():
    category = "komiic"
    root     = "https://komiic.com"

    def _gql(self, operation, query, variables):
        data = self.request(
            _API,
            method  = "POST",
            headers = {"Content-Type": "application/json"},
            json    = {"operationName": operation,
                       "query"        : query,
                       "variables"    : variables},
        ).json()
        return data["data"]

    def _comic_info(self, comic_id):
        data  = self._gql("comicById", _GQL_COMIC, {"comicId": comic_id})
        comic = data["comicById"]
        return {
            "manga"      : comic["title"],
            "manga_id"   : comic["id"],
            "author"     : [a["name"] for a in comic.get("authors", [])],
            "tags"       : [c["name"] for c in comic.get("categories", [])],
            "status"     : comic.get("status", ""),
            "year"       : comic.get("year", ""),
            "cover"      : comic.get("imageUrl", ""),
            "lang"       : "zh",
            "language"   : "Chinese",
        }

    def _chapter_list(self, comic_id):
        data = self._gql("chapterByComicId", _GQL_CHAPTERS, {"comicId": comic_id})
        return data["chaptersByComicId"]

    def _chapter_images(self, comic_id, chapter_id):
        data   = self._gql("imagesByChapterId", _GQL_IMAGES, {"chapterId": chapter_id})
        images = data["imagesByChapterId"]
        hdrs   = {"Referer": "https://komiic.com/"}
        return [
            (f"https://komiic.com/api/image/{img['kid']}"
             f"?mangaId={comic_id}&chapterId={chapter_id}",
             {"_http_headers": hdrs})
            for img in images
        ]


class KomiicChapterExtractor(KomiicBase, ChapterExtractor):
    """Extractor for a single Komiic chapter"""
    directory_fmt = ("{category}", "{manga}", "{chapter_string}")
    filename_fmt  = "{page:>03}.{extension}"
    archive_fmt   = "{manga_id}_{chapter_id}_{page}"
    pattern       = BASE_PATTERN + r"/comic/(\d+)/chapter/(\d+)"
    example       = "https://komiic.com/comic/12345/chapter/67890/images/all"

    def metadata(self, page):
        comic_id, chapter_id = self.groups
        manga          = self._comic_info(comic_id)
        chapter_string = chapter_id
        for ch in self._chapter_list(comic_id):
            if ch["id"] == chapter_id:
                prefix         = "Vol." if ch["type"] == "book" else "Ch."
                chapter_string = f"{prefix}{ch['serial']}"
                break
        self._comic_id   = comic_id
        self._chapter_id = chapter_id
        return {**manga, "chapter_string": chapter_string,
                "chapter_id": chapter_id}

    def images(self, page):
        del page
        return self._chapter_images(self._comic_id, self._chapter_id)


class KomiicMangaExtractor(KomiicBase, MangaExtractor):
    """Extractor for all chapters of a Komiic series"""
    chapterclass = KomiicChapterExtractor
    pattern      = BASE_PATTERN + r"/comic/(\d+)(?:/[^/].*)?$"
    example      = "https://komiic.com/comic/12345"

    def chapters(self, page):
        comic_id, = self.groups
        manga  = self._comic_info(comic_id)
        result = []
        for ch in self._chapter_list(comic_id):
            prefix  = "Vol." if ch["type"] == "book" else "Ch."
            ch_str  = f"{prefix}{ch['serial']}"
            url     = f"{self.root}/comic/{comic_id}/chapter/{ch['id']}/images/all"
            result.append((url, {
                **manga,
                "chapter_string": ch_str,
                "chapter_id"    : ch["id"],
                "chapter"       : text.parse_float(ch["serial"]),
                "date"          : ch.get("dateUpdated", ""),
                "count"         : ch.get("size", 0),
            }))
        return result
