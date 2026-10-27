# Windows: recover from repeated marketplace update failures

Use this guide if ARS marketplace updates fail and repeated temporary checkouts
consume disk space. If C: is full, first stop Codex and free space as described
in step 1. Then check the Codex version (see
[Before you switch](#before-you-switch-check-the-codex-version)). If growth
continues on a fixed version, this guide switches **only `ars-codex`** from a
Git marketplace to a local snapshot. Future ARS updates become manual. It does
not repair Codex's installer.

## What is known

In [issue #43](https://github.com/Imbad0202/academic-research-skills-codex/issues/43),
a Windows user reported roughly one new staging checkout per minute, more than
10 GB of accumulated data, and eventually no free space on C:. The reported CLI
was `0.163.0-alpha.10.2`; ARS remained installed at `3.23.0` while an unpromoted
staging checkout contained `3.23.1`.

One explicit upgrade failed with `Access is denied` (`os error 5`) when moving
the previous marketplace root. A concurrent backup was running during that
attempt; the original lock holder and the cause of every earlier failure remain
unknown. Separate proxy/connection errors do not explain all leftover checkouts.
The evidence points toward marketplace replacement, retry, and cleanup handling;
it does not establish that ARS research scripts created the directories.

The reporter switched to a local source and observed no new checkout for about
nine minutes. This is a short observation on one machine, not a Windows-wide
validation. The packaged ARS plugin does not register the vendored Claude
SessionStart updater as a Codex hook.

## Before you switch: check the Codex version

[Codex CLI 0.164.0](https://github.com/openai/codex/releases/tag/rust-v0.164.0),
released on 2026-10-23, includes two upstream cleanup fixes:

- [openai/codex#55689](https://github.com/openai/codex/pull/55689) removes
  temporary checkouts when a marketplace add or upgrade finishes or fails, and
  reclaims up to four abandoned staging directories per pass during later add
  and upgrade operations; current staging directories are protected by owner locks.
- [openai/codex#55690](https://github.com/openai/codex/pull/55690) reclaims
  legacy directories left by older Codex versions, which have no owner lock, by
  directory modification time: `marketplace-upgrade-*` after 10 minutes and
  `marketplace-add-*` after 24 hours.

These fixes address leftover staging directories. They have not been shown to
fix the `os error 5` failure in #43 or the repeated upgrade attempts, and the
upstream report [openai/codex#39421](https://github.com/openai/codex/issues/39421)
remains open.

If C: is full, free enough space first as described in step 1. Then check the
CLI bundled with the affected Codex Desktop installation; updating a separate
CLI on PATH may not change the runtime that Desktop uses. On a version earlier
than 0.164.0, update Codex and watch the two locations in step 4 before
switching sources. A running add or upgrade still creates a staging directory,
and old directories are reclaimed only a few at a time during later operations,
so a new directory alone is not a failure. If leftover directories keep
accumulating after operations finish, or disk use keeps growing, on 0.164.0 or
later, continue with step 1, and please report the versions and errors in #43.

## 1. Stop growth and preserve the current state

1. Stop manual upgrade attempts. Quit Codex Desktop and other Codex processes
   using this marketplace before copying its files; check Task Manager for
   remaining processes rather than relying on a closed window. If C: is full, first recover
   enough space for Windows and a standalone terminal to work; do not depend on
   Codex's command runner to recover itself. If space cannot be freed elsewhere,
   apply the [stale-file criteria below](#4-restart-verify-then-consider-stale-files)
   to individually verified ARS staging checkouts before continuing. Preserve the
   active root (normally `.tmp\marketplaces\ars-codex`), configuration, sessions,
   and installed plugin cache. Do not delete the active root before a verified
   independent copy exists. Moving verified stale files to the Recycle Bin does
   not free space on that drive; permanently remove only those identified items,
   not unrelated Recycle Bin contents.
2. Preserve the Codex configuration and the working marketplace on a drive with
   sufficient space. The default configuration is
   `%USERPROFILE%\.codex\config.toml`; if you use a custom Codex home, use its
   actual location. Keep that backup private.
3. In a standalone PowerShell window, record the current sources and plugin
   state locally. Run from a neutral directory outside any repository containing
   `.agents/plugins/marketplace.json`, to avoid an implicitly discovered project
   marketplace with the same name. Use the CLI belonging to the affected Codex
   installation and the same Codex home. A separate `codex` on PATH may be a
   different version; compare its version with the affected installation.

Paste each PowerShell block as a whole, then press Enter. The surrounding `. {`
and `}` keep the operations together; `try`/`catch` also stops the block on a
terminating statement error. After any error, fix it and rerun the whole block.

```powershell
. {
    try {
        codex --version
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'CLI version check failed' }
        codex plugin marketplace list --json
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Marketplace inspection failed' }
        codex plugin list --marketplace ars-codex --json
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Plugin inspection failed' }
    } catch {
        throw
    }
}
```

Save these outputs privately on the backup drive before proceeding. Record the
original ARS source/ref, installed version, and enabled state, including the
before-state for other marketplaces. If a command fails, stop and resolve
that failure before changing the source. If your CLI lacks these subcommands,
check its `--help`; this guide's commands were checked against CLI `0.163.0`.

**Disabling the plugin alone is insufficient.** Codex can still refresh files
for configured plugins when they are disabled. Remove the Git source in step 3
to stop using it for ARS. See the official
[plugin packaging documentation](https://developers.openai.com/plugins/build/plugins).

## 2. Prepare a separate, complete local snapshot

Use a short, absolute, ASCII-only permanent destination path outside `.codex` and
its caches, on a drive with sufficient space. This also avoids native-output
encoding differences in Windows PowerShell 5.1. The paths below are examples: set `$arsSourceRoot` to the
working marketplace root reported in step 1 and `$arsLocalRoot` to a **new**
directory. The version in the directory name is only a label; the manifest is
checked afterward. Keep Codex and backup jobs using the source closed.

The following Windows PowerShell block uses Windows' `robocopy.exe` to preserve
hidden folders, excludes the root Git/install metadata, and compares every
relative file path and SHA-256 hash before and after copying. It rejects links
and junctions rather than following them. Any copy, enumeration, long-path, or
hash error must be resolved before switching sources. A failed copy can leave
an incomplete destination; preserve the source and choose a new destination for
another attempt. Do not reuse the failed directory as the local marketplace.
If Windows PowerShell 5.1 reports path-too-long during enumeration or hashing,
retry the verification in PowerShell 7 (`pwsh`); do not skip the failing files.
Robocopy's exit codes are documented by
[Microsoft](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy).

```powershell
. {
    try {
        $arsSourceRoot = "$env:USERPROFILE\.codex\.tmp\marketplaces\ars-codex"
        $arsLocalRoot = 'D:\ars-local\3.23.0'
        $arsSourceRoot = (Resolve-Path -LiteralPath $arsSourceRoot -ErrorAction Stop).ProviderPath.TrimEnd('\')
        $arsLocalRoot = [IO.Path]::GetFullPath($arsLocalRoot).TrimEnd('\')
        if (Test-Path -LiteralPath $arsLocalRoot) { throw 'Destination exists; choose a new directory' }
        if ($arsLocalRoot -ieq $arsSourceRoot -or
            $arsLocalRoot.StartsWith($arsSourceRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
            $arsSourceRoot.StartsWith($arsLocalRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Source and destination must be separate directories'
        }
        $arsRobocopy = (Get-Command robocopy.exe -CommandType Application -ErrorAction Stop).Source

        function Get-ArsSnapshotManifest([string]$Root) {
            $arsBase = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).ProviderPath.TrimEnd('\')
            $arsRootItem = Get-Item -LiteralPath $arsBase -Force -ErrorAction Stop
            if (-not $arsRootItem.PSIsContainer -or
                ($arsRootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Not a regular directory: $arsBase"
            }
            $arsQueue = New-Object 'System.Collections.Generic.Queue[string]'
            $arsRows = New-Object 'System.Collections.Generic.List[string]'
            $arsQueue.Enqueue($arsBase)
            while ($arsQueue.Count -gt 0) {
                foreach ($arsItem in (Get-ChildItem -LiteralPath $arsQueue.Dequeue() -Force -ErrorAction Stop)) {
                    $arsRelative = $arsItem.FullName.Substring($arsBase.Length + 1)
                    if ($arsRelative -eq '.git' -or $arsRelative -eq '.codex-marketplace-install.json') { continue }
                    if ($arsItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                        throw "Link or junction is not allowed: $arsRelative"
                    }
                    if ($arsItem.PSIsContainer) {
                        $arsQueue.Enqueue($arsItem.FullName)
                    } else {
                        $arsHash = (Get-FileHash -LiteralPath $arsItem.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
                        $arsRows.Add("$arsHash`t$arsRelative")
                    }
                }
            }
            if ($arsRows.Count -eq 0) { throw 'Empty snapshot' }
            $arsRows | Sort-Object
        }

        $arsBefore = @(Get-ArsSnapshotManifest $arsSourceRoot)
        & $arsRobocopy "$arsSourceRoot" "$arsLocalRoot" /E /R:1 /W:1 /XJ /XD (Join-Path $arsSourceRoot '.git') /XF (Join-Path $arsSourceRoot '.codex-marketplace-install.json')
        # Robocopy uses 0-7 for non-failure results; file equality is checked below.
        if ($LASTEXITCODE -ge 8) { throw "Copy failed: robocopy exit $LASTEXITCODE" }
        $arsAfter = @(Get-ArsSnapshotManifest $arsSourceRoot)
        $arsCopied = @(Get-ArsSnapshotManifest $arsLocalRoot)
        if (Compare-Object $arsBefore $arsAfter) { throw 'Source changed during copying; stop here' }
        if (Compare-Object $arsBefore $arsCopied) { throw 'Snapshot files or hashes differ; stop here' }
        "Verified $($arsCopied.Count) files. Keep the original source for recovery."
    } catch {
        throw
    }
}
```

Do not point the local source at `.staging`, a `git-*` temporary directory, or
only `plugins/ars-codex`. The marketplace root must retain this layout, including
**all** files below the bundled skill:

```text
<local-root>/
  .agents/plugins/marketplace.json
  plugins/ars-codex/.codex-plugin/plugin.json
  plugins/ars-codex/skills/academic-research-suite/
    SKILL.md
    manifest.json
    ars/...
    codex/...
```

Check the layout and version after the verified copy. Continue in the same
PowerShell window, keeping `$arsLocalRoot` from the copy block above.

```powershell
. {
    try {
        $arsMarketplace = $null
        $arsPlugin = $null
        $arsLocalRoot = (Resolve-Path -LiteralPath $arsLocalRoot -ErrorAction Stop).ProviderPath.TrimEnd('\')
        $arsRequiredFiles = @(
            '.agents/plugins/marketplace.json',
            'plugins/ars-codex/.codex-plugin/plugin.json',
            'plugins/ars-codex/skills/academic-research-suite/SKILL.md',
            'plugins/ars-codex/skills/academic-research-suite/manifest.json'
        )
        foreach ($arsRelativePath in $arsRequiredFiles) {
            if (-not (Test-Path -LiteralPath (Join-Path $arsLocalRoot $arsRelativePath) -PathType Leaf)) {
                throw "Incomplete marketplace: $arsRelativePath"
            }
        }
        $arsMarketplace = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $arsLocalRoot '.agents/plugins/marketplace.json') -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        $arsPlugin = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $arsLocalRoot 'plugins/ars-codex/.codex-plugin/plugin.json') -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        if ($arsMarketplace.name -ne 'ars-codex' -or $arsPlugin.name -ne 'ars-codex') {
            throw 'Unexpected marketplace or plugin identity'
        }
        $arsPlugin.version
    } catch {
        throw
    }
}
```

Confirm that the printed version is the one you chose. Do not continue if either
block reported any error. Keep this window open for the next step.

## 3. Switch only ARS to the local source

Keep Codex Desktop closed. Run the whole block below. `marketplace remove`
changes the configured source; do not substitute `codex plugin remove`, which
uninstalls the plugin. Install from the selected local source before verifying
the installed version and source paths.

```powershell
. {
    try {
        # Recheck the selected snapshot before removing any configured source.
        $arsPlugin = $null
        $arsMarketplace = $null
        $arsActualRoot = $null
        $arsActualPlugin = $null
        if ([string]::IsNullOrWhiteSpace($arsLocalRoot)) { throw 'Set $arsLocalRoot to the verified snapshot first' }
        $arsLocalRoot = (Resolve-Path -LiteralPath $arsLocalRoot -ErrorAction Stop).ProviderPath.TrimEnd('\')
        foreach ($arsRequired in @(
            '.agents/plugins/marketplace.json',
            'plugins/ars-codex/.codex-plugin/plugin.json',
            'plugins/ars-codex/skills/academic-research-suite/SKILL.md',
            'plugins/ars-codex/skills/academic-research-suite/manifest.json'
        )) {
            if (-not (Test-Path -LiteralPath (Join-Path $arsLocalRoot $arsRequired) -PathType Leaf -ErrorAction Stop)) {
                throw "Incomplete local snapshot: $arsRequired"
            }
        }
        $arsMarketplace = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $arsLocalRoot '.agents/plugins/marketplace.json') -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        $arsPlugin = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $arsLocalRoot 'plugins/ars-codex/.codex-plugin/plugin.json') -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        $arsCandidates = @($arsMarketplace.plugins | Where-Object { $_.name -eq 'ars-codex' })
        if ($arsMarketplace.name -ne 'ars-codex' -or $arsCandidates.Count -ne 1 -or
            $arsCandidates[0].source.source -ne 'local' -or $arsCandidates[0].source.path -ne './plugins/ars-codex' -or
            $arsPlugin.name -ne 'ars-codex' -or [string]::IsNullOrWhiteSpace([string]$arsPlugin.version)) {
            throw 'Invalid local marketplace or plugin manifest'
        }

        function ConvertTo-ArsComparablePath([string]$Path) {
            if ([string]::IsNullOrWhiteSpace($Path)) { throw 'Missing source path' }
            if ($Path.StartsWith('\\?\UNC\', [StringComparison]::OrdinalIgnoreCase)) {
                $Path = '\\' + $Path.Substring(8)
            } elseif ($Path.StartsWith('\\?\', [StringComparison]::OrdinalIgnoreCase)) {
                $Path = $Path.Substring(4)
            }
            [IO.Path]::GetFullPath($Path).TrimEnd('\')
        }

        $arsSourcesJson = codex plugin marketplace list --json
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Marketplace inspection failed; stop here' }
        $arsSources = $arsSourcesJson | ConvertFrom-Json -ErrorAction Stop
        if ($null -eq $arsSources.marketplaces) { throw 'Unexpected marketplace list format' }
        $arsCurrent = @($arsSources.marketplaces | Where-Object { $_.name -eq 'ars-codex' })
        if ($arsCurrent.Count -gt 1) { throw 'Multiple ARS sources found; inspect them before continuing' }
        if ($arsCurrent.Count -eq 1) {
            codex plugin marketplace remove ars-codex --json
            if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Marketplace removal failed; stop here' }
        }
        codex plugin marketplace add "$arsLocalRoot" --json
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Local registration failed; keep Desktop closed and see rollback below' }
        codex plugin add ars-codex@ars-codex --json
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Local installation failed; stop here' }
        $arsStateJson = codex plugin list --marketplace ars-codex --json
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Plugin inspection failed; stop here' }
        $arsState = $arsStateJson | ConvertFrom-Json -ErrorAction Stop
        $arsInstalled = @($arsState.installed | Where-Object { $_.pluginId -eq 'ars-codex@ars-codex' })
        if ($arsInstalled.Count -ne 1) { throw 'Expected exactly one installed ARS entry' }
        $arsEntry = $arsInstalled[0]
        if ($arsEntry.installed -ne $true -or $arsEntry.version -ne $arsPlugin.version) {
            throw 'Installation state or version does not match the selected snapshot'
        }
        if ($arsEntry.source.source -ne 'local' -or $arsEntry.marketplaceSource.sourceType -ne 'local') {
            throw 'Plugin and marketplace must both use local sources'
        }
        $arsActualRoot = ConvertTo-ArsComparablePath $arsEntry.marketplaceSource.source
        $arsActualPlugin = ConvertTo-ArsComparablePath $arsEntry.source.path
        $arsExpectedRoot = ConvertTo-ArsComparablePath $arsLocalRoot
        $arsExpectedPlugin = ConvertTo-ArsComparablePath (Join-Path $arsLocalRoot 'plugins\ars-codex')
        if ($arsActualRoot -ine $arsExpectedRoot -or $arsActualPlugin -ine $arsExpectedPlugin) {
            "Expected marketplace: $arsExpectedRoot; actual: $arsActualRoot"
            "Expected plugin: $arsExpectedPlugin; actual: $arsActualPlugin"
            throw 'Source paths do not match the permanent local snapshot'
        }
        $arsEntry | ConvertTo-Json -Depth 6
    } catch {
        throw
    }
}
```

Inspect `enabled` in the printed entry. For a normally enabled installation it
should be `true`. If installation changes a deliberately disabled setting,
restore only that plugin's `enabled` setting in the configuration before reopening
Desktop. A plugin source under the old Git checkout is not acceptable even if it
is marked `local`; the block checks **both exact paths** against the new snapshot.

Run `codex plugin marketplace list --json` again and compare with the saved
before-state: only the ARS source should have changed. If verification fails,
keep Desktop closed and correct the local path or use the rollback procedure.
Command fields are described in the official
[Codex CLI reference](https://learn.chatgpt.com/docs/cli/reference).

## 4. Restart, verify, then consider stale files

Reopen Codex Desktop and start a new conversation. Confirm ARS is available and
repeat the source/version checks. Watch free disk space and the two reported
locations for several former retry intervals:

- `%USERPROFILE%\.codex\.tmp\marketplaces\.staging\marketplace-upgrade-*`
- `%USERPROFILE%\.codex\.tmp\git-*`

Use the corresponding paths under a custom Codex home if applicable. Normal
operations of other Git marketplaces can still create and remove staging
directories there. If leftover directories keep accumulating after operations
finish, or disk use keeps growing, stop Codex again and investigate which
configured Git marketplace owns them. Other marketplaces may use the same temporary root.
Do not claim recovery solely because a directory count briefly reaches zero.

Switching the source does not promise to remove old staging files. On Codex
0.164.0 or later, later marketplace add or upgrade operations may reclaim some
of them; do not rely on that alone. Before any manual cleanup, close Codex and matching Git/backup processes, preserve the
working source (and its independent copy when already prepared), and identify
each candidate by its path, repository origin
where available, age, absence of directory links/junctions, and absence of active
operations. A `git-*` name by itself does not establish ARS ownership. If ownership
or inactivity cannot be established, leave that candidate for diagnosis. Do not
bulk-delete `.codex`, `.tmp`, or every `git-*` directory. This guide intentionally
provides no recursive deletion command.

## Manual updates and rollback

**Manual update:** obtain the intended release in a separate, short checkout,
then use step 2 to copy and verify it into another new permanent snapshot. For
example, this makes one explicit Git clone outside Codex's caches; edit the tag
and destination to your chosen release and an unused directory:

```powershell
. {
    try {
        git -c core.longpaths=true -c core.autocrlf=false clone --depth 1 --branch v3.23.1 https://github.com/Imbad0202/academic-research-skills-codex.git D:\ars-fetch\3.23.1
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Release checkout failed; keep using the existing snapshot' }
    } catch {
        throw
    }
}
```

Set the first two variables in step 2 to that checkout and a new local snapshot
path. After copy and layout validation, close Desktop, repeat step 3 with the new
path, and verify the new version after restarting. Keep the previous snapshot
until the new one works. `marketplace upgrade` refreshes Git sources and is not
the update method for this local snapshot. Do not overwrite the active snapshot
in place. A clone failure does not change the active local source.

**Local rollback after a manual update:** keep Desktop closed, use the preserved
previous local snapshot as `$arsLocalRoot` (for example, run
`$arsLocalRoot = 'D:\ars-local\3.23.0'` in the PowerShell window), repeat its layout/version check in
step 2 (so `$arsPlugin.version` also refers to the previous version), and repeat
the source switch and verification in step 3. No copy is needed for an already
verified preserved snapshot.

**Failed first switch or failed registration:** keep Desktop closed. If removal
succeeded but adding the local source failed, fix the local snapshot, repeat
step 2's verification, and rerun step 3's full block. It inspects the sources and
skips removal when no ARS source is registered. If no usable local snapshot can be
prepared, restoring the original Git URL/ref using `marketplace add` is an
explicit fallback, but resumes the potentially failing refreshes. For the
original source reported in #43, that command is:

```powershell
. {
    try {
        codex plugin marketplace add https://github.com/Imbad0202/academic-research-skills-codex.git --ref main --json
        if (-not $? -or $LASTEXITCODE -ne 0) { throw 'Original source registration failed; keep Desktop closed' }
    } catch {
        throw
    }
}
```

Use the URL/ref recorded in step 1 if yours differs. Run this fallback only when
the ARS source is absent; if a local ARS source was already added, remove it with
the checked removal command first. Verify the installed plugin/version and
intended enabled state before reopening Desktop. Returning to Git is not proof
of recovery; if growth resumes, close Desktop again and continue local-source
recovery. Do not repeatedly retry a failing Git registration.

**Return to Git later:** only after deciding to resume automatic Git refreshes,
remove the local marketplace source and add the original Git URL/ref recorded
in step 1, then install and verify ARS. Returning to Git may reintroduce the
reported failure. Preserve the local snapshot for recovery. Do not restore the
entire old configuration over unrelated changes.

## Validation scope

The maintainer exercised local registration, installation, source switching,
updates from `3.23.0` to `3.23.1`, and rollback with Codex CLI `0.163.0` on macOS
using disposable configuration. The installed manifest matched the selected
snapshot, the old snapshot was not deleted, and an unrelated marketplace remained
registered. This does not reproduce Windows directory locking or prove that the
full procedure works on the affected Windows build. All six PowerShell blocks
were parsed with PowerShell `7.6.6` on macOS; the manifest comparison detected
changed/missing files, included hidden files, excluded root metadata, and rejected
a directory link. Native-command failure stopped the surrounding block. These
checks also refused unset/missing/malformed snapshots before any CLI call and
an unexpected source-list format before any source mutation. Drive and UNC
extended-prefix comparisons were tested as string normalization on macOS.
These checks do not validate Windows PowerShell 5.1, Windows Robocopy/long-path behavior,
or Desktop restart behavior; those still need confirmation there.

## Evidence for further diagnosis

Record the affected Desktop and CLI versions, Windows and Git versions, ARS
version, free space, directory creation times/counts, exact errors, and whether
growth stops after changing the marketplace source. Include only relevant,
redacted output; do not post full configuration files, credentials, conversation
logs, or personal files. Avoid repeatedly running a failing upgrade merely to
collect evidence. Link any Codex upstream report back to
[#43](https://github.com/Imbad0202/academic-research-skills-codex/issues/43).
