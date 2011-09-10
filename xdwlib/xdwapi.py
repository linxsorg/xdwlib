#!/usr/bin/env python
#vim:fileencoding=cp932:fileformat=dos

"""xdwapi.py -- DocuWorks API

Copyright (C) 2010 HAYASI Hideki <linxs@linxs.org>  All rights reserved.

This software is subject to the provisions of the Zope Public License,
Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
FOR A PARTICULAR PURPOSE.
"""


from ctypes import *


######################################################################
### ERROR DEFINITIONS ################################################


def _uint32(n):
    return (n + 0x100000000) & 0xffffffff


def _int32(n):
    return n - 0x100000000 if 0x80000000 <= n else n


XDW_E_NOT_INSTALLED                 = _int32(0x80040001)
XDW_E_INFO_NOT_FOUND                = _int32(0x80040002)
XDW_E_INSUFFICIENT_BUFFER           = _int32(0x8007007A)
XDW_E_FILE_NOT_FOUND                = _int32(0x80070002)
XDW_E_FILE_EXISTS                   = _int32(0x80070050)
XDW_E_ACCESSDENIED                  = _int32(0x80070005)
XDW_E_BAD_FORMAT                    = _int32(0x8007000B)
XDW_E_OUTOFMEMORY                   = _int32(0x8007000E)
XDW_E_WRITE_FAULT                   = _int32(0x8007001D)
XDW_E_SHARING_VIOLATION             = _int32(0x80070020)
XDW_E_DISK_FULL                     = _int32(0x80070027)
XDW_E_INVALIDARG                    = _int32(0x80070057)
XDW_E_INVALID_NAME                  = _int32(0x8007007B)
XDW_E_INVALID_ACCESS                = _int32(0x80040003)
XDW_E_INVALID_OPERATION             = _int32(0x80040004)
XDW_E_NEWFORMAT                     = _int32(0x800E0004)
XDW_E_BAD_NETPATH                   = _int32(0x800E0005)
XDW_E_APPLICATION_FAILED            = _int32(0x80001156)
XDW_E_SIGNATURE_MODULE              = _int32(0x800E0010)
XDW_E_PROTECT_MODULE                = _int32(0x800E0012)
XDW_E_UNEXPECTED                    = _int32(0x8000FFFF)
XDW_E_CANCELED                      = _int32(0x80040005)
XDW_E_ANNOTATION_NOT_ACCEPTED       = _int32(0x80040006)

XDW_ERROR_MESSAGES = {
        XDW_E_NOT_INSTALLED         : "XDW_E_NOT_INSTALLED",
        XDW_E_INFO_NOT_FOUND        : "XDW_E_INFO_NOT_FOUND",
        XDW_E_INSUFFICIENT_BUFFER   : "XDW_E_INSUFFICIENT_BUFFER",
        XDW_E_FILE_NOT_FOUND        : "XDW_E_FILE_NOT_FOUND",
        XDW_E_FILE_EXISTS           : "XDW_E_FILE_EXISTS",
        XDW_E_ACCESSDENIED          : "XDW_E_ACCESSDENIED",
        XDW_E_BAD_FORMAT            : "XDW_E_BAD_FORMAT",
        XDW_E_OUTOFMEMORY           : "XDW_E_OUTOFMEMORY",
        XDW_E_WRITE_FAULT           : "XDW_E_WRITE_FAULT",
        XDW_E_SHARING_VIOLATION     : "XDW_E_SHARING_VIOLATION",
        XDW_E_DISK_FULL             : "XDW_E_DISK_FULL",
        XDW_E_INVALIDARG            : "XDW_E_INVALIDARG",
        XDW_E_INVALID_NAME          : "XDW_E_INVALID_NAME",
        XDW_E_INVALID_ACCESS        : "XDW_E_INVALID_ACCESS",
        XDW_E_INVALID_OPERATION     : "XDW_E_INVALID_OPERATION",
        XDW_E_NEWFORMAT             : "XDW_E_NEWFORMAT",
        XDW_E_BAD_NETPATH           : "XDW_E_BAD_NETPATH",
        XDW_E_APPLICATION_FAILED    : "XDW_E_APPLICATION_FAILED",
        XDW_E_SIGNATURE_MODULE      : "XDW_E_SIGNATURE_MODULE",
        XDW_E_PROTECT_MODULE        : "XDW_E_PROTECT_MODULE",
        XDW_E_UNEXPECTED            : "XDW_E_UNEXPECTED",
        XDW_E_CANCELED              : "XDW_E_CANCELED",
        XDW_E_ANNOTATION_NOT_ACCEPTED   : "XDW_E_ANNOTATION_NOT_ACCEPTED",
        }


class XDWError(Exception):

    def __init__(self, error_code):
        self.error_code = error_code
        msg = XDW_ERROR_MESSAGES.get(error_code, "XDW_E_UNDEFINED")
        Exception.__init__(self, "%s (%08X)" % (msg, _uint32(error_code)))


######################################################################
### CONSTANTS ########################################################

NULL = None

ANSI_CHARSET = 0
DEFAULT_CHARSET = 1
MAC_CHARSET = 77
OEM_CHARSET = 255
SHIFTJIS_CHARSET = 128
SYMBOL_CHARSET = 2


class XDWConst(dict):

    def __init__(self, constants, default=None):
        dict.__init__(self, constants)
        self.constants = constants
        self.reverse = dict([(v, k) for (k, v) in constants.items()])
        self.default = default

    def inner(self, value):
        return self.reverse.get(str(value).upper(), self.default)

    def normalize(self, key_or_value):
        if isinstance(key_or_value, basestring):
            return self.inner(key_or_value)
        return key_or_value


### Environment

XDW_GI_VERSION                      =  1
XDW_GI_INSTALLPATH                  =  2
XDW_GI_BINPATH                      =  3
XDW_GI_PLUGINPATH                   =  4
XDW_GI_FOLDERROOTPATH               =  5
XDW_GI_USERFOLDERPATH               =  6
XDW_GI_SYSTEMFOLDERPATH             =  7
XDW_GI_RECEIVEFOLDERPATH            =  8
XDW_GI_SENDFOLDERPATH               =  9
XDW_GI_DWINPUTPATH                  = 10
XDW_GI_DWDESKPATH                   = 11
XDW_GI_DWVIEWERPATH                 = 12
XDW_GI_DWVLTPATH                    = 13
XDW_GI_DWDESK_FILENAME_DELIMITER    = 1001
XDW_GI_DWDESK_FILENAME_DIGITS       = 1002

XDW_ENVIRON = XDWConst({
        XDW_GI_VERSION                  : "VERSION",
        XDW_GI_INSTALLPATH              : "INSTALLPATH",
        XDW_GI_BINPATH                  : "BINPATH",
        XDW_GI_PLUGINPATH               : "PLUGINPATH",
        XDW_GI_FOLDERROOTPATH           : "FOLDERROOTPATH",
        XDW_GI_USERFOLDERPATH           : "USERFOLDERPATH",
        XDW_GI_SYSTEMFOLDERPATH         : "SYSTEMFOLDERPATH",
        XDW_GI_RECEIVEFOLDERPATH        : "RECEIVEFOLDERPATH",
        XDW_GI_SENDFOLDERPATH           : "SENDFOLDERPATH",
        XDW_GI_DWINPUTPATH              : "DWINPUTPATH",
        XDW_GI_DWDESKPATH               : "DWDESKPATH",
        XDW_GI_DWVIEWERPATH             : "DWVIEWERPATH",
        XDW_GI_DWVLTPATH                : "DWVLTPATH",
        XDW_GI_DWDESK_FILENAME_DELIMITER: "DWDESK_FILENAME_DELIMITER",
        XDW_GI_DWDESK_FILENAME_DIGITS   : "DWDESK_FILENAME_DIGITS",
        })

XDW_MAXPATH                         = 255
XDW_MAXINPUTIMAGEPATH               = 127

### Common

XDW_COMPRESS_NORMAL                 = 0
XDW_COMPRESS_LOSSLESS               = 1
XDW_COMPRESS_HIGHQUALITY            = 2
XDW_COMPRESS_HIGHCOMPRESS           = 3
XDW_COMPRESS_NOCOMPRESS             = 4
XDW_COMPRESS_JPEG                   = 5
XDW_COMPRESS_PACKBITS               = 6
XDW_COMPRESS_G4                     = 7
XDW_COMPRESS_MRC_NORMAL             = 8
XDW_COMPRESS_MRC_HIGHQUALITY        = 9
XDW_COMPRESS_MRC_HIGHCOMPRESS       = 10
XDW_COMPRESS_MRC                    = 11
XDW_COMPRESS_JPEG_TTN2              = 12

XDW_CONVERT_MRC_ORIGINAL            = 0
XDW_CONVERT_MRC_OS                  = 1

XDW_IMAGE_DIB                       = 0
XDW_IMAGE_TIFF                      = 1
XDW_IMAGE_JPEG                      = 2
XDW_IMAGE_PDF                       = 3

XDW_TEXT_UNKNOWN                    = 0
XDW_TEXT_MULTIBYTE                  = 1
XDW_TEXT_UNICODE                    = 2
XDW_TEXT_UNICODE_IFNECESSARY        = 3

XDW_TEXT_TYPE = XDWConst({
        XDW_TEXT_UNKNOWN            : "UNKNOWN",
        XDW_TEXT_MULTIBYTE          : "MULTIBYTE",
        XDW_TEXT_UNICODE            : "UNICODE",
        }, default=XDW_TEXT_UNKNOWN)

### Document/Binder related

XDW_DT_DOCUMENT                     = 0
XDW_DT_BINDER                       = 1

# open/create

XDW_OPEN_READONLY                   = 0
XDW_OPEN_UPDATE                     = 1

XDW_AUTH_NONE                       = 0
XDW_AUTH_NODIALOGUE                 = 1
XDW_AUTH_CONDITIONAL_DIALOGUE       = 2

XDW_PERM_DOC_EDIT                   = 0x02
XDW_PERM_ANNO_EDIT                  = 0x04
XDW_PERM_PRINT                      = 0x08
XDW_PERM_COPY                       = 0x10

XDW_CREATE_FITDEF                   = 0
XDW_CREATE_FIT                      = 1
XDW_CREATE_USERDEF                  = 2
XDW_CREATE_USERDEF_FIT              = 3
XDW_CREATE_FITDEF_DIVIDEBMP         = 4

XDW_CREATE_HCENTER                  = 0
XDW_CREATE_LEFT                     = 1
XDW_CREATE_RIGHT                    = 2

XDW_CREATE_VCENTER                  = 0
XDW_CREATE_TOP                      = 1
XDW_CREATE_BOTTOM                   = 2

XDW_CREATE_DEFAULT_SIZE             = 0
XDW_CREATE_A3_SIZE                  = 1
XDW_CREATE_2A0_SIZE                 = 2

XDW_CRTP_BEGINNING                  = 1
XDW_CRTP_PRINTING                   = 2
XDW_CRTP_PAGE_CREATING              = 3
XDW_CRTP_ORIGINAL_APPENDING         = 4
XDW_CRTP_WRITING                    = 5
XDW_CRTP_ENDING                     = 6
XDW_CRTP_CANCELING                  = 7
XDW_CRTP_FINISHED                   = 8
XDW_CRTP_CANCELED                   = 9

# size

XDW_SIZE_FREE                       = 0
XDW_SIZE_A3_PORTRAIT                = 1
XDW_SIZE_A3_LANDSCAPE               = 2
XDW_SIZE_A4_PORTRAIT                = 3
XDW_SIZE_A4_LANDSCAPE               = 4
XDW_SIZE_A5_PORTRAIT                = 5
XDW_SIZE_A5_LANDSCAPE               = 6
XDW_SIZE_B4_PORTRAIT                = 7
XDW_SIZE_B4_LANDSCAPE               = 8
XDW_SIZE_B5_PORTRAIT                = 9
XDW_SIZE_B5_LANDSCAPE               = 10

# binder color

XDW_BINDER_COLOR_0                  = 0
XDW_BINDER_COLOR_1                  = 1
XDW_BINDER_COLOR_2                  = 2
XDW_BINDER_COLOR_3                  = 3
XDW_BINDER_COLOR_4                  = 4
XDW_BINDER_COLOR_5                  = 5
XDW_BINDER_COLOR_6                  = 6
XDW_BINDER_COLOR_7                  = 7
XDW_BINDER_COLOR_8                  = 8
XDW_BINDER_COLOR_9                  = 9
XDW_BINDER_COLOR_10                 = 10
XDW_BINDER_COLOR_11                 = 11
XDW_BINDER_COLOR_12                 = 12
XDW_BINDER_COLOR_13                 = 13
XDW_BINDER_COLOR_14                 = 14
XDW_BINDER_COLOR_15                 = 15

