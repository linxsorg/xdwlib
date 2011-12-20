#!/usr/bin/env python
#vim:fileencoding=cp932:fileformat=dos

"""documentinbinder.py -- DocuWorks library for Python.

Copyright (C) 2010 HAYASI Hideki <linxs@linxs.org>  All rights reserved.

This software is subject to the provisions of the Zope Public License,
Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
FOR A PARTICULAR PURPOSE.
"""

from xdwapi import *
from common import *
from observer import *
from basedocument import BaseDocument


__all__ = ("DocumentInBinder",)


class DocumentInBinder(BaseDocument, Observer):

    """Document part of DocuWorks binder."""

    __type__ = "DOCUMENT_IN_BINDER"

    def __init__(self, binder, pos):
        BaseDocument.__init__(self)
        self.pos = pos
        Observer.__init__(self, binder, EV_DOC_INSERTED)
        self.binder = binder
        self.handle = binder.handle
        self._set_page_offset()  # self.page_offset
        self.name = XDW_GetDocumentNameInBinderW(
                self.handle, pos + 1, codepage=CP)[0]
        document_info = XDW_GetDocumentInformationInBinder(
                self.handle, pos + 1)
        self.pages = document_info.nPages
        self.original_data = document_info.nOriginalData
        self.type = DocumentInBinder.__type__

    def __repr__(self):
        return u"DocumentInBinder(%s(%s[%d]))" % (
                self.name, self.binder.name, self.pos)

    def __str__(self):
        return u"DocumentInBinder(%s (%s[%d]): %d pages, %d attachments)" % (
                self.name, self.binder.name, self.pos,
                self.pages, self.original_data)

    def update(self, event):
        if not isinstance(event, Notification):
            raise TypeError("not an instance of Notification class")
        if event.type == EV_DOC_REMOVED:
            if event.para[0] < self.pos:
                self.pos -= 1
                self._set_page_offset()
        elif event.type == EV_DOC_INSERTED:
            if event.para[0] < self.pos:
                self.pos += 1
                self._set_page_offset()
        else:
            raise ValueError("illegal event type: %d" % event.type)

    def _set_page_offset(self):
        """Private method to renew the page offset for DocumentInBinder."""
        self.page_offset = sum(self.binder.document_pages()[:self.pos])

    def absolute_page(self, pos, append=False):
        """Concrete method over dirname()."""
        pos = self._pos(pos, append=append)
        return self.page_offset + pos

    def dirname(self):
        """Concrete method over dirname()."""
        return self.binder.dir
