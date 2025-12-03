#!/usr/bin/env python3
#
# This file is a part of `hoardy-adb` project.
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

"""`main()`."""

import dataclasses as _dc
import io as _io
import os
import os.path as _op
import secrets
import struct
import subprocess as _subp
import sys
import time as _time
import typing as _t

from gettext import gettext

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.padding import PKCS7

from kisstdlib import *
from kisstdlib import argparse_ext as argparse
from kisstdlib import tariter
from kisstdlib.argparse_ext import Namespace
from kisstdlib.failure import *
from kisstdlib.fs import iter_subtree
from kisstdlib.io.adapter import *

__prog__ = "hoardy-adb"
__short__ = "hyadb"
BUFFER_SIZE = 16 * 1024**2

backup_waiting_msg = gettext("Waiting for the `bu` to start...")
backup_auto_confirm_msg = gettext(
    'In case auto-confirm does not work, unlock your Android device and press "Back up my data" button at the bottom of the screen.'
)
backup_confirm_msg = gettext(
    'Unlock your Android device and press "Back up my data" button at the bottom of the screen.'
)
backup_done_msg = gettext("Done. Wrote backup to `%s`.")
backup_init_msg = gettext("Getting APK list...")
backup_apk_msg = gettext("(%d%% %d/%d) Backing up an APK for `%s` into `%s`...")
backup_apks_msg = gettext("(%d%% %d/%d) Backing up multiple APKs for `%s` into `%s`...")
backup_apks_done_msg = gettext("Done. Backed up %d APKs for %d apps.")
restore_apk_msg = gettext("(%d%% %d/%d) Restoring `%s`...")
restore_apks_done_msg = gettext("Done. Restored %d APKs for %d apps.")
writing_msg = gettext("Writing `%s`...")
progress_msg = gettext("Writing `%s`... %d%%")


def cmd_backup(cargs: Namespace, lhnd: ANSILogHandler) -> None:
    cmd = ["adb", "shell", "bu", "backup", "-apk", "-obb", "-all", "-keyvalue"]
    if cargs.include_system:
        cmd.append("-system")
    else:
        cmd.append("-nosystem")

    auto_confirm_cmd = ["adb", "shell", "input", "keyevent", "61", "61", "61", "66"]

    if cargs.output_path is None:
        output = "backup_" + _time.strftime("%Y-%m-%d", _time.localtime()) + ".ab"
    else:
        output = cargs.output_path

    created = False
    if output == "-":
        fobj = stdout.fobj
    else:
        try:
            fobj = open(output, "xb")
        except FileExistsError:
            error("file already exists: `%s`", output)
            return
        created = True

    written = 0
    try:
        with fobj:
            with _subp.Popen(cmd, stdout=_subp.PIPE, stderr=_subp.PIPE) as p:
                fd: _io.IOBase = p.stdout  # type: ignore
                if WINDOWS:
                    fd = DOS2UNIXReader(fd)  # type: ignore

                if cargs.auto_confirm:
                    info(backup_waiting_msg)
                    _time.sleep(3)
                    info(backup_auto_confirm_msg)
                    with _subp.Popen(auto_confirm_cmd):
                        pass
                else:
                    info(backup_confirm_msg)

                while out := fd.read(BUFFER_SIZE):
                    raise_delayed_signals()

                    fobj.write(out)
                    if written == 0:
                        info(writing_msg, output)
                    written += len(out)

        if p.returncode != 0 or written == 0:
            written = 0
            raise CatastrophicFailure("failed `adb shell bu backup`")

        info(backup_done_msg, output)
        lhnd.reset()
    finally:
        if created and written == 0:
            os.unlink(output)


def get_pkgs(include_system: bool = False) -> set[str]:
    """Produce a `set` of all AppIDs."""
    cmd = ["adb", "shell", "pm", "list", "packages", "--user", "0"]
    if not include_system:
        cmd.append("-3")

    with _subp.Popen(cmd, stdout=_subp.PIPE) as p:
        fd: _io.IOBase = p.stdout  # type: ignore
        if WINDOWS:
            fd = DOS2UNIXReader(fd)  # type: ignore
        out = fd.read().decode("utf-8")
    if p.returncode != 0:
        raise CatastrophicFailure("failed `adb shell pm list packages`")

    res = set()
    for line in out.splitlines():
        if not line.startswith("package:"):
            raise CatastrophicFailure("failed `adb shell pm list packages`")
        res.add(line[8:])

    return res


def get_apks(include_system: bool = False) -> dict[str, list[str]]:
    """Produce a `dict` AppID -> APK paths."""
    res = {}
    for pkg in get_pkgs(include_system):
        with _subp.Popen(["adb", "shell", "pm", "path", pkg], stdout=_subp.PIPE) as p:
            fd: _io.IOBase = p.stdout  # type: ignore
            if WINDOWS:
                fd = DOS2UNIXReader(fd)  # type: ignore
            out = fd.read().decode("utf-8")
        if p.returncode != 0:
            warning("failed `adb shell pm path %s`: installed in work profile only?", pkg)
            continue

        paths = []
        for path in out.splitlines():
            if not path.startswith("package:"):
                raise CatastrophicFailure("failed `adb shell pm path`")
            paths.append(path[8:])
        res[pkg] = paths

    return res


