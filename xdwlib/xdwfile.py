#!/usr/bin/env python
#vim:fileencoding=cp932:fileformat=dos

"""xdwfile.py -- DocuWorks library for Python.

Copyright (C) 2010 HAYASI Hideki <linxs@linxs.org>  All rights reserved.

This software is subject to the provisions of the Zope Public License,
Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
FOR A PARTICULAR PURPOSE.
"""

import os
import datetime
import shutil
import atexit

from xdwapi import *
from common import *
from struct import Point
from timezone import *
from observer import Subject, Observer


__all__ = (
        "XDWFile", "PageForm", "AttachmentList", "Attachment",
        "StampSignature", "PKISignature",
        "xdwopen", "create_sfx", "extract_sfx", "optimize", "copy",
        "VALID_DOCUMENT_HANDLES", "close_all",
        )


# The last resort to close documents in interactive session.
try:
    VALID_DOCUMENT_HANDLES
except NameError:
    VALID_DOCUMENT_HANDLES = []


@atexit.register
def atexithandler():
    """Close all files and perform finalization before finishing process."""
    for handle in VALID_DOCUMENT_HANDLES:
        try:
            XDW_CloseDocumentHandle(handle)
        except:
            continue
        VALID_DOCUMENT_HANDLES.remove(handle)
    XDW_Finalize()


def xdwopen(path, readonly=False, authenticate=True):
    """General opener.  Returns Document or Binder object."""
    from document import Document
    from binder import Binder
    path = cp(path)
    XDW_TYPES = {".XDW": Document, ".XBD": Binder}
    ext = os.path.splitext(path)[1].upper()
    if ext not in XDW_TYPES:
        raise BadFormatError("extension must be .xdw or .xbd")
    return XDW_TYPES[ext](path, readonly=readonly, authenticate=authenticate)


def create_sfx(input_path, output_path=None):
    """Create self-extract executable file.

    Returns pathname of generated sfx executable file.
    """
    input_path, output_path = cp(input_path), cp(output_path)
    output_path = os.path.splitext(output_path or input_path)[0] + ".exe"
    XDW_CreateSfxDocument(input_path, output_path)
    return output_path


def extract_sfx(input_path, output_path=None):
    """Extract DocuWorks document/binder from self-extract executable file.

    Returns pathname of generated document/binder file.
    """
    input_path, output_path = cp(input_path), cp(output_path)
    root = os.path.splitext(output_path or input_path)[0]
    output_path = root + ".xdw"  # for now
    XDW_ExtractFromSfxDocument(input_path, output_path)
    # Created file can be either document or binder.  We have to examine
    # which type of file was generated and rename if needed.
    xdwfile = xdwopen(output_path, readonly=True)
    doctype = xdwfile.type
    xdwfile.close()
    if doctype == XDW_DT_BINDER:
        orig, output_path = output_path, root + ".xbd"
        os.rename(orig, output_path)
    return output_path


def optimize(input_path, output_path=None):
    """Optimize document/binder file.

    Returns pathname of optimized document/binder file.
    """
    input_path, output_path = cp(input_path), cp(output_path)
    output_path = derivative_path(output_path or input_path)
    XDW_OptimizeDocument(input_path, output_path)
    return output_path


def copy(input_path, output_path=None):
    """Copy DocuWorks document/binder to another one.

    Returns pathname of copied file.
    """
    input_path, output_path = cp(input_path), cp(output_path)
    output_path = derivative_path(output_path or input_path)
    shutil.copyfile(input_path, output_path)
    return output_path


def protection_info(path):
    """Get protection information on a document/binder.

    Returns (protect_type, permission) where:
    protect_type    "PSWD" | "PSWD128" | "PKI" | "STAMP" | "CONTEXT_SERVICE"
    permission      allowed operation(s); comma separated list of
                    "EDIT_DOCUMENT", "EDIT_ANNOTATION", "PRINT" and "COPY"
    """
    info = XDW_GetProtectionInformation(cp(path))
    protect_type = XDW_PROTECT[info.nProtectType]
    permission = flagvalue(XDW_PERM, info.nPermission, store=False)
    return (protect_type, permission)