# succession

XDW_SUMMARY_INFO                    = 1
XDW_USER_DEF                        = 2
XDW_ANNOTATION                      = 4

# protection

XDW_PROTECT_PSWD                    = 1
XDW_PROTECT_PSWD128                 = 3
XDW_PROTECT_PKI                     = 4
XDW_PROTECT_STAMP                   = 5
XDW_PROTECT_CONTEXT_SERVICE         = 6

# signature

XDW_SIGNATURE_STAMP                                     = 100
XDW_SIGNATURE_PKI                                       = 102

XDW_SIGNATURE_STAMP_DOC_NONE                            = 0
XDW_SIGNATURE_STAMP_DOC_NOEDIT                          = 1
XDW_SIGNATURE_STAMP_DOC_EDIT                            = 2
XDW_SIGNATURE_STAMP_DOC_BAD                             = 3

XDW_SIGNATURE_STAMP_STAMP_NONE                          = 0
XDW_SIGNATURE_STAMP_STAMP_TRUSTED                       = 1
XDW_SIGNATURE_STAMP_STAMP_NOTRUST                       = 2

XDW_SIGNATURE_STAMP_ERROR_OK                            = 0
XDW_SIGNATURE_STAMP_ERROR_NO_OPENING_CASE               = 1
XDW_SIGNATURE_STAMP_ERROR_NO_SELFSTAMP                  = 2
XDW_SIGNATURE_STAMP_ERROR_OUT_OF_VALIDITY               = 3
XDW_SIGNATURE_STAMP_ERROR_INVALID_DATA                  = 4
XDW_SIGNATURE_STAMP_ERROR_OUT_OF_MEMORY                 = 100
XDW_SIGNATURE_STAMP_ERROR_UNKNOWN                       = 9999

XDW_SIGNATURE_PKI_DOC_UNKNOWN                           = 0
XDW_SIGNATURE_PKI_DOC_GOOD                              = 1
XDW_SIGNATURE_PKI_DOC_MODIFIED                          = 2
XDW_SIGNATURE_PKI_DOC_BAD                               = 3
XDW_SIGNATURE_PKI_DOC_GOOD_TRUSTED                      = 4
XDW_SIGNATURE_PKI_DOC_MODIFIED_TRUSTED                  = 5

XDW_SIGNATURE_PKI_TYPE_LOW                              = 0
XDW_SIGNATURE_PKI_TYPE_MID_LOCAL                        = 1
XDW_SIGNATURE_PKI_TYPE_MID_NETWORK                      = 2
XDW_SIGNATURE_PKI_TYPE_HIGH_LOCAL                       = 3
XDW_SIGNATURE_PKI_TYPE_HIGH_NETWORK                     = 4

XDW_SIGNATURE_PKI_CERT_UNKNOWN                          = 0
XDW_SIGNATURE_PKI_CERT_OK                               = 1
XDW_SIGNATURE_PKI_CERT_NO_ROOT_CERTIFICATE              = 2
XDW_SIGNATURE_PKI_CERT_NO_REVOCATION_CHECK              = 3
XDW_SIGNATURE_PKI_CERT_OUT_OF_VALIDITY                  = 4
XDW_SIGNATURE_PKI_CERT_OUT_OF_VALIDITY_AT_SIGNED_TIME   = 5
XDW_SIGNATURE_PKI_CERT_REVOKE_CERTIFICATE               = 6
XDW_SIGNATURE_PKI_CERT_REVOKE_INTERMEDIATE_CERTIFICATE  = 7
XDW_SIGNATURE_PKI_CERT_INVALID_SIGNATURE                = 8
XDW_SIGNATURE_PKI_CERT_INVALID_USAGE                    = 9
XDW_SIGNATURE_PKI_CERT_UNDEFINED_ERROR                  = 10

XDW_SIGNATURE_PKI_ERROR_UNKNOWN                         = 0
XDW_SIGNATURE_PKI_ERROR_OK                              = 1
XDW_SIGNATURE_PKI_ERROR_BAD_PLATFORM                    = 2
XDW_SIGNATURE_PKI_ERROR_WRITE_REG_ERROR                 = 3
XDW_SIGNATURE_PKI_ERROR_BAD_TRUST_LEVEL                 = 4
XDW_SIGNATURE_PKI_ERROR_BAD_REVOKE_CHECK_TYPE           = 5
XDW_SIGNATURE_PKI_ERROR_BAD_AUTO_IMPORT_CERT_FLAG       = 6
XDW_SIGNATURE_PKI_ERROR_BAD_SIGN_CONFIG                 = 7
XDW_SIGNATURE_PKI_ERROR_NO_IMAGE_FILE                   = 8
XDW_SIGNATURE_PKI_ERROR_BAD_SIGN_CERT                   = 9
XDW_SIGNATURE_PKI_ERROR_NO_SIGN_CERT                    = 10
XDW_SIGNATURE_PKI_ERROR_NOT_USE_PRIVATE_KEY             = 11
XDW_SIGNATURE_PKI_ERROR_INVALID                         = 12
XDW_SIGNATURE_PKI_ERROR_BAD_SIGN                        = 13
XDW_SIGNATURE_PKI_ERROR_REVOKE_CHECK_ERROR              = 14
XDW_SIGNATURE_PKI_ERROR_OUT_OF_VALIDITY                 = 15
XDW_SIGNATURE_PKI_ERROR_NO_CERT                         = 16
XDW_SIGNATURE_PKI_ERROR_FAILURE_IMPOPT_CERT             = 17
XDW_SIGNATURE_PKI_ERROR_NO_ROOT_CERT                    = 18
XDW_SIGNATURE_PKI_ERROR_BAD_CERT_SIZE                   = 19
XDW_SIGNATURE_PKI_ERROR_BAD_ARG                         = 20
XDW_SIGNATURE_PKI_ERROR_BAD_CERT_FORMAT                 = 21

XDW_SECURITY_PKI_ERROR_UNKNOWN                          = 0
XDW_SECURITY_PKI_ERROR_OK                               = 1
XDW_SECURITY_PKI_ERROR_BAD_PLATFORM                     = 2
XDW_SECURITY_PKI_ERROR_WRITE_REG_ERROR                  = 3
XDW_SECURITY_PKI_ERROR_BAD_TRUST_LEVEL                  = 4
XDW_SECURITY_PKI_ERROR_BAD_REVOKE_CHECK_TYPE            = 5
XDW_SECURITY_PKI_ERROR_REVOKED                          = 6
XDW_SECURITY_PKI_ERROR_BAD_SIGN                         = 7
XDW_SECURITY_PKI_ERROR_REVOKE_CHECK_ERROR               = 8
XDW_SECURITY_PKI_ERROR_OUT_OF_VALIDITY                  = 9
XDW_SECURITY_PKI_ERROR_NO_CERT                          = 10
XDW_SECURITY_PKI_ERROR_FAILURE_IMPORT_CERT              = 11
XDW_SECURITY_PKI_ERROR_NO_ROOT_CERT                     = 12
XDW_SECURITY_PKI_ERROR_BAD_CERT_FORMAT                  = 13
XDW_SECURITY_PKI_ERROR_BAD_CERT_USAGE                   = 14
XDW_SECURITY_PKI_ERROR_CA_CERT_IS_REVOKED               = 15
XDW_SECURITY_PKI_ERROR_TOO_MANY_CERT                    = 16

XDW_DOCUMENT_TYPE = XDWConst({
        XDW_DT_DOCUMENT             : "DOCUMENT",
        XDW_DT_BINDER               : "BINDER",
        }, default=XDW_DT_DOCUMENT)

XDW_PROP_TITLE                      = "%Title"
XDW_PROP_SUBJECT                    = "%Subject"
XDW_PROP_AUTHOR                     = "%Author"
XDW_PROP_KEYWORDS                   = "%Keywords"
XDW_PROP_COMMENTS                   = "%Comments"

XDW_DOCUMENT_ATTRIBUTE = XDWConst({
        XDW_PROP_TITLE:             "%Title",
        XDW_PROP_SUBJECT:           "%Subject",
        XDW_PROP_AUTHOR:            "%Author",
        XDW_PROP_KEYWORDS:          "%Keywords",
        XDW_PROP_COMMENTS:          "%Comments",
        }, default=None)

XDW_PROPW_TITLE                     = u"%Title"
XDW_PROPW_SUBJECT                   = u"%Subject"
XDW_PROPW_AUTHOR                    = u"%Author"
XDW_PROPW_KEYWORDS                  = u"%Keywords"
XDW_PROPW_COMMENTS                  = u"%Comments"

XDW_DOCUMENT_ATTRIBUTE_W = XDWConst({
        XDW_PROPW_TITLE:            u"%Title",
        XDW_PROPW_SUBJECT:          u"%Subject",
        XDW_PROPW_AUTHOR:           u"%Author",
        XDW_PROPW_KEYWORDS:         u"%Keywords",
        XDW_PROPW_COMMENTS:         u"%Comments",
        }, default=None)

XDW_BINDER_SIZE = XDWConst({
        XDW_SIZE_FREE               : "FREE",
        XDW_SIZE_A3_PORTRAIT        : "A3R",
        XDW_SIZE_A3_LANDSCAPE       : "A3",
        XDW_SIZE_A4_PORTRAIT        : "A4R",
        XDW_SIZE_A4_LANDSCAPE       : "A4",
        XDW_SIZE_A5_PORTRAIT        : "A5R",
        XDW_SIZE_A5_LANDSCAPE       : "A5",
        XDW_SIZE_B4_PORTRAIT        : "B4R",
        XDW_SIZE_B4_LANDSCAPE       : "B4",
        XDW_SIZE_B5_PORTRAIT        : "B5R",
        XDW_SIZE_B5_LANDSCAPE       : "B5",
        }, default=XDW_SIZE_FREE)

XDW_BINDER_COLOR = XDWConst({
        # Here we describe colors in RRGGBB format, though DocuWorks
        # inner color representation is BBGGRR.
        XDW_BINDER_COLOR_0          : "003366",   # neutral navy (kon)
        XDW_BINDER_COLOR_1          : "006633",   # neutral green
        XDW_BINDER_COLOR_2          : "3366FF",   # neutral bule
        XDW_BINDER_COLOR_3          : "FFFF66",   # neutral yellow
        XDW_BINDER_COLOR_4          : "FF6633",   # neutral orange
        XDW_BINDER_COLOR_5          : "FF3366",   # neutral red
        XDW_BINDER_COLOR_6          : "FF00FF",   # fuchsia (akamurasaki)
        XDW_BINDER_COLOR_7          : "FFCCFF",   # neutral pink
        XDW_BINDER_COLOR_8          : "CC99FF",   # neutral purple
        XDW_BINDER_COLOR_9          : "663333",   # neutral brown
        XDW_BINDER_COLOR_10         : "999933",   # neutral olive
        XDW_BINDER_COLOR_11         : "00FF00",   # lime (kimidori)
        XDW_BINDER_COLOR_12         : "00FFFF",   # aqua (mizuiro)
        XDW_BINDER_COLOR_13         : "FFFFCC",   # neutral lightyellow (cream)
        XDW_BINDER_COLOR_14         : "BBBBBB",   # neutral silver
        XDW_BINDER_COLOR_15         : "FFFFFF",   # white
        }, default=XDW_BINDER_COLOR_5)

### Page related

XDW_GPTI_TYPE_EMF                   = 0
XDW_GPTI_TYPE_OCRTEXT               = 1

XDW_IMAGE_MONO                      = 0
XDW_IMAGE_COLOR                     = 1
XDW_IMAGE_MONO_HIGHQUALITY          = 2

# rotation

XDW_ROT_0                           = 0
XDW_ROT_90                          = 90
XDW_ROT_180                         = 180
XDW_ROT_270                         = 270

# OCR

XDW_REDUCENOISE_NONE                            = 0
XDW_REDUCENOISE_NORMAL                          = 1
XDW_REDUCENOISE_WEAK                            = 2
XDW_REDUCENOISE_STRONG                          = 3

XDW_OCR_NOISEREDUCTION = XDWConst({
        XDW_REDUCENOISE_NONE                    : "NONE",
        XDW_REDUCENOISE_NORMAL                  : "NORMAL",
        XDW_REDUCENOISE_WEAK                    : "WEAK",
        XDW_REDUCENOISE_STRONG                  : "STRONG",
        }, default=XDW_REDUCENOISE_NONE)

