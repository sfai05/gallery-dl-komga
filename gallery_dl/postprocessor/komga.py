# -*- coding: utf-8 -*-

# Copyright 2025 gallery-dl-komga contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Inject ComicInfo.xml and write series.json for Komga media server"""

from .common import PostProcessor
import json
import os
import zipfile


class KomgaPP(PostProcessor):
    """Postprocessor that injects ComicInfo.xml into CBZ archives and writes
    series.json — only when manga metadata fields are present."""

    def __init__(self, job, options):
        PostProcessor.__init__(self, job)
        self._extension = options.get("extension", "cbz")
        self._write_comic_info = options.get("comic-info", True)
        self._write_series = options.get("series-json", True)
        self._dir_meta = {}

        job.register_hooks({"file": self._on_file}, options)
        job.hooks["finalize"].append(self._finalize)

    def _on_file(self, pathfmt):
        if not pathfmt.kwdict.get("manga"):
            return
        dirpath = pathfmt.realdirectory.rstrip("/\\")
        self._dir_meta[dirpath] = pathfmt.kwdict

    def _finalize(self, pathfmt):
        written_series = set()
        for dirpath, meta in self._dir_meta.items():
            cbz = dirpath + "." + self._extension
            if not os.path.isfile(cbz):
                continue

            if self._write_comic_info:
                try:
                    self._inject_comic_info(cbz, meta)
                except Exception as exc:
                    self.log.warning("ComicInfo.xml injection failed for %s: %s", cbz, exc)

            if self._write_series:
                parent = os.path.dirname(cbz)
                if parent not in written_series:
                    try:
                        self._write_series_json(parent, meta)
                        written_series.add(parent)
                    except Exception as exc:
                        self.log.warning("series.json write failed in %s: %s", parent, exc)

    def _inject_comic_info(self, cbz_path, meta):
        comic_info = self._build_comic_info(meta).encode("utf-8")
        zip_comment = self._build_zip_comment(meta).encode("utf-8")

        tmp_path = cbz_path + ".komga.tmp"
        try:
            existing = []
            with zipfile.ZipFile(cbz_path, "r") as zin:
                for info in zin.infolist():
                    if info.filename != "ComicInfo.xml":
                        existing.append((info, zin.read(info.filename)))

            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_STORED, True) as zout:
                zout.comment = zip_comment
                zout.writestr("ComicInfo.xml", comic_info)
                for info, data in existing:
                    zout.writestr(info, data)

            os.replace(tmp_path, cbz_path)
        finally:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

    def _build_comic_info(self, meta):
        parts = [
            '<?xml version="1.0"?>',
            '<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            ' xmlns:xsd="http://www.w3.org/2001/XMLSchema">',
        ]

        def tag(name, value):
            if value is not None and str(value).strip():
                parts.append("  <{}>{}</{}>".format(name, _esc(str(value)), name))

        tag("Title", meta.get("title"))
        tag("Series", meta.get("manga"))

        ch = meta.get("chapter")
        if ch is not None:
            minor = meta.get("chapter_minor", "")
            tag("Number", "{}{}".format(ch, minor))

        vol = meta.get("volume")
        if vol:
            tag("Volume", vol)

        tag("Summary", meta.get("description"))

        date = meta.get("date")
        if date is not None:
            try:
                tag("Year", date.year)
                tag("Month", date.month)
                tag("Day", date.day)
            except AttributeError:
                s = str(date)
                if len(s) >= 4:
                    tag("Year", s[:4])
                if len(s) >= 7:
                    tag("Month", s[5:7])
                if len(s) >= 10:
                    tag("Day", s[8:10])

        authors = meta.get("author") or []
        if isinstance(authors, str):
            authors = [authors]
        if authors:
            tag("Writer", ", ".join(authors))

        artists = meta.get("artist") or []
        if isinstance(artists, str):
            artists = [artists]
        if artists:
            tag("Penciller", ", ".join(artists))

        groups = meta.get("group") or []
        if isinstance(groups, str):
            groups = [groups]
        if groups:
            tag("Translator", ", ".join(groups))

        category = meta.get("category") or ""
        publisher = "MangaDex" if meta.get("manga_id") and category == "mangadex" \
            else category.title()
        tag("Publisher", publisher)

        genres = meta.get("genres") or []
        if genres:
            tag("Genre", ", ".join(genres))

        tags = meta.get("tags") or []
        if tags:
            tag("Tags", ", ".join(tags))

        chapter_id = meta.get("chapter_id")
        if chapter_id and category == "mangadex":
            tag("Web", "https://mangadex.org/chapter/{}".format(chapter_id))

        count = meta.get("count")
        if count:
            tag("PageCount", count)

        lang = meta.get("lang")
        if lang:
            tag("LanguageISO", lang)
            tag("Manga", "YesAndRightToLeft" if lang == "ja" else "Yes")

        demographic = meta.get("demographic")
        if demographic:
            age_rating = {
                "shounen": "Teen",
                "shoujo": "Everyone 10+",
                "seinen": "Mature 17+",
                "josei":  "Mature 17+",
            }.get(demographic.lower(), "Unknown")
            tag("AgeRating", age_rating)

        parts.append("</ComicInfo>")
        return "\n".join(parts)

    def _build_zip_comment(self, meta):
        lines = []
        manga_id = meta.get("manga_id")
        chapter_id = meta.get("chapter_id")
        if manga_id:
            lines.append("Title UUID: {}".format(manga_id))
        if chapter_id:
            lines.append("Chapter UUID: {}".format(chapter_id))
        ch = meta.get("chapter")
        if ch is not None:
            minor = meta.get("chapter_minor", "")
            lines.append("Chapter: {}{}".format(ch, minor))
        vol = meta.get("volume")
        if vol:
            lines.append("Volume: {}".format(vol))
        return "\n".join(lines)

    def _write_series_json(self, series_dir, meta):
        alt_titles = meta.get("manga_alt") or meta.get("manga_titles") or []
        if isinstance(alt_titles, str):
            alt_titles = [alt_titles]

        category = meta.get("category") or ""
        publisher = "MangaDex" if meta.get("manga_id") and category == "mangadex" \
            else category.title()

        m = {
            "type": "comicSeries",
            "name": meta.get("manga", ""),
            "alternate_titles": [
                {"title": t, "language": "unknown"}
                for t in alt_titles
                if isinstance(t, str)
            ],
            "publisher": publisher,
        }

        manga_id = meta.get("manga_id")
        if manga_id:
            m["comicid"] = manga_id

        authors = meta.get("author") or []
        if isinstance(authors, str):
            authors = [authors]
        if authors:
            m["author"] = ", ".join(authors)

        if meta.get("description"):
            m["description_text"] = meta["description"]
        if meta.get("year"):
            m["year"] = meta["year"]
        if meta.get("status"):
            m["status"] = meta["status"]
        if meta.get("demographic"):
            m["publication_demographic"] = meta["demographic"]

        genres = meta.get("genres") or []
        if genres:
            m["genres"] = genres

        tags = meta.get("tags") or []
        if tags:
            m["tags"] = tags

        content = json.dumps({"metadata": m}, ensure_ascii=False, indent=2)
        target = os.path.join(series_dir, "series.json")
        tmp = target + ".komga.tmp"

        if os.path.isfile(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    if f.read() == content:
                        return
            except Exception:
                pass

        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, target)


def _esc(value):
    return (value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


__postprocessor__ = KomgaPP