def protect(input_path, output_path=None, protect_type="PASSWORD", auth="NONE", **options):
    """Generate protected document/binder.

    protect_type    "PASSWORD" | "PASSWORD128" | "PKI"
    auth            "NONE" | "NODIALOGUE" | "CONDITIONAL"

    **options for PSWD and PSWD128:
    permission      allowed operation(s); comma separated list of
                    "EDIT_DOCUMENT", "EDIT_ANNOTATION", "PRINT" and "COPY"
    password        str or None; password to open document/binder
    fullaccess      str or None; password to open document/binder with full-access privilege
    comment         str or None; notice in password dialogue

    **options for PKI:
    permission      allowed operation(s); comma separated list of
                    "EDIT_DOCUMENT", "EDIT_ANNOTATION", "PRINT" and "COPY"
    certificates    list of certificates in DER (RFC3280) formatted str
    fullaccesscerts list of certificates in DER (RFC3280) formatted str

    Returns pathname of protected file.
    """
    input_path, output_path = cp(input_path), cp(output_path)
    output_path = derivative_path(output_path or input_path)
    protect_option = XDW_PROTECT_OPTION()
    protect_option.nAuthMode = XDW_AUTH.normalize(auth)
    protect_type = XDW_PROTECT.normalize(protect_type)
    if protect_type in (XDW_PROTECT_PSWD, XDW_PROTECT_PSWD128):
        opt = XDW_SECURITY_OPTION_PSWD()
        opt.nPermission = flagvalue(XDW_PERM, options.get("permission"), store=True)
        opt.szOpenPswd = options.get("password") or ""
        opt.szFullAccessPswd = options.get("fullaccess") or ""
        opt.lpszComment = options.get("comment") or ""
    elif protect_type == XDW_PROTECT_PKI:
        opt = XDW_SECURITY_OPTION_PKI()
        opt.nPermission = flagvalue(XDW_PERM, options.get("permission"), store=True)
        certificates = options.get("certificates")
        if not certificates:
            raise ValueError("a list of certificate(s) is required")
        fullaccesscerts = options.get("fullacccesscerts")
        opt.nCertsNum = len(certificates) + len(fullaccesscerts)
        opt.nFullAccessCertsNum = len(fullaccesscerts)
        certs = fullaccesscerts + certificates
        ders = XDW_DER_CERTIFICATE() * opt.nCertsNum
        for i in range(opt.nCertsNum):
            ders[i].pCert = pointer(certs[i])
            ders[i].nCertSize = len(certs[i])
        opt.lpxdcCerts = byref(ders)
    elif protect_type in (XDW_PROTECT_STAMP, XDW_PROTECT_CONTEXT_SERVICE):
        raise NotImplementedError("currently STAMP and CONTEXT_SERVICE is not available")
    else:
        raise ValueError("protect_type must be PASSWORD, PASSWORD128 or PKI")
    try:
        XDW_ProtectDocument(input_path, output_path, protect_type, opt, protect_option)
    except ProtectModuleError as e:
        msg = XDW_SECURITY_PKI_ERROR[opt.nErrorStatus]
        if 0 <= opt.nFirstErrorCert:
            msg += " in cert[%d]" % opt.nFirstErrorCert
        raise ProtectModuleError(msg)
    return output_path