XDW_PRIORITY_NONE                               = 0
XDW_PRIORITY_SPEED                              = 1
XDW_PRIORITY_RECOGNITION                        = 2

XDW_OCR_PREPROCESSING = XDWConst({
        XDW_PRIORITY_NONE                       : "NONE",
        XDW_PRIORITY_SPEED                      : "SPEED",
        XDW_PRIORITY_RECOGNITION                : "ACCURACY",
        })

XDW_OCR_ENGINE_V4                               = 1  # for = compatibility
XDW_OCR_ENGINE_DEFAULT                          = 1
XDW_OCR_ENGINE_WRP                              = 2
XDW_OCR_ENGINE_FRE                              = 3

XDW_OCR_ENGINE = XDWConst({
        XDW_OCR_ENGINE_DEFAULT                  : "DEFAULT",
        XDW_OCR_ENGINE_WRP                      : "WINREADER PRO",
        })

XDW_OCR_LANGUAGE_AUTO                           = -1
XDW_OCR_LANGUAGE_JAPANESE                       = 0
XDW_OCR_LANGUAGE_ENGLISH                        = 1

XDW_OCR_LANGUAGE = XDWConst({
        XDW_OCR_LANGUAGE_AUTO                   : "AUTO",
        XDW_OCR_LANGUAGE_JAPANESE               : "JAPANESE",
        XDW_OCR_LANGUAGE_ENGLISH                : "ENGLISH",
        })

XDW_OCR_MULTIPLELANGUAGES_ENGLISH               = 0x02
XDW_OCR_MULTIPLELANGUAGES_FRENCH                = 0x04
XDW_OCR_MULTIPLELANGUAGES_SIMPLIFIED_CHINESE    = 0x08
XDW_OCR_MULTIPLELANGUAGES_TRADITIONAL_CHINESE   = 0x10
XDW_OCR_MULTIPLELANGUAGES_THAI                  = 0x20

XDW_OCR_FORM_AUTO                               = 0
XDW_OCR_FORM_TABLE                              = 1
XDW_OCR_FORM_WRITING                            = 2

XDW_OCR_FORM = XDWConst({
        XDW_OCR_FORM_AUTO                       : "AUTO",
        XDW_OCR_FORM_TABLE                      : "TABLE",
        XDW_OCR_FORM_WRITING                    : "WRITING",
        })

XDW_OCR_COLUMN_AUTO                             = 0
XDW_OCR_COLUMN_HORIZONTAL_SINGLE                = 1
XDW_OCR_COLUMN_HORIZONTAL_MULTI                 = 2
XDW_OCR_COLUMN_VERTICAL_SINGLE                  = 3
XDW_OCR_COLUMN_VERTICAL_MULTI                   = 4

XDW_OCR_COLUMN = XDWConst({
        XDW_OCR_COLUMN_AUTO                     : "AUTO",
        XDW_OCR_COLUMN_HORIZONTAL_SINGLE        : "HORIZONTAL SINGLE",
        XDW_OCR_COLUMN_HORIZONTAL_MULTI         : "HORIZONTAL MULTI",
        XDW_OCR_COLUMN_VERTICAL_SINGLE          : "VERTICAL SINGLE",
        XDW_OCR_COLUMN_VERTICAL_MULTI           : "VERTICAL MULTI",
        })

XDW_OCR_DOCTYPE_AUTO                            = 0
XDW_OCR_DOCTYPE_HORIZONTAL_SINGLE               = 1
XDW_OCR_DOCTYPE_PLAINTEXT                       = 2

XDW_OCR_ENGINE_LEVEL_SPEED                      = 1
XDW_OCR_ENGINE_LEVEL_STANDARD                   = 2
XDW_OCR_ENGINE_LEVEL_ACCURACY                   = 3

XDW_OCR_STRATEGY = XDWConst({
        XDW_OCR_ENGINE_LEVEL_SPEED              : "SPEED",
        XDW_OCR_ENGINE_LEVEL_STANDARD           : "STANDARD",
        XDW_OCR_ENGINE_LEVEL_ACCURACY           : "ACCURACY",
        })

XDW_OCR_MIXEDRATE_JAPANESE                      = 1
XDW_OCR_MIXEDRATE_BALANCED                      = 2
XDW_OCR_MIXEDRATE_ENGLISH                       = 3

XDW_OCR_MAIN_LANGUAGE = XDWConst({
        XDW_OCR_MIXEDRATE_JAPANESE              : "JAPANESE",
        XDW_OCR_MIXEDRATE_BALANCED              : "BALANCED",
        XDW_OCR_MIXEDRATE_ENGLISH               : "ENGLISH",
        })

# page type

XDW_PGT_NULL                        = 0
XDW_PGT_FROMIMAGE                   = 1
XDW_PGT_FROMAPPL                    = 2

XDW_PAGE_TYPE = XDWConst({
        XDW_PGT_FROMIMAGE           : "IMAGE",
        XDW_PGT_FROMAPPL            : "APPLICATION",
        XDW_PGT_NULL                : "UNKNOWN",
        }, default=XDW_PGT_NULL)

### Annotation related

XDW_AID_FUSEN                       = 32794
XDW_AID_TEXT                        = 32785
XDW_AID_STAMP                       = 32819
XDW_AID_STRAIGHTLINE                = 32828
XDW_AID_RECTANGLE                   = 32829
XDW_AID_ARC                         = 32830
XDW_AID_POLYGON                     = 32834
XDW_AID_MARKER                      = 32795
XDW_AID_LINK                        = 49199
XDW_AID_PAGEFORM                    = 32814
XDW_AID_OLE                         = 32783
XDW_AID_BITMAP                      = 32831
XDW_AID_RECEIVEDSTAMP               = 32832
XDW_AID_CUSTOM                      = 32837
XDW_AID_TITLE                       = 32838
XDW_AID_GROUP                       = 32839

XDW_ANNOTATION_TYPE = XDWConst({
        XDW_AID_FUSEN               : "FUSEN",
        XDW_AID_TEXT                : "TEXT",
        XDW_AID_STAMP               : "STAMP",
        XDW_AID_STRAIGHTLINE        : "STRAIGHTLINE",
        XDW_AID_RECTANGLE           : "RECTANGLE",
        XDW_AID_ARC                 : "ARC",
        XDW_AID_POLYGON             : "POLYGON",
        XDW_AID_MARKER              : "MARKER",
        XDW_AID_LINK                : "LINK",
        XDW_AID_PAGEFORM            : "PAGEFORM",
        XDW_AID_OLE                 : "OLE",
        XDW_AID_BITMAP              : "BITMAP",
        XDW_AID_RECEIVEDSTAMP       : "RECEIVEDSTAMP",
        XDW_AID_CUSTOM              : "CUSTOM",
        XDW_AID_TITLE               : "TITLE",
        XDW_AID_GROUP               : "GROUP",
        }, default=XDW_AID_TEXT)

XDW_ATYPE_INT                       = 0
XDW_ATYPE_STRING                    = 1
XDW_ATYPE_DATE                      = 2
XDW_ATYPE_BOOL                      = 3
XDW_ATYPE_OCTS                      = 4
XDW_ATYPE_OTHER                     = 999

XDW_LINE_NONE                       = 0
XDW_LINE_BEGINNING                  = 1
XDW_LINE_ENDING                     = 2
XDW_LINE_BOTH                       = 3
XDW_LINE_WIDE_POLYLINE              = 0
XDW_LINE_POLYLINE                   = 1
XDW_LINE_POLYGON                    = 2

XDW_BORDER_TYPE_SOLID               = 0
XDW_BORDER_TYPE_DOT                 = 1
XDW_BORDER_TYPE_DASH                = 2
XDW_BORDER_TYPE_DASHDOT             = 3
XDW_BORDER_TYPE_DOUBLE              = 4

XDW_STAMP_AUTO                      = 0
XDW_STAMP_MANUAL                    = 1
XDW_STAMP_NO_BASISYEAR              = 0
XDW_STAMP_BASISYEAR                 = 1
XDW_STAMP_DATE_YMD                  = 0
XDW_STAMP_DATE_DMY                  = 1

XDW_PAGEFORM_HEADER                 = 0
XDW_PAGEFORM_FOOTER                 = 1
XDW_PAGEFORM_TOPIMAGE               = 2
XDW_PAGEFORM_BOTTOMIMAGE            = 3
XDW_PAGEFORM_PAGENUMBER             = 4

XDW_PAGEFORM = XDWConst({
        XDW_PAGEFORM_HEADER         : "HEADER",
        XDW_PAGEFORM_FOOTER         : "FOOTER",
        XDW_PAGEFORM_TOPIMAGE       : "TOPIMAGE",
        XDW_PAGEFORM_BOTTOMIMAGE    : "BOTTOMIMAGE",
        XDW_PAGEFORM_PAGENUMBER     : "PAGENUMBER",
        }, default=XDW_PAGEFORM_PAGENUMBER)

XDW_PAGEFORM_STAY                   = 0
XDW_PAGEFORM_REMOVE                 = 1

XDW_ALIGN_LEFT                      = 0
XDW_ALIGN_HCENTER                   = 1
XDW_ALIGN_RIGHT                     = 2
XDW_ALIGN_TOP                       = 0
XDW_ALIGN_BOTTOM                    = 1
XDW_ALIGN_VCENTER                   = 2

XDW_PAGERANGE_ALL                   = 0
XDW_PAGERANGE_SPECIFIED             = 1

XDW_IGNORE_CASE                     = 0x02
XDW_IGNORE_WIDTH                    = 0x04
XDW_IGNORE_HIRAKATA                 = 0x08

XDW_STARCH                          = 1
XDW_STARCH_OFF                      = 0

XDW_ATN_Text                        = "%Text"
XDW_ATN_FontName                    = "%FontName"
XDW_ATN_FontStyle                   = "%FontStyle"
XDW_ATN_FontSize                    = "%FontSize"
XDW_ATN_ForeColor                   = "%ForeColor"
XDW_ATN_FontPitchAndFamily          = "%FontPitchAndFamily"
XDW_ATN_FontCharSet                 = "%FontCharSet"
XDW_ATN_BackColor                   = "%BackColor"
XDW_ATN_Caption                     = "%Caption"
XDW_ATN_Url                         = "%Url"
XDW_ATN_XdwPath                     = "%XdwPath"
XDW_ATN_ShowIcon                    = "%ShowIcon"
XDW_ATN_LinkType                    = "%LinkType"
XDW_ATN_XdwPage                     = "%XdwPage"
XDW_ATN_Tooltip                     = "%Tooltip"
XDW_ATN_Tooltip_String              = "%TooltipString"
XDW_ATN_XdwPath_Relative            = "%XdwPathRelative"
XDW_ATN_XdwLink                     = "%XdwLink"
XDW_ATN_LinkAtn_Title               = "%LinkAtnTitle"
XDW_ATN_OtherFilePath               = "%OtherFilePath"
XDW_ATN_OtherFilePath_Relative      = "%OtherFilePathRelative"
XDW_ATN_MailAddress                 = "%MailAddress"
XDW_ATN_BorderStyle                 = "%BorderStyle"
XDW_ATN_BorderWidth                 = "%BorderWidth"
XDW_ATN_BorderColor                 = "%BorderColor"
XDW_ATN_BorderTransparent           = "%BorderTransparent"
XDW_ATN_BorderType                  = "%BorderType"
XDW_ATN_FillStyle                   = "%FillStyle"
XDW_ATN_FillColor                   = "%FillColor"
XDW_ATN_FillTransparent             = "%FillTransparent"
XDW_ATN_ArrowheadType               = "%ArrowheadType"
XDW_ATN_ArrowheadStyle              = "%ArrowheadStyle"
XDW_ATN_WordWrap                    = "%WordWrap"
XDW_ATN_TextDirection               = "%TextDirection"
XDW_ATN_TextOrientation             = "%TextOrientation"
XDW_ATN_LineSpace                   = "%LineSpace"
XDW_ATN_AutoResize                  = "%AutoResize"
XDW_ATN_Invisible                   = "%Invisible"
XDW_ATN_PageFrom                    = "%PageFrom"
XDW_ATN_XdwNameInXbd                = "%XdwNameInXbd"
XDW_ATN_TopField                    = "%TopField"
XDW_ATN_BottomField                 = "%BottomField"
XDW_ATN_DateStyle                   = "%DateStyle"
XDW_ATN_YearField                   = "%YearField"
XDW_ATN_MonthField                  = "%MonthField"
XDW_ATN_DayField                    = "%DayField"
XDW_ATN_BasisYearStyle              = "%BasisYearStyle"
XDW_ATN_BasisYear                   = "%BasisYear"
XDW_ATN_DateField_FirstChar         = "%DateFieldFirstChar"
XDW_ATN_Alignment                   = "%Alignment"
XDW_ATN_LeftRightMargin             = "%LeftRightMargin"
XDW_ATN_TopBottomMargin             = "%TopBottomMargin"
XDW_ATN_VerPosition                 = "%VerPosition"
XDW_ATN_StartingNumber              = "%StartingNumber"
XDW_ATN_Digit                       = "%Digit"
XDW_ATN_PageRange                   = "%PageRange"
XDW_ATN_BeginningPage               = "%BeginningPage"
XDW_ATN_EndingPage                  = "%EndingPage"
XDW_ATN_Zoom                        = "%Zoom"
XDW_ATN_ImageFile                   = "%ImageFile"
XDW_ATN_Points                      = "%Points"
XDW_ATN_DateFormat                  = "%DateFormat"
XDW_ATN_DateOrder                   = "%DateOrder"
XDW_ATN_TextSpacing                 = "%Spacing"
XDW_ATN_TextTopMargin               = "%TopMargin"
XDW_ATN_TextLeftMargin              = "%LeftMargin"
XDW_ATN_TextBottomMargin            = "%BottomMargin"
XDW_ATN_TextRightMargin             = "%RightMargin"
XDW_ATN_TextAutoResizeHeight        = "%AutoResizeHeight"
XDW_ATN_GUID                        = "%CustomAnnGuid"
XDW_ATN_CustomData                  = "%CustomAnnCustomData"

