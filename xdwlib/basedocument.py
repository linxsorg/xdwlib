#!/usr/bin/env python2.6
#vim:fileencoding=cp932:fileformat=dos

"""basedocument.py -- DocuWorks library for Python.

Copyright (C) 2010 HAYASI Hideki <linxs@linxs.org>  All rights reserved.

This software is subject to the provisions of the Zope Public License,
Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
FOR A PARTICULAR PURPOSE.
"""

import sys
import os
import tempfile

from xdwapi import *
from common import *
from observer import *
from struct import Point
from xdwfile import xdwopen
from page import Page, PageCollection


__all__ = ("BaseDocument",)


class BaseDocument(Subject):

    """DocuWorks document base class.

    This class is a base class, which is expected to be inherited by Document
    or DocumentInBinder class.

    Each BaseDocument instance has an observer dict.  This dict holds
    (page_number, Page_object) pairs, and is used to notify page insertion
    or deletion.  Receiving this notification, every Page object should adjust
    its memorized page number.
    """

    def _pos(self, pos, append=False):
        append = 1 if append else 0
        if not (-self.pages <= pos < self.pages + append):
            raise IndexError("Page number must be in [%d, %d), %d given" % (
                    -self.pages, self.pages + append, pos))
        if pos < 0:
            pos += self.pages
        return pos

    def _slice(self, pos):
        if pos.step == 0 and pos.start != pos.stop:
            raise ValueError("slice.step must not be 0")
        return slice(
                self._pos(pos.start or 0),
                self.pages if pos.stop is None else pos.stop,
                1 if pos.step is None else pos.step)

    def __init__(self):
        Subject.__init__(self)

    def __repr__(self):  # abstract
        raise NotImplementedError()

    def __str__(self):  # abstract
        raise NotImplementedError()

    def __len__(self):
        return self.pages

    def __getitem__(self, pos):
        if isinstance(pos, slice):
            pos = self._slice(pos)
            return PageCollection(self.page(p)
                    for p in range(pos.start, pos.stop, pos.step))
        return self.page(pos)

    def __setitem__(self, pos, val):
        raise NotImplementedError()

    def __delitem__(self, pos):
        if isinstance(pos, slice):
            pos = self._slice(pos)
            for p in range(pos.start, pos.stop, pos.step):
                self.delete(p)
        else:
            self.delete(pos)

    def __iter__(self):
        for pos in xrange(self.pages):
            yield self.page(pos)

    def absolute_page(self, pos, append=False):
        """Abstract method to get absolute page number in binder/document."""
        raise NotImplementedError()

    def update_pages(self):
        """Abstract method to update number of pages."""
        raise NotImplementedError()

    def page(self, pos):
        """Get a Page."""
        pos = self._pos(pos)
        if pos not in self.observers:
            self.observers[pos] = Page(self, pos)
        return self.observers[pos]

    def append(self, obj):
        """Append a Page/PageCollection/Document at the end of document."""
        self.insert(self.pages, obj)

    def insert(self, pos, obj):
        """Insert a Page/PageCollection/Document.

        pos: position to insert; starts with 0
        obj: Page/PageCollection/BaseDocument or path
        """
        pos = self._pos(pos, append=True)
        doc = None
        if isinstance(obj, Page):
            pc = PageCollection([obj])
        elif isinstance(obj, PageCollection):
            pc = obj
        elif isinstance(obj, BaseDocument):
            pc = PageCollection(obj)
        elif isinstance(obj, basestring):  # XDW path
            assert obj.lower().endswith(".xdw")  # binder is not acceptable
            doc = xdwopen(cp(obj))
            pc = PageCollection(doc)
        else:
            raise ValueError("can't insert %s object" % (obj.__class__))
        temp = pc.combine("temp.xdw")
        XDW_InsertDocument(
                self.handle,
                self.absolute_page(pos, append=True) + 1,
                temp)
        self.pages += len(pc)
        if doc:
            doc.close()
        os.remove(temp)
        # Check inserted pages in order to attach them to this document and
        # shift observer entries appropriately.
        for p in xrange(pos, pos + len(pc)):
            Page(self, p)

    def append_image(self, *args, **kw):
        """Append a page created from image file(s)."""
        self.insert_image(self.pages, *args, **kw)

    def insert_image(self, pos, input_path,
            fitimage="FITDEF",
            compress="NORMAL",
            zoom=0,  # %; 0=100%
            size=Point(0, 0),  # Point(width, height); 0=A4R
            align=("center", "center"),  # left/center/right, top/center/bottom
            maxpapersize="DEFAULT",
            ):
        """Insert a page created from image file(s)."""
        prev_pages = self.pages
        pos = self._pos(pos, append=True)
        input_path = cp(input_path)
        opt = XDW_CREATE_OPTION_EX2()
        opt.nFitImage = XDW_CREATE_FITIMAGE.normalize(fitimage)
        opt.nCompress = XDW_COMPRESS.normalize(compress)
        #opt.nZoom = 0
        opt.nZoomDetail = int(zoom * 1000)  # .3f
        # NB. Width and height are valid only for XDW_CREATE_USERDEF(_FIT).
        opt.nWidth, opt.nHeight = map(int, size * 100)  # .2f;
        opt.nHorPos = XDW_CREATE_HPOS.normalize(align[0])
        opt.nVerPos = XDW_CREATE_VPOS.normalize(align[1])
        opt.nMaxPaperSize = XDW_CREATE_MAXPAPERSIZE.normalize(maxpapersize)
        XDW_CreateXdwFromImageFileAndInsertDocument(
                self.handle,
                self.absolute_page(pos, append=True) + 1,
                input_path,
                opt)
        self.update_pages()
        # Check inserted pages in order to attach them to this document and
        # shift observer entries appropriately.
        for p in range(pos, pos + (self.pages - prev_pages)):
            Page(self, p)

    def export_image(self, pos, path, pages=1,
            dpi=600, color="COLOR", format=None, compress="NORMAL"):
        """Export page(s) to image file.

        pos:        (int or tuple (start:stop) in half-open style like slice)
        path:       (basestring) pathname to output
        pages:      (int)
        dpi:        (int) 10..600
        color:      (str) COLOR | MONO | MONO_HIGHQUALITY
        format:     (str) BMP | TIFF | JPEG | PDF
        compress:   (str) for BMP, not available
                    for TIFF, NOCOMPRESS | PACKBITS | JPEG | JPEG_TTN2 | G4
                    for JPEG, NORMAL | HIGHQUALITY | HIGHCOMPRESS
                    for PDF,  NORMAL | HIGHQUALITY | HIGHCOMPRESS |
                              MRC_NORMAL | MRC_HIGHQUALITY | MRC_HIGHCOMPRESS
        """
        path = cp(path)
        if isinstance(pos, (list, tuple)):
            pos, pages = pos
            pages -= pos
        pos = self._pos(pos)
        if not format:
            _, ext = os.path.splitext(path)
            ext = ((ext or "").lstrip(".") or "bmp").lower()
            format = {"dib": "bmp", "tif": "tiff", "jpg": "jpeg"}.get(ext, ext)
        if format.lower() not in ("bmp", "tiff", "jpeg", "pdf"):
            raise TypeError("image type must be BMP, TIFF, JPEG or PDF.")
        if not path:
            path = "%s_P%d" % (self.name, pos + 1)
            path = cp(path, dir=self.dirname())
            if 1 < pages:
                path += "-%d" % ((pos + pages - 1) + 1)
            path += "." + format
        if not (10 <= dpi <= 600):
            raise ValueError("specify resolution between 10 and 600")
        opt = XDW_IMAGE_OPTION_EX()
        opt.nDpi = int(dpi)
        opt.nColor = XDW_IMAGE_COLORSCHEME.normalize(color)
        opt.nImageType = XDW_IMAGE_FORMAT.normalize(format)
        if opt.nImageType == XDW_IMAGE_DIB:
            opt.pDetailOption = NULL
        elif opt.nImageType == XDW_IMAGE_TIFF:
            dopt = XDW_IMAGE_OPTION_TIFF()
            dopt.nCompress = XDW_COMPRESS.normalize(compress)
            if dopt.nCompress not in (
                    XDW_COMPRESS_NOCOMPRESS,
                    XDW_COMPRESS_PACKBITS,
                    XDW_COMPRESS_JPEG,
                    XDW_COMPRESS_JPEG_TTN2,
                    XDW_COMPRESS_G4,
                    ):
                dopt.nCompress = XDW_COMPRESS_NOCOMPRESS
            dopt.nEndOfMultiPages = (pos + pages - 1) + 1
            opt.pDetailOption = cast(pointer(dopt), c_void_p)
        elif opt.nImageType == XDW_IMAGE_JPEG:
            dopt = XDW_IMAGE_OPTION_JPEG()
            dopt.nCompress = XDW_COMPRESS.normalize(compress)
            if dopt.nCompress not in (
                    XDW_COMPRESS_NORMAL,
                    XDW_COMPRESS_HIGHQUALITY,
                    XDW_COMPRESS_HIGHCOMPRESS,
                    ):
                dopt.nCompress = XDW_COMPRESS_NORMAL
            opt.pDetailOption = cast(pointer(dopt), c_void_p)
        elif opt.nImageType == XDW_IMAGE_PDF:
            dopt = XDW_IMAGE_OPTION_PDF()
            dopt.nCompress = XDW_COMPRESS.normalize(compress)
            if dopt.nCompress not in (
                    XDW_COMPRESS_NORMAL,
                    XDW_COMPRESS_HIGHQUALITY,
                    XDW_COMPRESS_HIGHCOMPRESS,
                    XDW_COMPRESS_MRC_NORMAL,
                    XDW_COMPRESS_MRC_HIGHQUALITY,
                    XDW_COMPRESS_MRC_HIGHCOMPRESS,
                    ):
                dopt.nCompress = XDW_COMPRESS_MRC_NORMAL
            dopt.nEndOfMultiPages = (pos + pages - 1) + 1
            # Compression method option is deprecated.
            dopt.nConvertMethod = XDW_CONVERT_MRC_OS
            opt.pDetailOption = cast(pointer(dopt), c_void_p)
        XDW_ConvertPageToImageFile(
                self.handle, self.absolute_page(pos) + 1, path, opt)

    def delete(self, pos):
        """Delete a page."""
        pos = self._pos(pos)
        page = self.page(pos)
        XDW_DeletePage(self.handle, self.absolute_page(pos) + 1)
        self.detach(page, EV_PAGE_REMOVED)
        self.pages -= 1

    def rasterize(self, pos, dpi=600, color="COLOR"):
        """Rasterize; convert an application page into DocuWorks image page."""
        pos = self._pos(pos)
        if not (10 <= dpi <= 600):
            raise ValueError("specify resolution between 10 and 600")
        opt = XDW_IMAGE_OPTION()
        opt.nDpi = int(dpi)
        opt.nColor = XDW_IMAGE_COLORSCHEME.normalize(color)
        temp = tempfile.NamedTemporaryFile(suffix=".bmp")
        temppath = temp.name
        temp.close()  # On Windows, you cannot reopen temp.  TODO: better code
        XDW_ConvertPageToImageFile(
                self.handle, self.absolute_page(pos) + 1, temppath, opt)
        self.insert_image(pos, temppath)  # Insert rasterized image page.
        self.delete(pos + 1)  # Delete original application page.
        os.remove(temppath)

    def content_text(self, type=None):
        """Get all content text.

        type: None | "image" | "application"
              None means both.
        """
        return joinf(PSEP, [page.content_text(type=type) for page in self])

    def annotation_text(self):
        """Get all text in annotations."""
        return joinf(PSEP, [page.annotation_text() for page in self])

    def fulltext(self):
        """Get all content and annotation text."""
        return joinf(PSEP, [
                joinf(ASEP, [page.content_text(), page.annotation_text()])
                for page in self])

    def find_content_text(self, pattern, type=None):
        """Find given pattern (text or regex) in all content text.

        type: None | "image" | "application"
              None means both.
        """
        func = lambda page: page.content_text(type=type)
        return self.find(pattern, func=func)

    def find_annotation_text(self, pattern):
        """Find given pattern (text or regex) in all annotation text."""
        func = lambda page: page.annotation_text()
        return self.find(pattern, func=func)

    def find_fulltext(self, pattern):
        """Find given pattern in all content and annotation text."""
        return self.find(pattern)

    def find(self, pattern, func=None):
        """Find given pattern (text or regex) through document.

        find(pattern, func) --> PageCollection

        pattern:  a string/unicode or regexp (by re module)
        func:  a function which takes a page and returns text in it
               (default) lambda page: page.fulltext()
        """
        func = func or (lambda page: page.fulltext())
        if isinstance(pattern, (str, unicode)):
            f = lambda page: pattern in func(page)
        else:
            f = lambda page: pattern.search(func(page))
        return PageCollection(filter(f, self))

    def dirname(self):
        """Abstract method for concrete dirname()."""
        raise NotImplementedError()