def unprotect(input_path, output_path=None, auth="NONE"):
    """Release protection on document/binder.

    auth            "NODIALOGUE" | "CONDITIONAL"

    Returns pathname of unprotected file.
    """
    input_path, output_path = cp(input_path), cp(output_path)
    output_path = derivative_path(output_path or input_path)
    if protection_info(input_path)[0] not in ("PKI", "STAMP"):
        raise ValueError("file is neither protected in PKI nor STAMP")
    auth = XDW_AUTH.normalize(auth)
    if auth not in (XDW_AUTH_NODIALOGUE, XDW_AUTH_CONDITIONAL_DIALOGUE):
        raise ValueError("auth must be NODIALOGUE or CONDITIONAL")
    opt = XDW_RELEASE_PROTECTION_OPTION()
    opt.nAuthMode = auth
    XDW_ReleaseProtectionOfDocument(input_path, output_path, opt)
    return output_path


class AttachmentList(Subject):

    """Collection of Attachments aka original data."""

    __type__ = "ATTACHMENTLIST"

    def __init__(self, doc, size=None):
        Subject.__init__(self)
        self.doc = doc
        if size:
            self.size = size
        else:
            doc_info = XDW_GetDocumentInformation(doc.handle)
            self.size = doc_info.nOriginalData

    def __len__(self):
        return self.size

    def __iter__(self):
        for pos in range(self.size):
            yield self.attachment(pos)

    def _pos(self, pos, append=False):
        append = 1 if append else 0
        if not (-self.size <= pos < self.size + append):
            raise IndexError(
                    "Attachment number must be in [{0}, {1}), {2} given".format(
                    -self.size, self.size + append, pos))
        if pos < 0:
            pos += self.size
        return pos

    def attachment(self, pos):
        """Get an attachment, aka original data."""
        pos = self._pos(pos)
        if pos not in self.observers:
            self.observers[pos] = Attachment(self.doc, pos)
        return self.observers[pos]

    def __getitem__(self, pos):
        return self.attachment(pos)

    def append(self, path):
        """Append an attachment, aka original data, at the end of XDW/XBD."""
        return self.insert(self.size, path)

    def insert(self, pos, path):
        """Insert an attachment, aka original data.

        pos     position to insert; starts with 0
        path    pathname of a file to insert
        """
        pos = self._pos(pos, append=True)
        XDW_InsertOriginalData(self.doc.handle, pos + 1, path)
        self.size += 1
        att = self.attachment(pos)
        self.attach(att, EV_ATT_INSERTED)

    def delete(self, pos):
        """Remove an attachment, aka original data."""
        pos = self._pos(pos)
        att = self.attachment(pos)
        XDW_DeleteOriginalData(self.doc.handle, pos + 1)
        self.detach(att, EV_ATT_REMOVED)
        self.size -= 1

    def __delitem__(self, pos):
        self.delete(pos)


class Attachment(Observer):

    """Place holder for attachments aka original data."""

    __type__ = "ATTACHMENT"

    def __init__(self, doc, pos):
        self.doc = doc
        self.pos = pos
        info, text_type = XDW_GetOriginalDataInformationW(doc.handle, pos + 1, codepage=CP)
        self.text_type = XDW_TEXT_TYPE[text_type]
        self.size = info.nDataSize
        self.datetime = datetime.datetime.fromtimestamp(info.nDate)
        self.name = info.szName

    def update(self, event):
        """Update self as an observer."""
        if not isinstance(event, Notification):
            raise TypeError("not an instance of Notification class")
        if event.type == EV_ATT_REMOVED:
            if event.para[0] < self.pos:
                self.pos -= 1
        elif event.type == EV_ATT_INSERTED:
            if event.para[0] < self.pos:
                self.pos += 1
        else:
            raise ValueError("Illegal event type: {0}".format(event.type))

    def save(self, path=None):
        """Save attached file.

        Returns pathname actually saved.
        """
        path = derivative_path(path or self.name)
        XDW_GetOriginalData(self.doc.handle, self.pos + 1, path)
        return path


