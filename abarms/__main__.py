#!/usr/bin/env python3
#
# This file is a part of abarms project.
#
# Copyright (c) 2018-2024 Jan Malakhovski <oxij@oxij.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import io
import os
import secrets
import re
import struct
import sys
import time
import typing as _t
import zlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.padding import PKCS7
from gettext import gettext, ngettext

from . import argparse_better as argparse
from .argparse_better import Namespace
from .exceptions import *
from . import tariter

BUFFER_SIZE = 16 * 1024 ** 2

class ReadProxy:
    def __init__(self, fobj : _t.Any, block_size : int) -> None:
        self._fobj = fobj
        self._block_size = block_size
        self._buffer = b""
        self._eof = False

    def _handle_eof(self) -> bytes:
        raise NotImplementedError

    def _handle_data(self, data : bytes) -> bytes:
        raise NotImplementedError

    def read(self, size : int = -1) -> bytes:
        while not self._eof and (size == -1 or len(self._buffer) < size):
            data = self._fobj.read(self._block_size)
            if len(data) == 0:
                self._buffer += self._handle_eof()
                self._eof = True
            else:
                self._buffer += self._handle_data(data)

        if len(self._buffer) == 0:
            return b""

        if size == -1 or len(self._buffer) == size:
            res = self._buffer
            self._buffer = b""
            return res
        else:
            res = self._buffer[:size]
            self._buffer = self._buffer[len(res):]
            return res

    def tell(self) -> int:
        return self._fobj.tell() # type: ignore

    def fileno(self) -> int:
        return self._fobj.fileno() # type: ignore

    def close(self) -> None:
        self._fobj.close()

class ReadPreprocessor(ReadProxy):
    def __init__(self, preprocessor : _t.Any, fobj : _t.Any, block_size : int) -> None:
        super().__init__(fobj, block_size)
        self._preprocessor = preprocessor

    def _handle_eof(self) -> bytes:
        return self._preprocessor.finalize() # type: ignore

    def _handle_data(self, data : bytes) -> bytes:
        return self._preprocessor.update(data) # type: ignore

class WritePreprocessor:
    def __init__(self, preprocessor : _t.Any, fobj : _t.Any) -> None:
        self._fobj = fobj
        self._preprocessor = preprocessor

    def write(self, data : bytes) -> None:
        self._fobj.write(self._preprocessor.update(data))

    def flush(self) -> None:
        self._fobj.write(self._preprocessor.finalize())
        self._fobj.flush()

    def close(self) -> None:
        self._fobj.close()

class Decompressor(ReadProxy):
    def __init__(self, fobj : _t.Any, block_size : int) -> None:
        super().__init__(fobj, block_size)
        self._decompressor = zlib.decompressobj(0)

    def _handle_eof(self) -> bytes:
        return self._decompressor.flush()

    def _handle_data(self, data : bytes) -> bytes:
        return self._decompressor.decompress(data)

class Compressor:
    def __init__(self, fobj : _t.Any) -> None:
        self._fobj = fobj
        self._compressor = zlib.compressobj()

    def write(self, data : bytes) -> None:
        self._fobj.write(self._compressor.compress(data))

    def flush(self) -> None:
        self._fobj.write(self._compressor.flush())
        self._fobj.flush()

    def close(self) -> None:
        self._fobj.close()

