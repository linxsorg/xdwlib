#!/usr/bin/env python
#vim:fileencoding=cp932:fileformat=dos

"""xdwlib.py -- DocuWorks library for Python.

Copyright (C) 2010 HAYASI Hideki <linxs@linxs.org>  All rights reserved.

This software is subject to the provisions of the Zope Public License,
Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
FOR A PARTICULAR PURPOSE.
"""

import sys
from os.path import splitext, basename
import datetime

from xdwapi import *


CODEPAGE = 932

try:
    VALID_DOCUMENT_HANDLES
except NameError:
    VALID_DOCUMENT_HANDLES = []


def xdwopen(path, readonly=False, authenticate=True):
    """General opener"""
    doctype = {
            ".XDW": XDWDocument,
            ".XBD": XDWBinder,
            }[splitext(basename(path))[1].upper()]
    return doctype(path, readonly=readonly, authenticate=authenticate)


def create_document_from_image(
        inputPath,
        outputPath,
        size=XDW_SIZE_A4_PORTRAIT,
        fit_image=XDW_CREATE_FIT,
        compress=XDW_COMPRESS_LOSSLESS,
        zoom=100,
        width=0, height=0,
        horizontal_position=XDW_CREATE_HCENTER,
        vertical_position=XDW_CREATE_VCENTER,
        ):
    """A XDW generator"""
    create_option = XDW_CREATE_OPTION()
    create_option.nSize = normalize_binder_size(size)
    create_option.nFitImage = fit_image
    create_option.nCompress = compress
    create_option.nZoom = zoom
    create_option.nWidth = width
    create_option.nHeight = height
    create_option.nHorPos = horizontal_position
    create_option.nVerPos = vertical_position
    XDW_CreateXdwFromImageFile(inputPath, outputPath, create_option)


def create_binder(path, color=XDW_BINDER_COLOR_0, size=XDW_SIZE_FREE):
    """The XBD generator"""
    XDW_CreateBinder(path, color, size)


# Annotations


def _annotation_in(annotation, rect):  # Assume rect is half-opened.
    return (rect.left <= annotation.horizontal_position \
                     <= rect.right - annotation.width \
            and \
            rect.top <= annotation.vertical_position \
                     <= rect.bottom - annotation.height)


def _find_annotations(object,
        recursive=False, rect=None, types=None,
        half_open=True):
    if rect and not half_open:
        rect.right += 1
        rect.bottom += 1
    if types:
        if not isinstance(types, (list, tuple)):
            types = [types]
        types = [XDW_ANNOTATION_TYPE.normalize(t) for t in types]
    annotation_list = []
    for i in range(object.annotations):
        annotation = object.annotation(i)
        sublist = []
        if recursive and annotation.annotations:
            sublist = _find_annotations(annotation,
                    recursive=recursive, rect=rect, types=types,
                    half_open=half_open)
        if (not rect or annotation_in(annotation, rect)) and \
                (not types or annotation.annotation_type in types):
            if sublist:
                sublist.insert(0, annotation)
                annotation_list.append(sublist)
            else:
                annotation_list.append(annotation)
        elif sublist:
            sublist.insert(0, None)
            annotation_list.append(sublist)
    return annotation_list