class XDWFile(object):

    """Docuworks file, XDW or XBD."""

    @staticmethod
    def all_attributes():  # for debugging
        return [outer_attribute_name(k) for k in XDW_DOCUMENT_ATTRIBUTE_W]

    def register(self):
        VALID_DOCUMENT_HANDLES.append(self.handle)

    def free(self):
        VALID_DOCUMENT_HANDLES.remove(self.handle)

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
        path = cp(path)
        self.handle = XDW_OpenDocumentHandle(path, open_mode)
        self.register()
        self.dir, self.name = os.path.split(path)
        self.dir = unicode(self.dir, CODEPAGE)
        self.name = unicode(os.path.splitext(self.name)[0], CODEPAGE)
        # Set document properties.
        document_info = XDW_GetDocumentInformation(self.handle)
        self.pages = document_info.nPages
        self.version = document_info.nVersion - 3  # DocuWorks version
        self.attachments = AttachmentList(self, size=document_info.nOriginalData)
        self.type = XDW_DOCUMENT_TYPE[document_info.nDocType]
        self.editable = bool(document_info.nPermission & XDW_PERM_DOC_EDIT)
        self.annotatable = bool(document_info.nPermission & XDW_PERM_ANNO_EDIT)
        self.printable = bool(document_info.nPermission & XDW_PERM_PRINT)
        self.copyable = bool(document_info.nPermission & XDW_PERM_COPY)
        self.show_annotations = bool(document_info.nShowAnnotations)
        # Followings are effective only for binders.
        self.documents = document_info.nDocuments
        self.binder_color = XDW_BINDER_COLOR[document_info.nBinderColor]
        self.binder_size = XDW_BINDER_SIZE[document_info.nBinderSize]
        # Document attributes.
        self.attributes = XDW_GetDocumentAttributeNumber(self.handle)
        # Attached signatures.
        self.signatures = XDW_GetDocumentSignatureNumber(self.handle)

    def update_pages(self):
        """Update number of pages; used after insert multiple pages in."""
        document_info = XDW_GetDocumentInformation(self.handle)
        self.pages = document_info.nPages

    def save(self):
        """Save document regardless of whether it is modified or not."""
        XDW_SaveDocument(self.handle)

    def close(self):
        """Close document."""
        XDW_CloseDocumentHandle(self.handle)
        self.free()

    def __getattr__(self, name):
        if isinstance(name, int):
            name, t, value = XDW_GetDocumentAttributeByOrder(self.handle, name)
            return (name, makevalue(t, value))
        attribute_name = unicode(inner_attribute_name(name))
        try:
            return XDW_GetDocumentAttributeByNameW(
                    self.handle, attribute_name, codepage=CP)[1]
        except InvalidArgError as e:
            pass
        return self.__dict__[name]

    def __setattr__(self, name, value):
        if name == "show_annotations":
            XDW_ShowOrHideAnnotations(self.handle, bool(value))
            return
        attribute_name = unicode(inner_attribute_name(name))
        if isinstance(value, basestring):
            attribute_type = XDW_ATYPE_STRING
        elif isinstance(value, bool):
            attribute_type = XDW_ATYPE_BOOL
        elif isinstance(value, datetime.datetime):
            attribute_type = XDW_ATYPE_DATE
            if not value.tzinfo:
                value = value.replace(tzinfo=DEFAULT_TZ)  # TODO: Care locale.
            value = unixtime(value)
        else:
            attribute_type = XDW_ATYPE_INT  # TODO: Scaling may be required.
        # TODO: XDW_ATYPE_OTHER should also be valid.
        if attribute_name in XDW_DOCUMENT_ATTRIBUTE_W:
            XDW_SetDocumentAttributeW(
                    self.handle, attribute_name, attribute_type, value,
                    XDW_TEXT_MULTIBYTE, codepage=CP)
            return
        self.__dict__[name] = value

    def get_userattr(self, name):
        """Get user defined attribute."""
        if isinstance(name, unicode):
            name = name.encode(CODEPAGE)
        return XDW_GetUserAttribute(self.handle, name)

    def set_userattr(self, name, value):
        """Set user defined attribute."""
        if isinstance(name, unicode):
            name = name.encode(CODEPAGE)
        XDW_SetUserAttribute(self.handle, name, value)

    def get_property(self, name):
        """Get user defined property."""
        if isinstance(name, str):
            name = name.decode(CODEPAGE)
        return XDW_GetDocumentAttributeByNameW(self.handle, name, codepage=CP)[1]

    def set_property(self, name, value):
        """Set user defined property."""
        if isinstance(name, str):
            name = name.decode(CODEPAGE)
        if isinstance(value, str):
            value = value.decode(CODEPAGE)
        t, value = typevalue(value)
        XDW_SetDocumentAttributeW(self.handle, name, t, value, XDW_TEXT_MULTIBYTE, codepage=CP)

    getprop = get_property
    setprop = set_property

    def pageform(self, form):
        return PageForm(self, form)

    def pageform_text(self):
        """Get all text in page form."""
        return ASEP.join(self.pageform(form).text
                for form in ("header", "footer"))

    def signature(self, pos):
        """Get signature information.

        Returns StampSignature or PKISignature object.
        """
        siginfo, modinfo = XDW_GetSignatureInformation(self.handle, pos + 1)
        is_stamp = (siginfo.nSignatureType == XDW_SIGNATURE_STAMP)
        sig = (StampSignature if is_stamp else PKISignature)(
                self,
                siginfo.nPage - 1,
                Point(siginfo.nHorPos, siginfo.nVerPos) / 100.0,
                Point(siginfo.nWidth, siginfo.nHeight) / 100.0,
                fromunixtime(siginfo.nSignedTime),
                )
        if is_stamp:
            sig.stamp_name = modinfo.lpszStampName
            sig.owner_name = modinfo.lpszOwnerName
            sig.valid_until = fromunixtime(modinfo.nValidDate)
            sig.memo = modinfo.lpszRemarks
            sig.document_status = XDW_SIGNATURE_STAMP_DOC[modinfo.nDocVerificationStatus]
            sig.stamp_status = XDW_SIGNATURE_STAMP_STAMP[modinfo.nStampVerificationStatus]
        else:
            def parsedt(s):
                return datetime.datetime.strptime(s, "%Y/%m/%d %H:%M:%S")
            sig.module = modinfo.lpszModule
            sig.subject_dn = modinfo.lpszSubjectDN
            sig.subject = modinfo.lpszSubject
            sig.issuer_dn = modinfo.lpszIssuerDN
            sig.issuer = modinfo.lpszIssuer
            sig.not_before = parsedt(modinfo.lpszNotBefore)
            sig.not_after = parsedt(modinfo.lpszNotAfter)
            sig.serial = modinfo.lpszSerial
            sig.signer_cert = modinfo.signer_cert
            sig.memo = modinfo.lpszRemarks
            sig.signing_time = parsedt(modinfo.lpszSigningTime)
            sig.document_status = XDW_SIGNATURE_PKI_DOC[modinfo.nDocVerificationStatus]
            sig.cert_type = XDW_SIGNATURE_PKI_TYPE[modinfo.nCertVerificationType]
            sig.cert_status = XDW_SIGNATURE_PKI_CERT[modinfo.nCertVerificationStatus]
        return sig


