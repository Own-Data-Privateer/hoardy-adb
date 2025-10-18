# Table of Contents
<details><summary>(Click me to see it.)</summary>
<ul>
<li><a href="#what-is-hoardy-adb" id="toc-what-is-hoardy-adb">What is <code>hoardy-adb</code>?</a></li>
<li><a href="#why-does-hoardy-adb-exists" id="toc-why-does-hoardy-adb-exists"><span id="why"/>Why does <code>hoardy-adb</code> exists?</a>
<ul>
<li><a href="#unix-in-1970s-had-better-system-backup-tools-than-current-android-os" id="toc-unix-in-1970s-had-better-system-backup-tools-than-current-android-os"><span id="adb-backup"/>UNIX in 1970s had better system backup tools than current Android OS</a></li>
</ul></li>
<li><a href="#quickstart" id="toc-quickstart">Quickstart</a>
<ul>
<li><a href="#pre-installation" id="toc-pre-installation">Pre-installation</a></li>
<li><a href="#installation" id="toc-installation">Installation</a></li>
<li><a href="#backup-all-apps-from-your-android-device-then-restore-a-single-app-without-root" id="toc-backup-all-apps-from-your-android-device-then-restore-a-single-app-without-root">Backup all apps from your Android device, then restore a single app, without root</a>
<ul>
<li><a href="#prepare-your-pc-and-phone" id="toc-prepare-your-pc-and-phone">Prepare your PC and phone</a></li>
<li><a href="#do-a-full-backup" id="toc-do-a-full-backup">Do a full backup</a></li>
<li><a href="#split-it-into-pieces" id="toc-split-it-into-pieces">Split it into pieces</a></li>
<li><a href="#restore-a-single-app" id="toc-restore-a-single-app">Restore a single app</a></li>
<li><a href="#rebuild-full-backup-from-parts" id="toc-rebuild-full-backup-from-parts">Rebuild full backup from parts</a></li>
</ul></li>
<li><a href="#backup-all-app-apks-and-then-restore-them" id="toc-backup-all-app-apks-and-then-restore-them">Backup all app APKs and then restore them</a>
<ul>
<li><a href="#backup-all-apks" id="toc-backup-all-apks">Backup all APKs</a></li>
<li><a href="#restore-the-apks" id="toc-restore-the-apks">Restore the APKs</a></li>
</ul></li>
</ul></li>
<li><a href="#alternatives" id="toc-alternatives">Alternatives</a>
<ul>
<li><a href="#for-hoardy-adb-backup-apks-and-hoardy-adb-restore-apks" id="toc-for-hoardy-adb-backup-apks-and-hoardy-adb-restore-apks">… for <code>hoardy-adb backup-apks</code> and <code>hoardy-adb restore-apks</code></a></li>
<li><a href="#for-hoardy-adb-backup-followed-by-hoardy-adb-split" id="toc-for-hoardy-adb-backup-followed-by-hoardy-adb-split">… for <code>hoardy-adb backup</code> followed by <code>hoardy-adb split</code></a></li>
<li><a href="#for-other-hoardy-adb-subcommands" id="toc-for-other-hoardy-adb-subcommands">… for other <code>hoardy-adb</code> subcommands</a></li>
<li><a href="#if-you-have-root-access-on-your-device" id="toc-if-you-have-root-access-on-your-device">If you have root access on your device</a></li>
</ul></li>
<li><a href="#frequently-asked-questions" id="toc-frequently-asked-questions">Frequently Asked Questions</a>
<ul>
<li><a href="#backup.ab-produced-by-hyadb-backupadb-shell-bu-backupadb-backup-does-not-contain-the-app-i-want.-can-hoardy-adb-help-me-backup-it-somehow" id="toc-backup.ab-produced-by-hyadb-backupadb-shell-bu-backupadb-backup-does-not-contain-the-app-i-want.-can-hoardy-adb-help-me-backup-it-somehow"><code>backup.ab</code> produced by <code>hyadb backup</code>/<code>adb shell bu backup</code>/<code>adb backup</code> does not contain the app I want. Can <code>hoardy-adb</code> help me backup it somehow?</a></li>
<li><a href="#but-uninstalling-the-app-will-loose-all-that-apps-data-state" id="toc-but-uninstalling-the-app-will-loose-all-that-apps-data-state">But uninstalling the app will loose all that app’s data state!</a></li>
<li><a href="#but-i-need-to-backup-that-app" id="toc-but-i-need-to-backup-that-app">But I need to backup that app!</a></li>
<li><a href="#but-that-app-has-no-custom-backup-function" id="toc-but-that-app-has-no-custom-backup-function">But that app has no custom backup function!</a></li>
<li><a href="#anything-else-nice-and-relevant-from-f-droid" id="toc-anything-else-nice-and-relevant-from-f-droid">Anything else nice and relevant from F-Droid?</a></li>
</ul></li>
<li><a href="#meta" id="toc-meta">Meta</a>
<ul>
<li><a href="#changelog" id="toc-changelog">Changelog?</a></li>
<li><a href="#todo" id="toc-todo">TODO?</a></li>
<li><a href="#license" id="toc-license">License</a></li>
<li><a href="#contributing" id="toc-contributing">Contributing</a></li>
</ul></li>
<li><a href="#usage" id="toc-usage">Usage</a>
<ul>
<li><a href="#hoardy-adb" id="toc-hoardy-adb">hoardy-adb</a>
<ul>
<li><a href="#hoardy-adb-backup" id="toc-hoardy-adb-backup">hoardy-adb backup</a></li>
<li><a href="#hoardy-adb-backup-apks" id="toc-hoardy-adb-backup-apks">hoardy-adb backup-apks</a></li>
<li><a href="#hoardy-adb-restore-apks" id="toc-hoardy-adb-restore-apks">hoardy-adb restore-apks</a></li>
<li><a href="#hoardy-adb-ls" id="toc-hoardy-adb-ls">hoardy-adb ls</a></li>
<li><a href="#hoardy-adb-rewrap" id="toc-hoardy-adb-rewrap">hoardy-adb rewrap</a></li>
<li><a href="#hoardy-adb-split" id="toc-hoardy-adb-split">hoardy-adb split</a></li>
<li><a href="#hoardy-adb-merge" id="toc-hoardy-adb-merge">hoardy-adb merge</a></li>
<li><a href="#hoardy-adb-unwrap" id="toc-hoardy-adb-unwrap">hoardy-adb unwrap</a></li>
<li><a href="#hoardy-adb-wrap" id="toc-hoardy-adb-wrap">hoardy-adb wrap</a></li>
</ul></li>
<li><a href="#usage-notes" id="toc-usage-notes">Usage notes</a></li>
<li><a href="#examples" id="toc-examples">Examples</a></li>
</ul></li>
<li><a href="#development-.test-hyadb.sh---help---wine---output-version-version-path-path-..." id="toc-development-.test-hyadb.sh---help---wine---output-version-version-path-path-...">Development: <code>./test-hyadb.sh [--help] [--wine] [--output-version VERSION] PATH [PATH ...]</code></a>
<ul>
<li><a href="#example" id="toc-example">Example</a></li>
</ul></li>
</ul>
</details>