def androidKDF(length : int, salt : bytes, iterations : int, passphrase : bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(passphrase)

def make_mangled_key(master_key : bytes) -> bytes:
    # this is actually what Java does on implicit conversion from String
    # to Bytes: it smears the last bit into the next byte; inspired by a
    # similar, but less comprehensible, line in
    # https://github.com/xBZZZZ/abpy
    c = 255 << 8
    return "".join(chr(x | (0 if x < 128 else c)) for x in master_key).encode("utf8")

def getpass(prompt : str = "Passphrase: ") -> bytes:
    import termios
    with open("/dev/tty", "r+b", buffering=0) as tty:
        tty.write(b"Passphrase: ")
        old = termios.tcgetattr(tty)
        new = termios.tcgetattr(tty)
        new[3] = new[3] & ~termios.ECHO
        try:
            termios.tcsetattr(tty, termios.TCSADRAIN, new)
            data = tty.readline()
            tty.write(b"\n")
        finally:
            termios.tcsetattr(tty, termios.TCSADRAIN, old)

        if data[-2:] == b"\r\n": data = data[:-2]
        elif data[-1:] == b"\n": data = data[:-1]
        return data

def begin_input(cfg : Namespace, input_exts : _t.List[str]) -> None:
    if cfg.input_file == "-":
        cfg.basename = "backup"
        cfg.input = os.fdopen(0, "rb")
        return

    cfg.input_file = os.path.expanduser(cfg.input_file)

    root, ext = os.path.splitext(cfg.input_file)
    if ext in input_exts:
        cfg.basename = root
    else:
        cfg.basename = cfg.input_file

    try:
        cfg.input = open(cfg.input_file, "rb")
    except FileNotFoundError:
        raise CatastrophicFailure(gettext("file `%s` does not exists"), cfg.input_file)

    cfg.input_size = None
    if cfg.input.seekable():
        cfg.input_size = cfg.input.seek(0, io.SEEK_END)
        cfg.input.seek(0)

def get_passphrase(cfg_passphrase : str, cfg_passfile : str, basename : _t.Optional[str]) -> _t.Optional[bytes]:
    passphrase = None
    if cfg_passphrase is not None:
        passphrase = os.fsencode(cfg_passphrase)
    elif cfg_passfile is not None:
        try:
            with open(cfg_passfile, "rb") as f:
                passphrase = f.read()
        except FileNotFoundError:
            raise CatastrophicFailure(gettext("file `%s` does not exists"), cfg_passfile)
    elif basename:
        passfile = basename + ".passphrase.txt"
        try:
            with open(passfile, "rb") as f:
                passphrase = f.read()
        except FileNotFoundError:
            pass
    return passphrase

def begin_ab_input(cfg : Namespace, decompress : bool = True) -> None:
    begin_input(cfg, [".ab", ".adb"])

    passphrase = get_passphrase(cfg.passphrase, cfg.passfile,
                                cfg.basename if cfg.input_file != "-" else None)

    # The original backing up code: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/master/services/backup/java/com/android/server/backup/fullbackup/PerformAdbBackupTask.java
    def readline(what : str) -> bytes:
        data : bytes = cfg.input.readline()
        if data[-1:] == b"\n":
            data = data[:-1]
        else:
            raise CatastrophicFailure(gettext("%s: unable to parse header: %s"), cfg.input_file, what)
        return data

    def readint(what : str) -> int:
        data = readline(what)
        try:
            res = int(data)
        except Exception:
            raise CatastrophicFailure(gettext("%s: unable to parse header: %s"), cfg.input_file, what)
        return res

    def readhex(what : str) -> bytes:
        data = readline(what)
        try:
            res = bytes.fromhex(data.decode("ascii"))
        except Exception:
            raise CatastrophicFailure(gettext("%s: unable to parse header: %s"), cfg.input_file, what)
        return res

    magic = readline("magic")
    if magic != b"ANDROID BACKUP":
        raise CatastrophicFailure(gettext("%s: not an Android Backup file"), cfg.input_file)

    version = readint("version")
    if version < 1 or version > 5:
        raise CatastrophicFailure(gettext("%s: unknown Android Backup version: %s"), cfg.input_file, version)
    cfg.input_version = version

    compression = readint("compression")
    if compression not in [0, 1]:
        raise CatastrophicFailure(gettext("%s: unknown Android Backup compression: %s"), cfg.input_file, compression)
    cfg.input_compression = compression

    encryption = readline("encryption")
    cfg.input_encryption = encryption

    algo = encryption.upper()
    if algo == b"NONE":
        pass
    elif algo == b"AES-256":
        user_salt = readhex("user_salt")
        checksum_salt = readhex("checksum_salt")
        iterations = readint("iterations")
        user_iv = readhex("user_iv")
        user_blob = readhex("user_blob")

        if passphrase is None:
            passphrase = getpass()

        blob_key = androidKDF(32, user_salt, iterations, passphrase)

        decryptor = Cipher(algorithms.AES(blob_key), modes.CBC(user_iv)).decryptor()
        unpadder = PKCS7(128).unpadder()
        try:
            data = decryptor.update(user_blob) + decryptor.finalize()
            decrypted_blob = unpadder.update(data) + unpadder.finalize()
        except:
            raise CatastrophicFailure(gettext("%s: failed to decrypt, wrong passphrase?"), cfg.input_file)

        state = {"data": decrypted_blob}

        def readb(want : int) -> bytes:
            blob = state["data"]
            length = struct.unpack("B", blob[:1])[0]
            if length != want:
                raise CatastrophicFailure(gettext("%s: failed to decrypt, wrong passphrase?"), cfg.input_file)
            data = blob[1:length + 1]
            blob = blob[length + 1:]
            state["data"] = blob
            return data

        master_iv = readb(16)
        master_key = readb(32)
        checksum = readb(32)

        mangled_master_key = make_mangled_key(master_key)
        ok_checksum = cfg.ignore_checksum
        for key in [mangled_master_key, master_key]:
            our_checksum = androidKDF(32, checksum_salt, iterations, key)
            if checksum == our_checksum:
                ok_checksum = True
                break

        if not ok_checksum:
            raise CatastrophicFailure(gettext("%s: bad Android Backup checksum, wrong passphrase?"), cfg.input_file)

        decryptor = Cipher(algorithms.AES(master_key), modes.CBC(master_iv)).decryptor()
        cfg.input = ReadPreprocessor(decryptor, cfg.input, BUFFER_SIZE)

        unpadder = PKCS7(128).unpadder()
        cfg.input = ReadPreprocessor(unpadder, cfg.input, BUFFER_SIZE)
    else:
        raise CatastrophicFailure(gettext("%s: unknown Android Backup encryption: %s"), cfg.input_file, algo)

    if decompress and compression == 1:
        cfg.input = Decompressor(cfg.input, BUFFER_SIZE)

def begin_output_encryption(cfg : Namespace) -> None:
    if cfg.encrypt:
        cfg.output_passphrase_bytes = get_passphrase(cfg.output_passphrase, cfg.output_passfile, None)
        if cfg.output_passphrase_bytes is None:
            raise CatastrophicFailure(gettext("you are trying to `--encrypt` with no `--output-passphrase` or `--output-passfile` specified"))

def begin_output(cfg : Namespace, output_ext : str) -> None:
    if cfg.output_file is None:
        if cfg.input_file != "-":
            cfg.output_file = cfg.basename + output_ext
        else:
            cfg.output_file = "-"

    if cfg.output_file == "-":
        cfg.output = os.fdopen(1, "wb")
        cfg.report = False # let's not clutter the tty when inside a pipe
        return

    cfg.output_file = os.path.expanduser(cfg.output_file)
    try:
        cfg.output = open(cfg.output_file, "xb")
    except FileExistsError:
        raise CatastrophicFailure(gettext("file `%s` already exists"), cfg.output_file)

    if cfg.report:
        sys.stderr.write("Writing output to `%s`..." % (cfg.output_file,))
        sys.stderr.flush()

def begin_ab_header(cfg : Namespace, output : _t.Any, output_version : int) -> _t.Any:
    output_compression = 1 if cfg.compress else 0
    output_encryption = b"AES-256" if cfg.encrypt else b"none"
    output.write(b"ANDROID BACKUP\n%d\n%d\n%s\n" % (output_version, output_compression, output_encryption))
    if cfg.encrypt:
        user_salt = secrets.token_bytes(cfg.salt_bytes)
        checksum_salt = secrets.token_bytes(cfg.salt_bytes)
        iterations = cfg.iterations
        user_iv = secrets.token_bytes(16)

        master_iv = secrets.token_bytes(16)
        master_key = secrets.token_bytes(32)

        key = make_mangled_key(master_key)
        checksum = androidKDF(32, checksum_salt, iterations, key)

        plain_blob = \
            struct.pack("B", 16) + master_iv + \
            struct.pack("B", 32) + master_key + \
            struct.pack("B", 32) + checksum

        blob_key = androidKDF(32, user_salt, iterations, cfg.output_passphrase_bytes)
        encryptor = Cipher(algorithms.AES(blob_key), modes.CBC(user_iv)).encryptor()
        padder = PKCS7(128).padder()

        padded_blob = padder.update(plain_blob) + padder.finalize()
        user_blob = encryptor.update(padded_blob) + encryptor.finalize()

        enc_header = \
            user_salt.hex().upper() + "\n" + \
            checksum_salt.hex().upper() + "\n" + \
            str(iterations) + "\n" + \
            user_iv.hex().upper() + "\n" + \
            user_blob.hex().upper() + "\n"

        output.write(enc_header.encode("ascii"))

        encryptor = Cipher(algorithms.AES(master_key), modes.CBC(master_iv)).encryptor()
        output = WritePreprocessor(encryptor, output)

        padder = PKCS7(128).padder()
        output = WritePreprocessor(padder, output)
    if cfg.compress:
        output = Compressor(output)
    return output

def begin_ab_output(cfg : Namespace, output_ext : str, output_version : int) -> None:
    begin_output_encryption(cfg)
    begin_output(cfg, output_ext)
    cfg.output = begin_ab_header(cfg, cfg.output, output_version)

prev_percent = None
def report_progress(cfg : Namespace) -> None:
    if not cfg.report: return

    global prev_percent
    percent = 100 * cfg.input.tell() / cfg.input_size
    if prev_percent == percent: return
    prev_percent = percent

    sys.stderr.write("\r\033[KWriting output to `%s`... %d%%" % (cfg.output_file, percent))
    sys.stderr.flush()

def copy_input_to_output(cfg : Namespace, report : bool = True) -> None:
    while True:
        data = cfg.input.read(BUFFER_SIZE)
        if data == b"": break
        cfg.output.write(data)
        if report:
            report_progress(cfg)

def finish_input(cfg : Namespace) -> None:
    cfg.input.close()

def finish_output(cfg : Namespace) -> None:
    cfg.output.flush()
    cfg.output.close()

    if cfg.report:
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()

def str_ftype(ftype : bytes) -> str:
    if ftype == b"\x00" or ftype == b"0":
        return "-"
    elif ftype == b"1":
        return "h"
    elif ftype == b"2":
        return "l"
    elif ftype == b"3":
        return "c"
    elif ftype == b"4":
        return "b"
    elif ftype == b"5":
        return "d"
    elif ftype == b"6":
        return "f"
    else:
        raise CatastrophicFailure(gettext("unknown TAR header file type: %s"), repr(ftype))

def str_modes(mode : int) -> str:
    mode_ = oct(mode)[2:]
    if len(mode_) > 3:
        mode_ = mode_[-3:]
    mode = int(mode_, 8)

    res = ""
    rwx = ["r", "w", "x"]
    n = 0
    for b in bin(mode)[2:]:
        if b == "0":
            res += "-"
        else:
            res += rwx[n % 3]
        n += 1
    return res

def str_uidgid(uid : int, gid : int, uname : str, gname : str) -> str:
    res = ""
    if uname != "":
        res += uname
    else:
        res += str(uid)
    res += "/"
    if gname != "":
        res += gname
    else:
        res += str(gid)

    return res.ljust(12)

def str_size(x : int) -> str:
    return str(x).rjust(8)

def str_mtime(x : int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x))