XDW_COLOR_NONE                      = 0x010101
XDW_COLOR_BLACK                     = 0x000000
XDW_COLOR_MAROON                    = 0x000080
XDW_COLOR_GREEN                     = 0x008000
XDW_COLOR_OLIVE                     = 0x008080
XDW_COLOR_NAVY                      = 0x800000
XDW_COLOR_PURPLE                    = 0x800080
XDW_COLOR_TEAL                      = 0x808000
XDW_COLOR_GRAY                      = 0x808080
XDW_COLOR_SILVER                    = 0xC0C0C0
XDW_COLOR_RED                       = 0x0000FF
XDW_COLOR_LIME                      = 0x00FF00
XDW_COLOR_YELLOW                    = 0x00FFFF
XDW_COLOR_BLUE                      = 0xFF0000
XDW_COLOR_FUCHIA                    = 0xFF00FF
XDW_COLOR_AQUA                      = 0xFFFF00
XDW_COLOR_WHITE                     = 0xFFFFFF
XDW_COLOR_FUSEN_RED                 = 0xFFC2FF
XDW_COLOR_FUSEN_BLUE                = 0xFFBF9D
XDW_COLOR_FUSEN_YELLOW              = 0x64FFFF
XDW_COLOR_FUSEN_LIME                = 0xC2FF9D
XDW_COLOR_FUSEN_PALE_RED            = 0xE1D7FF
XDW_COLOR_FUSEN_PALE_BLUE           = 0xFAE1C8
XDW_COLOR_FUSEN_PALE_YELLOW         = 0xC3FAFF
XDW_COLOR_FUSEN_PALE_LIME           = 0xD2FACD

XDW_COLOR = XDWConst({
        XDW_COLOR_NONE                  : "NONE",
        XDW_COLOR_BLACK                 : "BLACK",
        XDW_COLOR_MAROON                : "MAROON",
        XDW_COLOR_GREEN                 : "GREEN",
        XDW_COLOR_OLIVE                 : "OLIVE",
        XDW_COLOR_NAVY                  : "NAVY",
        XDW_COLOR_PURPLE                : "PURPLE",
        XDW_COLOR_TEAL                  : "TEAL",
        XDW_COLOR_GRAY                  : "GRAY",
        XDW_COLOR_SILVER                : "SILVER",
        XDW_COLOR_RED                   : "RED",
        XDW_COLOR_LIME                  : "LIME",
        XDW_COLOR_YELLOW                : "YELLOW",
        XDW_COLOR_BLUE                  : "BLUE",
        XDW_COLOR_FUCHIA                : "FUCHIA",
        XDW_COLOR_AQUA                  : "AQUA",
        XDW_COLOR_WHITE                 : "WHITE",
        }, default=XDW_COLOR_BLACK)

XDW_COLOR_FUSEN = XDWConst({
        XDW_COLOR_FUSEN_RED             : "RED",
        XDW_COLOR_FUSEN_BLUE            : "BLUE",
        XDW_COLOR_FUSEN_YELLOW          : "YELLOW",
        XDW_COLOR_FUSEN_LIME            : "LIME",
        XDW_COLOR_FUSEN_PALE_RED        : "PALE_RED",
        XDW_COLOR_FUSEN_PALE_BLUE       : "PALE_BLUE",
        XDW_COLOR_FUSEN_PALE_YELLOW     : "PALE_YELLOW",
        XDW_COLOR_FUSEN_PALE_LIME       : "PALE_LIME",
        }, default=XDW_COLOR_FUSEN_PALE_YELLOW)

XDW_FS_ITALIC_FLAG                  = 1
XDW_FS_BOLD_FLAG                    = 2
XDW_FS_UNDERLINE_FLAG               = 4
XDW_FS_STRIKEOUT_FLAG               = 8

XDW_LT_LINK_TO_ME                   = 0
XDW_LT_LINK_TO_XDW                  = 1
XDW_LT_LINK_TO_URL                  = 2
XDW_LT_LINK_TO_OTHERFILE            = 3
XDW_LT_LINK_TO_MAILADDR             = 4

XDW_PF_XDW                          = 0
XDW_PF_XBD                          = 1
XDW_PF_XDW_IN_XBD                   = 2

# Assert to ensure XDW_ANNOTATION_ATTRIBUTE.
assert XDW_ATYPE_INT == 0
assert XDW_ATYPE_STRING == 1

XDW_ANNOTATION_ATTRIBUTE = {
        # attribute_id: (type, unit, available_ann_types)
        #   where type is either 0(int), 1(string) or 2(points)
        XDW_ATN_Alignment           : (0, None, ()),
        XDW_ATN_ArrowheadStyle      : (0, None, (XDW_AID_STRAIGHTLINE,)),
        XDW_ATN_ArrowheadType       : (0, None, (XDW_AID_STRAIGHTLINE,)),
        XDW_ATN_AutoResize          : (0, None, (XDW_AID_LINK, XDW_AID_FUSEN,)),
        XDW_ATN_BackColor           : (0, None, (XDW_AID_TEXT,)),
        XDW_ATN_BasisYear           : (0, None, (XDW_AID_STAMP,)),
        XDW_ATN_BasisYearStyle      : (0, None, (XDW_AID_STAMP,)),
        XDW_ATN_BeginningPage       : (0, None, ()),
        XDW_ATN_BorderColor         : (0, None, (XDW_AID_STRAIGHTLINE, XDW_AID_RECTANGLE, XDW_AID_ARC, XDW_AID_STAMP, XDW_AID_MARKER, XDW_AID_POLYGON,)),
        XDW_ATN_BorderStyle         : (0, None, (XDW_AID_RECTANGLE, XDW_AID_ARC, XDW_AID_POLYGON,)),
        XDW_ATN_BorderTransparent   : (0, None, (XDW_AID_STRAIGHTLINE, XDW_AID_MARKER,)),
        XDW_ATN_BorderType          : (0, None, (XDW_AID_STRAIGHTLINE,)),
        XDW_ATN_BorderWidth         : (0, "pt", (XDW_AID_STRAIGHTLINE, XDW_AID_RECTANGLE, XDW_AID_ARC, XDW_AID_MARKER, XDW_AID_POLYGON,)),
        XDW_ATN_BottomField         : (1, None, (XDW_AID_STAMP,)),
        XDW_ATN_Caption             : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_CustomData          : (0, None, ()),
        XDW_ATN_DateField_FirstChar : (1, None, (XDW_AID_STAMP,)),
        XDW_ATN_DateFormat          : (1, None, (XDW_AID_STAMP,)),  # "yy.mm.dd", "yy.m.d", "dd.mmm.yy" or "dd.mmm.yyyy"
        XDW_ATN_DateOrder           : (0, None, (XDW_AID_STAMP,)),
        XDW_ATN_DateStyle           : (0, None, (XDW_AID_STAMP,)),
        XDW_ATN_DayField            : (1, None, (XDW_AID_STAMP,)),
        XDW_ATN_Digit               : (0, None, ()),
        XDW_ATN_EndingPage          : (0, None, ()),
        XDW_ATN_FillColor           : (0, None, (XDW_AID_FUSEN, XDW_AID_RECTANGLE, XDW_AID_ARC, XDW_AID_POLYGON,)),
        XDW_ATN_FillStyle           : (0, None, (XDW_AID_RECTANGLE, XDW_AID_ARC, XDW_AID_POLYGON,)),
        XDW_ATN_FillTransparent     : (0, None, (XDW_AID_RECTANGLE, XDW_AID_ARC, XDW_AID_POLYGON,)),
        XDW_ATN_FontCharSet         : (0, None, (XDW_AID_TEXT, XDW_AID_LINK,)),
        XDW_ATN_FontName            : (1, None, (XDW_AID_TEXT, XDW_AID_LINK,)),
        XDW_ATN_FontPitchAndFamily  : (0, None, (XDW_AID_TEXT, XDW_AID_LINK,)),
        XDW_ATN_FontSize            : (0, "1/10pt", (XDW_AID_TEXT, XDW_AID_LINK,)),
        XDW_ATN_FontStyle           : (0, None, (XDW_AID_TEXT, XDW_AID_LINK,)),
        XDW_ATN_ForeColor           : (0, None, (XDW_AID_TEXT, XDW_AID_LINK,)),
        XDW_ATN_GUID                : (0, None, ()),
        XDW_ATN_ImageFile           : (0, None, ()),
        XDW_ATN_Invisible           : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_LeftRightMargin     : (0, None, ()),
        XDW_ATN_LineSpace           : (0, "1/100line", (XDW_AID_TEXT,)),  # 1-10
        XDW_ATN_LinkAtn_Title       : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_LinkType            : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_MailAddress         : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_MonthField          : (1, None, (XDW_AID_STAMP,)),
        XDW_ATN_OtherFilePath       : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_OtherFilePath_Relative  : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_PageFrom            : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_PageRange           : (0, None, ()),
        XDW_ATN_Points              : (2, None, (XDW_AID_STRAIGHTLINE, XDW_AID_MARKER, XDW_AID_POLYGON,)),  # TODO: TREAT SPECIALLY
        XDW_ATN_ShowIcon            : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_StartingNumber      : (0, None, ()),
        XDW_ATN_Text                : (1, None, (XDW_AID_TEXT,)),
        XDW_ATN_TextAutoResizeHeight    : (0, None, (XDW_AID_TEXT,)),
        XDW_ATN_TextBottomMargin    : (0, "1/100mm", (XDW_AID_TEXT,)),  # 0-20000
        XDW_ATN_TextDirection       : (0, None, (XDW_AID_TEXT,)),
        XDW_ATN_TextLeftMargin      : (0, "1/100mm", (XDW_AID_TEXT,)),  # 0-20000
        XDW_ATN_TextOrientation     : (0, None, (XDW_AID_TEXT,)),
        XDW_ATN_TextRightMargin     : (0, "1/100mm", (XDW_AID_TEXT,)),  # 0-20000
        XDW_ATN_TextSpacing         : (0, "1/10char", (XDW_AID_TEXT,)),
        XDW_ATN_TextTopMargin       : (0, "1/100mm", (XDW_AID_TEXT,)),  # 0-20000
        XDW_ATN_Tooltip             : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_Tooltip_String      : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_TopBottomMargin     : (0, None, ()),
        XDW_ATN_TopField            : (1, None, (XDW_AID_STAMP,)),
        XDW_ATN_Url                 : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_VerPosition         : (0, None, ()),
        XDW_ATN_WordWrap            : (0, None, (XDW_AID_TEXT,)),
        XDW_ATN_XdwLink             : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_XdwNameInXbd        : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_XdwPage             : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_XdwPath             : (1, None, (XDW_AID_LINK,)),
        XDW_ATN_XdwPath_Relative    : (0, None, (XDW_AID_LINK,)),
        XDW_ATN_YearField           : (1, None, (XDW_AID_STAMP,)),
        XDW_ATN_Zoom                : (0, None, ()),
        }

