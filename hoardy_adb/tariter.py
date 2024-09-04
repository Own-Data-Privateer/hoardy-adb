# This file is a part of kisstdlib project.
#
# This file is a streaming/iterator version of Python's `tarfile`.
# I.e. you give it a file-like object, it returns an iterator.
# The file object will be read once, without seeking, which is not true for `tarfile`.
#
# Copyright (c) 2018-2024 Jan Malakhovski <oxij@oxij.org>
# Copyright (c) 2002 Lars Gustaebel <lars@gustaebel.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import dataclasses as _dc
import typing as _t

from .exceptions import *

BUFFER_SIZE = 16 * 1024 ** 2

def nts(s : bytes, encoding : str, errors : str) -> str:
    """Convert a null-terminated bytes object to a string.
    """
    p = s.find(b"\0")
    if p != -1:
        s = s[:p]
    return s.decode(encoding, errors)

class ParsingError(Failure): pass
class InvalidHeader(ParsingError): pass

def nti(s : bytes) -> int:
    """Convert a number field to a python number.
    """
    # There are two possible encodings for a number field, see
    # itn() below.
    if s[0] in (0o200, 0o377):
        n = 0
        for i in range(len(s) - 1):
            n <<= 8
            n += s[i + 1]
        if s[0] == 0o377:
            n = -(256 ** (len(s) - 1) - n)
    else:
        try:
            ss = nts(s, "ascii", "strict")
            n = int(ss.strip() or "0", 8)
        except ValueError:
            raise InvalidHeader("invalid TAR header")
    return n

@_dc.dataclass
class TarHeader:
    """Informational class which holds the details about TAR file header.
    """
    path : str
    mode : int
    uid : int
    gid : int
    size : int
    leftovers : int
    mtime : int
    chksum : int
    ftype : bytes
    linkpath : str
    uname : str
    gname : str
    devmajor : int
    devminor : int

    raw : bytes
    pax_headers : _t.Dict[str, _t.Any]

def parse_pax_headers(data : bytes) -> _t.Dict[str, _t.Any]:
    res = dict()
    try:
        while len(data) > 0:
            size_, _ = data.split(b" ", 1)
            size = int(size_)
            if size < 1 or data[size-1:size] != b"\n":
                raise ValueError()
            pax_value = data[:size - 1]
            data = data[size:]

            _, rest = pax_value.split(b" ", 1)
            name, value = rest.split(b"=", 1)
            res[name.decode("ascii", "strict")] = value
    except ValueError:
        raise InvalidHeader("invalid PAX header data")
    return res

def yield_tar_headers(fobj : _t.Any, encoding : str = "utf-8", errors : str = "surrogateescape") -> _t.Iterator[TarHeader]:
    """Given a file-like object `fobj`, parse and yield the next TAR file header,
       repeatedly. PAX headers will be parsed and skipped over and normal TAR
       headers will be updated based the results, but for other header types
       it's caller's responsibility to skip or seek over file data in `fobj`
       before calling `next()` on this iterator.
    """
    global_pax_headers = dict()
    pax_headers = dict()

    empty = 0
    while True:
        buf = fobj.read(512)
        if len(buf) != 512:
            raise ParsingError("unexpected EOF")

        path = nts(buf[0:100], encoding, errors)
        size = nti(buf[124:136])

        if path == "" and size == 0:
            # empty header
            empty += 1
            if empty >= 2: break
            else: continue

        if buf[257:265] != b"ustar\x0000":
            raise InvalidHeader("invalid TAR header, expecting UStar format")

        mode = nti(buf[100:108])
        uid = nti(buf[108:116])
        gid = nti(buf[116:124])
        mtime = nti(buf[136:148])
        chksum = nti(buf[148:156])
        ftype = buf[156:157]
        linkpath = nts(buf[157:257], encoding, errors)
        uname = nts(buf[265:297], encoding, errors)
        gname = nts(buf[297:329], encoding, errors)
        devmajor = nti(buf[329:337])
        devminor = nti(buf[337:345])
        prefix = nts(buf[345:500], encoding, errors)

        if prefix != "":
            path = prefix + "/" + path

        if ftype == b"x" or ftype == b"g":
            # parse and process PAX headers, see "pax Header Block" section in `man 1 pax`
            leftovers = 0
            if size % 512 != 0:
                leftovers = 512 - size % 512

            pax_data = fobj.read(size)
            if len(pax_data) != size:
                raise ParsingError("unexpected EOF")

            pax_leftovers = fobj.read(leftovers)
            if len(pax_leftovers) != leftovers:
                raise ParsingError("unexpected EOF")

            pax_prefix = b"".join([buf, pax_data, pax_leftovers])
            parsed_headers = parse_pax_headers(pax_data)
            del pax_data
            del pax_leftovers

            yield TarHeader(path, mode, uid, gid,
                            0, 0,
                            mtime, chksum, ftype,
                            linkpath, uname, gname,
                            devmajor, devminor,
                            pax_prefix, dict())

            if ftype == b"g":
                global_pax_headers = parsed_headers
                pax_headers = global_pax_headers.copy()
            else:
                pax_headers = global_pax_headers.copy()
                pax_headers.update(parsed_headers)

            try:
                hcharset = pax_headers["hdrcharset"]
            except KeyError:
                charset = encoding
            else:
                if hcharset == b"ISO-IR 10646 2000 UTF-8":
                    charset = "utf-8"
                elif hcharset == b"BINARY":
                    charset = encoding
                else:
                    raise InvalidHeader("invalid PAX header data: unknown hdrcharset")

            for k in pax_headers:
                v = pax_headers[k]
                v_ : _t.Any
                if k in ["path", "linkpath", "uname", "gname"]:
                    try:
                        v_ = v.decode(charset)
                    except UnicodeEncodeError:
                        raise InvalidHeader("invalid PAX header data: can't decode str")
                elif k in ["size", "uid", "gid", "atime", "mtime"]:
                    try:
                        v_ = int(v.decode("ascii", "strict"))
                    except Exception:
                        raise InvalidHeader("invalid PAX header data: can't decode int")
                else:
                    raise InvalidHeader("invalid PAX header data: unknown header `%s`", k)
                pax_headers[k] = v_

            continue

        # generate TAR header
        header = TarHeader(path, mode, uid, gid,
                           size, 0,
                           mtime, chksum, ftype,
                           linkpath, uname, gname,
                           devmajor, devminor,
                           buf, pax_headers)

        # update values from pax_headers
        for k, v in pax_headers.items():
            if hasattr(header, k):
                setattr(header, k, v)

        # compute leftovers for size possibly updated from pax_headers
        size = header.size
        leftovers = 0
        if size % 512 != 0:
            leftovers = 512 - size % 512
        header.leftovers = leftovers

        yield header
        pax_headers = dict()

def iter_tar_headers(fobj : _t.Any, encoding : str = "utf-8", errors : str = "surrogateescape") -> _t.Iterator[TarHeader]:
    """Given a file-like object `fobj`, iterate over its parsed non-PAX TAR file
       headers. File data will `read` and thrown out.
    """
    for h in yield_tar_headers(fobj, encoding, errors):
        ftype = h.ftype
        if ftype not in [b"g", b"x"]:
            yield h
        fsize = h.size + h.leftovers
        while fsize > 0:
            data = fobj.read(min(fsize, BUFFER_SIZE))
            if len(data) == 0:
                raise ParsingError("unexpected EOF")
            fsize -= len(data)
