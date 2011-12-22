#!/usr/bin/env python
#vim:fileencoding=cp932:fileformat=dos

"""annotatable.py -- DocuWorks library for Python.

Copyright (C) 2010 HAYASI Hideki <linxs@linxs.org>  All rights reserved.

This software is subject to the provisions of the Zope Public License,
Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
FOR A PARTICULAR PURPOSE.
"""

import os

from xdwapi import *
from common import *
from observer import *
from struct import Point, Rect


__all__ = ("Annotatable",)


_WIDTH = 75
_HEIGHT = 25
_POSITION = Point(_HEIGHT, _HEIGHT)
_SIZE = Point(_WIDTH, _HEIGHT)
_RECT = Rect(_POSITION, _POSITION + _SIZE)
_POINTS = (
        _POSITION,
        _POSITION + Point(_WIDTH, 0),
        _POSITION + _SIZE,
        _POSITION + Point(0, _HEIGHT))


class Annotatable(Subject):

    """Annotatable objects ie. page or annotation."""

    def _pos(self, pos, append=False):
        append = 1 if append else 0
        if not (-self.annotations <= pos < self.annotations + append):
            raise IndexError(
                    "Annotation number must be in [%d, %d), %d given" % (
                    -self.annotations, self.annotations + append, pos))
        if pos < 0:
            pos += self.annotations
        return pos

    def _slice(self, pos):
        if pos.step == 0 and pos.start != pos.stop:
            raise ValueError("slice.step must not be 0")
        return slice(
                self._pos(pos.start or 0),
                self.annotations if pos.stop is None else pos.stop,
                1 if pos.step is None else pos.step,
                )

    def __len__(self):
        return self.annotations

    def __getitem__(self, pos):
        if isinstance(pos, slice):
            pos = self._slice(pos)
            return tuple(self.annotation(p)
                    for p in range(pos.start, pos.stop, pos.step or 1))
        return self.annotation(pos)

    def __setitem__(self, pos, val):
        raise NotImplementedError()

    def __delitem__(self, pos):
        if isinstance(pos, slice):
            for p in range(pos.start, pos.stop, pos.step or 1):
                self.delete(p)
        return self.delete(pos)

    def __iter__(self):
        for pos in xrange(self.annotations):
            yield self.annotation(pos)

    def annotation(self, pos):
        """Get an annotation by position."""
        from annotation import Annotation
        pos = self._pos(pos)
        if pos not in self.observers:
            self.observers[pos] = Annotation(self, pos, parent=self)
        return self.observers[pos]

    @staticmethod
    def initial_data(ann_type, **kw):
        """Generate annotation-type-specific initialization data."""
        try:
            cls = XDW_AID_INITIAL_DATA[ann_type]
        except KeyError:
            raise ValueError("illegal annotation type %d" % ann_type)
        if cls is None:
            return None
        init_dat = cls()
        init_dat.common.nAnnotationType = \
                XDW_ANNOTATION_TYPE.normalize(ann_type)
        for k, v in kw.items():
            if k.startswith("n"):
                v = int(v)
            elif k.startswith("sz"):
                v = str(v)
            elif k.startswith("lpsz"):
                v = byref(v)
            elif k.startswith("p"):
                v = byref(v)
            setattr(init_dat, k, v)
        return init_dat

    def _add(self, ann_type, position, init_dat):
        """Abstract method as a stub for add()."""
        raise NotImplementedError()

    def add(self, ann_type, position, **kw):
        """Paste an annotation.

        add(ann_type, position, **kw)
            ann_type    annotation type
            position    Point; float, unit:mm
        """
        from annotation import Annotation
        if isinstance(position, (tuple, list)):
            position = Point(*position)
        init_dat = Annotatable.initial_data(ann_type, **kw)
        ann_handle = self._add(ann_type, position, init_dat)
        pos = self.annotations  # TODO: Ensure this is correct.
        self.annotations += 1
        ann = self.annotation(pos)
        return ann

    def add_text(self, text, position=_POSITION, **kw):
        """Paste a text annotation."""
        ann = self.add(XDW_AID_TEXT, position)
        ann.Text = text
        for k, v in kw.items():
            setattr(ann, k, v)
        return ann

    def add_fusen(self, position=_POSITION, size=_SIZE):
        """Paste a fusen annotation."""
        if size.x < 5 or size.y < 5:
            raise ValueError("Annotation size must be >= 5mm square")
        return self.add(XDW_AID_FUSEN, position,
                nWidth=int(size.x * 100), nHeight=int(size.y * 100))

    def add_line(self, points=(_POSITION, _POSITION + _SIZE)):
        """Paste a straight line annotation."""
        return self.add(XDW_AID_STRAIGHTLINE, int(points[0] * 100),
                nWidth=int(points[1].x * 100), nHeight=int(point[1].y * 100))

    add_straightline = add_line

    def add_rectangle(self, rect=_RECT):
        """Paste a rectangular annotation."""
        position, size = rect.position_and_size()
        if size.x < 3 or size.y < 3:
            raise ValueError("Annotation size must be >= 3mm square")
        return self.add(XDW_AID_RECTANGLE, position,
                nWidth=int(size.x * 100), nHeight=int(size.y * 100))

    add_rect = add_rectangle

    def add_arc(self, rect=_RECT):
        """Paste an ellipse annotation."""
        position, size = rect.position_and_size()
        if size.x < 3 or size.y < 3:
            raise ValueError("Annotation size must be >= 3mm square")
        return self.add(XDW_AID_ARC, position,
                nWidth=int(size.x * 100), nHeight=int(size.y * 100))

    def add_bitmap(self, position=_POSITION, path=None):
        """Paste an image annotation."""
        return self.add(XDW_AID_BITMAP, position,
                szImagePath=byref(path))

    def add_stamp(self, position=_POSITION, width=_WIDTH):
        """Paste a (date) stamp annotation."""
        return self.add(XDW_AID_STAMP, position,
                nWidth=int(width * 100))

    def add_receivedstamp(self, position=_POSITION, width=_WIDTH):
        """Paste a received (datetime) stamp annotation."""
        return self.add(XDW_AID_RECEIVEDSTAMP, position,
                nWidth=int(width * 100))

    def add_custom(self, position=_POSITION,
                size=_SIZE, guid="???", data="???"):
        """Paste a custom specification annotation."""
        return self.add(XDW_AID_CUSTOM, position,
                nWidth=int(size.x * 100), nHeight=int(size.y * 100),
                lpszGuid=byref(guid),
                nCustomDataSize=len(data), pCustomData=byref(data))

    def add_marker(self, position=_POSITION, points=_POINTS):
        """Paste a marker annotation."""
        points = [p * 100 for p in points]  # Assuming isinstance(p, Point).
        return self.add(XDW_AID_MARKER, position,
                nCounts=len(points), pPoints=byref(points))

    def add_polygon(self, position=_POSITION, points=_POINTS):
        """Paste a polygon annotation."""
        points = [p * 100 for p in points]  # Assuming isinstance(p, Point).
        return self.add(XDW_AID_POLYGON, position,
                nCounts=len(points), pPoints=byref(points))

    def _delete(self, pos):
        """Abstract method as a stub for delete()."""
        raise NotImplementedError()

    def delete(self, pos):
        """Remove an annotation."""
        pos = self._pos(pos)
        ann = self.annotation(pos)
        self._delete(ann)
        self.detach(ann, EV_ANN_REMOVED)
        self.annotations -= 1

    def content_text(self, recursive=True):
        """Abstract method for concrete content_text()."""
        raise NotImplementedError()

    def annotation_text(self, recursive=True):
        """Get text in child/descendant annotations."""
        result = []
        for ann in self:
            result.append(ann.content_text())
            if ann.annotations and recursive:
                result.append(ann.annotation_text(recursive=True))
        return joinf(ASEP, result)

    def fulltext(self):
        """Get text in this object and all descendant annotations."""
        return  joinf(ASEP, [
                self.content_text(),
                self.annotation_text(recursive=True)])

    def find_annotations(self, handles=None, types=None, rect=None,
            half_open=True, recursive=False):
        """Find annotations on page or annotation by criteria.

        find_annotations(handles=None, types=None, rect=None, half_open=True,
                         recursive=False)
            handles     sequence of annotation handles.  None means all.
            types       sequence of types.  None means all.
            rect        Rect which includes annotations.
                        Note that right and bottom values are innermost of
                        outside unless half_open==False.  None means all.
            recursive   also return descendant (child) annotations.
        """
        if handles and not isinstance(handles, (tuple, list)):
            handles = list(handles)
        if types:
            if not isinstance(types, (list, tuple)):
                types = [types]
        if rect and not half_open:
            rect.right += 0.01  # minimal gap for xdwapi
            rect.bottom += 0.01  # minimal gap for xdwapi
        annotation_list = []
        for i in range(self.annotations):
            annotation = self.annotation(i)
            sublist = []
            if recursive and annotation.annotations:
                sublist = find_annotations(annotation,
                        handles=handles,
                        types=types,
                        rect=rect, half_open=half_open,
                        recursive=recursive)
            if (not rect or annotation.inside(rect)) and \
                    (not types or annotation.type in types) and \
                    (not handles or annotation.handle in handles):
                if sublist:
                    sublist.insert(0, annotation)
                    annotation_list.append(sublist)
                else:
                    annotation_list.append(annotation)
            elif sublist:
                sublist.insert(0, None)
                annotation_list.append(sublist)
        return annotation_list