class BaseSignature(object):

    def __init__(self, xdwfile, page, position, size, dt):
        self.xdwfile = xdwfile
        self.page = page
        self.position = position
        self.size = size
        self.dt = dt
        self.type = "UNKNOWN"  # Override this in subclasses.

    def __repr__(self):
        return  "{0}({1}[{2}]{3};{4})".format(
                self.__class__.__name__,
                self.xdwfile,
                self.page,
                self.position,
                self.type,
                )


class StampSignature(BaseSignature):

    def __init__(self, xdwfile, page, position, size, dt,
            stamp_name="",
            owner_name="",
            valid_until=None,
            memo="",
            ):
        Signature.__init__(self, xdwfile, page, position, size, dt)
        self.type = "STAMP"
        self.stamp_name = stamp_name
        self.owner_name = owner_name
        self.valid_until = valid_until
        self.memo = memo


class PKISignature(BaseSignature):

    def __init__(self, xdwfile, page, position, size, dt,
            module="",
            subjectdn="",
            subject="",
            issuerdn="",
            issuer="",
            not_before=None,
            not_after=None,
            serial=None,
            signer_cert=None,
            memo="",
            signing_time=None,
            ):
        Signature.__init__(self, xdwfile, page, position, size, dt)
        self.type = "PKI"
        self.module = module
        self.subjectdn = subjectdn  # max. 511 bytes
        self.subject = subject  # CN, OU, O or E
        self.issuerdn = issuerdn  # max. 511 bytes
        self.issuer = issuer  # CN, OU, O or E
        self.not_before = not_before
        self.not_after = not_after
        self.serial = serial
        self.signer_cert = signer_cert
        self.memo = memo
        self.signing_time = signing_time