# What is `hoardy-adb`?

`hoardy-adb` is a tool that can help you to:

- invoke the `adb` utility of Android Platform Tools to backup and restore your Android devices, but with a trivial CLI, and using safe default values,
- list contents of Android Backup files (`backup.ab`, `*.ab` and `*.adb` files produced by `adb shell bu backup`, `adb backup`, `bmgr`, and similar tools),
- strip encryption and/or compression from Android Backup files (so that you could re-compress them with something better for long-term storage),
- (re-)encrypt and/or (re-)compress Android Backup files (to change encryption passphrase, or to compress with higher levels of compression compared to that Android OS uses by default),
- convert Android Backup files into TAR files (which you can then unpack with standard `tar`),
- convert TAR files into Android Backup files (though, see the documentation for `hoardy-adb wrap` below explaining why you should be careful about doing that),
- split Android Backup files into smaller by-app backups (each of which you can then give to `adb restore` to restore that one app, or just file-level de-duplicate them between different backups),
- merge those small by-app backups back into full-system backups like those produced by `adb backup`,
- and other similar things.

In other words, `hoardy-adb` is a simple front-end for backup and restore commands of `adb` as well as a Swiss-army-knife-like utility for manipulating Android Backup files some of those backup commands produce and consume.

Basically, this is a simpler pure Python implementation of parts of [Adebar](https://codeberg.org/izzy/Adebar), [android-backup-extractor](https://github.com/nelenkov/android-backup-extractor), [android-backup-toolkit](https://sourceforge.net/projects/android-backup-toolkit/), and [android-backup-processor](https://sourceforge.net/projects/android-backup-processor/) that I use myself.

`hoardy-adb` will run on Linux and all other POSIX-compatible operating systems Python supports.
The author also expects it will work fine on Windows, even though it was not tested there (do report an Issue if it does not).

`hoardy-adb` was previously knows as `abarms`.

# <span id="why"/>Why does `hoardy-adb` exists?

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
On old Android versions you could ask `bmgr` to make a backup to an SD card directly from the settings menu, but Google removed that functionality to force users to use Cloud-based backups.

So, basically, according to Google (and Samsung, which ship with their own `bmgr`-like service in parallel with `bmgr`), to restore to a previous state of an app, or to migrate between phones you now apparently have to upload all your data to their servers in plain-text for their convenient data-mining and selling of your data to interested third parties.
Google even went as far as to hide `adb backup` subcommand from their official Android documentation: compare the [old manual for `adb`](https://web.archive.org/web/20180426100826/https://developer.android.com/studio/command-line/adb) with the [current one](https://web.archive.org/web/20240129131223/https://developer.android.com/tools/adb), Control+F for "backup".

This resulted into every Android vendor now making their own vendor-specific phone-to-phone migration utilities, and a whole ecosystem of commercial apps that do what `adb backup` already does, but worse.

This also resulted in usefulness of `adb backup` itself being reduced because in Android version 6 Google made automatic daily file-based backups that get uploaded to Google the default when you attach your phone to your Google account.
So, most apps started opting out of those backups for privacy and security reasons -- which also started opting them out of being included in `adb backup` output, since `bmgr` and `bu` share most of the infrastructure.
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

**Hopefully, `hoardy-adb` existing will inspire more app and alternative firmware developers to support `adb backup` properly and so personal computing devices of late 2020s will finally reach feature parity with 1970s-era Tape ARchiving (TAR) backup technology.**
(You can backup any UNIX box to an external HDD with `tar -cvvf /media/external/backup.tar --one-file-system /`.
Yes, it will actually work.)

# Quickstart

## Pre-installation

- Install `Python 3`:

  - On a Windows system: [Download Python installer from the official website](https://www.python.org/downloads/windows/), run it, **set `Add python.exe to PATH` checkbox**, then `Install` (the default options are fine).
  - On a conventional POSIX system like most GNU/Linux distros and MacOS X: Install `python3` via your package manager. Realistically, it probably is installed already.

- Install Android Platform Tools:

  - Either [from there](https://developer.android.com/tools/releases/platform-tools),
  - or via your package manager.

## Installation

- On a Windows system:

  Open `cmd.exe` (press `Windows+R`, enter `cmd.exe`, press `Enter`), install this with
  ```bash
  python -m pip install hoardy-adb
  ```
  and run as
  ```bash
  python -m hoardy_adb --help
  ```

- On a POSIX system or on a Windows system with Python's `/Scripts` added to `PATH`:

  Open a terminal/`cmd.exe`, install this with
  ```bash
  pip install hoardy-adb
  ```
  and run as
  ```bash
  hoardy-adb --help
  ```

- Alternatively, for light development (without development tools, for those see `nix-shell` below):

  Open a terminal/`cmd.exe`, `cd` into this directory, then install with
  ```bash
  python -m pip install -e .
  # or
  pip install -e .
  ```
  and run as:
  ```bash
  python -m hoardy_adb --help
  # or
  hoardy-adb --help
  ```

- Alternatively, on a system with [Nix package manager](https://nixos.org/nix/)

  ```bash
  nix-env -i -f ./default.nix
  hoardy-adb --help
  ```

- Alternatively, to replicate my development environment:

  ```bash
  nix-shell ./default.nix --arg developer true
  ```

## Backup all apps from your Android device, then restore a single app, without root

### Prepare your PC and phone

Before you make a full backup of your Android phone (or other device) you need to

- enable "Developer Mode" and turn on "USB Debugging" in "Developer Options" (see [Android Docs](https://web.archive.org/web/20240129131223/https://developer.android.com/tools/adb) for instructions);

- on Windows, you might need to run `adb start-server` in `cmd`, unless you configured it to start automatically;

- on Linux, you usually need to run

  ```bash
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

  ```bash
  hoardy-adb backup
  # or
  hyadb backup
  ```

  on your PC,

- it should start the backup automatically, but if auto-confirm machinery fails to work (which can happen if it took you too long between steps), unlock your phone again, and press "Back up my data" button at the bottom of your screen manually.

Now you need to wait awhile for it to finish.
The result will be saved in `backup_<date>.ab` file.

If you want to include system apps in the backup too, run

```bash
hyadb backup --system
```

instead.
**Though, doing this is not recommended, as accidentally restoring a system app from an old backup can brick your device.**

If you are unhappy with the options `hyadb backup` uses by default, you can invoke `bu` via `adb shell` manually instead:

```bash
adb shell bu backup -apk -obb -all -keyvalue -nosystem > backup_2024-01-01.ab
# or
adb backup -f backup_2024-01-01.ab -apk -obb -all -keyvalue -nosystem
```

The above command is, essentially, what `hyadb backup` does by default.

### Split it into pieces

You can view contents of the generated Android Backup file via

```bash
hyadb ls backup_2024-01-01.ab
```

and split it into per-app backups via

```bash
hyadb split backup_2024-01-01.ab
```

which will produce a bunch of files named `hoardy_adb_split_<filename>__<num>_<appname>.ab` (e.g. `hoardy_adb_split_backup_2024-01-01__020_org.fdroid.fdroid.ab`).

### Restore a single app

A single per-app file can be fed back to `adb shell bu restore` to restore that singe app, e.g.

```bash
adb shell bu restore < hoardy_adb_split_backup_2024-01-01__020_org.fdroid.fdroid.ab
# or
adb restore hoardy_adb_split_backup_2024-01-01__020_org.fdroid.fdroid.ab
```

### Rebuild full backup from parts

You can also rebuild the original full-system backup from parts via

```bash
hyadb merge hoardy_adb_split_backup_2024-01-01__*.ab backup_2024-01-01.rebuilt.ab
```

to check that it produces exactly the same backup file

```bash
# strip encryption and compression from the original
hyadb strip backup_2024-01-01.ab backup_2024-01-01.stripped.ab

# compare to the stipped original and the rebuilt file
diff backup_2024-01-01.stripped.ab backup_2024-01-01.rebuilt.ab || echo differ
```

## Backup all app APKs and then restore them

### Backup all APKs

As noted above, apps that have `android:allowBackup` disabled in their manifests will be excluded from generated `backup_<date>.ab` files.
For such apps, only their APKs can be backed up by running

```bash
hyadb backup-apks
```

which will produce a bunch of files named `backup_<date>__<app>.apk` for each installed single-APK app and a bunch of directories named `backup_<date>__<app>` containing all app's APKs for multi-APK apps.

Inclusion of system apps among those is also supported with

```bash
hyadb backup-apks --system
```

### Restore the APKs

The resulting APKs can later be restored by running something like

```bash
hyadb restore-apks backup_2024-01-01__org.fdroid.fdroid.apk
```

or, to restore all of them at once:

```bash
hyadb restore-apks backup_2024-01-01__*
```

Note that, at the moment, `hyadb restore-apks` is not recursive and each app to be restored must be given as a separate argument.
When restoring a multi-APK app, it must be given as a directory containing its split-APK parts (and nothing else).

`hyadb backup-apks` generates result in this way, so, normally, you don't need to think about it.

Also note that, by default, `hyadb restore-apks` won't re-install APKs for apps that are already installed of the device.
Thus, if you run `hyadb backup-apks`, uninstall some apps, and then run `hyadb restore-apks backup_2024-01-01__*` later, after some of the still installed apps were updated, it will only restore the missing apps.
If you do want to force re-install, run `hyadb restore-apks --force <apk>` or re-install them manually via `adb install`.

# Alternatives

## ... for `hoardy-adb backup-apks` and `hoardy-adb restore-apks`

- [App Manager from F-Droid](
https://f-droid.org/packages/io.github.muntashirakon.AppManager/),
  which is an Android app with a nice UI:
  just select the apps you want, and press "Save APK";

- [BARIA from F-Droid](https://f-droid.org/packages/com.easwareapps.baria/),
  which is an Android app with much less nice UI:
  long-press all the apps you want to save, and then press the "Copy" button on the top of the screen to back them up;

- `getapk` and `restoreapks` scripts from [Adebar](https://codeberg.org/izzy/Adebar);

- or just run `adb shell pm path <app>`, `adb pull <resulting_path>`, and `adb install`/`adb install-multiple` manually.

## ... for `hoardy-adb backup` followed by `hoardy-adb split`

- [A gist by AnatomicJC](https://gist.github.com/AnatomicJC/e773dd55ae60ab0b2d6dd2351eb977c1), among other useful `adb` hacks, shows how to do per-app backups with pure `adb shell` and `adb backup` calls.

  Though, `hoardy-adb` is a nicer solution for this, since invoking `adb backup` repeatedly means you'll have to unlock your phone and press "Back up my data" button on the screen repeatedly, `hyadb backup` followed by `hyadb split` is much more convenient.

- [Adebar](https://codeberg.org/izzy/Adebar) can also generate scripts performing the above-mentioned `adb` commands, but it also intersperses them with `adb shell input` invocations, thus removing the need to manually press anything on the phone, most of the time.

  The result is similar to `hyadb backup` followed by `hyadb split`.

  Though, `Adebar` is rather flaky for large backups because it needs to intersperse `sleep`s all over those scripts to make them work, and if some of those backup steps take a while, the screen might get locked, and the rest of the backup will fail, which is not a problem with `hoardy-adb`.

## ... for other `hoardy-adb` subcommands

- `android-backup-toolkit` and friends:

  - [android-backup-extractor](https://github.com/nelenkov/android-backup-extractor) is a Java app that can decrypt and decompress Android Backup archives and convert them into TAR.

  - [android-backup-toolkit](https://sourceforge.net/projects/android-backup-toolkit/) builds on top of `android-backup-extractor` and provides a way to split full-system backup ADB files into per-app pieces.

  - [android-backup-processor](https://sourceforge.net/projects/android-backup-processor/) is an older version of `android-backup-toolkit`.

- [abpy](https://github.com/xBZZZZ/abpy) is a Python utility that can convert Android Backup files into TAR and back, so it's an alternative implementation of `hyadb unwrap` and `hyadb wrap`. I was unaware it existed when I made this, and I probably would have patched that instead if I were. After I became aware of it, `hoardy-adb` already had more features, so I was simply inspired by encryption passphrase checksum computation code there to implement it properly here (Android code has a bug causing checksums to be computed in a very idiosyncratic way that became a required behaviour when encryption support became the part of the file format), after which `hoardy-adb` gained its ability to produce encrypted `.ab` files as outputs.

- [ABX](https://github.com/info-lab/ABX) is a Python utility that can strip Android Backup headers from unencrypted backup files.
  So, basically, it's `hyadb unwrap` without decryption support.

- `ab2tar` of [Adebar](https://codeberg.org/izzy/Adebar) is a shell script (requires `openssl` and `zlib-flate` utils) doing `hyadb unwrap` thing without decryption support.

## If you have root access on your device

..., then instead of all of the above, you can backup all of your stuff with

- [Neo Backup from F-Droid](https://f-droid.org/packages/com.machiav3lli.backup/) and/or [Syncthing-Fork from F-Droid](https://f-droid.org/packages/com.github.catfriend1.syncthingandroid/);

  the latter of which is useful even without root access, though it won't be helping you backup your apps in that case;

- use `root_appbackup.sh` and `root_apprestore.sh` scripts from [Adebar](https://codeberg.org/izzy/Adebar);

- simply `adb pull` and/or `adb shell su -c 'tar ...' > backup.tar` from the device;

- running the following

  ```bash
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

  and then take per-app backup files from `/data/data/com.android.localtransport/files/`;

# Frequently Asked Questions

## `backup.ab` produced by `hyadb backup`/`adb shell bu backup`/`adb backup` does not contain the app I want. Can `hoardy-adb` help me backup it somehow?

Probably not.

If you are okay with only backing up the APKs, simply run `hyadb backup-apks`, as shown above.
No app data state will be preserved when restoring.

If you want to be able to backup both the APKs and app data states, including the current states of apps not included in `backup.ab`, you are probably out of luck.

As noted above, you can force an app to be included in `backup.ab` by [setting `android:allowBackup` in its manifest, re-signing the APK with your own key](https://stackpointer.io/mobile/android-enable-adb-backup-for-any-app/462/), and then re-installing the app.
**But, you won't be able to install that re-signed APK while the original APK in installed.
You will have to uninstall the app first.**
And you will have to repeat the re-signing on each app update.

## But uninstalling the app will loose all that app's data state!

Yes, unfortunately.
I completely agree that this is absolutely stupid.
Blame Google for your suffering.

## But I need to backup that app!

Check if the app in question has a custom backup function, usually somewhere in its settings.
If it does, then

- use it to make a backup,
- check that the restore function actually works (you'd be surprised how often it does not):

  - the simple safe way to do this is to install the original APK to another phone and then use app's restore function to restore from your backup there;

  - or you can use [Shelter from F-Droid](https://f-droid.org/packages/net.typeblog.shelter/) to clone the app into your Work Profile and restore the backup there instead;

    this does not require a second phone, but it's a bit involved;

    see Shelter's help in its "Settings" menu for how to copy your backup files to your Work Profile, as this part will be rather annoying;
- then uninstall the app and install your re-signed version;
- restore your custom app backup in your re-signed app.

You can now use `hyadb backup` for future backups.

## But that app has no custom backup function!

If the app does not have a custom backup function, you can either

- root your phone and then use the above ["If you have root access on your device"](#if-you-have-root-access-on-your-device) instructions; or
- ask your app's developers to either publish a version of the app with `android:allowBackup` set (signed with their key) or add a custom backup function to the app; or
- loose your current data state by uninstalling the app, installing your re-signed APK, and thus, at the very least, stopping data loss from this point on.

## Anything else nice and relevant from F-Droid?

A ton of stuff.
Simply browse F-Droid's "System" category, or use search.

Also, you can switch to [`Droid-ify`](https://f-droid.org/packages/com.looker.droidify/) as your default F-Droid UI, which, IMHO, is nicer than the default one.

# Meta

## Changelog?

See [`CHANGELOG.md`](./CHANGELOG.md).

## TODO?

See the [bottom of `CHANGELOG.md`](./CHANGELOG.md#todo).

## License

[GPLv3](./LICENSE.txt)+, some small library parts are MIT.

## Contributing

Contributions are accepted both via GitHub issues and PRs, and via pure email.
In the latter case I expect to see patches formatted with `git-format-patch`.

If you want to perform a major change and you want it to be accepted upstream here, you should probably write me an email or open an issue on GitHub first.

# Usage

## hoardy-adb

A simple front-end to backup and restore commands of the `adb` tool and a handy Swiss-army-knife-like utility for manipulating Android Backup files (`backup.ab`, `*.ab`, `*.adb`) produced by `adb shell bu backup`, `adb backup`, `bmgr`, and similar tools.

Android Backup file consists of a metadata header followed by a PAX-formatted TAR file (optionally) compressed with zlib (the only compressing Android Backup file format supports) and then (optionally) encrypted with AES-256 (the only encryption Android Backup file format supports).

Below, all input decryption options apply to all subcommands taking Android Backup files as input(s) and all output encryption options apply to all subcommands producing Android Backup files as output(s).

- options:
  - `--version`
  : show program's version number and exit
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown

- input decryption parameters:
  - `-p PASSPHRASE, --passphrase PASSPHRASE`
  : passphrase for an encrypted `INPUT_AB_FILE`
  - `--passfile PASSFILE`
  : a file containing the passphrase for an encrypted `INPUT_AB_FILE`; similar to `-p` option but the whole contents of the file will be used verbatim, allowing you to, e.g. use new line symbols or strange character encodings in there; default: guess based on `INPUT_AB_FILE` trying to replace ".ab" or ".adb" extension with ".passphrase.txt"
  - `--ignore-checksum`
  : ignore checksum field in `INPUT_AB_FILE`, useful when decrypting backups produced by weird Android firmwares

- output encryption parameters:
  - `--output-passphrase OUTPUT_PASSPHRASE`
  : passphrase for an encrypted `OUTPUT_AB_FILE`
  - `--output-passfile OUTPUT_PASSFILE`
  : a file containing the passphrase for an encrypted `OUTPUT_AB_FILE`
  - `--output-salt-bytes SALT_BYTES`
  : PBKDF2HMAC salt length in bytes; default: 64
  - `--output-iterations ITERATIONS`
  : PBKDF2HMAC iterations; default: 10000

- subcommands:
  - `{backup,backup-apks,restore-apks,ls,list,rewrap,strip,ab2ab,split,ab2many,merge,many2ab,unwrap,ab2tar,wrap,tar2ab}`
    - `backup`
    : backup an Android device into an Android Backup file
    - `backup-apks`
    : backup all available APKs from an Android device into separate APK files
    - `restore-apks`
    : restore APKs backed up by `backup-apks`
    - `ls (list)`
    : list contents of an Android Backup file
    - `rewrap (strip, ab2ab)`
    : convert an Android Backup file into a equivalent Android Backup file, stripping away or (re-)applying encyption and/or compression to it
    - `split (ab2many)`
    : split a full-system Android Backup file into a bunch of per-app Android Backup files
    - `merge (many2ab)`
    : merge a bunch of Android Backup files into one
    - `unwrap (ab2tar)`
    : convert an Android Backup file into a TAR file
    - `wrap (tar2ab)`
    : convert a TAR file into an Android Backup file

### hoardy-adb backup

Backup a device by running `adb shell bu backup` command and saving its output to a `.ab` file.

Note that this will only backup data of apps that permit themselves being backed up.
See this project's top-level `README.md` for more info.

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown
  - `--system`
  : include system apps in the backup too; default: only include user apps
  - `--no-auto-confirm`
  : do not try to automatically start the backup on the device side via `adb shell input`, ask the user to do it manually instead
  - `--to OUTPUT_AB_FILE`
  : file to write the output to, set to "-" to use standard output; default: `backup_<date>.ab`

### hoardy-adb backup-apks

Backup all available APK files from a device by running `adb shell pm` and then `adb pull`ing each APK file.

Note that, unlike `hoardy-adb backup`, this subcommand will backup everything, but only the APKs, i.e. no app data will be backed up.
See this project's top-level `README.md` for more info.

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown
  - `--system`
  : include system apps in the backup too; default: only include user apps
  - `--prefix PREFIX`
  : file name prefix for output files; default: `backup_<date>`

### hoardy-adb restore-apks

The inverse to `backup-apks`, which runs `adb install` (for single-APK apps) or `adb install-multiple` (for multi-APK apps) as appropriate.

- positional arguments:
  - `APK_OR_DIR`
  : what to restore; a separate APK file for a single-APK app or a directory of APK files for a multi-APK app; can be specified multiple times, in which case each given input will be restored

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown
  - `--force`
  : force-reinstall apps that appear to be already installed on the device; by default, APKs for such apps will be skipped

### hoardy-adb ls

List contents of an Android Backup file similar to how `tar -tvf` would do, but this will also show Android Backup file version, compression, and encryption parameters.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown

### hoardy-adb rewrap

Convert a given Android Backup file into another Android Backup file with encyption and/or compression stripped away or (re-) applied.

Versioning parameters and the TAR file stored inside the input file are copied into the output file verbatim.

For instance, with this subcommand you can convert an encrypted and compressed Android Backup file into a simple unencrypted and uncompressed version of the same, or vice versa.
The former of which is useful if your Android firmware forces you to encrypt your backups but you store your backups on an encrypted media anyway and don't want to remember more passphrases than strictly necessary.
Or if you want to strip encryption and compression and re-compress using something better than zlib.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input
  - `OUTPUT_AB_FILE`
  : file to write the output to, set to "-" to use standard output; default: "-" if `INPUT_TAR_FILE` is "-", otherwise replaces ".ab" or ".adb" extension of `INPUT_TAR_FILE` with `.stripped.ab`

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown
  - `-k, --keep-compression`
  : copy compression flag and data from input to output verbatim; this will make the output into a compressed Android Backup file if the input Android Backup file is compressed and vice versa; this is the fastest way to `strip`, since it just copies bytes around
  - `-c, --compress`
  : (re-)compress the output file; it will use higher compression level defaults than those used by Android; with this option enabled `hoardy-adb` will be quite slow; by default, compression will be stripped away
  - `-e, --encrypt`
  : (re-)encrypt the output file; on a modern CPU (with AES-NI) enabling this option costs almost nothing, on an old CPU it will be quite slow; by default, encription will be stripped away

### hoardy-adb split

Split a full-system Android Backup file into a bunch of per-app Android Backup files.

Resulting per-app files can be given to `adb restore` to restore selected apps.

Also, if you do backups regularly, then splitting large Android Backup files like this and then deduplicating resulting per-app files between backups could save a lot of disk space.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown
  - `-c, --compress`
  : compress per-app output files; by default, the outputs will be uncompressed
  - `-e, --encrypt`
  : encrypt per-app output files; when enabled, the `--output-passphrase`/`--output-passfile` and other `output encryption parameters` will be reused for all the generated files, but all encryption keys and salts will be unique; by default, the outputs will be unencrypted
  - `--prefix PREFIX`
  : file name prefix for output files; default: `hoardy_adb_split_backup` if `INPUT_AB_FILE` is "-", `hoardy_adb_split_<INPUT_AB_FILE without its ".ab" or ".adb" extension>` otherwise

### hoardy-adb merge

Merge many smaller Android Backup files into a single larger one.
A reverse operation to `split`.

This mostly exists for testing of `split`.

- positional arguments:
  - `INPUT_AB_FILE`
  : Android Backup files to be used as inputs
  - `OUTPUT_AB_FILE`
  : file to write the output to

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown
  - `-c, --compress`
  : compress the output file; by default, the output will be uncompressed
  - `-e, --encrypt`
  : encrypt the output file; by default, the output will be unencrypted

### hoardy-adb unwrap

Convert Android Backup file into a TAR file by stripping Android Backup header, decrypting and decompressing as necessary.

The TAR file stored inside the input file gets copied into the output file verbatim.

- positional arguments:
  - `INPUT_AB_FILE`
  : an Android Backup file to be used as input, set to "-" to use standard input
  - `OUTPUT_TAR_FILE`
  : file to write output to, set to "-" to use standard output; default: guess based on `INPUT_AB_FILE` while setting extension to `.tar`

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown

### hoardy-adb wrap

Convert a TAR file into an Android Backup file by prepending Android Backup header, compressing and encrypting as requested.

The input TAR file gets copied into the output file verbatim.

Note that unwrapping a `.ab` file, unpacking the resulting `.tar`, editing the resulting files, packing them back with GNU `tar` utility, running `hoardy-adb wrap`, and then running `adb restore` on the resulting file will probably crash your Android device (phone or whatever) because the Android-side code restoring from the backup expects the data in the packed TAR to be in a certain order and have certain PAX headers, which GNU `tar` will not produce.

So you should only use this on files previously produced by `hoardy-adb unwrap` or if you know what it is you are doing.

- positional arguments:
  - `INPUT_TAR_FILE`
  : a TAR file to be used as input, set to "-" to use standard input
  - `OUTPUT_AB_FILE`
  : file to write the output to, set to "-" to use standard output; default: "-" if `INPUT_TAR_FILE` is "-", otherwise replaces ".ab" or ".adb" extension of `INPUT_TAR_FILE` with `.ab`

- options:
  - `-h, --help`
  : show this help message and exit
  - `--markdown`
  : show `--help` formatted in Markdown
  - `-c, --compress`
  : compress the output file; by default, the output will be uncompressed
  - `-e, --encrypt`
  : encrypt the output file; by default, the output will be unencrypted
  - `--output-version OUTPUT_VERSION`
  : Android Backup file version to use; required

## Usage notes

Giving an encrypted `INPUT_AB_FILE` as input, not specifying `--passphrase` or `--passfile`, and not having a file named `{INPUT_AB_FILE with ".ab" or ".adb" extension replaced with ".passphrase.txt"}` in the same directory will cause the passphrase to be read interactively from the tty.

## Examples

- List contents of an Android Backup file:
  ```
  hyadb ls backup.ab
  ```

- Use `tar` util to list contents of an Android Backup file instead of running `hyadb ls`:
  ```
  hyadb unwrap backup.ab - | tar -tvf -
  ```

- Extract contents of an Android Backup file:
  ```
  hyadb unwrap backup.ab - | tar -xvf -
  ```

- Strip encryption and compression from an Android Backup file:
  ```
  # equivalent
  hyadb strip backup.ab backup.stripped.ab
  hyadb strip backup.ab
  ```

  ```
  # equivalent
  hyadb strip --passphrase secret backup.ab
  hyadb strip -p secret backup.ab
  ```

  ```
  # with passphrase taken from a file
  echo -n secret > backup.passphrase.txt
  # equivalent
  hyadb strip backup.ab
  hyadb strip --passfile backup.passphrase.txt backup.ab
  ```

  ```
  # with a weird passphrase taken from a file
  echo -ne "secret\r\n\x00another line" > backup.passphrase.txt
  hyadb strip backup.ab
  ```

- Strip encryption but keep compression, if any:
  ```
  # equivalent
  hyadb strip --keep-compression backup.ab backup.stripped.ab
  hyadb strip -k backup.ab
  ```

- Strip encryption and compression from an Android Backup file and then re-compress using `xz`:
  ```
  hyadb strip backup.ab - | xz --compress -9 - > backup.ab.xz
  # ... and then convert to tar and list contents:
  xzcat backup.ab.xz | hyadb unwrap - | tar -tvf -
  ```

- Convert an Android Backup file into a TAR archive:
  ```
  # equivalent
  hyadb unwrap backup.ab backup.tar
  hyadb unwrap backup.ab
  ```

- Convert a TAR archive into an Android Backup file:
  ```
  # equivalent
  hyadb wrap --output-version=5 backup.tar backup.ab
  hyadb wrap --output-version=5 backup.tar
  ```

# Development: `./test-hyadb.sh [--help] [--wine] [--output-version VERSION] PATH [PATH ...]`

Sanity check and test `hoardy-adb` command-line interface.

## Example

```
./test-hyadb.sh backup.ab backup2.ab
```