def cmd_backup_apks(cargs: Namespace, lhnd: ANSILogHandler) -> None:
    if cargs.prefix is None:
        prefix = "backup_" + _time.strftime("%Y-%m-%d", _time.localtime())
    else:
        prefix = cargs.prefix

    info(backup_init_msg)

    class Stats:
        apps = 0
        apks = 0

    apks = get_apks(cargs.include_system)
    total = len(apks)

    def pull(name: str, src: str, dst: str) -> None:
        if _op.exists(dst):
            warning("skipping existing `%s`", dst)
            return
        with _subp.Popen(["adb", "pull", "-a", src, dst], stdout=_subp.DEVNULL) as p:
            pass
        if p.returncode != 0:
            error("failed to `adb pull` an APK for `%s`", name)
            try:
                os.unlink(dst)
            except OSError:
                pass
        else:
            Stats.apks += 1

    for i, (name, paths) in enumerate(apks.items()):
        raise_delayed_signals()

        if len(paths) == 1:
            dst = f"{prefix}__{name}.apk"
            info(backup_apk_msg, 100 * i // total, i + 1, total, name, dst)
            pull(name, paths[0], dst)
        else:
            dst_base = f"{prefix}__{name}"
            os.makedirs(dst_base, exist_ok=True)
            info(backup_apks_msg, 100 * i // total, i + 1, total, name, dst_base)
            for j, path in enumerate(paths):
                dst = _op.join(dst_base, str(j) + "_" + _op.basename(path))
                pull(name, path, dst)
        Stats.apps += 1

    info(backup_apks_done_msg, Stats.apks, Stats.apps)
    lhnd.reset()


def cmd_restore_apks(cargs: Namespace, lhnd: ANSILogHandler) -> None:
    pkgs = get_pkgs(True)
    suffixes = ["__" + p.lower() for p in pkgs]
    suffixes += [s + ".apk" for s in suffixes]

    class Stats:
        apps = 0
        apks = 0

    total = len(cargs.paths)
    for i, path in enumerate(cargs.paths):
        raise_delayed_signals()

        if not cargs.force and any(map(path.lower().endswith, suffixes)):
            warning("skipping apparently already installed `%s`", path)
            continue

        info(restore_apk_msg, 100 * i // total, i + 1, total, path)

        if _op.isdir(path):
            elements: list[str] = list(map(first, iter_subtree(path, include_directories=False)))
            with _subp.Popen(["adb", "install-multiple"] + elements) as p:
                pass
        else:
            elements = [path]
            with _subp.Popen(["adb", "install", path]) as p:
                pass

        if p.returncode != 0:
            error("failed `adb install` for `%s`", path)
        else:
            Stats.apps += 1
            Stats.apks += len(elements)

    info(restore_apks_done_msg, Stats.apks, Stats.apps)
    lhnd.reset()


@_dc.dataclass
class ABParams:
    version: int
    compression: int
    encryption: str
    user_salt_len: int
    checksum_salt_len: int
    iterations: int


def androidKDF(length: int, salt: bytes, iterations: int, passphrase: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(passphrase)


def make_mangled_key(master_key: bytes) -> bytes:
    # this is actually what Java does on implicit conversion from String
    # to Bytes: it smears the last bit into the next byte; inspired by a
    # similar, but less comprehensible, line in
    # https://github.com/xBZZZZ/abpy
    c = 255 << 8
    return "".join(chr(x | (0 if x < 128 else c)) for x in master_key).encode("utf8")


def getpass(prompt: str = "Passphrase: ") -> bytes:
    import termios

    with open("/dev/tty", "r+b", buffering=0) as tty:
        tty.write(prompt.encode(sys.getdefaultencoding()))
        old = termios.tcgetattr(tty)
        new = termios.tcgetattr(tty)
        new[3] = new[3] & ~termios.ECHO
        try:
            termios.tcsetattr(tty, termios.TCSADRAIN, new)
            data = tty.readline()
            tty.write(b"\n")
        finally:
            termios.tcsetattr(tty, termios.TCSADRAIN, old)

        if data[-2:] == b"\r\n":
            data = data[:-2]
        elif data[-1:] == b"\n":
            data = data[:-1]
        return data


def get_passphrase(
    prompt: str, passphrase: str | None, passfile: str | None, base_path: str | None
) -> bytes | _t.Callable[[], bytes]:
    if passphrase is not None:
        return passphrase.encode(sys.getdefaultencoding())
    if passfile is not None:
        try:
            with open(passfile, "rb") as f:
                return f.read()
        except FileNotFoundError as exc:
            raise CatastrophicFailure("file `%s` does not exists", passfile) from exc
    if base_path is not None:
        passfile = base_path + ".passphrase.txt"
        try:
            with open(passfile, "rb") as f:
                return f.read()
        except FileNotFoundError:
            pass
    return lambda: getpass(prompt)


def open_input_base(  # pylint: disable=dangerous-default-value
    path: str, exts: list[str] = []
) -> tuple[_t.Any, int | None, str, str | None]:
    """Returns [fobj, size | None, path, base_path | None]."""

    if path == "-":
        return os.fdopen(0, "rb"), None, "-", None

    path = _op.expanduser(path)

    root, ext = _op.splitext(path)
    if ext in exts:
        base_path = root
    else:
        base_path = path

    try:
        fobj = open(path, "rb")  # pylint: disable=consider-using-with
    except FileNotFoundError as exc:
        raise CatastrophicFailure("file `%s` does not exists", path) from exc

    size = None
    if fobj.seekable():
        size = fobj.seek(0, _io.SEEK_END)
        fobj.seek(0)

    return fobj, size, path, base_path


def ab_input(
    fobj: _t.Any,
    passphrase: bytes | _t.Callable[[], bytes] = getpass,
    ignore_checksum: bool = True,
    decompress: bool = True,
) -> tuple[_t.Any, ABParams]:
    """Returns [fobj, ABParams]."""

    # The original backing up code: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/master/services/backup/java/com/android/server/backup/fullbackup/PerformAdbBackupTask.java
    def readline(field: str) -> bytes:
        data: bytes = fobj.readline()
        if data[-1:] == b"\n":
            data = data[:-1]
        else:
            raise ParsingFailure("unable to parse Android Backup `%s` field", field)
        return data

    def readint(field: str) -> int:
        data = readline(field)
        try:
            res = int(data)
        except Exception as exc:
            raise ParsingFailure("unable to parse Android Backup `%s` field", field) from exc
        return res

    def readhex(field: str) -> bytes:
        data = readline(field)
        try:
            res = bytes.fromhex(data.decode("ascii"))
        except Exception as exc:
            raise ParsingFailure("unable to parse Android Backup `%s` field", field) from exc
        return res

    magic = readline("magic")
    if magic != b"ANDROID BACKUP":
        raise ParsingFailure("not an Android Backup file")

    version = readint("version")
    if version < 1 or version > 5:
        raise ParsingFailure("unknown Android Backup version: `%s`", version)

    compression = readint("compression")
    if compression not in [0, 1]:
        raise ParsingFailure("unknown Android Backup compression algorithm: `%s`", compression)

    encryption_ = readline("encryption")

    try:
        encryption = encryption_.decode("ascii")
    except UnicodeDecodeError:
        raise ParsingFailure(  # pylint: disable=raise-missing-from
            "unknown Android Backup encryption algorithm: `%s`", repr(encryption)
        )

    if encryption == "none":
        user_salt_len = 0
        checksum_salt_len = 0
        iterations = 0
    elif encryption == "AES-256":
        if isinstance(passphrase, bytes):
            passphrase_bytes = passphrase
        else:
            passphrase_bytes = passphrase()

        user_salt = readhex("user_salt")
        user_salt_len = len(user_salt)
        checksum_salt = readhex("checksum_salt")
        checksum_salt_len = len(user_salt)
        iterations = readint("iterations")
        user_iv = readhex("user_iv")
        user_blob = readhex("user_blob")

        blob_key = androidKDF(32, user_salt, iterations, passphrase_bytes)

        decryptor = Cipher(algorithms.AES(blob_key), modes.CBC(user_iv)).decryptor()
        unpadder = PKCS7(128).unpadder()
        try:
            data = decryptor.update(user_blob) + decryptor.finalize()
            decrypted_blob = unpadder.update(data) + unpadder.finalize()
        except Exception as exc:
            raise ParsingFailure("failed to decrypt, wrong passphrase?") from exc

        class Mutable:
            data: bytes = decrypted_blob

        def readb(want: int) -> bytes:
            blob = Mutable.data
            length = struct.unpack("B", blob[:1])[0]
            if length != want:
                raise ParsingFailure("failed to decrypt, wrong passphrase?")
            data = blob[1 : length + 1]
            blob = blob[length + 1 :]
            Mutable.data = blob
            return data

        master_iv = readb(16)
        master_key = readb(32)
        checksum = readb(32)

        mangled_master_key = make_mangled_key(master_key)
        ok_checksum = ignore_checksum
        for key in [mangled_master_key, master_key]:
            our_checksum = androidKDF(32, checksum_salt, iterations, key)
            if checksum == our_checksum:
                ok_checksum = True
                break

        if not ok_checksum:
            raise ParsingFailure("bad Android Backup checksum, wrong passphrase?")

        decryptor = Cipher(algorithms.AES(master_key), modes.CBC(master_iv)).decryptor()
        fobj = UpdateFinalizeReader(fobj, decryptor, BUFFER_SIZE)

        unpadder = PKCS7(128).unpadder()
        fobj = UpdateFinalizeReader(fobj, unpadder, BUFFER_SIZE)
    else:
        raise ParsingFailure("unknown Android Backup encryption algorithm: `%s`", encryption)

    if compression == 0:
        pass
    elif compression == 1:
        if decompress:
            fobj = ZlibDecompressor(fobj, BUFFER_SIZE)
    else:
        raise AssertionFailure("unknown Android Backup compression algorithm: `%s`", compression)

    return fobj, ABParams(
        version, compression, encryption, user_salt_len, checksum_salt_len, iterations
    )


def begin_ab_input(
    cargs: Namespace, input_path: str, decompress: bool
) -> tuple[_t.Any, int | None, str, str | None, ABParams]:
    ifobj_, isize, ipath, ibase_path = open_input_base(input_path, [".ab", ".adb"])
    ipassphrase = get_passphrase("Input passphrase: ", cargs.passphrase, cargs.passfile, ibase_path)
    try:
        try:
            ifobj, iparams = ab_input(ifobj_, ipassphrase, cargs.ignore_checksum, decompress)
        except CatastrophicFailure as exc:
            raise exc.elaborate("while reading `%s`", ipath)
    except:
        ifobj_.close()
        raise
    return ifobj, isize, ipath, ibase_path, iparams


def open_output_base(path: str | None, base_path: str | None, ext: str) -> tuple[_t.Any, str]:
    """Returns [fobj, path]."""
    if path == "-" or path is None and base_path is None:
        return os.fdopen(1, "wb"), "-"

    if path is None:
        assert base_path is not None
        path = base_path + ext
    else:
        path = _op.expanduser(path)

    try:
        fobj = open(path, "xb")  # pylint: disable=consider-using-with
    except FileExistsError as exc:
        raise CatastrophicFailure("file `%s` already exists", path) from exc

    return fobj, path


def ab_output(
    fobj: _t.Any,
    params: ABParams,
    passphrase: bytes | _t.Callable[[], bytes],
    keep_compression: bool = False,
) -> _t.Any:
    compression = params.compression
    if compression not in (0, 1):
        raise AssertionFailure("unknown Android Backup compression algorithm: `%s`", compression)

    encryption = params.encryption
    if encryption not in ("none", "AES-256"):
        raise AssertionFailure("unknown Android Backup encryption algorithm: `%s`", encryption)

    header = f"ANDROID BACKUP\n{params.version}\n{compression}\n{encryption}\n"
    fobj.write(header.encode("ascii"))

    if encryption == "none":
        pass
    elif encryption == "AES-256":
        if isinstance(passphrase, bytes):
            passphrase_bytes = passphrase
        else:
            passphrase_bytes = passphrase()

        user_salt = secrets.token_bytes(params.user_salt_len)
        checksum_salt = secrets.token_bytes(params.checksum_salt_len)
        iterations = params.iterations
        user_iv = secrets.token_bytes(16)

        master_iv = secrets.token_bytes(16)
        master_key = secrets.token_bytes(32)

        key = make_mangled_key(master_key)
        checksum = androidKDF(32, checksum_salt, iterations, key)

        plain_blob = (
            struct.pack("B", 16)
            + master_iv
            + struct.pack("B", 32)
            + master_key
            + struct.pack("B", 32)
            + checksum
        )

        blob_key = androidKDF(32, user_salt, iterations, passphrase_bytes)
        encryptor = Cipher(algorithms.AES(blob_key), modes.CBC(user_iv)).encryptor()
        padder = PKCS7(128).padder()

        padded_blob = padder.update(plain_blob) + padder.finalize()
        user_blob = encryptor.update(padded_blob) + encryptor.finalize()

        enc_header = (
            user_salt.hex().upper()
            + "\n"
            + checksum_salt.hex().upper()
            + "\n"
            + str(iterations)
            + "\n"
            + user_iv.hex().upper()
            + "\n"
            + user_blob.hex().upper()
            + "\n"
        )

        fobj.write(enc_header.encode("ascii"))

        encryptor = Cipher(algorithms.AES(master_key), modes.CBC(master_iv)).encryptor()
        fobj = UpdateFinalizeWriter(fobj, encryptor)

        padder = PKCS7(128).padder()
        fobj = UpdateFinalizeWriter(fobj, padder)
    else:
        assert False

    if compression == 0:
        pass
    elif compression == 1:
        if not keep_compression:
            fobj = ZlibCompressor(fobj)
    else:
        assert False

    return fobj


def get_output_ABParams(
    cargs: Namespace, version: int, compression: int
) -> tuple[ABParams, bytes | _t.Callable[[], bytes]]:
    if cargs.encrypt:
        encryption = "AES-256"
        passphrase = get_passphrase(
            "Output passphrase: ", cargs.output_passphrase, cargs.output_passfile, None
        )
        if not isinstance(passphrase, bytes):
            passphrase = passphrase()
    else:
        encryption = "none"

        def passphrase() -> bytes:
            raise NotImplementedError()

    return (
        ABParams(
            version, compression, encryption, cargs.salt_bytes, cargs.salt_bytes, cargs.iterations
        ),
        passphrase,
    )


prev_percent = None


def progress(path: str, now: int, size: int) -> None:
    global prev_percent
    percent = 100 * now / size
    if prev_percent == percent:
        return
    prev_percent = percent

    info(progress_msg, path, percent)


def copy_input_to_output(ifobj: _t.Any, isize: int | None, ipath: str, ofobj: _t.Any) -> None:
    while True:
        data = ifobj.read(BUFFER_SIZE)
        if data == b"":
            break
        ofobj.write(data)
        if isize is not None:
            progress(ipath, ifobj.tell(), isize)


def str_ftype(ftype: bytes) -> str:
    if ftype in (b"\x00", b"0"):
        return "-"
    if ftype == b"1":
        return "h"
    if ftype == b"2":
        return "l"
    if ftype == b"3":
        return "c"
    if ftype == b"4":
        return "b"
    if ftype == b"5":
        return "d"
    if ftype == b"6":
        return "f"
    raise CatastrophicFailure("unknown TAR header file type: `%s`", repr(ftype))


def str_modes(mode: int) -> str:
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


def str_uidgid(uid: int, gid: int, uname: str, gname: str) -> str:
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


def str_size(x: int) -> str:
    return str(x).rjust(8)


def str_mtime(x: int) -> str:
    return _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(x))


def cmd_ab_ls(cargs: Namespace, _lhnd: ANSILogHandler) -> None:
    ifobj, _isize, _ipath, _ibase_path, iparams = begin_ab_input(cargs, cargs.input_path, True)
    with ifobj:
        printf(
            gettext("# Android Backup, version: %d, compression: %d, encryption: %s"),
            iparams.version,
            iparams.compression,
            iparams.encryption,
        )
        for h in tariter.iter_tar_headers(ifobj):
            print(
                str_ftype(h.ftype) + str_modes(h.mode),
                str_uidgid(h.uid, h.gid, h.uname, h.gname),
                str_size(h.size),
                str_mtime(h.mtime),
                h.path,
            )


def cmd_ab_strip(cargs: Namespace, _lhnd: ANSILogHandler) -> None:
    ifobj, isize, ipath, ibase_path, iparams = begin_ab_input(
        cargs, cargs.input_path, not cargs.keep_compression
    )
    with ifobj:
        oparams, opassphrase = get_output_ABParams(
            cargs,
            iparams.version,
            iparams.compression if cargs.keep_compression else (1 if cargs.compress else 0),
        )
        ofobj_, opath = open_output_base(cargs.output_path, ibase_path, ".stripped.ab")
        with ofobj_:
            ofobj = ab_output(ofobj_, oparams, opassphrase, cargs.keep_compression)
            with ofobj:
                info(writing_msg, opath)
                copy_input_to_output(ifobj, isize, ipath, ofobj)


def write_tar_chunk(
    ifobj: _t.Any, ofobj: _t.Any, pax_header: bytes | None, h: tariter.TarHeader
) -> None:
    if pax_header is not None:
        ofobj.write(pax_header)

    ofobj.write(h.raw)
    fsize = h.size + h.leftovers
    while fsize > 0:
        data = ifobj.read(min(fsize, BUFFER_SIZE))
        if len(data) == 0:
            raise ParsingFailure("unexpected EOF")
        fsize -= len(data)
        ofobj.write(data)


def finish_tar(ofobj: _t.Any) -> None:
    ofobj.write(b"\0" * 1024)
    ofobj.flush()
    ofobj.close()


def cmd_ab_split(cargs: Namespace, _lhnd: ANSILogHandler) -> None:
    ifobj, _isize, _ipath, ibase_path, iparams = begin_ab_input(cargs, cargs.input_path, True)
    with ifobj:
        if cargs.prefix is None:
            base_path = ibase_path if ibase_path is not None else "backup"
            dirname = _op.dirname(base_path)
            basename = _op.basename(base_path)
            prefix = _op.join(dirname, "hoardy_adb_split_" + basename)
        else:
            prefix = cargs.prefix

        oparams, opassphrase = get_output_ABParams(
            cargs, iparams.version, 1 if cargs.compress else 0
        )

        ofobj: _t.Any | None = None
        ofname: str | None = None
        app: str | None = None
        appnum = 0

        global_pax_header: bytes | None = None
        pax_header: bytes | None = None

        for h in tariter.yield_tar_headers(ifobj):
            ftype = h.ftype
            if ftype == b"g":
                global_pax_header = h.raw
                pax_header = None
                continue
            if ftype == b"x":
                pax_header = h.raw
                continue

            happ = "other"
            spath = h.path.split("/")
            if len(spath) > 2 and spath[0] == "apps":
                happ = spath[1]

            if app is None or happ != app:
                if ofobj is not None:
                    # finish the previous one
                    finish_tar(ofobj)
                    appnum += 1

                app = happ
                ofname = "%s__%03d_%s.ab" % (  # pylint: disable=consider-using-f-string
                    prefix,
                    appnum,
                    app,
                )

                try:
                    ofobj_ = open(ofname, "xb")  # pylint: disable=consider-using-with
                except FileExistsError as exc:
                    raise CatastrophicFailure("file `%s` already exists", ofname) from exc

                ofobj = ab_output(ofobj_, oparams, opassphrase)

                info(writing_msg, ofname)

                if global_pax_header is not None:
                    ofobj.write(global_pax_header)

            write_tar_chunk(ifobj, ofobj, pax_header, h)
            pax_header = None

        if ofobj is not None:
            # finish last
            finish_tar(ofobj)


def cmd_ab_merge(cargs: Namespace, _lhnd: ANSILogHandler) -> None:
    ofobj = None
    version = 0
    for input_path in cargs.input_paths:
        ifobj, _isize, _ipath, ibase_path, iparams = begin_ab_input(cargs, input_path, True)
        with ifobj:
            if ofobj is None:
                version = iparams.version
                oparams, opassphrase = get_output_ABParams(
                    cargs, version, 1 if cargs.compress else 0
                )
                ofobj_, opath = open_output_base(cargs.output_path, ibase_path, ".merged.ab")
                ofobj = ab_output(ofobj_, oparams, opassphrase)
                info(writing_msg, opath)
                del ofobj_
            elif iparams.version != version:
                raise CatastrophicFailure(
                    "can't merge files with different Android Backup versions: `%s` is has version `%d`, but we are merging into version `%d`",
                    input_path,
                    iparams.version,
                    version,
                )

            info("Merging `%s`...", input_path)

            for h in tariter.yield_tar_headers(ifobj):
                write_tar_chunk(ifobj, ofobj, None, h)

    finish_tar(ofobj)


def cmd_ab_unwrap(cargs: Namespace, _lhnd: ANSILogHandler) -> None:
    ifobj, isize, ipath, ibase_path, _iparams = begin_ab_input(cargs, cargs.input_path, True)
    with ifobj:
        ofobj, opath = open_output_base(cargs.output_path, ibase_path, ".tar")
        with ofobj:
            info(writing_msg, opath)
            copy_input_to_output(ifobj, isize, ipath, ofobj)


def cmd_ab_wrap(cargs: Namespace, _lhnd: ANSILogHandler) -> None:
    ifobj, isize, ipath, ibase_path = open_input_base(cargs.input_path, [".tar"])
    with ifobj:
        oparams, opassphrase = get_output_ABParams(
            cargs, cargs.output_version, 1 if cargs.compress else 0
        )
        ofobj_, opath = open_output_base(cargs.output_path, ibase_path, ".ab")
        with ofobj_:
            ofobj = ab_output(ofobj_, oparams, opassphrase)
            with ofobj:
                info(writing_msg, opath)
                copy_input_to_output(ifobj, isize, ipath, ofobj)


def add_examples(fmt: _t.Any) -> None:
    # fmt: off
    fmt.add_text("# Usage notes")

    fmt.add_text('Giving an encrypted `INPUT_AB_FILE` as input, not specifying `--passphrase` or `--passfile`, and not having a file named `{INPUT_AB_FILE with ".ab" or ".adb" extension replaced with ".passphrase.txt"}` in the same directory will cause the passphrase to be read interactively from the tty.')

    fmt.add_text("# Examples")

    fmt.start_section("List contents of an Android Backup file")
    fmt.add_code(f"{__short__} ls backup.ab")
    fmt.end_section()

    fmt.start_section(f"Use `tar` util to list contents of an Android Backup file instead of running `{__short__} ls`")
    fmt.add_code(f"{__short__} unwrap backup.ab - | tar -tvf -")
    fmt.end_section()

    fmt.start_section("Extract contents of an Android Backup file")
    fmt.add_code(f"{__short__} unwrap backup.ab - | tar -xvf -")
    fmt.end_section()

    fmt.start_section("Strip encryption and compression from an Android Backup file")
    fmt.add_code(f"""# equivalent
{__short__} strip backup.ab backup.stripped.ab
{__short__} strip backup.ab
""")
    fmt.add_code(f"""# equivalent
{__short__} strip --passphrase secret backup.ab
{__short__} strip -p secret backup.ab
""")
    fmt.add_code(f"""# with passphrase taken from a file
echo -n secret > backup.passphrase.txt
# equivalent
{__short__} strip backup.ab
{__short__} strip --passfile backup.passphrase.txt backup.ab
""")
    fmt.add_code(f"""# with a weird passphrase taken from a file
echo -ne "secret\\r\\n\\x00another line" > backup.passphrase.txt
{__short__} strip backup.ab
""")
    fmt.end_section()

    fmt.start_section("Strip encryption but keep compression, if any")
    fmt.add_code(f"""# equivalent
{__short__} strip --keep-compression backup.ab backup.stripped.ab
{__short__} strip -k backup.ab
""")
    fmt.end_section()

    fmt.start_section("Strip encryption and compression from an Android Backup file and then re-compress using `xz`")
    fmt.add_code(f"""{__short__} strip backup.ab - | xz --compress -9 - > backup.ab.xz
# ... and then convert to tar and list contents:
xzcat backup.ab.xz | {__short__} unwrap - | tar -tvf -
""")
    fmt.end_section()

    fmt.start_section("Convert an Android Backup file into a TAR archive")
    fmt.add_code(f"""# equivalent
{__short__} unwrap backup.ab backup.tar
{__short__} unwrap backup.ab
""")
    fmt.end_section()

    fmt.start_section("Convert a TAR archive into an Android Backup file")
    fmt.add_code(f"""# equivalent
{__short__} wrap --output-version=5 backup.tar backup.ab
{__short__} wrap --output-version=5 backup.tar
""")
    fmt.end_section()
    # fmt: on


def make_argparser(real: bool = True) -> _t.Any:
    _ = gettext

    # fmt: off
    parser = argparse.BetterArgumentParser(
        prog=__prog__,
        description=_("""A simple front-end to backup and restore commands of the `adb` tool and a handy Swiss-army-knife-like utility for manipulating Android Backup files (`backup.ab`, `*.ab`, `*.adb`) produced by `adb shell bu backup`, `adb backup`, `bmgr`, and similar tools.

Android Backup file consists of a metadata header followed by a PAX-formatted TAR file (optionally) compressed with zlib (the only compressing Android Backup file format supports) and then (optionally) encrypted with AES-256 (the only encryption Android Backup file format supports).
""")
        + ("" if real else _("""
Below, all input decryption options apply to all subcommands taking Android Backup files as input(s) and all output encryption options apply to all subcommands producing Android Backup files as output(s).""")),
        additional_sections=[add_examples],
        allow_abbrev=False,
        add_help=True,
        add_version=True,
    )

    def no_cmd(_cargs: Namespace, _lhnd: ANSILogHandler) -> None:
        parser.print_help(sys.stderr)
        parser.error(_("no subcommand specified"))

    parser.set_defaults(func=no_cmd)

    def add_pass(cmd: _t.Any) -> None:
        agrp = cmd.add_argument_group(_("input decryption parameters"))

        grp = agrp.add_mutually_exclusive_group()
        grp.add_argument("-p", "--passphrase", type=str,
            help=_("passphrase for an encrypted `INPUT_AB_FILE`")
        )
        grp.add_argument("--passfile", type=str,
            help=_('a file containing the passphrase for an encrypted `INPUT_AB_FILE`; similar to `-p` option but the whole contents of the file will be used verbatim, allowing you to, e.g. use new line symbols or strange character encodings in there; default: guess based on `INPUT_AB_FILE` trying to replace ".ab" or ".adb" extension with ".passphrase.txt"'),
        )

        agrp.add_argument("--ignore-checksum", action="store_true",
            help=_("ignore checksum field in `INPUT_AB_FILE`, useful when decrypting backups produced by weird Android firmwares"),
        )

    def add_encpass(cmd: _t.Any) -> None:
        agrp = cmd.add_argument_group(_("output encryption parameters"))

        grp = agrp.add_mutually_exclusive_group()
        grp.add_argument("--output-passphrase", type=str,
            help=_("passphrase for an encrypted `OUTPUT_AB_FILE`")
        )
        grp.add_argument("--output-passfile", type=str,
            help=_("a file containing the passphrase for an encrypted `OUTPUT_AB_FILE`"),
        )

        agrp.add_argument("--output-salt-bytes", dest="salt_bytes", default=64, type=int,
            help=_("PBKDF2HMAC salt length in bytes; default: %(default)s"),
        )
        agrp.add_argument("--output-iterations", dest="iterations", default=10000, type=int,
            help=_("PBKDF2HMAC iterations; default: %(default)s"),
        )

    if not real:
        add_pass(parser)
        add_encpass(parser)

    subparsers = parser.add_subparsers(title="subcommands")

    def add_backup(cmd: _t.Any) -> None:
        cmd.add_argument("--system", dest="include_system", action="store_true",
            help=_("include system apps in the backup too; default: only include user apps")
        )

    cmd = subparsers.add_parser("backup", help=_("backup an Android device into an Android Backup file"),
        description=_("""Backup a device by running `adb shell bu backup` command and saving its output to a `.ab` file.

Note that this will only backup data of apps that permit themselves being backed up.
See this project's top-level `README.md` for more info.
"""),
    )
    add_backup(cmd)
    cmd.add_argument("--no-auto-confirm", dest="auto_confirm", action="store_false",
        help=_("do not try to automatically start the backup on the device side via `adb shell input`, ask the user to do it manually instead")
    )
    cmd.add_argument("--to", dest="output_path", metavar="OUTPUT_AB_FILE", type=str,
        help=_('file to write the output to, set to "-" to use standard output; default: `backup_<date>.ab`')
    )
    cmd.set_defaults(func=cmd_backup)

    cmd = subparsers.add_parser("backup-apks",
        help=_("backup all available APKs from an Android device into separate APK files"),
        description=_(f"""Backup all available APK files from a device by running `adb shell pm` and then `adb pull`ing each APK file.

Note that, unlike `{__prog__} backup`, this subcommand will backup everything, but only the APKs, i.e. no app data will be backed up.
See this project's top-level `README.md` for more info.
"""),
    )
    add_backup(cmd)
    cmd.add_argument("--prefix", type=str,
        help=_('file name prefix for output files; default: `backup_<date>`'),
    )
    cmd.set_defaults(func=cmd_backup_apks)

    cmd = subparsers.add_parser("restore-apks",
        help=_("restore APKs backed up by `backup-apks`"),
        description=_("The inverse to `backup-apks`, which runs `adb install` (for single-APK apps) or `adb install-multiple` (for multi-APK apps) as appropriate."),
    )
    cmd.add_argument("--force", action="store_true",
        help=_("force-reinstall apps that appear to be already installed on the device; by default, APKs for such apps will be skipped"),
    )
    cmd.add_argument("paths", metavar="APK_OR_DIR", nargs="+", type=str,
        help=_('what to restore; a separate APK file for a single-APK app or a directory of APK files for a multi-APK app; can be specified multiple times, in which case each given input will be restored'),
    )
    cmd.set_defaults(func=cmd_restore_apks)

    def add_input(cmd: _t.Any) -> None:
        cmd.add_argument("input_path", metavar="INPUT_AB_FILE", type=str,
            help=_('an Android Backup file to be used as input, set to "-" to use standard input'),
        )

    def add_output(cmd: _t.Any, extension: str) -> None:
        cmd.add_argument("output_path", metavar="OUTPUT_AB_FILE", nargs="?", default=None, type=str,
            help=_(
                _('file to write the output to, set to "-" to use standard output; default: "-" if `INPUT_TAR_FILE` is "-", otherwise replaces ".ab" or ".adb" extension of `INPUT_TAR_FILE` with `%s`')
                % (extension,)
            ),
        )

    cmd = subparsers.add_parser("ls", aliases=["list"], help=_("list contents of an Android Backup file"),
        description=_("List contents of an Android Backup file similar to how `tar -tvf` would do, but this will also show Android Backup file version, compression, and encryption parameters."),
    )
    if real:
        add_pass(cmd)
    add_input(cmd)
    cmd.set_defaults(func=cmd_ab_ls)

    cmd = subparsers.add_parser("rewrap", aliases=["strip", "ab2ab"],
        help=_("convert an Android Backup file into a equivalent Android Backup file, stripping away or (re-)applying encyption and/or compression to it"),
        description=_("""Convert a given Android Backup file into another Android Backup file with encyption and/or compression stripped away or (re-) applied.

Versioning parameters and the TAR file stored inside the input file are copied into the output file verbatim.

For instance, with this subcommand you can convert an encrypted and compressed Android Backup file into a simple unencrypted and uncompressed version of the same, or vice versa.
The former of which is useful if your Android firmware forces you to encrypt your backups but you store your backups on an encrypted media anyway and don't want to remember more passphrases than strictly necessary.
Or if you want to strip encryption and compression and re-compress using something better than zlib."""),
    )
    if real:
        add_pass(cmd)
        add_encpass(cmd)
    grp = cmd.add_mutually_exclusive_group()
    grp.add_argument("-k", "--keep-compression", action="store_true",
        help=_("copy compression flag and data from input to output verbatim; this will make the output into a compressed Android Backup file if the input Android Backup file is compressed and vice versa; this is the fastest way to `strip`, since it just copies bytes around"),
    )
    grp.add_argument("-c", "--compress", action="store_true",
        help=_(f"(re-)compress the output file; it will use higher compression level defaults than those used by Android; with this option enabled `{__prog__}` will be quite slow; by default, compression will be stripped away"),
    )
    cmd.add_argument("-e", "--encrypt", action="store_true",
        help=_("(re-)encrypt the output file; on a modern CPU (with AES-NI) enabling this option costs almost nothing, on an old CPU it will be quite slow; by default, encription will be stripped away"),
    )

    add_input(cmd)
    add_output(cmd, ".stripped.ab")
    cmd.set_defaults(func=cmd_ab_strip)

    cmd = subparsers.add_parser("split", aliases=["ab2many"],
        help=_("split a full-system Android Backup file into a bunch of per-app Android Backup files"),
        description=_("""Split a full-system Android Backup file into a bunch of per-app Android Backup files.

Resulting per-app files can be given to `adb restore` to restore selected apps.

Also, if you do backups regularly, then splitting large Android Backup files like this and then deduplicating resulting per-app files between backups could save a lot of disk space.
"""),
    )
    if real:
        add_pass(cmd)
        add_encpass(cmd)
    cmd.add_argument("-c", "--compress", action="store_true",
        help=_("compress per-app output files; by default, the outputs will be uncompressed")
    )
    cmd.add_argument("-e", "--encrypt", action="store_true",
        help=_("encrypt per-app output files; when enabled, the `--output-passphrase`/`--output-passfile` and other `output encryption parameters` will be reused for all the generated files, but all encryption keys and salts will be unique; by default, the outputs will be unencrypted"),
    )
    cmd.add_argument("--prefix", type=str,
        help=_('file name prefix for output files; default: `hoardy_adb_split_backup` if `INPUT_AB_FILE` is "-", `hoardy_adb_split_<INPUT_AB_FILE without its ".ab" or ".adb" extension>` otherwise'),
    )
    add_input(cmd)
    cmd.set_defaults(func=cmd_ab_split)

    cmd = subparsers.add_parser("merge", aliases=["many2ab"],
        help=_("merge a bunch of Android Backup files into one"),
        description=_("""Merge many smaller Android Backup files into a single larger one.
A reverse operation to `split`.

This mostly exists for testing of `split`.
"""),
    )
    if real:
        add_pass(cmd)
        add_encpass(cmd)
    cmd.add_argument("-c", "--compress", action="store_true",
        help=_("compress the output file; by default, the output will be uncompressed")
    )
    cmd.add_argument("-e", "--encrypt", action="store_true",
        help=_("encrypt the output file; by default, the output will be unencrypted")
    )
    cmd.add_argument("input_paths", metavar="INPUT_AB_FILE", nargs="+", type=str,
        help=_("Android Backup files to be used as inputs"),
    )
    cmd.add_argument("output_path", metavar="OUTPUT_AB_FILE", type=str,
        help=_("file to write the output to")
    )
    cmd.set_defaults(func=cmd_ab_merge)

    cmd = subparsers.add_parser("unwrap", aliases=["ab2tar"],
        help=_("convert an Android Backup file into a TAR file"),
        description=_("""Convert Android Backup file into a TAR file by stripping Android Backup header, decrypting and decompressing as necessary.

The TAR file stored inside the input file gets copied into the output file verbatim."""),
    )
    if real:
        add_pass(cmd)
    add_input(cmd)
    cmd.add_argument("output_path", metavar="OUTPUT_TAR_FILE", nargs="?", default=None, type=str,
        help=_('file to write output to, set to "-" to use standard output; default: guess based on `INPUT_AB_FILE` while setting extension to `.tar`'),
    )
    cmd.set_defaults(func=cmd_ab_unwrap)

    cmd = subparsers.add_parser("wrap", aliases=["tar2ab"],
        help=_("convert a TAR file into an Android Backup file"),
        description=_(f"""Convert a TAR file into an Android Backup file by prepending Android Backup header, compressing and encrypting as requested.

The input TAR file gets copied into the output file verbatim.

Note that unwrapping a `.ab` file, unpacking the resulting `.tar`, editing the resulting files, packing them back with GNU `tar` utility, running `{__prog__} wrap`, and then running `adb restore` on the resulting file will probably crash your Android device (phone or whatever) because the Android-side code restoring from the backup expects the data in the packed TAR to be in a certain order and have certain PAX headers, which GNU `tar` will not produce.

So you should only use this on files previously produced by `{__prog__} unwrap` or if you know what it is you are doing.
"""),
    )
    if real:
        add_encpass(cmd)
    cmd.add_argument("-c", "--compress", action="store_true",
        help=_("compress the output file; by default, the output will be uncompressed")
    )
    cmd.add_argument("-e", "--encrypt", action="store_true",
        help=_("encrypt the output file; by default, the output will be unencrypted")
    )
    cmd.add_argument("--output-version", type=int, required=True,
        help=_("Android Backup file version to use; required"),
    )
    cmd.add_argument("input_path", metavar="INPUT_TAR_FILE", type=str,
        help=_('a TAR file to be used as input, set to "-" to use standard input'),
    )
    add_output(cmd, ".ab")
    cmd.set_defaults(func=cmd_ab_wrap)
    # fmt: on

    return parser


def massage(_cargs: _t.Any, lhnd: ANSILogHandler) -> None:
    if sys.stderr.isatty():
        lhnd.level = INFO


def run(cargs: _t.Any, lhnd: ANSILogHandler) -> None:
    with yes_signals():
        massage(cargs, lhnd)
    cargs.func(cargs, lhnd)


def main() -> None:
    _counter, lhnd = setup_result = setup_kisstdlib(__prog__, ephemeral_below=WARNING)
    run_kisstdlib_main(
        setup_result,
        argparse.make_argparser_and_run,
        make_argparser,
        lambda cargs: run(cargs, lhnd),
    )


if __name__ == "__main__":
    main()
