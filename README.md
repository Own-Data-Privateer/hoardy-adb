# What is `abarms`?

`abarms` is a *handy* Swiss-army-knife-like tool for manipulating Android Backup files (`*.ab`, `*.adb`) produced by `adb backup`, `bmgr`, and similar tools.

`abarms` can

- list contents of Android Backup files,
- strip encryption and compression from Android Backup files (so that you could re-compress them with something better for long-term storage),
- convert Android Backup files into TAR files (which you can then unpack with standard `tar`),
- convert TAR files into Android Backup files (though, see the documentation for `abarms wrap` below explaining why you should be careful about doing that),
- split Android Backup files into smaller by-app backups (each of which you can then give to `adb restore` to restore that one app, or just file-level de-duplicate them between different backups),
- merge those back into full-system backups like those produced by `adb backup`,
- and other similar things.

Basically, this is a simpler pure Python implementation (only requires `setuptools` and `cryptography` modules) of [android-backup-extractor](https://github.com/nelenkov/android-backup-extractor) and the parts of [android-backup-toolkit](https://sourceforge.net/projects/android-backup-toolkit/) and [android-backup-processor](https://sourceforge.net/projects/android-backup-processor/) that I use myself.

`abarms` will run on Linux and all other POSIX-compatible operating systems Python supports.
The author also expects it will work fine on Windows, even though it was not tested there (do report an Issue if it does not).

# <span id="why"/>Why does `abarms` exists?

Read the parts highlighted in bold in the following subsection.

## <span id="adb-backup"/>UNIX in 1970s had better system backup tools than current Android OS

**Did you know that your Android OS device already has an awesome built-in full-system phone-to-PC backup and PC-to-phone restore tool that does not require root access?**
`adb` utility of Android Platform Tools has `adb backup` subcommand that, in principle, can do basically everything you could possibly want there.

Internally this is implemented via Android OS setuid root binary named `bu` --- which you can run manually via `adb shell bu help` --- that simply backs up every app on the device one by one and streams the resulting `.ab` file --- which is a wrapped PAX-formatted TAR file (see "EXTENDED DESCRIPTION" section in [`man 1 pax`](https://man7.org/linux/man-pages/man1/pax.1p.html#EXTENDED_DESCRIPTION)) --- to stdout. `adb backup` subcommand is just a simple wrapper around it.

**But then Android Platform Tools bundle gives no tools to manipulate those backup files!
So, if you make a full-system backup with `adb backup`, and then want to restore a single app out of 100+ you have installed on your device, you need third-party tools now.**
This is kind of embarrassing, to be honest.
A tool to manipulate backup files should have been a standard utility in Android Platform Tools since Android version 0.1 or something.
(Seriously, are you not embarrassed? I'm embarrassed for the state of humanity thinking about how the most popular OS on the planet gives no widely accessible local backup and restore tools on par with what every user of 1970s-era UNIX mainframe had out of the box. I'm not asking for automatic opportunistic incremental quantum-safely encrypted full-system replication to cooperative nearby devices in a local mesh-network here!)

Well, technically speaking, Android OS also has automatic scheduled non-interactive backup service `bmgr` --- which can be controlled via Android settings menu and `adb shell bmgr help`, that does per-app backups and restores.
Internally, `bmgr` service also generates `.ab` files and then either uploads them to Google --- which is the default and the only option available through the settings menu --- or stores them locally under `/data/data/com.android.localtransport/files/` --- which requires root to access.
On old Android versions you could ask `bmgr` to do a backup to an SD card directly from the settings menu, but Google removed that functionality to force users to use Cloud-based backups.

So, basically, according to Google (and Samsung, which ship with their own `bmgr`-like service in parallel with `bmgr`), to restore to a previous state of an app, or to migrate between phones you now apparently have to upload all your data to their servers in plain-text for their convenient data-mining and selling of your data to interested third parties.
Google even went as far as to hide `adb backup` subcommand from their official Android documentation: compare the [old manual for `adb`](https://web.archive.org/web/20180426100826/https://developer.android.com/studio/command-line/adb) with the [current one](https://web.archive.org/web/20240129131223/https://developer.android.com/tools/adb), Control+F for "backup".

This resulted into every Android vendor now making their own vendor-specific phone-to-phone migration utilities, and a whole ecosystem of commercial apps that do what `adb backup` already does, but worse.

This also resulted in usefulness of `adb backup` itself being reduced because in Android version 6 Google made automatic daily file-based backups that get uploaded to Google the default when you attach your phone to your Google account.
So, most apps started to opt-out of those backups for privacy and security reasons -- which also started opting them out of being included in `adb backup` output, since `bmgr` and `bu` share most of the infrastructure.
Some of those apps now implement their own in-app backup buttons hidden away in the settings menu somewhere, but most do not.

Yes, this is stupid, see [this discussion on StackOverflow](https://stackoverflow.com/questions/12648373/what-is-androidallowbackup).
See also old Android developer docs that explained this fairly clearly [here](https://web.archive.org/web/20181122123338/https://developer.android.com/guide/topics/data/backup) and [here](https://web.archive.org/web/20181118184751/https://developer.android.com/guide/topics/data/testingbackup).

(You can also force an app to be included in `adb backup` by rebuilding its APK to enable `android:allowBackup` attribute in the manifest and installing the result manually, see [this](https://stackpointer.io/mobile/android-enable-adb-backup-for-any-app/462/) for more info.
But this will only work for newly installed apps as you will have to re-sign the resulting APK with your own private key and Android forbids app updates that change the signing key.)

But, hopefully, eventually, some alternative firmware developer will fix the above bug and allow `adb backup` to backup all apps regardless of `android:allowBackup` manifest setting, as it should.

Still, `adb backup` works fine for a lot of apps and, hopefully, will eventually get back to working as well as it did before Android version 6 in the future.
Meanwhile, [android-backup-toolkit](https://sourceforge.net/projects/android-backup-toolkit/) allows you to split full-system dumps produced by `adb backup` into per-app backups that can then be restored with `adb restore`.

The problem is that, while I'm thankful that [android-backup-toolkit](https://sourceforge.net/projects/android-backup-toolkit/) exists, I find it really annoying to use: it is a bundle of pre-compiled Java apps, binaries, and shell scripts that manages to work somehow, but modifying anything there is basically impossible as building all of those things from sources is an adventure I failed to complete, and then you need to install the gigantic Java VM and libraries to run it all.

**So, as it currently stands, to have per-app backups of your Android device you have to either:**

- **root your device;**
- **give up your privacy by uploading your backups to other people's computers (aka "the cloud"); or**
- **repack all you APKs with `android:allowBackup = true` and either run older Android firmware that can do backup to an SD card or run `adb backup` from your PC, and then extract per-app backups from its output with third-party tools like [android-backup-toolkit](https://sourceforge.net/projects/android-backup-toolkit/) (yes, this is not ideal, but it works, and does not need root).**

**So, one day I was looking at all of this.
I couldn't root or change the firmware on a phone I wanted to keep backed up, but I could follow the last option and get most of what I wanted with almost no effort.
Except figuring out how to run `android-backup-toolkit` to do the very last step of this took me quite a while.
And so I thought, "Hmm, this seems overly complicated, something as simple as splitting and merging TAR files with some additional headers should be doable with a simple Python program."
So I made one.**

It turned out to be a bit less simple than I though it would be, mostly because Python's `tarfile` module was not designed for this, so I had to make my own, and PAX-formatted TAR files are kind of ugly to parse, but it works now, so, eh.

**Hopefully, `abarms` existing will inspire more app and alternative firmware developers to support `adb backup` properly and so personal computing devices of late 2020s will finally reach feature parity with 1970s-era Tape ARchiving (TAR) backup technology.**
(You can backup any UNIX box to an external HDD with `tar -cvvf /media/external/backup.tar --one-file-system /`.
Yes, it will actually work.)

# Quickstart

## Installation

- Install with:
  ``` {.bash}
  pip install abarms
  ```
  and run as
  ``` {.bash}
  abarms --help
  ```
- Alternatively, install it via Nix
  ``` {.bash}
  nix-env -i -f ./default.nix
  abarms --help
  ```
- Alternatively, run without installing:
  ``` {.bash}
  alias abarms="python3 -m abarms"
  abarms --help
  ```

## Backup all apps from your Android device, then restore a single app, without root

### Prepare your PC and phone

Before you make a full backup of your Android phone (or other device) you need to

- install Android Platform Tools (either from [there](https://developer.android.com/tools/releases/platform-tools) or from you distribution);

- enable "Developer Mode" and turn on "USB Debugging" in "Developer Options" (see [Android Docs](https://web.archive.org/web/20240129131223/https://developer.android.com/tools/adb) for instructions);

- then, usually, on your PC you need to run

  ```
  sudo adb kill-server
  sudo adb start-server
  ```

  unless, you added special UDev rules for your phone.

Additionally, depending your device, you might also need to enable "Stay awake" in "Developer Options", otherwise long enough backups might get interrupted in the middle by your device going to sleep.
Personally, I find having it enabled kind of annoying, so I recommend trying to do everything below with it disabled first, and enable it only if your backups get truncated.

### Do a full backup

To do the backup, you need to

- unlock your phone and connect it to your PC via a USB cable (in that order, otherwise USB Debugging will be disabled),

- confirm that the PC is allowed to do USB Debugging in the popup on the phone, then

- run

  ```
  adb backup -apk -obb -all -system -keyvalue
  ```

  on your PC (see below if that does not work),

- unlock your phone again, and

- press "Back up my data" button at the bottom of your screen.

Now you need to wait awhile for `adb` to finish.
The result will be saved in `backup.ab` file.

If you want to backup to an explicitly named file, e.g. to note the date of the backup, run

```
adb backup -f backup_20240101.ab -apk -obb -all -system -keyvalue
```

If `adb backup` does not work, you can invoke `bu` via `adb shell` instead:

```
adb shell 'bu backup -apk -obb -all -system -keyvalue' > backup_20240101.ab
```

### Split it into pieces

You can view contents of the backup via

```
abarms ls backup_20240101.ab
```

and split it into per-app backups via

```
abarms split backup_20240101.ab
```

which will produce a bunch of files named `abarms_split_<filename>_<num>_<appname>.ab` (e.g. `abarms_split_backup_20240101_020_org.fdroid.fdroid.ab`).

### Restore a single app

A single per-app file can be fed back to `adb restore` to restore that singe app, e.g.

```
adb restore abarms_split_backup_20240101_020_org.fdroid.fdroid.ab
```

Or, alternatively, if `adb restore` does not work, invoke `bu` via `adb shell`:
```
adb shell 'bu restore' < abarms_split_backup_20240101_020_org.fdroid.fdroid.ab
```

### Rebuild full backup from parts

You can also rebuild the original full-backup from parts via

```
abarms merge abarms_split_backup_20240101_*.ab backup_20240101.rebuilt.ab
```

to check that it produces exactly the same backup file

```
# strip encryption and compression from the original
abarms strip backup_20240101.ab backup_20240101.stripped.ab

# compare to the stipped original and the rebuilt file
diff backup_20240101.stripped.ab backup_20240101.rebuilt.ab || echo differ
```

# Alternatives

## `android-backup-toolkit` and friends

- [android-backup-extractor](https://github.com/nelenkov/android-backup-extractor) is a Java app that can decrypt and decompress Android Backup archives and convert them into TAR.

- [android-backup-toolkit](https://sourceforge.net/projects/android-backup-toolkit/) builds on top of `android-backup-extractor` and provides a way to split full-system backup ADB files into per-app pieces.

- [android-backup-processor](https://sourceforge.net/projects/android-backup-processor/) is an older version of `android-backup-toolkit`.

## Others

- [This gist by AnatomicJC](https://gist.github.com/AnatomicJC/e773dd55ae60ab0b2d6dd2351eb977c1), among other useful `adb` hacks, shows how to do per-app backups with pure `adb shell` and `adb backup` calls.
  Though, I think `abarms` is a better solution for this, since invoking `adb backup` repeatedly means you'll have to unlock your phone and press "Back up my data" button on the screen repeatedly, `adb backup` followed by `abarms split` is much more convenient.

- [abpy](https://github.com/xBZZZZ/abpy) is a Python utility that can convert Android Backup files into TAR and back, so it's an alternative implementation of `abarms unwrap` and `abarms wrap`. I was unaware it existed when I made this, and I was inspired by checksum verification code there to implement it properly here after I became aware of it.

- [ABX](https://github.com/info-lab/ABX) is a Python utility that can strip Android Backup headers from unencrypted backup files.
  So, basically, it's `abarms unwrap` without decryption support.

## If you have root on your device

Assuming you have root on your Android phone, you can do

```
# check if bmgr is enabled
adb shell bmgr enabled

# list bmgr transports
adb shell bmgr list transports
# localtransport should be there, enable it
adb shell bmgr transport com.android.localtransport/.LocalTransport

# enable bmgr
adb shell bmgr enable true

# do a full backup now
adb shell bmgr fullbackup
```

and then take per-app backup files from `/data/data/com.android.localtransport/files/`.

# License

GPLv3+, small library parts are MIT.

# Usage

## abarms

A handy Swiss-army-knife-like utility for manipulating Android Backup files (`*.ab`, `*.adb`) produced by `adb backup`, `bmgr`, and similar tools.

Android Backup files consist of a metadata header followed by a PAX-formatted TAR files optionally compressed with zlib (the only compressing Android Backup file format supports) optionally encrypted with AES-256 (the only encryption Android Backup file format supports).

Below, all input decryption options apply to all subcommands taking Android Backup files as input(s) and all output encryption options apply to all subcommands producing Android Backup files as output(s).

- options:
  - `--version`
  : show program's version number and exit
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show help messages formatted in Markdown

- input decryption passphrase:
  - `-p PASSPHRASE, --passphrase PASSPHRASE`
  : passphrase for an encrypted `INPUT_AB_FILE`
  - `--passfile PASSFILE`
  : a file containing the passphrase for an encrypted `INPUT_AB_FILE`; similar to `-p` option but the whole contents of the file will be used verbatim, allowing you to, e.g. use new line symbols or strange character encodings in there; default: guess based on `INPUT_AB_FILE` trying to replace ".ab" and ".adb" extensions with ".passphrase.txt"

- input decryption checksum verification:
  - `--ignore-checksum`
  : ignore checksum field in `INPUT_AB_FILE`, useful when decrypting backups produced by weird Android firmwares

- output encryption passphrase:
  - `--output-passphrase OUTPUT_PASSPHRASE`
  : passphrase for an encrypted `OUTPUT_AB_FILE`
  - `--output-passfile OUTPUT_PASSFILE`
  : a file containing the passphrase for an encrypted `OUTPUT_AB_FILE`

- output encryption parameters:
  - `--output-salt-bytes SALT_BYTES`
  : PBKDF2HMAC salt length in bytes (default: 64)
  - `--output-iterations ITERATIONS`
  : PBKDF2HMAC iterations (default: 10000)

- subcommands:
  - `{ls,list,rewrap,strip,ab2ab,split,ab2many,merge,many2ab,unwrap,ab2tar,wrap,tar2ab}`
    - `ls (list)`
    : list contents of an Android Backup file
    - `rewrap (strip, ab2ab)`
    : strip or apply encyption and/or compression from/to an Android Backup file
    - `split (ab2many)`
    : split a full-system Android Backup file into a bunch of per-app Android Backup files
    - `merge (many2ab)`
    : merge a bunch of Android Backup files into one
    - `unwrap (ab2tar)`
    : convert an Android Backup file into a TAR file
    - `wrap (tar2ab)`
    : convert a TAR file into an Android Backup file

### abarms ls

List contents of an Android Backup file similar to how `tar -tvf` would do, but this will also show Android Backup file version, compression, and encryption parameters.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input

### abarms rewrap

Convert a given Android Backup file into another Android Backup file with encyption and/or compression applied or stripped away.

Versioning parameters and the TAR file stored inside the input file are copied into the output file verbatim.

For instance, with this subcommand you can convert an encrypted and compressed Android Backup file into a simple unencrypted and uncompressed version of the same, or vice versa.
The former of which is useful if your Android firmware forces you to encrypt your backups but you store your backups on an encrypted media anyway and don't want to remember more passphrases than strictly necessary.
Or if you want to strip encryption and compression and re-compress using something better than zlib.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input
  - `OUTPUT_AB_FILE`
  : file to write the output to, set to "-" to use standard output; default: "-" if `INPUT_TAR_FILE` is "-", otherwise replace ".ab" and ".adb" extension of `INPUT_TAR_FILE` with `.stripped.ab`

- options:
  - `-d, --decompress`
  : produce decompressed output; this is the default
  - `-k, --keep-compression`
  : copy compression flag and data from input to output verbatim; this will make the output into a compressed Android Backup file if the input Android Backup file is compressed; this is the fastest way to `strip`, since it just copies bytes around
  - `-c, --compress`
  : (re-)compress the output file; it will use higher compression level defaults than those used by Android, so enabling this option could make it take awhile
  - `-e, --encrypt`
  : (re-)encrypt the output file; enabling this option costs basically nothing on a modern CPU

### abarms split

Split a full-system Android Backup file into a bunch of per-app Android Backup files.

Resulting per-app files can be given to `adb restore` to restore selected apps.

Also, if you do backups regularly, then splitting large Android Backup files like this and deduplicating per-app files between backups could save a lot of disk space.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input

- options:
  - `-c, --compress`
  : compress per-app output files
  - `-e, --encrypt`
  : encrypt per-app output files; when enabled, the `--output-passphrase` will be reused for all the generated files (but all encryption keys will be unique)
  - `--prefix PREFIX`
  : file name prefix for output files; default: `abarms_split_backup` if `INPUT_AB_FILE` is "-", `abarms_split_<INPUT_AB_FILE without its ".ab" or ".adb" extension>` otherwise

### abarms merge

Merge many smaller Android Backup files into a single larger one.
A reverse operation to `split`.

This exists mostly for checking that `split` is not buggy.

- positional arguments:
  - `INPUT_AB_FILE`
  : Android Backup files to be used as inputs
  - `OUTPUT_AB_FILE`
  : file to write the output to

- options:
  - `-c, --compress`
  : compress the output file
  - `-e, --encrypt`
  : encrypt the output file

### abarms unwrap

Convert Android Backup file into a TAR file by stripping Android Backup header, decrypting and decompressing as necessary.

The TAR file stored inside the input file gets copied into the output file verbatim.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input
  - `OUTPUT_TAR_FILE`
  : file to write output to, set to "-" to use standard output; default: guess based on `INPUT_AB_FILE` while setting extension to `.tar`

### abarms wrap

Convert a TAR file into an Android Backup file by prepending Android Backup header, compressing and encrypting as requested.

The input TAR file gets copied into the output file verbatim.

Note that unwrapping a `.ab` file, unpacking the resulting `.tar`, editing the resulting files, packing them back with GNU `tar` utility, running `abarms wrap`, and then running `adb restore` on the resulting file will probably crash your Android device (phone or whatever) because the Android-side code restoring from the backup expects the data in the packed TAR to be in a certain order and have certain PAX headers, which GNU `tar` will not produce.

So you should only use this on files previously produced by `abarms unwrap` or if you know what it is you are doing.

- positional arguments:
  - `INPUT_TAR_FILE`
  : a TAR file to be used as input, set to "-" to use standard input
  - `OUTPUT_AB_FILE`
  : file to write the output to, set to "-" to use standard output; default: "-" if `INPUT_TAR_FILE` is "-", otherwise replace ".ab" and ".adb" extension of `INPUT_TAR_FILE` with `.ab`

- options:
  - `-c, --compress`
  : compress the output file
  - `-e, --encrypt`
  : encrypt the output file
  - `--output-version OUTPUT_VERSION`
  : Android Backup file version to use (required)

## Usage notes

Giving an encrypted `INPUT_AB_FILE` as input, not specifying `--passphrase` or `--passfile`, and not having a file named `{INPUT_AB_FILE with ".ab" or ".adb" extension replaced with ".passphrase.txt"}` in the same directory will case the passphrase to be read interactively from the tty.

## Examples

- List contents of an Android Backup file:
  ```
  abarms ls backup.ab
  ```

- Use `tar` util to list contents of an Android Backup file instead of running `abarms ls`:
  ```
  abarms unwrap backup.ab - | tar -tvf -
  ```

- Extract contents of an Android Backup file:
  ```
  abarms unwrap backup.ab - | tar -xvf -
  ```

- Strip encryption and compression from an Android Backup file:
  ```
  # equivalent
  abarms strip backup.ab backup.stripped.ab
  abarms strip backup.ab
  ```

  ```
  # equivalent
  abarms strip --passphrase secret backup.ab
  abarms strip -p secret backup.ab
  ```

  ```
  # with passphrase taken from a file
  echo -n secret > backup.passphrase.txt
  # equivalent
  abarms strip backup.ab
  abarms strip --passfile backup.passphrase.txt backup.ab
  ```

  ```
  # with a weird passphrase taken from a file
  echo -ne "secret\r\n\x00another line" > backup.passphrase.txt
  abarms strip backup.ab
  ```

- Strip encryption but keep compression, if any:
  ```
  # equivalent
  abarms strip --keep-compression backup.ab backup.stripped.ab
  abarms strip -k backup.ab
  ```

- Strip encryption and compression from an Android Backup file and then re-compress using `xz`:
  ```
  abarms strip backup.ab - | xz --compress -9 - > backup.ab.xz
  # ... and then convert to tar and list contents:
  xzcat backup.ab.xz | abarms unwrap - | tar -tvf -
  ```

- Convert an Android Backup file into a TAR archive:
  ```
  # equivalent
  abarms unwrap backup.ab backup.tar
  abarms unwrap backup.ab
  ```

- Convert a TAR archive into an Android Backup file:
  ```
  # equivalent
  abarms wrap --output-version=5 backup.tar backup.ab
  abarms wrap --output-version=5 backup.tar
  ```