class XDWAnnotation(object):

    """An annotation on DocuWorks document page"""

    def __init__(self, page, index, parent_annotation=None):
        self.page = page
        self.parent_annotation = parent_annotation
        self.index = index
        if parent_annotation:
            pah = parent_annotation.annotation_handle
        else:
            pah = None
        info = XDW_GetAnnotationInformation(
                page.xdw.document_handle,
                page.page + 1,
                pah,
                index + 1)
        self.annotation_handle = info.handle
        self.horizontal_position = info.nHorPos
        self.vertical_position = info.nVerPos
        self.width = info.nWidth
        self.height = info.nHeight
        self.annotation_type = info.nAnnotationType
        self.annotations = info.nChildAnnotations

    def __str__(self):
        return "XDWAnnotation(%s P%d: type=%s)" % (
                self.page.xdw.name,
                self.page.page,
                XDW_ANNOTATION_TYPE[self.annotation_type],
                )

    def __getattr__(self, name):
        if name == "text":
            at = self.annotation_type
            ah = self.annotation_handle
            ga = XDW_GetAnnotationAttributeW
            if at == XDW_AID_STAMP:
                text = "%s <DATE> %s" % (
                        ga(ah, XDW_ATN_TopField, CODEPAGE)[0],
                        ga(ah, XDW_ATN_BottomField, CODEPAGE)[0],
                        )
            elif at == XDW_AID_TEXT:
                text = ga(ah, XDW_ATN_Text, CODEPAGE)[0]
            elif at == XDW_AID_LINK:
                text = ga(ah, XDW_ATN_Caption, CODEPAGE)[0]
            else:
                text = None
            return text
        if name == "fulltext":
            if self.annotations:
                text = [self.text]
                text.extend([self.annotation(i).fulltext \
                        for i in range(self.annotations)])
                return "\v".join([
                        t for t in text if isinstance(t, basestring)])
            else:
                return self.text
        attribute_name = "%" + name
        if attribute_name in XDW_ANNOTATION_ATTRIBUTE:
            return XDW_GetAnnotationAttributeW(
                    self.annotation_handle, unicode(attribute_name), CODEPAGE)
        raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name))

    def __setattr__(self, name, value):
        attribute_name = "%" + name
        if attribute_name in XDW_ANNOTATION_ATTRIBUTE:
            if isinstance(value, basestring):
                attribute_type = XDW_ATYPE_STRING
            else:
                attribute_type = XDW_ATYPE_INT
            XDW_SetAnnotationAttributeW(
                    self.page.xdw.document_handle, self.annotation_handle,
                    unicode(attribute_name), attribute_type, byref(value),
                    XDW_TEXT_MULTIBYTE, CODEPAGE)
            return
        self.__dict__[name] = value
        #raise AttributeError("'%s' object has no attribute '%s'" % (
        #        self.__class__.__name__, name))

    def annotation(self, index):
        if self.annotations <= index:
            if self.annotations < 1:
                raise AttributeError("annotation object has no children")
            else:
                raise IndexError(
                        "annotation index %d out of range(0..%d)" % (
                        index, self.annotations - 1))
        return XDWAnnotation(self.page, index, parent_annotation=self)

    def find_annotations(*args, **kw):
        return _find_annotations(*args, **kw)


class XDWPage(object):

    """A page of DocuWorks document"""

    @staticmethod
    def normalize_resolution(n):
        if n <= 6:
            return (100, 200, 400, 200, 300, 400, 200)[n]
        return n

    def __init__(self, xdw, page):
        self.xdw = xdw
        self.page = page
        page_info = XDW_GetPageInformation(
                xdw.document_handle, page + 1, extend=True)
        self.width = page_info.nWidth  # 1/100 mm
        self.height = page_info.nHeight  # 1/100 mm
        # XDW_PGT_FROMIMAGE/FROMAPPL/NULL
        self.page_type = page_info.nPageType
        self.horizontal_resolution = XDWPage.normalize_resolution(
                page_info.nHorRes)  # dpi
        self.vertical_resolution = XDWPage.normalize_resolution(
                page_info.nVerRes)  # dpi
        self.compress_type = page_info.nCompressType
        self.annotations = page_info.nAnnotations
        self.degree = page_info.nDegree
        self.original_width = page_info.nOrgWidth  # 1/100 mm
        self.original_height = page_info.nOrgHeight  # 1/100 mm
        self.original_horizontal_resolution = XDWPage.normalize_resolution(
                page_info.nOrgHorRes)  # dpi
        self.original_vertical_resolution = XDWPage.normalize_resolution(
                page_info.nOrgVerRes)  # dpi
        self.image_width = page_info.nImageWidth  # px
        self.image_height = page_info.nImageHeight  # px

    def __getattr__(self, name):
        if name == "text":
            return XDW_GetPageTextToMemoryW(self.xdw.document_handle,
                    self.page + 1)
        if name == "annotation_text":
            return "\v".join([
                a.text for a in self.find_annotations() if a.text])
        if name == "annotation_fulltext":
            return "\v".join([
                a.fulltext for a in self.find_annotations() if a.fulltext])
        raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name))

    def __str__(self):
        return "XDWPage(page %d: %.2f*%.2fmm, %s, %d annotations)" % (
                self.page,
                self.width / 100.0, self.height / 100.0,
                XDW_PAGE_TYPE[self.page_type],
                self.annotations,
                )

    def annotation(self, index):
        """annotation(n) --> XDWAnnotation"""
        if self.annotations <= index:
            if self.annotations < 1:
                raise AttributeError("page object has no annotations")
            else:
                raise IndexError(
                        "annotation index %d out of range(0..%d)" % (
                        index, self.annotations - 1))
        return XDWAnnotation(self, index)

    def find_annotations(*args, **kw):
        return _find_annotations(*args, **kw)