def ab_ls(cfg : Namespace) -> None:
    begin_ab_input(cfg)
    print("# Android Backup, version: %d, compression: %d, encryption: %s" % (cfg.input_version, cfg.input_compression, cfg.input_encryption.decode("ascii", "ignore")))
    for h in tariter.iter_tar_headers(cfg.input):
        print(str_ftype(h.ftype) + str_modes(h.mode),
              str_uidgid(h.uid, h.gid, h.uname, h.gname),
              str_size(h.size), str_mtime(h.mtime), h.path)
    finish_input(cfg)

def ab_strip(cfg : Namespace) -> None:
    if cfg.keep_compression:
        begin_ab_input(cfg, False)
        begin_output(cfg, ".stripped.ab")
        cfg.output.write(b"ANDROID BACKUP\n%d\n%d\nnone\n" % (cfg.input_version, cfg.input_compression))
        copy_input_to_output(cfg)
    else:
        begin_ab_input(cfg)
        begin_ab_output(cfg, ".stripped.ab", cfg.input_version)
        copy_input_to_output(cfg)
    finish_input(cfg)
    finish_output(cfg)

def write_tar(pax_header : _t.Optional[bytes], h : tariter.TarHeader, input : _t.Any, output : _t.Any) -> None:
    if pax_header is not None:
        output.write(pax_header)

    output.write(h.raw)
    fsize = h.size + h.leftovers
    while fsize > 0:
        data = input.read(min(fsize, BUFFER_SIZE))
        if len(data) == 0:
            raise tariter.ParsingError("unexpected EOF")
        fsize -= len(data)
        output.write(data)

