# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import tonarinoyj


__tests__ = (

{
    "#url"     : "https://tonarinoyj.jp/episode/316190246968222595",
    "#category": ("", "tonarinoyj", "chapter"),
    "#class"   : tonarinoyj.TonarinoyjChapterExtractor,
    "#pattern" : r"https?://",
    "#count"   : range(1, 100),

    "manga"         : str,
    "manga_id"      : str,
    "chapter_string": str,
    "chapter_id"    : "316190246968222595",
    "lang"          : "ja",
    "language"      : "Japanese",
},

{
    "#url"     : "https://tonarinoyj.jp/rss/series/316190246968222595",
    "#category": ("", "tonarinoyj", "manga"),
    "#class"   : tonarinoyj.TonarinoyjMangaExtractor,
    "#pattern" : tonarinoyj.TonarinoyjChapterExtractor.pattern,

    "manga"   : str,
    "manga_id": "316190246968222595",
    "lang"    : "ja",
},

{
    "#url"  : "https://tonarinoyj.jp/atom/series/316190246968222595",
    "#class": tonarinoyj.TonarinoyjMangaExtractor,
},

)
