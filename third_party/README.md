# Third-Party Plugins

MetaBridge DNA talks to two other programs, and each needs a small plugin on
its own side. Both are here, and both are free to redistribute. Neither is
required — install one only when you want the feature it carries.

The Marvelous Designer plugin is not here; it lives in `md_plugin/` beside this
folder, because MetaBridge DNA writes its settings file directly.

| Folder | For | Feature it enables |
| --- | --- | --- |
| `KimodoCascadeurPlugin` | Cascadeur | **Send to Cascadeur**, and receiving the result back |
| `MotionForgeLiveLink` | Unreal Engine 5.8 | **Unreal Live** and **Follow Unreal** |

---

## Cascadeur

Installed from inside Blender, not from this folder directly: **Edit ▸
Preferences ▸ Add-ons**, find **MetaBridge DNA**, expand it, and click
**Install Cascadeur Plugin**.

It offers `C:\Program Files\Cascadeur`; type a different path if Cascadeur is
somewhere else. It then asks for a **KimodoEngine folder** — **leave that
blank.** It is for a separate motion-generation product, and MetaBridge DNA
does not use it.

Cascadeur's folder normally needs Administrator rights to write into; accept
the Windows prompt if one appears. Nothing here elevates Blender itself, only
the one copy step.

Restart Cascadeur afterwards. A new entry appears under **Animation Scripts ▸
Receive Poses (Blender)**. Run it once per session — it opens the bridge on
port **9564** and has to be running before Blender sends anything.

To install by hand instead, copy the loose `.py` files from
`KimodoCascadeurPlugin` into
`<Cascadeur>\resources\scripts\python\commands\animation_scripts\` and the
`models` folder into `<Cascadeur>\resources\scripts\python\models\`.

The folder carries more than MetaBridge DNA needs — a quadruped auto-rigger
and a facial capture tool come with it. They do no harm; ignore them, or use
them, as you like.

---

## Unreal Engine

**Edit ▸ Preferences ▸ Add-ons ▸ MetaBridge DNA** also has an **Open Unreal
Plugin Folder** button that jumps straight here. Copy the
**`MotionForgeLiveLink`** folder into your project's `Plugins` folder, so the
layout ends up as:

```
<YourProject>\Plugins\MotionForgeLiveLink\MotionForgeLiveLink.uplugin
```

Create the `Plugins` folder if the project does not have one. Restart the
editor; Unreal builds the plugin on the way in, so a C++ project (or the build
tools installed) is needed the first time.

Enable **Live Link** as well — this plugin extends it rather than replacing it.

### One plugin, two ports

The same plugin serves both directions, and the port decides which:

| Port | Direction | MetaBridge DNA panel |
| --- | --- | --- |
| **9561** | Blender → Unreal | **Unreal Live** — a MetaHuman's face and body |
| **9562** | Unreal → Blender | **Follow Unreal** — the pose of the MetaHuman in Unreal |

For 9561, add a **MotionForge** source in Live Link at `127.0.0.1:9561` and put
a **Live Link Pose** node in the character's Anim Blueprint.

For 9562, run `MotionForge.Send.Start` in Unreal's console with the MetaHuman
selected, and `MotionForge.Send.Stop` when finished.

`guide.md` inside the folder covers both in full, along with port **9560**,
which the separate MotionForge add-on uses for body motion.