def finish_tar(output : _t.Any) -> None:
    output.write(b"\0" * 1024)
    output.flush()
    output.close()

def ab_split(cfg : Namespace) -> None:
    begin_output_encryption(cfg)
    begin_ab_input(cfg)

    if cfg.prefix is None:
        dirname = os.path.dirname(cfg.basename)
        basename = os.path.basename(cfg.basename)
        cfg.prefix = os.path.join(dirname, "abarms_split_" + basename)

    print("# Android Backup, version: %d, compression: %d" % (cfg.input_version, cfg.input_compression))

    output : _t.Optional[_t.Any] = None
    fname : _t.Optional[str] = None
    app : _t.Optional[str] = None
    appnum = 0

    global_pax_header : _t.Optional[bytes] = None
    pax_header : _t.Optional[bytes] = None

    for h in tariter.yield_tar_headers(cfg.input):
        ftype = h.ftype
        if ftype == b"g":
            global_pax_header = h.raw
            pax_header = None
            continue
        elif ftype == b"x":
            pax_header = h.raw
            continue

        happ = "other"
        spath = h.path.split("/")
        if len(spath) > 2 and spath[0] == "apps":
            happ = spath[1]

        if app is None or happ != app:
            if output is not None:
                # finish the previous one
                finish_tar(output)
                appnum += 1

            app = happ
            fname = "%s_%03d_%s.ab" % (cfg.prefix, appnum, app)
            try:
                output = open(fname, "xb")
            except FileExistsError:
                raise CatastrophicFailure(gettext("file `%s` already exists"), fname)

            if cfg.report:
                sys.stderr.write("Writing `%s`...\n" % (fname,))
                sys.stderr.flush()

            output = begin_ab_header(cfg, output, cfg.input_version)
            if global_pax_header is not None:
                output.write(global_pax_header)

        write_tar(pax_header, h, cfg.input, output)
        pax_header = None

    if output is not None:
        # finish last
        finish_tar(output)

    finish_input(cfg)

