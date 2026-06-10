# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.mangacopy.com/ (CopyManga / 拷貝漫畫)"""

from .common import ChapterExtractor, MangaExtractor
from .. import exception

# CopyManga operates across several front-end domains; the back-end API
# lives at api.mangacopy.com.  Older copymanga.* domains have been largely
# taken over by ad networks — do NOT derive the API root from the input URL.
_DOMAIN_PAT = (
    r"(?:www\.)?"
    r"(?:copymanga\.(?:site|tv|com|org|info|net)"
    r"|mangacopy\.com"
    r"|copy20\.com"
    r"|2026copy\.com)"
)
BASE_PATTERN = r"(?:https?://)?" + _DOMAIN_PAT

_API_ROOT = "https://api.mangacopy.com/api/v3"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "use_oversea_cdn": "1",
    "use_webp"       : "1",
    "platform"       : "3",
}


class CopyMangaBase():
    """Base class for CopyManga extractors.

    Requires a registered CopyManga account.  Provide credentials via
    gallery-dl config::

        {"extractor": {"copymanga": {"username": "you@email.com",
                                     "password": "yourpassword"}}}

    Or supply a pre-obtained bearer token::

        {"extractor": {"copymanga": {"token": "your-token-here"}}}
    """

    category = "copymanga"
    root     = "https://www.mangacopy.com"

    def initialize(self):
        super().initialize()
        token    = self.config("token")
        username = self.config("username")
        password = self.config("password")
        if token:
            _HEADERS["authorization"] = f"Bearer {token}"
        elif username and password:
            tok = self._login(username, password)
            if tok:
                _HEADERS["authorization"] = f"Bearer {tok}"
            else:
                raise exception.AuthenticationError(
                    "CopyManga login failed — check credentials or wait for IP block to lift."
                )
        else:
            raise exception.AuthenticationError(
                "No CopyManga credentials configured. "
                "Set extractor.copymanga.username/password or .token."
            )

    def _login(self, username, password):
        import base64, random
        salt       = random.randint(100000, 999999)
        encoded_pw = base64.b64encode(f"{password}-{salt}".encode()).decode()
        url        = "https://api.mangacopy.com/api/kb/web/login"
        login_hdrs = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            ),
        }
        data = self.request(
            url, method="POST", headers=login_hdrs,
            data={"username": username, "password": encoded_pw, "salt": salt},
        ).json()
        if data.get("code") == 200:
            self.log.debug("CopyManga login successful")
            return data.get("results", {}).get("token")
        self.log.warning("CopyManga login failed: %s", data.get("message", ""))
        return None

    def _api(self, url):
        data = self.request(url, headers=_HEADERS).json()
        code = data.get("code")
        if code == 210:
            raise exception.AuthenticationError(
                f"CopyManga blocked (code 210): {data.get('message', 'IP block or upgrade required')}"
            )
        if data.get("results") is None:
            raise exception.AuthenticationError(
                f"CopyManga returned null results (partial IP block): "
                f"code={code} message={data.get('message', '')}"
            )
        return data

    def _manga_info(self, path_word):
        data  = self._api(f"{_API_ROOT}/comic2/{path_word}?in_mainland=false")
        comic = data["results"]["comic"]
        return {
            "manga"      : comic.get("name", path_word),
            "manga_id"   : path_word,
            "author"     : [a["name"] for a in comic.get("author", [])],
            "tags"       : [t["name"] for t in comic.get("theme", [])],
            "description": comic.get("brief", ""),
            "status"     : comic.get("status", {}).get("display", ""),
            "cover"      : comic.get("cover", ""),
            "lang"       : "zh",
            "language"   : "Chinese",
        }

    def _chapter_list(self, path_word, group="default"):
        chapters = []
        offset   = 0
        limit    = 500
        while True:
            url    = (f"{_API_ROOT}/comic/{path_word}"
                      f"/group/{group}/chapters"
                      f"?limit={limit}&offset={offset}&platform=3&in_mainland=false")
            data   = self._api(url)
            result = data["results"]
            chapters.extend(result["list"])
            if offset + limit >= result["total"]:
                break
            offset += limit
        return chapters

    def _chapter_images(self, path_word, chapter_uuid):
        data = self._api(
            f"{_API_ROOT}/comic/{path_word}/chapter2/{chapter_uuid}?in_mainland=false"
        )
        return [item["url"] for item in data["results"]["chapter"]["contents"]]


class CopyMangaChapterExtractor(CopyMangaBase, ChapterExtractor):
    """Extractor for a single CopyManga chapter"""
    directory_fmt = ("{category}", "{manga}", "{chapter_string}")
    filename_fmt  = "{page:>03}.{extension}"
    archive_fmt   = "{manga_id}_{chapter_id}_{page}"
    pattern       = BASE_PATTERN + r"/comic/([\w-]+)/chapter/([\w-]+)"
    example       = "https://www.mangacopy.com/comic/MANGA/chapter/UUID"

    def metadata(self, page):
        path_word, chapter_uuid = self.groups
        manga          = self._manga_info(path_word)
        group          = self.config("group") or "default"
        chapter_string = chapter_uuid
        for ch in self._chapter_list(path_word, group):
            if ch["uuid"] == chapter_uuid:
                chapter_string = ch["name"]
                break
        self._path_word    = path_word
        self._chapter_uuid = chapter_uuid
        return {**manga, "chapter_string": chapter_string,
                "chapter_id": chapter_uuid}

    def images(self, page):
        del page
        return [(url, None)
                for url in self._chapter_images(self._path_word, self._chapter_uuid)]


class CopyMangaMangaExtractor(CopyMangaBase, MangaExtractor):
    """Extractor for all chapters of a CopyManga series"""
    chapterclass = CopyMangaChapterExtractor
    pattern      = BASE_PATTERN + r"/comic/([\w-]+)/?(?:[?#].*)?$"
    example      = "https://www.mangacopy.com/comic/MANGA"

    def chapters(self, page):
        path_word, = self.groups
        manga  = self._manga_info(path_word)
        group  = self.config("group") or "default"
        result = []
        for ch in self._chapter_list(path_word, group):
            url = f"{self.root}/comic/{path_word}/chapter/{ch['uuid']}"
            result.append((url, {
                **manga,
                "chapter_string": ch["name"],
                "chapter_id"    : ch["uuid"],
            }))
        return result
