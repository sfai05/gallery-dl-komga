# -*- coding: utf-8 -*-

# Copyright 2026 gallery-dl contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import copymanga


__tests__ = (

{
    "#url"      : "https://www.2026copy.com/comic/onepiece/chapter/abc123-uuid-here",
    "#category" : ("", "copymanga", "chapter"),
    "#class"    : copymanga.CopymangaChapterExtractor,
},

{
    "#url"      : "https://www.2026copy.com/comic/onepiece",
    "#category" : ("", "copymanga", "manga"),
    "#class"    : copymanga.CopymangaMangaExtractor,
},

# Trailing slash and query-string variants
{
    "#url"  : "https://www.2026copy.com/comic/onepiece/",
    "#class": copymanga.CopymangaMangaExtractor,
},

{
    "#url"  : "https://www.2026copy.com/comic/onepiece?foo=bar",
    "#class": copymanga.CopymangaMangaExtractor,
},

# Legacy domain aliases still accepted
{
    "#url"  : "https://www.mangacopy.com/comic/onepiece",
    "#class": copymanga.CopymangaMangaExtractor,
},

# Domain aliases
{
    "#url"  : "https://copymanga.site/comic/onepiece/chapter/uuid-chapter-1",
    "#class": copymanga.CopymangaChapterExtractor,
},

{
    "#url"  : "https://copymanga.tv/comic/onepiece",
    "#class": copymanga.CopymangaMangaExtractor,
},

{
    "#url"  : "https://copymanga.com/comic/onepiece",
    "#class": copymanga.CopymangaMangaExtractor,
},

{
    "#url"  : "https://copy20.com/comic/onepiece",
    "#class": copymanga.CopymangaMangaExtractor,
},

)