def ab_merge(cfg : Namespace) -> None:
    cfg.output = None
    input_version = 0
    for input_file in cfg.input_files:
        cfg.input_file = input_file
        begin_ab_input(cfg)
        if cfg.output is None:
            input_version = cfg.input_version
            begin_ab_output(cfg, ".merged.ab", input_version)
        elif cfg.input_version != input_version:
            raise CatastrophicFailure(gettext("can't merge files with different Android Backup versions: `%s` is has version %d, but we are merging into version %d"), cfg.input_file, cfg.input_version, input_version)

        if cfg.report:
            sys.stderr.write("Merging `%s`...\n" % (input_file,))
            sys.stderr.flush()

        for h in tariter.yield_tar_headers(cfg.input):
            write_tar(None, h, cfg.input, cfg.output)

        finish_input(cfg)
    finish_tar(cfg.output)

def ab_unwrap(cfg : Namespace) -> None:
    begin_ab_input(cfg)
    begin_output(cfg, ".tar")
    copy_input_to_output(cfg)
    finish_input(cfg)
    finish_output(cfg)

def ab_wrap(cfg : Namespace) -> None:
    begin_input(cfg, [".tar"])
    begin_ab_output(cfg, ".ab", cfg.output_version)
    copy_input_to_output(cfg)
    finish_input(cfg)
    finish_output(cfg)

