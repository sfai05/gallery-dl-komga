# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://tonarinoyj.jp/ (Tonari no Young Jump)"""

from .common import ChapterExtractor, MangaExtractor
import json
import html as _html
import re as _re

BASE_PATTERN = r"(?:https?://)?tonarinoyj\.jp"
_API_CHAPTERS = "https://tonarinoyj.jp/api/viewer/pagination_readable_products"


class TonariyyjBase():
    category = "tonarinoyj"
    root     = "https://tonarinoyj.jp"

    def _parse_episode_json(self, page):
        m = _re.search(
            r"""id=['"]episode-json['"][^>]+data-value=['"]([^'"]+)['"]""",
            page,
        ) or _re.search(
            r"""data-value=['"]([^'"]+)['"][^>]+id=['"]episode-json['"]""",
            page,
        )
        if not m:
            raise Exception("episode-json not found in page")
        return json.loads(_html.unescape(m.group(1)))

    def _episode_images(self, page_structure):
        # TODO: choJuGiga=="baku" means 4×4 block-transposition scrambling.
        # Currently downloads raw scrambled images tagged with #scramble fragment.
        # Unscrambling requires a postprocessor or image-transform step — revisit later.
        is_scrambled = page_structure.get("choJuGiga") == "baku"
        result = []
        for p in page_structure.get("pages", []):
            if p.get("type") == "main" and p.get("src"):
                url = p["src"]
                if is_scrambled:
                    url += "#scramble"
                result.append((url, {
                    "width"      : p.get("width"),
                    "height"     : p.get("height"),
                    "_scrambled" : is_scrambled,
                }))
        return result

    def _fetch_all_episodes(self, aggregate_id):
        episodes = []
        for ep_type in ("episode", "volume"):
            offset = 0
            while True:
                params = {
                    "type"         : ep_type,
                    "aggregate_id" : aggregate_id,
                    "sort_order"   : "asc",
                    "offset"       : offset,
                }
                batch = self.request(
                    _API_CHAPTERS,
                    params  = params,
                    headers = {"Referer": self.root + "/"},
                ).json()
                if not batch:
                    break
                episodes.extend(batch)
                offset += len(batch)
        return episodes


class TonariyyjChapterExtractor(TonariyyjBase, ChapterExtractor):
    """Extractor for a single Tonari no Young Jump episode"""
    directory_fmt = ("{category}", "{manga}", "{chapter_string}")
    filename_fmt  = "{page:>03}.{extension}"
    archive_fmt   = "{manga_id}_{chapter_id}_{page}"
    # $ ensures this only matches clean episode URLs (no ?all_episodes suffix)
    pattern       = BASE_PATTERN + r"/episode/(\d+)$"
    example       = "https://tonarinoyj.jp/episode/12207421983749561558"

    def initialize(self):
        super().initialize()
        self.page_url = self.url

    def metadata(self, page):
        episode_id = self.groups[0]
        data       = self._parse_episode_json(page)
        product    = data["readableProduct"]
        series     = product.get("series") or {}

        self._page_structure = product["pageStructure"]

        return {
            "manga"         : series.get("title") or product.get("title", episode_id),
            "manga_id"      : series.get("id", ""),
            "chapter_string": product.get("title", episode_id),
            "chapter_id"    : episode_id,
            "lang"          : "ja",
            "language"      : "Japanese",
        }

    def images(self, page):
        del page
        return self._episode_images(self._page_structure)


class TonariyyjMangaExtractor(TonariyyjBase, MangaExtractor):
    """Extractor for all free episodes of a Tonari no Young Jump series.

    Use the RSS series URL — findable on any episode page in the browser's
    RSS autodiscovery or in the page source as:
      <link rel="alternate" type="application/rss+xml" href="https://tonarinoyj.jp/rss/series/{id}">

    Usage: gallery-dl "https://tonarinoyj.jp/rss/series/<series_id>"
    """
    chapterclass = TonariyyjChapterExtractor
    pattern      = BASE_PATTERN + r"/(?:rss|atom)/series/(\d+)"
    example      = "https://tonarinoyj.jp/rss/series/12207421983555296753"

    def initialize(self):
        super().initialize()
        self.page_url = self.root + "/rss/series/" + self.groups[0]

    def chapters(self, page):
        # RSS channel title format: "となりのヤングジャンプ（{series title}）"
        title_m = _re.search(r"<title>([^<]+)</title>", page)
        raw     = title_m.group(1).strip() if title_m else ""
        paren_m = _re.search(r"[（(](.+?)[）)]", raw)
        manga   = paren_m.group(1) if paren_m else raw

        series_id  = self.groups[0]
        manga_meta = {
            "manga"    : manga,
            "manga_id" : series_id,
            "lang"     : "ja",
            "language" : "Japanese",
        }

        result = []
        for ep in self._fetch_all_episodes(series_id):
            if not ep.get("purchase_info", {}).get("can_read", False):
                if ep.get("status", {}).get("label") not in ("is_free",):
                    continue
            viewer_uri = ep.get("viewer_uri", "")
            if not viewer_uri:
                continue
            result.append((viewer_uri, {
                **manga_meta,
                "chapter_string": ep.get("title", ""),
                "chapter_id"    : viewer_uri.rstrip("/").rsplit("/", 1)[-1],
            }))
        return result