class XDWDocument(object):

    """A DocuWorks document"""

    def register(self):
        VALID_DOCUMENT_HANDLES.append(self.document_handle)

    def free(self):
        VALID_DOCUMENT_HANDLES.remove(self.document_handle)

    def __init__(self, path, readonly=False, authenticate=True):
        open_mode = XDW_OPEN_MODE_EX()
        if readonly:
            open_mode.nOption = XDW_OPEN_READONLY
        else:
            open_mode.nOption = XDW_OPEN_UPDATE
        if authenticate:
            open_mode.nAuthMode = XDW_AUTH_NODIALOGUE
        else:
            open_mode.nAuthMode = XDW_AUTH_NONE
        self.document_handle = XDW_OpenDocumentHandle(path, open_mode)
        self.register()
        self.name = splitext(basename(path))[0]
        try:
            self.name = self.name.decode("cp%d" % CODEPAGE)
        except:
            pass
        # Set document properties.
        document_info = XDW_GetDocumentInformation(self.document_handle)
        self.pages = document_info.nPages
        self.version = document_info.nVersion - 3  # DocuWorks version
        self.original_data = document_info.nOriginalData
        self.document_type = document_info.nDocType
        self.editable = bool(document_info.nPermission & XDW_PERM_DOC_EDIT)
        self.annotatable = bool(
                document_info.nPermission & XDW_PERM_ANNO_EDIT)
        self.printable = bool(document_info.nPermission & XDW_PERM_PRINT)
        self.copyable = bool(document_info.nPermission & XDW_PERM_COPY)
        self.show_annotations = bool(document_info.nShowAnnotations)
        # Followings are effective only for binders.
        self.documents = document_info.nDocuments
        self.binder_color = document_info.nBinderColor
        self.binder_size = document_info.nBinderSize
        # Document attributes.
        self.attributes = XDW_GetDocumentAttributeNumber(self.document_handle)

    def close(self):
        XDW_CloseDocumentHandle(self.document_handle)
        self.free()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        self.current_page = 0
        return self

    def next(self):
        if self.pages <= self.current_page:
            raise StopIteration
        page = self.current_page
        self.current_page += 1
        return XDWPage(self, page)

    def __str__(self):
        return "XDWDocument(%s: %d pages, %d files attached)" % (
                self.name,
                self.pages,
                self.documents,
                )

    def __getattr__(self, name):
        if name == "text":
            return "\f".join(page.text for page in self)
        if name == "annotation_fulltext":
            return "\f".join(page.annotation_fulltext for page in self)
        if name == "fulltext":
            return "\f".join(
                    page.text + "\f" + page.annotation_fulltext
                    for page in self)
        attribute_name = u"%" + name
        if attribute_name in XDW_DOCUMENT_ATTRIBUTE:
            return XDW_GetDocumentAttributeByNameW(
                    self.document_handle, attribute_name, CODEPAGE)[1]
        raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name))

    def __setattr__(self, name, value):
        attribute_name = "%" + name
        if isinstance(value, basestring):
            attribute_type = XDW_ATYPE_STRING
        elif isinstance(value, bool):
            attribute_type = XDW_ATYPE_BOOL
        elif isinstance(value, datetime.datetime):
            attribute_type = XDW_ATYPE_DATE
        else:
            attribute_type = XDW_ATYPE_INT
        # TODO: XDW_ATYPE_OTHER should also be valid.
        if attribute_name in XDW_DOCUMENT_ATTRIBUTE:
            XDW_SetDocumentAttributeW(
                    self.document_handle,
                    attribute_name, attribute_type, byref(value),
                    XDW_TEXT_MULTIBYTE, CODEPAGE)
            return
        self.__dict__[name] = value
        #raise AttributeError("'%s' object has no attribute '%s'" % (
        #        self.__class__.__name__, name))

    def page(self, n):
        """page(n) --> XDWPage"""
        return XDWPage(self, n)

    def __len__(self):
        return self.pages

    def is_document(self):
        """is_document() --> True"""
        return True

    def is_binder(self):
        """is_binder() --> False"""
        return False

    def save(self):
        XDW_SaveDocument(self.document_handle)