def add_examples(fmt : _t.Any) -> None:
    fmt.add_text("# Usage notes")

    fmt.add_text('Giving an encrypted `INPUT_AB_FILE` as input, not specifying `--passphrase` or `--passfile`, and not having a file named `{INPUT_AB_FILE with ".ab" or ".adb" extension replaced with ".passphrase.txt"}` in the same directory will case the passphrase to be read interactively from the tty.')

    fmt.add_text("# Examples")

    fmt.start_section("List contents of an Android Backup file")
    fmt.add_code(f"{__package__} ls backup.ab")
    fmt.end_section()

    fmt.start_section(f"Use `tar` util to list contents of an Android Backup file instead of running `{__package__} ls`")
    fmt.add_code(f"{__package__} unwrap backup.ab - | tar -tvf -")
    fmt.end_section()

    fmt.start_section("Extract contents of an Android Backup file")
    fmt.add_code(f"{__package__} unwrap backup.ab - | tar -xvf -")
    fmt.end_section()

    fmt.start_section("Strip encryption and compression from an Android Backup file")
    fmt.add_code(f"""# equivalent
{__package__} strip backup.ab backup.stripped.ab
{__package__} strip backup.ab
""")
    fmt.add_code(f"""# equivalent
{__package__} strip --passphrase secret backup.ab
{__package__} strip -p secret backup.ab
""")
    fmt.add_code(f"""# with passphrase taken from a file
echo -n secret > backup.passphrase.txt
# equivalent
{__package__} strip backup.ab
{__package__} strip --passfile backup.passphrase.txt backup.ab
""")
    fmt.add_code(f"""# with a weird passphrase taken from a file
echo -ne "secret\\r\\n\\x00another line" > backup.passphrase.txt
{__package__} strip backup.ab
""")
    fmt.end_section()

    fmt.start_section("Strip encryption but keep compression, if any")
    fmt.add_code(f"""# equivalent
{__package__} strip --keep-compression backup.ab backup.stripped.ab
{__package__} strip -k backup.ab
""")
    fmt.end_section()

    fmt.start_section("Strip encryption and compression from an Android Backup file and then re-compress using `xz`")
    fmt.add_code(f"""{__package__} strip backup.ab - | xz --compress -9 - > backup.ab.xz
# ... and then convert to tar and list contents:
xzcat backup.ab.xz | {__package__} unwrap - | tar -tvf -
""")
    fmt.end_section()

    fmt.start_section("Convert an Android Backup file into a TAR archive")
    fmt.add_code(f"""# equivalent
{__package__} unwrap backup.ab backup.tar
{__package__} unwrap backup.ab
""")
    fmt.end_section()

    fmt.start_section("Convert a TAR archive into an Android Backup file")
    fmt.add_code(f"""# equivalent
{__package__} wrap --output-version=5 backup.tar backup.ab
{__package__} wrap --output-version=5 backup.tar
""")
    fmt.end_section()

