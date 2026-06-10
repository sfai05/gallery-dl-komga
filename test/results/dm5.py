# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import dm5


__tests__ = (

{
    "#url"     : "https://www.dm5.com/m1048064/",
    "#category": ("", "dm5", "chapter"),
    "#class"   : dm5.Dm5ChapterExtractor,
    "#pattern" : r"https://",
    "#count"   : range(1, 100),

    "manga"         : str,
    "manga_id"      : str,
    "chapter_string": str,
    "chapter_id"    : str,
    "lang"          : "zh",
    "language"      : "Chinese",
},

{
    "#url"  : "https://dm5.cn/m1048064/",
    "#class": dm5.Dm5ChapterExtractor,
},

{
    "#url"     : "https://www.dm5.com/manhua-haizoang/",
    "#category": ("", "dm5", "manga"),
    "#class"   : dm5.Dm5MangaExtractor,
    "#pattern" : dm5.Dm5ChapterExtractor.pattern,
    "#count"   : range(1000, 9999),

    "manga"   : str,
    "manga_id": str,
    "lang"    : "zh",
},

{
    "#url"  : "https://www.dm5.com/manhua-haizoang",
    "#class": dm5.Dm5MangaExtractor,
},

)