class XDWDocumentInBinder(object):

    """A document part of DocuWorks binder"""

    def __init__(self, binder, position):
        self.binder = binder
        self.position = position
        self.start_page = sum(binder.document_pages[:position])
        self.name = XDW_GetDocumentNameInBinderW(
                self.binder.document_handle, position + 1, CODEPAGE)[0]
        document_info = XDW_GetDocumentInformationInBinder(
                self.binder.document_handle, position + 1)
        self.pages = document_info.nPages
        self.original_data = document_info.nOriginalData

    def __iter__(self):
        self.current_page = 0
        return self

    def next(self):
        if self.pages <= self.current_page:
            raise StopIteration
        n = self.start_page + self.current_page
        self.current_page += 1
        return XDWPage(self.binder, n)

    def __str__(self):
        return "XDWDocumentInBinder(" \
                "%s = %s[%d]: %d pages, %d attachments)" % (
                self.name,
                self.binder.name, self.position,
                self.position + 1,
                self.pages,
                self.original_data,
                )

    def page(self, n):
        """page(n) --> XDWPage"""
        return XDWPage(self.binder, self.start_page + n)

    def __len__(self):
        return self.pages

    def __getattr__(self, name):
        if name == "text":
            return "\f".join(page.text for page in self)
        if name == "annotation_fulltext":
            return "\f".join(page.annotation_fulltext for page in self)
        if name == "fulltext":
            return "\f".join(
                    page.text + "\f" + page.annotation_fulltext
                    for page in self)
        raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name))


class XDWBinder(XDWDocument):

    """A DocuWorks Binder"""

    def is_document(self):
        """is_document() --> False"""
        return False

    def is_binder(self):
        """is_binder() --> True"""
        return True

    def __init__(self, path, readonly=False, authenticate=True):
        XDWDocument.__init__(self,
                path=path, readonly=readonly, authenticate=authenticate)
        assert self.document_type == XDW_DT_BINDER
        self.document_pages = self.document_pages()

    def __str__(self):
        return "XDWBinder(%s: %d documents, %d pages, %d attachments)" % (
                self.name,
                self.documents,
                self.pages,
                self.original_data,
                )

    def document_pages(self):
        """document_pages() --> list

        Get list of page count for each document in binder
        """
        pages = []
        for pos in range(self.documents):
            docinfo = XDW_GetDocumentInformationInBinder(
                    self.document_handle, pos + 1)
            pages.append(docinfo.nPages)
        return pages

    def document(self, position):
        """document(position) --> XDWDocument"""
        return XDWDocumentInBinder(self, position)

    def page(self, n):
        """page(n) --> XDWPage"""
        return XDWPage(self, n)

    def __iter__(self):
        self.current_position = 0
        return self

    def next(self):
        if self.documents <= self.current_position:
            raise StopIteration
        pos = self.current_position
        self.current_position += 1
        return  XDWDocumentInBinder(self, pos)

    def __len__(self):
        return self.documents

    def __getattr__(self, name):
        if name == "text":
            return "\f".join([doc.text for doc in self])
        raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name))