XDW_FONT_CHARSET = {
        "ANSI_CHARSET"              : 0,
        "DEFAULT_CHARSET"           : 1,
        "SYMBOL_CHARSET"            : 2,
        "MAC_CHARSET"               : 77,
        "SHIFTJIS_CHARSET"          : 128,
        "HANGEUL_CHARSET"           : 129,
        "CHINESEBIG5_CHARSET"       : 136,
        "GREEK_CHARSET"             : 161,
        "TURKISH_CHARSET"           : 162,
        "BALTIC_CHARSET"            : 186,
        "RUSSIAN_CHARSET"           : 204,
        "EASTEUROPE_CHARSET"        : 238,
        "OEM_CHARSET"               : 255,
        }

XDW_PITCH_AND_FAMILY = {
        "DEFAULT_PITCH"             : 0,
        "FIXED_PITCH"               : 1,
        "VARIABLE_PITCH"            : 2,
        "FF_DONTCARE"               : 0,
        "FF_ROMAN"                  : 16,
        "FF_SWISS"                  : 32,
        "FF_MODERN"                 : 48,
        "FF_SCRIPT"                 : 64,
        "FF_DECORATIVE"             : 80,
        }

######################################################################
### STRUCTURES #######################################################

### C types and structures used in xdwapi.dll

XDW_HGLOBAL = c_void_p
XDW_WCHAR = c_wchar


class SizedStructure(Structure):
    """ctypes.Structure with setting self.nSize automatically."""
    def __init__(self):
        Structure.__init__(self)
        self.nSize = sizeof(self)


class XDW_DOCUMENT_HANDLE(Structure):
    _fields_ = [("dummy", c_int), ]


class XDW_CREATE_HANDLE(Structure):
    _fields_ = [("dummy", c_int), ]


class XDW_ANNOTATION_HANDLE(Structure):
    _fields_ = [("dummy", c_int), ]


class XDW_FOUND_HANDLE(Structure):
    _fields_ = [("dummy", c_int), ]


class XDW_RECT(Structure):
    _fields_ = [
        ("left", c_long),
        ("top", c_long),
        ("right", c_long),
        ("bottom", c_long),
        ]


class XDW_GPTI_OCRTEXT_UNIT(Structure):
    _fields_ = [
        ("lpszText", c_char_p),
        ("rect", XDW_RECT),
        ]


class XDW_GPTI_OCRTEXT(Structure):
    _fields_ = [
        ("nUnitNum", c_int),
        ("pUnits", POINTER(XDW_GPTI_OCRTEXT_UNIT)),
        ]


class XDW_GPTI_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nInfoType", c_int),
        ("nPageWidth", c_int),
        ("nPageHeight", c_int),
        ("nRotateDegree", c_int),
        ("nDataSize", c_int),
        ("pData", XDW_HGLOBAL),
        ]


class XDW_DOCUMENT_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nPages", c_int),
        ("nVersion", c_int),
        ("nOriginalData", c_int),
        ("nDocType", c_int),
        ("nPermission", c_int),
        ("nShowAnnotations", c_int),
        ("nDocuments", c_int),
        ("nBinderColor", c_int),
        ("nBinderSize", c_int),
        ]


class XDW_PAGE_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("nPageType", c_int),
        ("nHorRes", c_int),
        ("nVerRes", c_int),
        ("nCompressType", c_int),
        ("nAnnotations", c_int),
        ]


class XDW_PAGE_INFO_EX(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("nPageType", c_int),
        ("nHorRes", c_int),
        ("nVerRes", c_int),
        ("nCompressType", c_int),
        ("nAnnotations", c_int),
        ("nDegree", c_int),
        ("nOrgWidth", c_int),
        ("nOrgHeight", c_int),
        ("nOrgHorRes", c_int),
        ("nOrgVerRes", c_int),
        ("nImageWidth", c_int),
        ("nImageHeight", c_int),
        ]


class XDW_IMAGE_OPTION(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nDpi", c_int),
        ("nColor", c_int),
        ]


class XDW_OPEN_MODE(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nOption", c_int),
        ]


class XDW_OPEN_MODE_EX(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nOption", c_int),
        ("nAuthMode", c_int),
        ]


class XDW_CREATE_OPTION(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nFitImage", c_int),
        ("nCompress", c_int),
        ("nZoom", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("nHorPos", c_int),
        ("nVerPos", c_int),
        ]


class XDW_CREATE_OPTION_EX(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nFitImage", c_int),
        ("nCompress", c_int),
        ("nZoom", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("nHorPos", c_int),
        ("nVerPos", c_int),
        ("nZoomDetail", c_int),
        ]


class XDW_CREATE_OPTION_EX2(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nFitImage", c_int),
        ("nCompress", c_int),
        ("nZoom", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("nHorPos", c_int),
        ("nVerPos", c_int),
        ("nZoomDetail", c_int),
        ("nMaxPaperSize", c_int),
        ]


XDW_SIZEOF_ORGDATANAME = 256


class XDW_ORGDATA_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nDataSize", c_int),
        ("nDate", c_long),
        ("szName", c_char * XDW_SIZEOF_ORGDATANAME),
        ]


class XDW_ORGDATA_INFOW(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nDataSize", c_int),
        ("nDate", c_long),
        ("szName", XDW_WCHAR * XDW_SIZEOF_ORGDATANAME),
        ]


XDW_SIZEOF_LINKROOTFOLDER = 256


class XDW_LINKROOTFOLDER_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
     ("szPath", c_char * XDW_SIZEOF_LINKROOTFOLDER),
     ("szLinkRootFolderName", c_char * XDW_SIZEOF_LINKROOTFOLDER),
        ]


class XDW_CREATE_STATUS(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("phase", c_int),
        ("nTotalPage", c_int),
        ("nPage", c_int),
        ]


class XDW_ANNOTATION_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("handle", XDW_ANNOTATION_HANDLE),
        ("nHorPos", c_int),
        ("nVerPos", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("nAnnotationType", c_int),
        ("nChildAnnotations", c_int),
        ]


class XDW_AA_INITIAL_DATA(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nAnnotationType", c_int),
        ("nReserved1", c_int),
        ("nReserved2", c_int),
        ]


class XDW_AA_FUSEN_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ]


class XDW_AA_STRAIGHTLINE_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nHorVec", c_int),
        ("nVerVec", c_int),
        ]


class XDW_AA_RECT_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ]


class XDW_AA_ARC_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ]


class XDW_AA_BITMAP_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("szImagePath", c_char * 256),
        ]


class XDW_AA_STAMP_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nWidth", c_int),
        ]


class XDW_AA_RECEIVEDSTAMP_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nWidth", c_int),
        ]


XDW_SIZEOF_GUID = 36


class XDW_AA_CUSTOM_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("lpszGuid", c_char_p),
        ("nCustomDataSize", c_int),
        ("pCustomData", c_char_p),
        ]


class XDW_IMAGE_OPTION_EX(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nDpi", c_int),
        ("nColor", c_int),
        ("nImageType", c_int),
        ("pDetailOption", c_void_p),
        ]


class XDW_IMAGE_OPTION_TIFF(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nCompress", c_int),
        ("nEndOfMultiPages", c_int),
        ]


class XDW_IMAGE_OPTION_JPEG(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nCompress", c_int),
        ]


class XDW_IMAGE_OPTION_PDF(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nCompress", c_int),
        ("nConvertMethod", c_int),
        ("nEndOfMultiPages", c_int),
        ]


class XDW_BINDER_INITIAL_DATA(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nBinderColor", c_int),
        ("nBinderSize", c_int),
        ]


class XDW_OCR_OPTION_V4(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nNoiseReduction", c_int),
        ("nLanguage", c_int),
        ("nInsertSpaceCharacter", c_int),
        ("nJapaneseKnowledgeProcessing", c_int),
        ("nForm", c_int),
        ("nColumn", c_int),
        ("nDisplayProcess", c_int),
        ("nAutoDeskew", c_int),
        ]


class XDW_OCR_OPTION_V5(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nNoiseReduction", c_int),
        ("nLanguage", c_int),
        ("nInsertSpaceCharacter", c_int),
        ("nJapaneseKnowledgeProcessing", c_int),
        ("nForm", c_int),
        ("nColumn", c_int),
        ("nDisplayProcess", c_int),
        ("nAutoDeskew", c_int),
        ("nAreaNum", c_uint),
        ("pAreaRects", POINTER(POINTER(XDW_RECT))),
        ]


class XDW_OCR_OPTION_V5_EX(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nNoiseReduction", c_int),
        ("nLanguage", c_int),
        ("nInsertSpaceCharacter", c_int),
        ("nJapaneseKnowledgeProcessing", c_int),
        ("nForm", c_int),
        ("nColumn", c_int),
        ("nDisplayProcess", c_int),
        ("nAutoDeskew", c_int),
        ("nAreaNum", c_uint),
        ("pAreaRects", POINTER(POINTER(XDW_RECT))),
        ("nPriority", c_int),
        ]


class XDW_OCR_OPTION_WRP(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nNoiseReduction", c_int),
        ("nLanguage", c_int),
        ("nInsertSpaceCharacter", c_int),
        ("nForm", c_int),
        ("nColumn", c_int),
        ("nAutoDeskew", c_int),
        ("nPriority", c_int),
        ]


class XDW_OCR_OPTION_FRE(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nNoiseReduction", c_int),
        ("nLanguage", c_int),
        ("nDocumentType", c_int),
        ("nDisplayProcess", c_int),
        ("nAutoDeskew", c_int),
        ("nAreaNum", c_uint),
        ("pAreaRects", POINTER(POINTER(XDW_RECT))),
        ("nPriority", c_int),
        ]


class XDW_OCR_OPTION_V7(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nNoiseReduction", c_int),
        ("nLanguage", c_int),
        ("nInsertSpaceCharacter", c_int),
        ("nJapaneseKnowledgeProcessing", c_int),
        ("nForm", c_int),
        ("nColumn", c_int),
        ("nDisplayProcess", c_int),
        ("nAutoDeskew", c_int),
        ("nAreaNum", c_uint),
        ("pAreaRects", POINTER(POINTER(XDW_RECT))),
        ("nPriority", c_int),
        ("nEngineLevel", c_int),
        ("nLanguageMixedRate", c_int),
        ("nHalfSizeChar", c_int),
        ]


class XDW_OCR_OPTION_FRE_V7(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nNoiseReduction", c_int),
        ("nLanguage", c_int),
        ("nDocumentType", c_int),
        ("nDisplayProcess", c_int),
        ("nAutoDeskew", c_int),
        ("nAreaNum", c_uint),
        ("pAreaRects", POINTER(POINTER(XDW_RECT))),
        ("nPriority", c_int),
        ("nEngineLevel", c_int),
        ]


class XDW_PAGE_COLOR_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nColor", c_int),
        ("nImageDepth", c_int),
        ]


XDW_SIZEOF_PSWD = 256


class XDW_SECURITY_OPTION_PSWD(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nPermission", c_int),
        ("szOpenPswd", c_char * XDW_SIZEOF_PSWD),
        ("szFullAccessPswd", c_char * XDW_SIZEOF_PSWD),
        ("lpszComment", c_char_p),
        ]


class XDW_DER_CERTIFICATE(Structure):
    _fields_ = [
        ("pCert", c_void_p),
        ("nCertSize", c_int),
        ]


class XDW_SECURITY_OPTION_PKI(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nPermission", c_int),
        ("lpxdcCerts", POINTER(XDW_DER_CERTIFICATE)),
        ("nCertsNum", c_int),
        ("nFullAccessCertsNum", c_int),
        ("nErrorStatus", c_int),
        ("nFirstErrorCert", c_int),
        ]


class XDW_PROTECT_OPTION(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nAuthMode", c_int),
        ]


class XDW_RELEASE_PROTECTION_OPTION(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nAuthMode", c_int),
        ]


class XDW_PROTECTION_INFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nProtectType", c_int),
        ("nPermission", c_int),
        ]


class XDW_SIGNATURE_OPTION_V5(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nPage", c_int),
        ("nHorPos", c_int),
        ("nVerPos", c_int),
        ("nSignatureType", c_int),
        ]