def make_argparser(real : bool = True) -> _t.Any:
    _ = gettext

    parser = argparse.BetterArgumentParser(
        prog=__package__,
        description = _("""A handy Swiss-army-knife-like utility for manipulating Android Backup files (`*.ab`, `*.adb`) produced by `adb backup`, `bmgr`, and similar tools.

Android Backup files consist of a metadata header followed by a PAX-formatted TAR files optionally compressed with zlib (the only compressing Android Backup file format supports) optionally encrypted with AES-256 (the only encryption Android Backup file format supports).

Below, all input decryption options apply to all subcommands taking Android Backup files as input(s) and all output encryption options apply to all subcommands producing Android Backup files as output(s).
"""),
        additional_sections = [add_examples],
        allow_abbrev = False,
        add_help = False,
        add_version = True)
    parser.add_argument("-h", "--help", action="store_true", help=_("show this help message and exit"))
    parser.add_argument("--markdown", action="store_true", help=_("show help messages formatted in Markdown"))
    parser.set_defaults(func=None)

    def no_cmd(cfg : Namespace) -> None:
        parser.print_help(sys.stderr)
        parser.error(_("no subcommand specified"))
    parser.set_defaults(func=no_cmd)

    def add_pass(cmd : _t.Any) -> None:
        agrp = cmd.add_argument_group(_("input decryption passphrase"))
        grp = agrp.add_mutually_exclusive_group()
        grp.add_argument("-p", "--passphrase", type=str, help=_("passphrase for an encrypted `INPUT_AB_FILE`"))
        grp.add_argument("--passfile", type=str, help=_('a file containing the passphrase for an encrypted `INPUT_AB_FILE`; similar to `-p` option but the whole contents of the file will be used verbatim, allowing you to, e.g. use new line symbols or strange character encodings in there; default: guess based on `INPUT_AB_FILE` trying to replace ".ab" and ".adb" extensions with ".passphrase.txt"'))

        agrp = cmd.add_argument_group(_("input decryption checksum verification"))
        agrp.add_argument("--ignore-checksum", action="store_true", help=_("ignore checksum field in `INPUT_AB_FILE`, useful when decrypting backups produced by weird Android firmwares"))

    def add_encpass(cmd : _t.Any) -> None:
        agrp = cmd.add_argument_group(_("output encryption passphrase"))
        grp = agrp.add_mutually_exclusive_group()
        grp.add_argument("--output-passphrase", type=str, help=_("passphrase for an encrypted `OUTPUT_AB_FILE`"))
        grp.add_argument("--output-passfile", type=str, help=_("a file containing the passphrase for an encrypted `OUTPUT_AB_FILE`"))

        agrp = cmd.add_argument_group(_("output encryption parameters"))
        agrp.add_argument("--output-salt-bytes", dest="salt_bytes", default=64, type=int, help=_("PBKDF2HMAC salt length in bytes (default: %(default)s)"))
        agrp.add_argument("--output-iterations", dest="iterations", default=10000, type=int, help=_("PBKDF2HMAC iterations (default: %(default)s)"))

    if not real:
        add_pass(parser)
        add_encpass(parser)

    subparsers = parser.add_subparsers(title="subcommands")

    def add_input(cmd : _t.Any) -> None:
        cmd.add_argument("input_file", metavar="INPUT_AB_FILE", type=str, help=_('an Android Backup file to be used as input, set to "-" to use standard input'))

    def add_output(cmd : _t.Any, extension : str) -> None:
        cmd.add_argument("output_file", metavar="OUTPUT_AB_FILE", nargs="?", default=None, type=str, help=_('file to write the output to, set to "-" to use standard output; default: "-" if `INPUT_TAR_FILE` is "-", otherwise replace ".ab" and ".adb" extension of `INPUT_TAR_FILE` with `%s`' % (extension,)))

    cmd = subparsers.add_parser("ls", aliases = ["list"],
                                help=_("list contents of an Android Backup file"),
                                description=_("List contents of an Android Backup file similar to how `tar -tvf` would do, but this will also show Android Backup file version, compression, and encryption parameters."))
    if real:
        add_pass(cmd)
    add_input(cmd)
    cmd.set_defaults(func=ab_ls)

    cmd = subparsers.add_parser("rewrap", aliases = ["strip", "ab2ab"],
                                help=_("strip or apply encyption and/or compression from/to an Android Backup file"),
                                description=_("""Convert a given Android Backup file into another Android Backup file with encyption and/or compression applied or stripped away.

Versioning parameters and the TAR file stored inside the input file are copied into the output file verbatim.

For instance, with this subcommand you can convert an encrypted and compressed Android Backup file into a simple unencrypted and uncompressed version of the same, or vice versa.
The former of which is useful if your Android firmware forces you to encrypt your backups but you store your backups on an encrypted media anyway and don't want to remember more passphrases than strictly necessary.
Or if you want to strip encryption and compression and re-compress using something better than zlib."""))
    if real:
        add_pass(cmd)
        add_encpass(cmd)
    grp = cmd.add_mutually_exclusive_group()
    grp.add_argument("-d", "--decompress", action="store_true", help=_("produce decompressed output; this is the default"))
    grp.add_argument("-k", "--keep-compression", action="store_true", help=_("copy compression flag and data from input to output verbatim; this will make the output into a compressed Android Backup file if the input Android Backup file is compressed; this is the fastest way to `strip`, since it just copies bytes around"))
    grp.add_argument("-c", "--compress", action="store_true", help=_("(re-)compress the output file; it will use higher compression level defaults than those used by Android, so enabling this option could make it take awhile"))
    cmd.add_argument("-e", "--encrypt", action="store_true", help=_("(re-)encrypt the output file; enabling this option costs basically nothing on a modern CPU"))

    add_input(cmd)
    add_output(cmd, ".stripped.ab")
    cmd.set_defaults(func=ab_strip)

    cmd = subparsers.add_parser("split", aliases = ["ab2many"],
                                help=_("split a full-system Android Backup file into a bunch of per-app Android Backup files"),
                                description=_("""Split a full-system Android Backup file into a bunch of per-app Android Backup files.

Resulting per-app files can be given to `adb restore` to restore selected apps.

Also, if you do backups regularly, then splitting large Android Backup files like this and deduplicating per-app files between backups could save a lot of disk space.
"""))
    if real:
        add_pass(cmd)
        add_encpass(cmd)
    cmd.add_argument("-c", "--compress", action="store_true", help=_("compress per-app output files"))
    cmd.add_argument("-e", "--encrypt", action="store_true", help=_("encrypt per-app output files; when enabled, the `--output-passphrase` will be reused for all the generated files (but all encryption keys will be unique)"))
    cmd.add_argument("--prefix", type=str, help=_('file name prefix for output files; default: `abarms_split_backup` if `INPUT_AB_FILE` is "-", `abarms_split_<INPUT_AB_FILE without its ".ab" or ".adb" extension>` otherwise'))
    add_input(cmd)
    cmd.set_defaults(func=ab_split)


    cmd = subparsers.add_parser("merge", aliases = ["many2ab"],
                                help=_("merge a bunch of Android Backup files into one"),
                                description=_("""Merge many smaller Android Backup files into a single larger one.
A reverse operation to `split`.

This exists mostly for checking that `split` is not buggy.
"""))
    if real:
        add_pass(cmd)
        add_encpass(cmd)
    cmd.add_argument("-c", "--compress", action="store_true", help=_("compress the output file"))
    cmd.add_argument("-e", "--encrypt", action="store_true", help=_("encrypt the output file"))
    cmd.add_argument("input_files", metavar="INPUT_AB_FILE", nargs="+", type=str, help=_('Android Backup files to be used as inputs'))
    cmd.add_argument("output_file", metavar="OUTPUT_AB_FILE", type=str, help=_('file to write the output to'))
    cmd.set_defaults(func=ab_merge)

    cmd = subparsers.add_parser("unwrap", aliases = ["ab2tar"],
                                help=_("convert an Android Backup file into a TAR file"),
                                description=_("""Convert Android Backup file into a TAR file by stripping Android Backup header, decrypting and decompressing as necessary.

The TAR file stored inside the input file gets copied into the output file verbatim."""))
    if real: add_pass(cmd)
    add_input(cmd)
    cmd.add_argument("output_file", metavar="OUTPUT_TAR_FILE", nargs="?", default=None, type=str, help=_('file to write output to, set to "-" to use standard output; default: guess based on `INPUT_AB_FILE` while setting extension to `.tar`'))
    cmd.set_defaults(func=ab_unwrap)

    cmd = subparsers.add_parser("wrap", aliases = ["tar2ab"],
                                help=_("convert a TAR file into an Android Backup file"),
                                description=_(f"""Convert a TAR file into an Android Backup file by prepending Android Backup header, compressing and encrypting as requested.

The input TAR file gets copied into the output file verbatim.

Note that unwrapping a `.ab` file, unpacking the resulting `.tar`, editing the resulting files, packing them back with GNU `tar` utility, running `{__package__} wrap`, and then running `adb restore` on the resulting file will probably crash your Android device (phone or whatever) because the Android-side code restoring from the backup expects the data in the packed TAR to be in a certain order and have certain PAX headers, which GNU `tar` will not produce.

So you should only use this on files previously produced by `{__package__} unwrap` or if you know what it is you are doing.
"""))
    if real:
        add_encpass(cmd)
    cmd.add_argument("-c", "--compress", action="store_true", help=_("compress the output file"))
    cmd.add_argument("-e", "--encrypt", action="store_true", help=_("encrypt the output file"))
    cmd.add_argument("--output-version", type=int, required=True, help=_("Android Backup file version to use (required)"))
    cmd.add_argument("input_file", metavar="INPUT_TAR_FILE", type=str, help=_('a TAR file to be used as input, set to "-" to use standard input'))
    add_output(cmd, ".ab")
    cmd.set_defaults(func=ab_wrap)

    return parser

def main() -> None:
    parser = make_argparser()
    cfg = parser.parse_args(sys.argv[1:])

    if cfg.help:
        if cfg.markdown:
            parser = make_argparser(False)
            parser.set_formatter_class(argparse.MarkdownBetterHelpFormatter)
            print(parser.format_help(1024))
        else:
            print(parser.format_help())
        sys.exit(0)

    if sys.stderr.isatty():
        cfg.report = True
    else:
        cfg.report = False

    try:
        cfg.func(cfg)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(1)
    except CatastrophicFailure as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
