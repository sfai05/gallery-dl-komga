# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.dm5.com/ (DM5 / 动漫屋)"""

from .common import ChapterExtractor, MangaExtractor
from .. import text
import re as _re

BASE_PATTERN = r"(?:https?://)?(?:www\.)?dm5\.com"
_BASE_URL    = "https://www.dm5.com"
_HEADERS     = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW",
}


class Dm5Base():
    category = "dm5"
    root     = _BASE_URL

    def _unpack_js(self, js):
        """Decode Dean Edwards p,a,c,k,e,r packed JavaScript."""
        m = _re.search(r"\('([^']+)',(\d+),(\d+),'([^']+)'", js)
        if not m:
            return js
        p, a, c = m.group(1), int(m.group(2)), int(m.group(3))
        k = m.group(4).split("|")
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"

        def decode(n):
            s = ""
            while n > 0:
                r = n % a
                s = (chr(r + 29) if r > 35 else chars[r]) + s
                n //= a
            return s or "0"

        lookup = {decode(i): (k[i] if i < len(k) and k[i] else decode(i))
                  for i in range(c)}
        return _re.sub(r"\b\w+\b", lambda mo: lookup.get(mo.group(), mo.group()), p)

    def _chapter_images(self, chapter_url, cid, mid, dt, sign, count):
        hdrs = {**_HEADERS, "Referer": chapter_url}
        images = []
        page = 1
        while len(images) < count:
            api_url = (
                f"{chapter_url}chapterfun.ashx"
                f"?cid={cid}&page={page}&key=&language=1&gtk=6"
                f"&_cid={cid}&_mid={mid}&_dt={dt}&_sign={sign}"
            )
            js      = self.request(api_url, headers=hdrs).text
            urls    = _re.findall(r'"(https://[^"]+)"', self._unpack_js(js))
            img_hdrs = {"Referer": f"{_BASE_URL}/m{cid}/"}
            for url in urls:
                images.append((url, {"_http_headers": img_hdrs}))
                if len(images) >= count:
                    break
            page += 2
        return images


class Dm5ChapterExtractor(Dm5Base, ChapterExtractor):
    """Extractor for a single DM5 chapter"""
    directory_fmt = ("{category}", "{manga}", "{chapter_string}")
    filename_fmt  = "{page:>03}.{extension}"
    archive_fmt   = "{manga_id}_{chapter_id}_{page}"
    pattern       = BASE_PATTERN + r"/(m\d+)/?"
    example       = "https://www.dm5.com/m12345/"

    def initialize(self):
        super().initialize()
        slug          = self.groups[0]
        self.page_url = f"{_BASE_URL}/{slug}/"

    def metadata(self, page):
        def _var(name):
            m = _re.search(rf'var {name}\s*=\s*"?([^";\n]+)"?', page)
            return m.group(1).strip().strip('"') if m else ""

        self._cid   = _var("DM5_CID")
        self._mid   = _var("DM5_MID")
        self._dt    = _var("DM5_VIEWSIGN_DT")
        self._sign  = _var("DM5_VIEWSIGN")
        self._count = int(_var("DM5_IMAGE_COUNT") or "0")

        ctitle = _var("DM5_CTITLE")
        if " " in ctitle:
            manga, _, chapter_string = ctitle.partition(" ")
        else:
            manga = text.unescape(_re.sub(r"漫画$", "", _re.search(
                r"<title>([^_<]+)", page).group(1).strip()) if _re.search(
                r"<title>([^_<]+)", page) else "")
            chapter_string = ctitle

        return {
            "manga"         : manga,
            "manga_id"      : self._mid,
            "chapter_string": chapter_string,
            "chapter_id"    : self._cid,
            "lang"          : "zh",
            "language"      : "Chinese",
        }

    def images(self, page):
        return self._chapter_images(
            self.page_url, self._cid, self._mid, self._dt, self._sign, self._count,
        )


class Dm5MangaExtractor(Dm5Base, MangaExtractor):
    """Extractor for all chapters of a DM5 series"""
    chapterclass = Dm5ChapterExtractor
    pattern      = BASE_PATTERN + r"/manhua-([^/?#]+)/?"
    example      = "https://www.dm5.com/manhua-TITLE/"

    def initialize(self):
        super().initialize()
        self.page_url = f"{_BASE_URL}/manhua-{self.groups[0]}/"

    def chapters(self, page):
        # Title: strip trailing "漫画" suffix from page title
        title_m = _re.search(r"<title>([^_<]+)", page)
        manga   = _re.sub(r"漫画$", "", title_m.group(1).strip()) if title_m else ""

        manga_id_m = _re.search(r"var DM5_MID\s*=\s*(\d+)", page)
        manga_id   = manga_id_m.group(1) if manga_id_m else ""

        result = []
        for ul_m in _re.finditer(
            r'<ul[^>]+id="detail-list-select-\d+"[^>]*>(.*?)</ul>', page, _re.DOTALL
        ):
            for a_m in _re.finditer(
                r'href="(/m(\d+)/)"[^>]*>([^<]+)', ul_m.group(1)
            ):
                href, cid, title = a_m.group(1), a_m.group(2), a_m.group(3).strip()
                url = _BASE_URL + href
                result.append((url, {
                    "manga"         : manga,
                    "manga_id"      : manga_id,
                    "chapter_string": title,
                    "chapter_id"    : cid,
                    "lang"          : "zh",
                    "language"      : "Chinese",
                }))
        result.reverse()
        return result