class XDW_SIGNATURE_INFO_V5(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nSignatureType", c_int),
        ("nPage", c_int),
        ("nHorPos", c_int),
        ("nVerPos", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("nSignedTime", c_long),
        ]


class XDW_SIGNATURE_MODULE_STATUS(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nSignatureType", c_int),
        ("nErrorStatus", c_int),
        ]


class XDW_SIGNATURE_MODULE_OPTION_PKI(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("pSignerCert", c_void_p),
        ("nSignerCertSize", c_int),
        ]


XDW_SIZEOF_STAMPNAME = 256
XDW_SIZEOF_STAMPOWNERNAME = 64
XDW_SIZEOF_STAMPREMARKS = 1024


class XDW_SIGNATURE_STAMP_INFO_V5(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("lpszStampName", c_char * XDW_SIZEOF_STAMPNAME),
        ("lpszOwnerName", c_char * XDW_SIZEOF_STAMPOWNERNAME),
        ("nValidDate", c_long),
        ("lpszRemarks", c_char * XDW_SIZEOF_STAMPREMARKS),
        ("nDocVerificationStatus", c_int),
        ("nStampVerificationStatus", c_int),
        ]


XDW_SIZEOF_PKIMODULENAME    = 16
XDW_SIZEOF_PKISUBJECTDN     = 512
XDW_SIZEOF_PKISUBJECT       = 256
XDW_SIZEOF_PKIISSUERDN      = 512
XDW_SIZEOF_PKIISSUER        = 256
XDW_SIZEOF_PKINOTBEFORE     = 32
XDW_SIZEOF_PKINOTAFTER      = 32
XDW_SIZEOF_PKISERIAL        = 64
XDW_SIZEOF_PKIREMARKS       = 64
XDW_SIZEOF_PKISIGNEDTIME    = 32


class XDW_SIGNATURE_PKI_INFO_V5(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
     ("lpszModule", c_char * XDW_SIZEOF_PKIMODULENAME),
     ("lpszSubjectDN", c_char * XDW_SIZEOF_PKISUBJECTDN),
     ("lpszSubject", c_char * XDW_SIZEOF_PKISUBJECT),
     ("lpszIssuerDN", c_char * XDW_SIZEOF_PKIISSUERDN),
     ("lpszIssuer", c_char * XDW_SIZEOF_PKIISSUER),
     ("lpszNotBefore", c_char * XDW_SIZEOF_PKINOTBEFORE),
     ("lpszNotAfter", c_char * XDW_SIZEOF_PKINOTAFTER),
     ("lpszSerial", c_char * XDW_SIZEOF_PKISERIAL),
        ("pSignerCert", c_void_p),
        ("nSignerCertSize", c_int),
        ("lpszRemarks", c_char * XDW_SIZEOF_PKIREMARKS),
        ("lpszSigningTime", c_char * XDW_SIZEOF_PKISIGNEDTIME),
        ("nDocVerificationStatus", c_int),
        ("nCertVerificationType", c_int),
        ("nCertVerificationStatus", c_int),
        ]


class XDW_OCR_TEXTINFO(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nWidth", c_int),
        ("nHeight", c_int),
        ("charset", c_long),
        ("lpszText", c_char_p),
        ("nLineRect", c_int),
        ("pLineRect", POINTER(XDW_RECT)),
        ]


class XDW_OCRIMAGE_OPTION(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nDpi", c_int),
        ("nNoiseReduction", c_int),
        ("nPriority", c_int),
        ]


class XDW_FIND_TEXT_OPTION(SizedStructure):
    _fields_ = [
        ("nSize", c_int),
        ("nIgnoreMode", c_int),
        ("nReserved", c_int),
        ("nReserved2", c_int),
        ]


XDW_FOUND_RECT_STATUS_HIT = 0
XDW_FOUND_RECT_STATUS_PAGE = 1


class XDW_POINT(Structure):
    _fields_ = [
        ("x", c_long),
        ("y", c_long),
        ]


class XDW_AA_MARKER_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nCounts", c_int),
        ("pPoints", POINTER(XDW_POINT)),
        ]


class XDW_AA_POLYGON_INITIAL_DATA(Structure):
    _fields_ = [
        ("common", XDW_AA_INITIAL_DATA),
        ("nCounts", c_int),
        ("pPoints", POINTER(XDW_POINT)),
        ]


XDW_AID_INITIAL_DATA = {
        XDW_AID_FUSEN           : XDW_AA_FUSEN_INITIAL_DATA,
        #XDW_AID_TEXT            : XDW_AA_TEXT_INITIAL_DATA,
        XDW_AID_STAMP           : XDW_AA_STAMP_INITIAL_DATA,
        XDW_AID_STRAIGHTLINE    : XDW_AA_STRAIGHTLINE_INITIAL_DATA,
        XDW_AID_RECTANGLE       : XDW_AA_RECT_INITIAL_DATA,
        XDW_AID_ARC             : XDW_AA_ARC_INITIAL_DATA,
        XDW_AID_POLYGON         : XDW_AA_POLYGON_INITIAL_DATA,
        XDW_AID_MARKER          : XDW_AA_MARKER_INITIAL_DATA,
        #XDW_AID_LINK            : XDW_AA_LINK_INITIAL_DATA,
        #XDW_AID_PAGEFORM        : XDW_AA_PAGEFORM_INITIAL_DATA,
        #XDW_AID_OLE             : XDW_AA_OLE_INITIAL_DATA,
        XDW_AID_BITMAP          : XDW_AA_BITMAP_INITIAL_DATA,
        #XDW_AID_RECEIVEDSTAMP   : XDW_AA_RECEIVEDSTAMP_INITIAL_DATA,
        #XDW_AID_CUSTOM          : XDW_AA_CUSTOM_INITIAL_DATA,
        # XDW_AID_TITLE           : XDW_AA_TITLE_INITIAL_DATA,
        # XDW_AID_GROUP           : XDW_AA_GROUP_INITIAL_DATA,
        }


######################################################################
### API ##############################################################

DLL = windll.LoadLibrary("xdwapi.dll")

### decorators and utility functions

NULL = None  # or POINTER(c_int)()


def ptr(obj):
    return byref(obj) if obj else NULL


def RAISE(api):
    def apifunc(*args):
        result = api(*args)
        if result & 0x80000000:
            raise XDWError(result)
        return result
    return apifunc


@RAISE
def TRY(api, *args):
    return api(*args)


def APPEND(*ext, **kw):
    """Decorator to call XDWAPI with trailing arguments *ext.

    NB. Decorated function must be of the same name as XDWAPI's one.
    """
    def deco(api):
        def func(*args, **kw):
            args = list(args)
            if "codepage" in kw:
                args.append(kw["codepage"])
            args.extend(ext)
            return TRY(getattr(DLL, api.__name__), *args)
        return func
    return deco


def STRING(api):
    """Decorator to get a string value via XDWAPI.

    NB. Decorated function must be of the same name as XDWAPI's one.
    """
    def func(*args):
        args = list(args)
        args.extend([NULL, 0, NULL])
        size = TRY(getattr(DLL, api.__name__), *args)
        buf = create_string_buffer(size)
        args[-3:] = [byref(buf), size, NULL]
        TRY(getattr(DLL, api.__name__), *args)
        return buf.value
    return func


def UNICODE(api):
    """Decorator to get a unicode (wchar) string value via XDWAPI.

    NB. Decorated function must be of the same name as XDWAPI's one.
    """
    def func(*args):
        args = list(args)
        args.extend([NULL, 0, NULL])
        size = TRY(getattr(DLL, api.__name__), *args)
        buf = create_unicode_buffer(size)
        args[-3:] = [byref(buf), size, NULL]
        TRY(getattr(DLL, api.__name__), *args)
        return buf.value
    return func


def ATTR(by_order=False, widechar=False):
    """Decorator to get document attribute via XDWAPI.

    NB. Decorated function must be of the same name as XDWAPI's one.
    """
    def deco(api):
        def func(*args, **kw):
            args = list(args)
            codepage = kw.get("codepage", 932)
            attr_type = c_int()
            if by_order:
                attr_name = create_unicode_buffer(256) if widechar \
                            else create_string_buffer(256)
                args.append(byref(attr_name))
            if widechar:
                text_type = c_int()
                args.extend([byref(attr_type), NULL, 0,
                        byref(text_type), codepage, NULL])
            else:
                args.extend([byref(attr_type), NULL, 0, NULL])
            size = TRY(getattr(DLL, api.__name__), *args)
            if attr_type.value in (XDW_ATYPE_INT, XDW_ATYPE_BOOL, XDW_ATYPE_DATE):
                attr_val = c_int()
            elif attr_type.value == XDW_ATYPE_DATE:
                attr_val = c_long()
            elif attr_type.value in (XDW_ATYPE_STRING, XDW_ATYPE_OTHER):
                attr_val = create_unicode_buffer(size) if widechar \
                            else create_string_buffer(size)
            else:
                raise XDWError(XDW_E_UNEXPECTED)
            p = -5 if widechar else -3
            args[p:p + 2] = [byref(attr_val), size]
            TRY(getattr(DLL, api.__name__), *args)
            result = []
            if by_order:
                result.append(attr_name.value)
            result.extend([attr_type.value, attr_val.value])
            if widechar:
                result.append(text_type.value)
            return tuple(result)
            # (name*, type, value, text_type*), *=optional
        return func
    return deco


### DocuWorks API's provided by xdwapi.dll

@STRING
def XDW_GetInformation(index):
    """XDW_GetInformation(index)"""
    pass


@APPEND(NULL)
def XDW_AddSystemFolder(index):
    """XDW_AddSystemFolder(index)"""
    pass


@RAISE
def XDW_MergeXdwFiles(input_paths, files, output_path):
    """XDW_MergeXdwFiles(input_paths, files, output_path)"""
    input_paths = c_char_p() * len(input_paths)
    for i in range(len(input_paths)):
        input_paths[i] = byref(input_paths[i])
    return DLL.XDW_MergeXdwFiles(input_paths, files, output_path, NULL)


def XDW_OpenDocumentHandle(path, open_mode):
    """XDW_OpenDocumentHandle(path, open_mode) --> doc_handle"""
    doc_handle = XDW_DOCUMENT_HANDLE()
    if isinstance(path, unicode):
        path = path.encode("mbcs")
    TRY(DLL.XDW_OpenDocumentHandle, path, byref(doc_handle), byref(open_mode))
    return doc_handle


@APPEND(NULL)
def XDW_CloseDocumentHandle(doc_handle):
    """XDW_CloseDocumentHandle(doc_handle)"""
    pass


def XDW_GetDocumentInformation(doc_handle):
    """XDW_GetDocumentInformation(handle) --> document_info"""
    document_info = XDW_DOCUMENT_INFO()
    TRY(DLL.XDW_GetDocumentInformation, doc_handle, byref(document_info))
    return document_info


def XDW_GetPageInformation(doc_handle, page, extend=False):
    """XDW_GetPageInformation(handle, page, extend=False) --> page_info"""
    page_info = XDW_PAGE_INFO_EX() if extend else XDW_PAGE_INFO()
    TRY(DLL.XDW_GetPageInformation, doc_handle, page, byref(page_info))
    return page_info


@APPEND(NULL)
def XDW_GetPageImage(doc_handle, page, output_path):
    """XDW_GetPageImage(doc_handle, page, output_path)"""
    pass


@APPEND(NULL)
def XDW_GetPageText(doc_handle, page, output_path):
    """XDW_GetPageText(doc_handle, page, output_path)"""
    pass


@RAISE
def XDW_ConvertPageToImageFile(doc_handle, page, output_path, img_option):
    """XDW_ConvertPageToImageFile(doc_handle, page, output_path, img_option)"""
    return DLL.XDW_ConvertPageToImageFile(
            doc_handle, page, output_path, byref(img_option))


@APPEND(NULL)
def XDW_GetPage(doc_handle, page, output_path):
    """XDW_GetPage(doc_handle, page, output_path)"""
    pass


@APPEND(NULL)
def XDW_DeletePage(doc_handle, page):
    """XDW_DeletePage(doc_handle, page)"""
    pass


@APPEND(NULL)
def XDW_RotatePage(doc_handle, page, degree):
    """XDW_RotatePage(doc_handle, page, degree)"""
    pass


@APPEND(NULL)
def XDW_SaveDocument(doc_handle):
    """XDW_SaveDocument(doc_handle)"""
    pass


@RAISE
def XDW_CreateXdwFromImageFile(input_path, output_path, cre_option):
    """XDW_CreateXdwFromImageFile(input_path, output_path, cre_option)"""
    return DLL.XDW_CreateXdwFromImageFile(input_path, output_path, byref(cre_option))


def XDW_GetOriginalDataInformation(doc_handle, org_dat):
    """XDW_GetOriginalDataInformation(doc_handle, org_dat) --> orgdata_info"""
    orgdata_info = XDW_ORGDATA_INFO()
    TRY(DLL.XDW_GetOriginalDataInformation, doc_handle, org_dat, byref(orgdata_info), NULL)
    return orgdata_info
    # NB. orgdata_info.nDate is UTC Unix time.