class PageForm(object):

    def __init__(self, xdwfile, form):
        self.xdwfile = xdwfile
        self.form = XDW_PAGEFORM.normalize(inner_attribute_name(form))

    def __setattr__(self, name, value):
        attrname = inner_attribute_name(name)
        if name == "xdwfile":
            self.__dict__[name] = value
            return
        elif name == "form":
            self.__dict__[name] = XDW_PAGEFORM.normalize(value)
            return
        special = isinstance(XDW_ANNOTATION_ATTRIBUTE[attrname][1], XDWConst)
        if special or isinstance(value, (int, float)):
            value = int(scale(attrname, value, store=True))
            value = byref(c_int(value))
            attribute_type = XDW_ATYPE_INT  # TODO: Scaling may be required.
        elif isinstance(value, basestring):
            attribute_type = XDW_ATYPE_STRING
            """TODO: unicode handling.
            Currently Author has no idea to take unicode with ord < 256.
            Python's unicode may have inner representation with 0x00,
            eg.  0x41 0x00 0x42 0x00 0x43 0x00 for "ABC".  This results in
            unexpected string termination eg. "ABC" -> "A".  So, if the next
            if-block is not placed, you will get much more but inexact
            elements in result for abbreviated search string.
            """
            if isinstance(value, unicode):
                value = value.encode(CODEPAGE)  # TODO: how can we take all unicodes?
            if 255 < len(value):
                raise ValueError("text length must be <= 255")
        # TODO: XDW_ATYPE_OTHER should also be valid.
        else:
            raise TypeError("illegal value " + repr(value))
        XDW_SetPageFormAttribute(
                self.__dict__["xdwfile"].handle,
                self.__dict__["form"],
                attrname, attribute_type, value)

    def __getattr__(self, name):
        if name in ("xdwfile", "form"):
            return self.__dict__[name]
        attrname = inner_attribute_name(name)
        value = XDW_GetPageFormAttribute(
                self.__dict__["xdwfile"].handle,
                self.__dict__["form"], attrname)
        attribute_type = XDW_ANNOTATION_ATTRIBUTE[attrname][0]
        if attribute_type == 1:  # string
            return unicode(value, CODEPAGE)
        value = unpack(value)
        return scale(attrname, value, store=False)

    def update(self, sync=False):
        """Update page form.

        sync    (bool) also update pageforms for documents in binder
        """
        sync = XDW_PAGEFORM_REMOVE if sync else XDW_PAGEFORM_STAY
        XDW_UpdatePageForm(self.xdwfile.handle, sync)

    def delete(self, sync=False):
        """Delete page form.

        sync    (bool) also delete pageforms for documents in binder
        """
        sync = XDW_PAGEFORM_REMOVE if sync else XDW_PAGEFORM_STAY
        XDW_RemovePageForm(self.xdwfile.handle, sync)
