# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import komiic


__tests__ = (

{
    "#url"     : "https://komiic.com/comic/3688/chapter/207741/images/all",
    "#category": ("", "komiic", "chapter"),
    "#class"   : komiic.KomiicChapterExtractor,
    "#pattern" : r"https://komiic\.com/api/image/\w+",

    "manga"         : str,
    "manga_id"      : "3688",
    "chapter_string": str,
    "chapter_id"    : "207741",
    "lang"          : "zh",
    "language"      : "Chinese",
    "author"        : list,
    "tags"          : list,
    "status"        : str,
},

{
    "#url"     : "https://komiic.com/comic/3688",
    "#category": ("", "komiic", "manga"),
    "#class"   : komiic.KomiicMangaExtractor,
    "#pattern" : komiic.KomiicChapterExtractor.pattern,
    "#count"   : range(1, 999),

    "manga"   : str,
    "manga_id": "3688",
    "lang"    : "zh",
},

{
    "#url"  : "https://komiic.com/comic/3688/",
    "#class": komiic.KomiicMangaExtractor,
},

)