@APPEND(NULL)
def XDW_GetOriginalData(doc_handle, org_dat, output_path):
    """XDW_GetOriginalData(doc_handle, org_dat, output_path)"""
    pass


@APPEND(NULL)
def XDW_InsertOriginalData(doc_handle, org_dat, input_path):
    """XDW_InsertOriginalData(doc_handle, org_dat, input_path)"""
    pass


@APPEND(NULL)
def XDW_DeleteOriginalData(doc_handle, org_dat):
    """XDW_DeleteOriginalData(doc_handle, org_dat)"""
    pass


def XDW_BeginCreationFromAppFile(input_path, output_path, with_org):
    """XDW_BeginCreationFromAppFile(input_path, output_path, with_org) --> cre_handle"""
    cre_handle = XDW_CREATE_HANDLE()
    TRY(DLL.XDW_BeginCreationFromAppFile, input_path, output_path, with_org, byref(cre_handle), NULL)
    return cre_handle


@APPEND(NULL)
def XDW_EndCreationFromAppFile(cre_handle):
    """XDW_EndCreationFromAppFile(cre_handle)"""
    pass


def XDW_GetStatusCreationFromAppFile(cre_handle):
    """XDW_GetStatusCreationFromAppFile(cre_handle) --> create_status"""
    create_status = XDW_CREATE_STATUS()
    TRY(DLL.XDW_GetStatusCreationFromAppFile, cre_handle, byref(create_status))
    return createStatus


@APPEND(NULL)
def XDW_CancelCreationFromAppFile(cre_handle):
    """XDW_CancelCreationFromAppFile(cre_handle)"""
    pass


@STRING
def XDW_GetUserAttribute(doc_handle, attr_name):
    """XDW_GetUserAttribute(doc_handle, attr_name)"""
    pass


@RAISE
def XDW_SetUserAttribute(doc_handle, attr_name, attr_val):
    """XDW_SetUserAttribute(doc_handle, attr_name, attr_val)"""
    size = attr_val and len(attr_val) or 0
    return DLL.XDW_SetUserAttribute(doc_handle, attr_name, attr_val, size, NULL)


def XDW_GetAnnotationInformation(doc_handle, page, parent_ann_handle, index):
    """XDW_GetAnnotationInformation(doc_handle, page, parent_ann_handle, index) --> annotation_info"""
    annotation_info = XDW_ANNOTATION_INFO()
    TRY(DLL.XDW_GetAnnotationInformation, doc_handle, page, parent_ann_handle, index, byref(annotation_info), NULL)
    return annotation_info


@STRING
def XDW_GetAnnotationAttribute(ann_handle, attr_name):
    """XDW_GetAnnotationAttribute(ann_handle, attr_name)"""
    pass


def XDW_AddAnnotation(doc_handle, ann_type, page, hpos, vpos, init_dat):
    """XDW_AddAnnotation(doc_handle, ann_type, page, hpos, vpos, init_dat) --> new_ann_handle"""
    new_ann_handle = XDW_ANNOTATION_HANDLE()
    TRY(DLL.XDW_AddAnnotation, doc_handle, ann_type, page, hpos, vpos, ptr(init_dat), byref(new_ann_handle), NULL)
    return new_ann_handle


@APPEND(NULL)
def XDW_RemoveAnnotation(doc_handle, ann_handle):
    """XDW_RemoveAnnotation(doc_handle, ann_handle)"""
    pass


@APPEND(0, NULL)
def XDW_SetAnnotationAttribute(doc_handle, ann_handle, attr_name, attr_type, attr_val):
    """XDW_SetAnnotationAttribute(doc_handle, ann_handle, attr_name, attr_type, attr_val)"""
    pass


@APPEND(NULL)
def XDW_SetAnnotationSize(doc_handle, ann_handle, width, height):
    """XDW_SetAnnotationSize(doc_handle, ann_handle, width, height)"""
    pass


@APPEND(NULL)
def XDW_SetAnnotationPosition(doc_handle, ann_handle, hpos, vpos):
    """XDW_SetAnnotationPosition(doc_handle, ann_handle, hpos, vpos)"""
    pass


@APPEND(NULL)
def XDW_CreateSfxDocument(input_path, output_path):
    """XDW_CreateSfxDocument(input_path, output_path)"""
    pass


@APPEND(NULL)
def XDW_ExtractFromSfxDocument(input_path, output_path):
    """XDW_ExtractFromSfxDocument(input_path, output_path)"""
    pass


def XDW_ConvertPageToImageHandle(doc_handle, page, img_option):
    """XDW_ConvertPageToImageHandle(doc_handle, page, img_option) --> dib"""
    dib = XDW_HGLOBAL()
    TRY(DLL.XDW_ConvertPageToImageHandle, doc_handle, page, byref(dib), byref(img_option))
    return dib


def XDW_GetThumbnailImageHandle(doc_handle, page):
    """XDW_GetThumbnailImageHandle(doc_handle, page) --> dib"""
    dib = XDW_HGLOBAL()
    TRY(DLL.XDW_GetThumbnailImageHandle, doc_handle, page, byref(dib), NULL)
    return dib


@STRING
def XDW_GetPageTextToMemory(doc_handle, page):
    """XDW_GetPageTextToMemory(doc_handle, page)"""
    pass


@APPEND(NULL)
def XDW_GetFullText(doc_handle, output_path):
    """XDW_GetFullText(doc_handle, output_path)"""
    pass


@STRING
def XDW_GetPageUserAttribute(doc_handle, page, attr_name):
    """XDW_GetPageUserAttribute(doc_handle, page, attr_name)"""
    pass


@RAISE
def XDW_SetPageUserAttribute(doc_handle, page, attr_name, attr_val):
    """XDW_SetPageUserAttribute(doc_handle, page, attr_name, attr_val)"""
    size = attr_val and len(attr_val) or 0
    return DLL.XDW_SetPageUserAttribute(doc_handle, page, attr_name, attr_val, size, NULL)


@APPEND(NULL)
def XDW_ReducePageNoise(doc_handle, page, level):
    """XDW_ReducePageNoise(doc_handle, page, level)"""
    pass


@APPEND(NULL)
def XDW_ShowOrHideAnnotations(doc_handle, show_annotations):
    """XDW_ShowOrHideAnnotations(doc_handle, show_annotations)"""
    pass


@APPEND(NULL)
def XDW_GetCompressedPageImage(doc_handle, page, output_path):
    """XDW_GetCompressedPageImage(doc_handle, page, output_path)"""
    pass


@APPEND(NULL)
def XDW_InsertDocument(doc_handle, page, input_path):
    """XDW_InsertDocument(doc_handle, page, input_path)"""
    pass


@RAISE
def XDW_ApplyOcr(doc_handle, page, ocr_engine, option):
    """XDW_ApplyOcr(doc_handle, page, ocr_engine, option)"""
    return DLL.XDW_ApplyOcr(doc_handle, page, ocr_engine, ptr(option), NULL)


@APPEND(NULL)
def XDW_RotatePageAuto(doc_handle, page):
    """XDW_RotatePageAuto(doc_handle, page)"""
    pass


@RAISE
def XDW_CreateBinder(output_path, binder_init_dat):
    """XDW_CreateBinder(output_path, binder_init_dat)"""
    return DLL.XDW_CreateBinder(output_path, ptr(binder_init_dat), NULL)


@APPEND(NULL)
def XDW_InsertDocumentToBinder(doc_handle, pos, input_path):
    """XDW_InsertDocumentToBinder(doc_handle, pos, input_path)"""
    pass


@APPEND(NULL)
def XDW_GetDocumentFromBinder(doc_handle, pos, output_path):
    """XDW_GetDocumentFromBinder(doc_handle, pos, output_path)"""
    pass


@APPEND(NULL)
def XDW_DeleteDocumentInBinder(doc_handle, pos):
    """XDW_DeleteDocumentInBinder(doc_handle, pos)"""
    pass


@STRING
def XDW_GetDocumentNameInBinder(doc_handle, pos):
    """XDW_GetDocumentNameInBinder(doc_handle, pos)"""
    pass


@APPEND(NULL)
def XDW_SetDocumentNameInBinder(doc_handle, pos, document_name):
    """XDW_SetDocumentNameInBinder(doc_handle, pos, document_name)"""
    pass


def XDW_GetDocumentInformationInBinder(doc_handle, pos):
    """XDW_GetDocumentInformationInBinder(doc_handle, pos) --> document_info"""
    document_info = XDW_DOCUMENT_INFO()
    TRY(DLL.XDW_GetDocumentInformationInBinder, doc_handle, pos, byref(document_info), NULL)
    return document_info


@APPEND(NULL)
def XDW_Finalize():
    """XDW_Finalize()"""
    pass


def XDW_GetPageColorInformation(doc_handle, page):
    """XDW_GetPageColorInformation(doc_handle, page) --> page_color_info"""
    page_color_info = XDW_PAGE_COLOR_INFO()
    TRY(DLL.XDW_GetPageColorInformation, doc_handle, page, byref(page_color_info), NULL)
    return page_color_info


@APPEND(NULL)
def XDW_OptimizeDocument(input_path, output_path):
    """XDW_OptimizeDocument(input_path, output_path)"""
    pass


@RAISE
def XDW_ProtectDocument(input_path, output_path, protect_type, module_option, protect_option):
    """XDW_ProtectDocument(input_path, output_path, protect_type, module_option, protect_option)"""
    return DLL.XDW_ProtectDocument(input_path, output_path, protect_type, byref(module_option), byref(protect_option))


@RAISE
def XDW_CreateXdwFromImageFileAndInsertDocument(doc_handle, page, input_path, create_option):
    """XDW_CreateXdwFromImageFileAndInsertDocument(doc_handle, page, input_path, create_option)"""
    return DLL.XDW_CreateXdwFromImageFileAndInsertDocument(doc_handle, page, input_path, byref(create_option), NULL)


@APPEND(NULL)
def XDW_GetDocumentAttributeNumber(doc_handle):
    """XDW_GetDocumentAttributeNumber(doc_handle)"""
    pass


@ATTR
def XDW_GetDocumentAttributeByName(doc_handle, attr_name):
    """XDW_GetDocumentAttributeByName(doc_handle, attr_name) --> (attr_type, attr_val)"""
    pass


@ATTR(by_order=True)
def XDW_GetDocumentAttributeByOrder(doc_handle, order):
    """XDW_GetDocumentAttributeByOrder(doc_handle, order) --> (attr_name, attr_type, attr_val)"""
    pass


@APPEND(NULL)
def XDW_SetDocumentAttribute(doc_handle, attr_name, attr_type, attr_val):
    """XDW_SetDocumentAttribute(doc_handle, attr_name, attr_type, attr_val)"""
    pass


@APPEND(NULL)
def XDW_SucceedAttribute(doc_handle, file_path, document, succession):
    """XDW_SucceedAttribute(doc_handle, file_path, document, succession)"""
    pass


@STRING
def XDW_GetPageFormAttribute(doc_handle, page_form, attr_name):
    """XDW_GetPageFormAttribute(doc_handle, page_form, attr_name)"""
    pass


@APPEND(0, NULL)
def XDW_SetPageFormAttribute(doc_handle, page_form, attr_name, attr_type, attr_val):
    """XDW_SetPageFormAttribute(doc_handle, page_form, attr_name, attr_type, attr_val)"""
    pass


@APPEND(NULL)
def XDW_UpdatePageForm(doc_handle, other_page_form):
    """XDW_UpdatePageForm(doc_handle, other_page_form)"""
    pass


@APPEND(NULL)
def XDW_RemovePageForm(doc_handle, other_page_form):
    """XDW_RemovePageForm(doc_handle, other_page_form)"""
    pass


def XDW_GetLinkRootFolderInformation(order):
    """XDW_GetLinkRootFolderInformation(order) --> linkrootfolder_info"""
    linkrootfolder_info = XDW_LINKROOTFOLDER_INFO()
    TRY(DLL.XDW_GetLinkRootFolderInformation, order, byref(linkrootfolder_info), NULL)
    return linkrootfolder_info


@APPEND()
def XDW_GetLinkRootFolderNumber():
    """XDW_GetLinkRootFolderNumber()"""
    pass


# Undocumented API in DocuWorksTM Development Tool Kit 7.1
# int XDWAPI XDW_GetPageTextInformation(XDW_DOCUMENT_HANDLE handle, int nPage, void* pInfo, void* reserved);


