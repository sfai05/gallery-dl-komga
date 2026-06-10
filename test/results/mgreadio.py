# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import mgreadio


__tests__ = (

{
    "#url"     : "https://mgread.io/manga/one-piece/chapter-1/",
    "#category": ("", "mgreadio", "chapter"),
    "#class"   : mgreadio.MgreadioChapterExtractor,
    "#pattern" : r"https://mg\.mgread\.io/\d+/\d+/[^\s\"']+?\.(?:jpg|jpeg|png|webp)",
    "#count"   : range(1, 100),

    "manga"        : str,
    "manga_id"     : "one-piece",
    "chapter"      : 1,
    "chapter_minor": "",
    "chapter_id"   : "chapter-1",
    "volume"       : 0,
    "lang"         : "en",
},

{
    "#url"  : "https://www.mgread.io/manga/one-piece/chapter-1/",
    "#class": mgreadio.MgreadioChapterExtractor,
},

{
    "#url"     : "https://mgread.io/manga/one-piece/chapter-2-5/",
    "#comment" : "decimal chapter",
    "#category": ("", "mgreadio", "chapter"),
    "#class"   : mgreadio.MgreadioChapterExtractor,

    "chapter"      : 2,
    "chapter_minor": ".5",
    "chapter_id"   : "chapter-2-5",
},

{
    "#url"     : "https://mgread.io/manga/one-piece/",
    "#category": ("", "mgreadio", "manga"),
    "#class"   : mgreadio.MgreadioMangaExtractor,
    "#pattern" : mgreadio.MgreadioChapterExtractor.pattern,
    "#count"   : range(1, 9999),

    "manga"   : str,
    "manga_id": "one-piece",
    "lang"    : "en",
},

{
    "#url"  : "https://mgread.io/manga/one-piece",
    "#class": mgreadio.MgreadioMangaExtractor,
},

)
