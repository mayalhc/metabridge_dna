# Kimodo Cascadeur Plugin

Copyright (c) 2026 Chamiseul. All rights reserved.

Three tools for Cascadeur, plus the listener a Blender add-on talks to.

## Install

Run **`install_plugin.bat`**. It finds Cascadeur, asks for Administrator
because the plugin folder lives under Program Files, and copies only the files
that differ from what is already there.

If Cascadeur is somewhere unusual:

    install_plugin.bat --cascadeur-root "D:\Games\Cascadeur"

It also asks for the **KimodoEngine folder** - the one holding
`start_ardy.bat`. Only ARDY Live needs it, so leaving it blank is fine if you
only want MetaArKit and Rig Quadruped; everything still installs.

Restart Cascadeur afterwards. It reads its scripts once, at startup.

## What you get, under Animation Scripts

**Rig Quadruped (auto)** — Cascadeur fills the Quick Rigging Tool for a biped
because it knows what a human skeleton is called. A quadruped is named however
its author felt, so all 161 fields are yours to type. This reads the skeleton
instead of the names and fills them.

Open the Quick Rigging Tool, switch it to four-legged, *then* run the command.
The panel keeps whichever document it was showing, so a humanoid setting
silently ignores a quadruped template.

Save what it found as a **preset** and every character boned that way is one
click from then on. Presets that ship: Unreal/Fortnite and Cascadeur's own
sabertooth naming. Your own go to `Documents\Cascadeur quadruped presets`.

**ARDY Live** — motion generation built up as a list of takes: "walk" for 120
frames, then "run" for 80, generated as one continuous motion onto the
ARDY.casc sample character. Needs KimodoEngine running (free, separate
download).

**MetaArKit** — an ARKit facial capture, keyed straight onto a character's
blendshapes. Reads Live Link and ARKit CSV as they come. Smoothing is off by
default, so captured values stay exactly as captured.

**Receive Poses (Blender)** — opens 127.0.0.1:9564 and waits. This is the
receiving half of a bridge; the sending half is a Blender add-on, and on its
own this does nothing.

## Requirements

**Cascadeur 2026.2**, Windows. Earlier versions will not run these -
the panel system and the idle hook they rely on arrived in 2026.2.

ARDY Live needs KimodoEngine. MetaArKit and Rig Quadruped need nothing else.

## Not included

Kimodo Roundtrip is not part of this package.

---

Free to download and use. Not open source: please do not redistribute or
republish it. Report anything broken — that is what makes it better.