def XDW_GetPageTextInformation(doc_handle, page):
    """XDW_GetPageTextInformation(doc_handle, page) --> gptiInfo"""
    gpti_info = XDW_GPTI_INFO()  # right?
    TRY(DLL.XDW_GetPageTextInformation, doc_handle, page, byref(gpti_info), NULL)
    return gpti_info


@APPEND(NULL)
def XDW_GetDocumentSignatureNumber(doc_handle):
    """XDW_GetDocumentSignatureNumber(doc_handle)"""
    pass


def XDW_AddAnnotationOnParentAnnotation(doc_handle, ann_handle, ann_type, hpos, vpos, init_dat):
    """XDW_AddAnnotationOnParentAnnotation(doc_handle, ann_handle, ann_type, hpos, vpos, init_dat) --> new_ann_handle"""
    new_ann_handle = XDW_ANNOTATION_HANDLE()
    TRY(DLL.XDW_AddAnnotationOnParentAnnotation, doc_handle, ann_handle, ann_type, hpos, vpos, ptr(init_dat), byref(new_ann_handle), NULL)
    return new_ann_handle


@RAISE
def XDW_SignDocument(input_path, output_path, option, module_option, module_status):
    """XDW_SignDocument(input_path, output_path, option, module_option, module_status)"""
    return DLL.XDW_SignDocument(input_path, output_path, byref(option), byref(module_option), NULL, byref(module_status))


def XDW_GetSignatureInformation(doc_handle, signature, module_info, module_status):
    """XDW_GetSignatureInformation(doc_handle, signature, module_info, module_status) --> signature_info_v5"""
    signature_info_v5 = XDW_SIGNATURE_INFO_V5()
    TRY(DLL.XDW_GetSignatureInformation, doc_handle, signature, byref(signature_info_v5), ptr(module_info), NULL, ptr(module_status))
    # NB. signature_info_v5.nSignedTime is UTC Unix time.
    return signature_info_v5


@RAISE
def XDW_UpdateSignatureStatus(doc_handle, signature, module_option, module_status):
    """XDW_UpdateSignatureStatus(doc_handle, signature, module_option, module_status)"""
    return XDW_UpdateSignatureStatus(doc_handle, signature, ptr(module_option), NULL, ptr(module_status))


@RAISE
def XDW_GetOcrImage(doc_handle, page, output_path, img_option):
    """XDW_GetOcrImage(doc_handle, page, output_path, img_option)"""
    return DLL.XDW_GetOcrImage(doc_handle, page, output_path, byref(img_option), NULL)


def XDW_SetOcrData(doc_handle, page):
    """XDW_SetOcrData(doc_handle, page) --> ocr_text_info"""
    ocr_text_info = XDW_OCR_TEXTINFO()
    TRY(DLL.XDW_SetOcrData, doc_handle, page, byref(ocr_text_info), NULL)
    return ocr_text_info


@APPEND(NULL)
def XDW_GetDocumentAttributeNumberInBinder(doc_handle, pos):
    """XDW_GetDocumentAttributeNumberInBinder(doc_handle, pos)"""
    pass


@ATTR
def XDW_GetDocumentAttributeByNameInBinder(doc_handle, pos, attr_name):
    """XDW_GetDocumentAttributeByNameInBinder(doc_handle, pos, attr_name) --> (attr_type, attr_val)"""
    pass


@ATTR(by_order=True)
def XDW_GetDocumentAttributeByOrderInBinder(doc_handle, pos, order):
    """XDW_GetDocumentAttributeByOrderInBinder(doc_handle, pos, order) --> (attr_name, attr_type, attr_val)"""
    pass

"""
int XDWAPI XDW_GetTMInfo(doc_handle, void* pTMInfo, int nTMInfoSize, void* reserved);
int XDWAPI XDW_SetTMInfo(doc_handle, const void* pTMInfo, int nTMInfoSize, void* reserved);
"""


@APPEND(NULL)
def XDW_CreateXdwFromImagePdfFile(input_path, output_path):
    """XDW_CreateXdwFromImagePdfFile(input_path, output_path)"""
    pass


def XDW_FindTextInPage(doc_handle, page, text, find_text_option):
    """XDW_FindTextInPage(doc_handle, page, text, find_text_option) --> found_handle"""
    found_handle = XDW_FOUND_HANDLE()
    TRY(DLL.XDW_FindTextInPage, doc_handle, page, text, ptr(find_text_option), byref(found_handle), NULL)
    return found_handle


def XDW_FindNext(found_handle):
    """XDW_FindNext(found_handle) --> found_handle"""
    TRY(DLL.XDW_FindNext, byref(found_handle), NULL)
    return found_handle


@RAISE
def XDW_GetNumberOfRectsInFoundObject(found_handle):
    """XDW_GetNumberOfRectsInFoundObject(found_handle)"""
    return DLL.XDW_GetNumberOfRectsInFoundObject(found_handle, NULL)


def XDW_GetRectInFoundObject(found_handle, pos):
    """XDW_GetRectInFoundObject(found_handle, pos) --> (rect, status)"""
    rect = XDW_RECT()
    status = c_int()
    TRY(DLL.XDW_GetRectInFoundObject, found_handle, pos, byref(rect), byref(status), NULL)
    return (rect, status.value)


@RAISE
def XDW_CloseFoundHandle(found_handle):
    """XDW_CloseFoundHandle(found_handle)"""
    return DLL.XDW_CloseFoundHandle(found_handle)


@STRING
def XDW_GetAnnotationUserAttribute(ann_handle, attr_name):
    """XDW_GetAnnotationUserAttribute(ann_handle, attr_name)"""
    pass


@RAISE
def XDW_SetAnnotationUserAttribute(doc_handle, ann_handle, attr_name, attr_val):
    """XDW_SetAnnotationUserAttribute(doc_handle, ann_handle, attr_name, attr_val)"""
    size = len(attr_val) if attr_val else 0
    return DLL.XDW_SetAnnotationUserAttribute(doc_handle, ann_handle, attr_name, attr_val, size, NULL)


@APPEND(NULL)
def XDW_StarchAnnotation(doc_handle, ann_handle, starch):
    """XDW_StarchAnnotation(doc_handle, ann_handle, starch)"""
    pass


@RAISE
def XDW_ReleaseProtectionOfDocument(input_path, output_path, release_protection_option):
    """XDW_ReleaseProtectionOfDocument(input_path, output_path, release_protection_option)"""
    return DLL.XDW_ReleaseProtectionOfDocument(input_path, output_path, byref(release_protection_option))


def XDW_GetProtectionInformation(input_path):
    """XDW_GetProtectionInformation(input_path) --> protection_info"""
    protection_info = XDW_PROTECTION_INFO()
    TRY(DLL.XDW_GetProtectionInformation, input_path, byref(protection_info), NULL)
    return protection_info


@ATTR
def XDW_GetAnnotationCustomAttributeByName(ann_handle, attr_name):
    """XDW_GetAnnotationCustomAttributeByName(ann_handle, attr_name) --> (attr_type, attr_val)"""
    pass


@ATTR(by_order=True)
def XDW_GetAnnotationCustomAttributeByOrder(ann_handle, order):
    """XDW_GetAnnotationCustomAttributeByOrder(ann_handle, order) --> (attr_name, attr_type, attr_val)"""
    pass


@APPEND(NULL)
def XDW_GetAnnotationCustomAttributeNumber(ann_handle):
    """XDW_GetAnnotationCustomAttributeNumber(ann_handle)"""
    pass


@APPEND(NULL)
def XDW_SetAnnotationCustomAttribute(doc_handle, ann_handle, attr_name, attr_type, attr_val):
    """XDW_SetAnnotationCustomAttribute(doc_handle, ann_handle, attr_name, attr_type, attr_val)"""
    pass


@UNICODE
def XDW_GetPageTextToMemoryW(doc_handle, page):
    """XDW_GetPageTextToMemoryW(doc_handle, page)"""
    pass


@APPEND(NULL)
def XDW_GetFullTextW(doc_handle, output_path):
    """XDW_GetFullTextW(doc_handle, output_path)"""
    pass


def XDW_GetAnnotationAttributeW(ann_handle, attr_name, codepage=932):
    """XDW_GetAnnotationAttributeW(ann_handle, attr_name, codepage=932) --> (attr_type, attr_val, text_type)"""
    data_type = XDW_ANNOTATION_ATTRIBUTE[attr_name][0]
    text_type = c_int()
    size = TRY(DLL.XDW_GetAnnotationAttributeW, ann_handle, attr_name, NULL, 0, byref(text_type), codepage, NULL)
    if data_type == XDW_ATYPE_INT:
        attr_val = c_int()
    elif data_type == XDW_ATYPE_STRING:
        attr_val = create_unicode_buffer(size)
    else:  # data_type == 2
        count = size / sizeof(XDW_POINT)
        attr_val = (XDW_POINT * count)()
    TRY(DLL.XDW_GetAnnotationAttributeW, ann_handle, attr_name, byref(attr_val), size, byref(text_type), codepage, NULL)
    if data_type == XDW_ATYPE_INT:
        return (data_type, attr_val.value, XDW_TEXT_UNKNOWN)
    elif data_type == XDW_ATYPE_STRING:
        return (data_type, attr_val.value, text_type.value)
    else:  # data_type == 2
        return (XDW_ATYPE_OTHER, attr_val, XDW_TEXT_UNKNOWN)


@APPEND(0, NULL)
def XDW_SetAnnotationAttributeW(doc_handle, ann_handle, attr_name, attr_type, attr_val, text_type, codepage=932):
    """XDW_SetAnnotationAttributeW(doc_handle, ann_handle, attr_name, attr_type, attr_val, text_type, codepage=932)"""
    pass


@ATTR(widechar=True)
def XDW_GetDocumentAttributeByNameW(doc_handle, attr_name, codepage=932):
    """XDW_GetDocumentAttributeByNameW(doc_handle, attr_name, codepage=932) --> (attr_type, attr_val, text_type)"""
    pass


@ATTR(by_order=True, widechar=True)
def XDW_GetDocumentAttributeByOrderW(doc_handle, order, codepage=932):
    """XDW_GetDocumentAttributeByOrderW(doc_handle, order, codepage=932) --> (attr_name, attr_type, attr_val, text_type)"""
    pass


@ATTR(widechar=True)
def XDW_GetDocumentAttributeByNameInBinderW(doc_handle, pos, attr_name, codepage=932):
    """XDW_GetDocumentAttributeByNameInBinderW(doc_handle, pos, attr_name, codepage=932) --> (attr_type, attr_val, text_type)"""
    pass


@ATTR(by_order=True, widechar=True)
def XDW_GetDocumentAttributeByOrderInBinderW(doc_handle, pos, order, codepage=932):
    """XDW_GetDocumentAttributeByOrderInBinderW(doc_handle, pos, order, codepage=932) --> (attr_name, attr_type, attr_val, text_type)"""
    pass


@APPEND(NULL)
def XDW_SetDocumentAttributeW(doc_handle, attr_name, attr_type, attr_val, text_type, codepage=932):
    """XDW_SetDocumentAttributeW(doc_handle, attr_name, attr_type, attr_val, text_type, codepage=932)"""
    pass


def XDW_GetDocumentNameInBinderW(doc_handle, pos, codepage=932):
    """XDW_GetDocumentNameInBinderW(doc_handle, pos, codepage=932) --> (doc_name, text_type)"""
    text_type = c_int()
    size = TRY(DLL.XDW_GetDocumentNameInBinderW, doc_handle, pos, NULL, 0, byref(text_type), codepage, NULL)
    doc_name = create_unicode_buffer(size)
    TRY(DLL.XDW_GetDocumentNameInBinderW, doc_handle, pos, byref(doc_name), size, byref(text_type), codepage, NULL)
    return (doc_name.value, text_type.value)


@APPEND(NULL)
def XDW_SetDocumentNameInBinderW(doc_handle, pos, doc_name, text_type, codepage=932):
    """XDW_SetDocumentNameInBinderW(doc_handle, pos, doc_name, text_type, codepage=932)"""
    pass


def XDW_GetOriginalDataInformationW(doc_handle, org_data, codepage=932):
    """XDW_GetOriginalDataInformationW(doc_handle, org_data, codepage=932) --> (orgdata_infow, text_type)"""
    text_type = c_int()
    orgdata_infow = XDW_ORGDATA_INFOW()
    TRY(DLL.XDW_GetOriginalDataInfomationW, doc_handle, org_data, byref(orgdata_infow), byref(text_type), codepage, NULL)
    return (orgdata_infow, text_type.value)
    # NB. orgdata_infow.nDate is UTC Unix time.