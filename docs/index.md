# MetaBridge DNA — User Guide

<div align="center">
  <iframe width="640" height="360" src="https://www.youtube.com/embed/4FGSyQCPH8Q" title="Blender metabridge_dna addon" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>


## What's New

**v2.1.0 — Cascadeur both ways, Unreal both ways, Undo**

*Unreal (NEW)*

- **NEW: Unreal Live** — a MetaHuman face animated in Blender performs on the
  MetaHuman in Unreal as you work on it, with nothing exported. See
  [section 13](#13-unreal-engine).
- **NEW: Follow Unreal** — the other direction. Whatever is moving the
  character in Unreal, a Control Rig in a sequence or a baked animation, drives
  this character here. Body, face, or both.
- **One plugin on the Unreal side, told apart by port.** 9560 for MotionForge
  body motion, 9561 for Unreal Live, 9562 for Follow Unreal. A face stream and
  a body stream can run at the same time as long as the ports differ.

*Send to Cascadeur (NEW)*

- **NEW: Send to Cascadeur** — its own panel in the sidebar. Put this character into Cascadeur and animate it there, with no FBX to export by hand. See [section 12](#12-send-to-cascadeur).
- **Send Character** hands over the rig, the meshes and whatever animation is on them. Head and body arrive as one character, so the face stays on the body when you move it.
- **Keyframes Only** sends a new pose or animation onto the character already there. Nothing is created in Cascadeur; it simply takes the motion.
- **Face Bones** is off by default. The face rides the head joint and only the body skeleton goes over — a quarter of the character, and all Cascadeur needs to animate a body.
- **Current Frame** sends just the pose you are looking at. **Append** adds after what Cascadeur already has.
- The panel says which tab the motion will land on before you press anything, and **Open sample character** brings up a rigged character when the scene is empty.
- **NEW: Receive from Cascadeur** — the bridge works both ways. Animate over
  there and bring it back onto the same character in the same scene.
  **Animation Only** keys onto the rig you already have; **Mesh + Animation**
  brings the character back as new objects. **Onto Rigify Controls** puts it on
  the control rig so it can be adjusted and layered.
- Reading a full MetaHuman take takes under a second, and root motion comes
  with it.

*Correctives (NEW)*

- **NEW: Bake to DNA** — a correction you sculpted can be written into the
  character's `.dna`, so it belongs to the character everywhere instead of only
  in this scene. **Bake Corrective to DNA** for one, **Bake All to DNA** for
  every one on the character.
- **NEW: Export Face CSV** — write the face's shape values over the frame range
  to a spreadsheet file, for taking a performance to another program.

*Undo (NEW)*

- **Ctrl+Z now works on the big steps.** Assemble, New, Delete Slot, Load Head/Body DNA, Build Meta-Rig, Generate Rigify Rig, Apply Retarget, Link/Unlink Head Rig, Remove Rigify Rig and Reload Materials can all be undone and redone like anything else in Blender.
- The face rig follows the undo. Undo past an Assemble and it switches off with the character; redo and it comes back on.
- Things that cannot be undone are deliberately left out: saving a `.dna`, saving material defaults, connecting ARKit Live. Undo cannot unwrite a file or close a connection, so those stay one-way.

*Body Blend — both libraries at the same time*

- **The standard bodies and the child bodies can now be loaded together.** Load `MH_All_Body.json`, then load `MH_Boy.json`, and both sets stay in the list — 39 rows to blend from instead of whichever you loaded last.
- Loading the same library again still just refreshes its own rows, so nothing doubles up.
- If you load a library built from a different skeleton, it now says so straight away instead of failing later at Build.

*ARKit Live — the Smoothing slider was backwards*

- **Smoothing now does what it says.** It was inverted: turning it down to 0 — the setting described as the raw, immediate one — froze the face completely instead. Turn it down for a raw, snappy feed and up for a smoother, slightly laggier one, as the label always claimed.
- If you had settled on a Smoothing value that felt right, try it again — the same number now behaves the opposite way. **0.5 is unchanged**, so anyone on the default sees no difference.

*Loading and saving a `.dna` tells you the truth*

- **Picking the wrong file now says so.** A PNG, a JSON or anything else that is not a DNA used to load "successfully" and leave you with a character that had no bones and no meshes. It is now refused with a message naming what is actually wrong with the file.
- **A failed save no longer reports success.** Saving to a folder that does not exist used to say "Saved" with no file written anywhere.
- **A failed load leaves the character you already had alone.** It used to switch the face rig off and leave it off.

*Smoother viewport*

- Characters with **Apply Retarget** done are lighter to work around. The body correctives were being recalculated on every viewport change — turning the camera, picking something, moving a face control — even when the body had not moved. Now that work only happens when a body bone actually moves.

*Load Live Link Face CSV — a recording now loads all the way through*

- **A CSV no longer stops partway with `could not make path to "value"`.** Bringing a recording in creates a slider for every shape at once, and each one it added left the ones before it unusable — so a file failed on its second shape and nothing was keyed. Live capture never hit this: it makes its sliders in the first tick and adds none afterwards. Recorded files now load whole.
- **The playhead goes back where it was.** A CSV whose columns did not match left the scene parked at the end of the recording, on top of reporting nothing matched.

*Plug-ins for the other programs now come with the addon*

- **The Cascadeur and Unreal plug-ins ship inside the addon**, in a `third_party` folder, alongside the Marvelous Designer one. Nothing to download and no separate product to install — [Installing](#installing) says where they are, and each section sets up its own.

*Smaller fixes*

- The **LOD** row now says when the level you picked carries no facial expressions. MetaHuman heads keep their expressions at LOD 0 only; above that the face moves on its joints alone, which used to look like the face rig having stopped working.
- **Import FBX Animation** now warns when the control rig is still driving the bones it just keyed. The warning existed but never appeared in the one case it was written for.
- In the DNA inspector's **Bone View**, the **Next** button stopped responding a few presses before the end of the list.
- Switching the add-on off now stops everything it started. Two background evaluations kept running with it disabled.

*For anyone who edits meshes and writes them back to `.dna`*

- Editing an **eye** mesh and exporting with **Include Mesh Edits** could quietly write those vertices into a different LOD of the same eye, leaving the one you edited unchanged. Jaw, teeth, tongue and the head itself were never affected. Fixed.

## What is this addon?

MetaBridge DNA lets you bring Epic Games **MetaHuman** characters into Blender, pose their faces in real time, and export them back out.

<div align="center"><iframe width="640" height="360" src="https://www.youtube.com/embed/rnNuLmuO7JE" title="Load MetaHuman DNA to Instant ARKit Controllers (No Shape Keys!)" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>

With it you can:

- Load a MetaHuman character (head + body) into Blender
- Move sliders or bones to make facial expressions — no shape key editing needed
- Save your favorite expressions as reusable presets, and blend several at once
- Drive the face **live from an iPhone** using Apple's Live Link Face app
- Build an animatable body rig (Rigify) for the character
- Blend multiple bodies together, and dress the result in clothing and hair
- Export everything back to DNA, FBX, or glTF

Everything is in one place: open the **N panel** on the right side of the 3D Viewport, and look for the **MetaBridge DNA** tab.

## Installing

MetaBridge DNA is a Blender Extension. Either:

- drag the `metabridge_dna-*.zip` into the Blender window, or
- **Edit ▸ Preferences ▸ Add-ons ▸ Install from Disk**, and pick the `.zip`.

Blender needs **4.5 or newer**, and Windows 64-bit.

Updating and removing are done from **Edit ▸ Preferences ▸ Add-ons**, the same as any other extension.

If you were using an earlier version installed the old way, remove it first — Blender will otherwise load both and the panels appear twice.

![metabridge_dna01.png](assets/metabridge_dna01.png)

### Plug-ins for the other programs

Three features reach into a program outside Blender, and each needs a small plug-in on that side. **They all come with this addon** — nothing to download.

| Program | Where it is | Needed for |
| --- | --- | --- |
| Marvelous Designer | the `md_plugin` folder | **MD Live** (§11) |
| Cascadeur | `third_party/KimodoCascadeurPlugin_free.zip` | **Send to Cascadeur** (§12) |
| Unreal Engine | `third_party/MotionForgeLiveLink_UE5.8.zip` | **Unreal Live**, **Follow Unreal** (§13) |

Install none of them to start with. Each section below sets up its own when you get there, and a feature you never use costs you nothing.

The `third_party` folder sits inside the installed addon:

```
%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\metabridge_dna\third_party
```

Replace `<version>` with the Blender you installed it into — `4.5`, `5.0` and so on. Paste the result into the address bar of a File Explorer window.

If you would rather not guess the version, Blender will tell you: **Edit ▸ Preferences ▸ Add-ons**, find **MetaBridge DNA**, and click the arrow to expand it. The **File** row shows the full path — `third_party` is beside the file it names.

Turning on **Preferences ▸ Interface ▸ Developer Extras** adds a small folder button to that same row, which opens the addon's folder for you.

The folder's own `README.md` repeats the steps below. Marvelous Designer is the exception — its **Open MD Plug-in Folder** button takes you straight there.

---

## 1. Loading a Character

**Steps:**

1. Click the folder icon and pick the folder that contains your MetaHuman characters.
2. Click a character's thumbnail to select it.
3. Turn Head / Body / Textures on or off, depending on what you want to load.
4. Pick a **LOD** level (0 = highest quality, higher numbers = lighter/faster).
5. Click **Assemble**.

![metabridge_img01.gif](assets/metabridge_img01.gif)

**Good to know:**

- You can load more than one character — click **New** to add another one as a separate slot.
- The list at the bottom shows every character currently in your scene. Click the radio button next to one to make it "active".
- The trash icon removes a character from the scene.
- If you want to load a different LOD later, change the LOD number and click **Re-Assemble**.
- **LOD and facial expressions**: a MetaHuman head carries its expressions at **LOD 0 only**. Above that the face still moves — the jaw opens, the eyes turn, anything driven by a bone works — but the shape-based detail is not there, because the character does not contain it at that level. The panel says `LOD n: joints only` when that is the case. Use LOD 0 for face work; the higher levels are for a lighter scene when you are animating the body.
- Need to load one specific `.dna` file? Use the **Load Head DNA...** / **Load Body DNA...** buttons next to Assemble.
- **Material defaults**: if a `material_defaults.json` file is present in the addon folder, its BSDF values are applied automatically to newly created materials on every Assemble. Existing (already-created) materials are never overwritten, so your edits are preserved across Re-Assembles.
- All meshes are automatically set to **Smooth Shading** on Assemble.

---

## 2. Making Facial Expressions (Face Rig)

**Steps:**

1. Click **Append GUIArmature** — this adds the control rig you'll use to make expressions.
2. Turn **Face Rig: ON**.
3. Select the GUIArmature in the viewport, go into **Pose Mode**, and move its bones. The face updates live as you move them.

![metabridge_img02.gif](assets/metabridge_img02.gif)

**Good to know:**

- You're never editing shape keys directly — you're only moving control bones.
- If you don't see any reaction when moving a bone, double check Face Rig is switched ON.

---

## 3. Expression Presets (save & reuse expressions)

Instead of posing a face from scratch every time, save an expression once and reuse it — and mix several expressions together.

**Saving a preset:**

1. Pose the face the way you want it.
2. Click **Save As Current Expression...** and give it a name.
3. To update a preset you already saved, select it in the list and click **Save Current Expression**.

**Using a preset:**

1. Pick a preset from the dropdown.
2. Click **Apply Preset** — it appears in the **Active Sliders** list just below, already turned on.
3. Drag its slider between 0 (no expression) and 1 (full expression).

**Blending multiple expressions:**

- You can have many sliders active at once — they combine automatically.
- **Add All From Active Folder** loads every preset in your current folder as a slider, all starting at 0.
- The **X** button removes one slider; **Clear All Sliders** resets everything back to neutral.
- Sliders are normal Blender properties, so you can keyframe and animate them.

![metabridge_img04.gif](assets/metabridge_img04.gif)

**Good to know:**

- **Set Folder...** lets you choose where presets are saved/loaded from.
- **Import...** lets you bring in a preset file from anywhere on your computer.

**Converting presets from other programs:**

- **Convert & Import (Maya/Houdini)...**: brings in a saved pose from Maya or Houdini and matches its bone names automatically.
- **Convert ARKit Payload...**: a one-time setup step that generates the 52 `ARKit_...` presets used by ARKit Live.

---

## 4. ARKit Live (real-time face tracking from your iPhone)

Stream your real facial expressions live from an iPhone straight onto the MetaHuman character, using Apple's free **Live Link Face** app.

**Setup:**

1. Make sure your iPhone and your computer are on the same Wi-Fi network.
2. In the Live Link Face app, use normal streaming mode (**not** "MetaHuman Animator" mode).
3. In the app, set the target IP address to your computer's address, and the port to **11111**.
4. In Blender's ARKit Live panel, leave **Host** as `0.0.0.0` and **Port** as `11111`, then click **Connect**.

![metabridge_img05.gif](assets/metabridge_img05.gif)

**Tuning the feel of the tracking:**

| Setting | What it does |
|---|---|
| **Smoothing** | Makes movement smoother and less jittery. Higher = smoother but slightly slower to react. |
| **Deadzone** | Ignores small, noisy values so the face doesn't drift or twitch at rest. |
| **Gain** | Boosts expressions that don't reach full strength. |

**Recording:**

- Click **Record** to save the live performance as keyframes on the timeline. Click **Stop Recording** when done.
- Or use **Load Live Link Face CSV...** to bake in a pre-recorded CSV file.

**Head Rotation (Experimental):**

- Requires the body's **Rigify** rig to be set up first, with **Apply Retarget** and **Link Head Rig** both done.
- If the head turns the wrong way on some axis, use the **Invert Pitch / Yaw / Roll** buttons.

**Troubleshooting:**

- **Nothing moves at all**: check for a red **Apply error** message and make sure the correct character is Activated.
- **Face looks slightly off at rest**: use the **Calibrate** feature in the Live Link Face app first, then fine-tune with Deadzone/Gain.

---

## 5. Rigify Body Control Rig

Turns the MetaHuman body into a fully animatable rig using Rigify.

Requires the **Rigify** addon to be enabled first (`Edit > Preferences > Add-ons`, search for "Rigify").

**Steps, in order:**

1. **Build Meta-Rig** — creates a draft skeleton matching the body.
2. **Generate Rigify Rig** — turns the draft into a real, posable control rig.
3. **Apply Retarget** — connects the control rig so it drives the MetaHuman body. Body correctives are registered at this step.
   > ⚠️ If the draft skeleton from step 1 wasn't positioned correctly, this can distort the mesh. Check that everything looks right after step 2, before applying.
4. **Link Head Rig** — connects the head so it moves with the body.
5. **Remove Rigify Rig** removes everything from steps 1–4 if you need to start over.

**Additional Options**
![Rigify_IK.gif](assets/Rigify_IK.gif)

A collapsed section below **Remove Rigify Rig**, holding two switches you rarely need to touch:

- **IK Stretch ON/OFF** — off by default, so limbs stay rigid. Turn it on if you want the arms and legs to stretch when you pull the IK controls past full reach.
- **Heel Pivot ON/OFF** — off by default. On, rotating the foot spin control pivots the foot around the heel; this also makes the foot drift away from its controller as you rotate it upward, so leave it off unless you specifically want heel pivoting.
- **Finger IK ON/OFF** — off by default. See below.

**Finger IK**

Normally each finger joint has to be rotated one at a time. With Finger IK on, each finger gets a target at its fingertip — drag the target and the whole finger follows. Much faster for gripping a prop, planting a hand on a surface, or shaping a pose.

Rigify has no finger IK of its own, so this is added by this addon. All ten fingers are covered, thumbs included.

1. Turn on **Finger IK** in **Additional Options**. Ten small box controls appear at the fingertips.
2. In **Pose Mode**, drag a fingertip control. That finger bends to reach it, and no other finger moves.
3. Turn it off to go back to rotating the joints by hand.

**Per-finger sliders**

Under the button there is a slider for each of the ten fingers: **0** poses that finger by rotating its joints, **1** makes it follow its fingertip target. The ON/OFF button just sets all ten at once.

This is what makes the feature useful for real hand animation:

- **Holding a prop** — put the fingers touching the object on 1 so they stay planted while the wrist moves, and leave the fingers in the air on 0 where hand-posed arcs look better. The thumb usually wants its own setting.
- **Easing into a contact** — a value in between blends the two. Keyframe a finger from 0 to 1 over a few frames as the hand lands on a surface and it settles into place instead of popping.
- **Backing off one bad finger** — if one finger bends oddly, drop just that slider instead of turning the whole hand back to FK.

**Switching without losing the pose — IK to FK / FK to IK**

The two sliders hold two separate poses, so moving a slider swaps between them rather than carrying one across. These two buttons carry it across:

- **IK to FK** — keeps the pose you built with the fingertip targets, hands it to the joint controls, and switches all ten fingers to 0. The fingers do not move. Use this once you're happy with an IK pose and want to keep refining it joint by joint, or before keyframing in FK.
- **FK to IK** — keeps the pose you built by hand, moves the fingertip targets onto it, and switches all ten fingers to 1. Again nothing moves. Use this when a hand you posed by hand now needs to hold onto something.

Both work on all ten fingers at once, and both are safe to press repeatedly.

**Good to know:**

- Switching it on keeps the fingers exactly where they already were — nothing jumps.
- Switching it off leaves the pose exactly as it was too, so you can move back and forth freely.
- The fingertip targets follow the hand, so posing the arm keeps the finger pose intact.
- **Snap Fingertip Targets to Pose** moves all ten targets onto wherever the fingers are right now, without changing the pose. You need it when a slider sits between 0 and 1 — the finger is then somewhere between its two results and no longer touching its target — or after loading an animation.
- Lowering a slider by hand does **not** keep the IK pose. The joint controls still hold whatever they held before, so the finger springs back to that. Use **IK to FK** instead — see below.
- There is no elbow-style direction control for fingers, so the solver picks which way a finger bends. It follows the joints sensibly for normal poses, but pulling a target far sideways can twist the finger oddly. Lower that finger's slider if it does.
- With Finger IK off, the rig behaves exactly like stock Rigify — the finger master curl and the individual joint controls work as usual.

![metabridge_img03.gif](assets/metabridge_img03.gif)

**Body Correctives — automatic muscle & twist detail**

Once Apply Retarget is done, the body rig automatically adds secondary deformation (shoulder blade, muscle bulge, limb twist) using data built into the character's DNA. No setup needed.

- **Body Correctives RBF: ON/OFF** — toggles the RBF solver layer. Leave it **ON** for the most realistic result. Basic twist/muscle correction stays active either way.
- If a character's DNA doesn't include this data, the button shows **"none in this DNA"** and is grayed out.

**Fine-tuning by hand (RBF Controllers)**

For spots that need a manual touch-up beyond the automatic result:

1. Pick the joint you want from the **Driver Bone** list, or leave it on **Auto** and select a control in **Pose Mode** (e.g. `shoulder.L`).
2. Click **Show RBF Controls** — small diamond-shaped helper bones appear for that area.

> Use the **Driver Bone** list for the knee. Its correctives belong to `calf_l` / `calf_r`, and while a leg is on IK there is no control you can select that points at those, so **Auto** finds nothing there.
3. Adjust the **influence slider** (0–1) per bone in the **Active RBF Controllers** list:
   - `0` = automatic corrective **off** (bone stays at rest/neutral)
   - `1` = automatic corrective **fully applied** (default)
4. **Rotate** a helper bone by hand to add an extra manual correction on top of the automatic result.
5. Click **Hide** when done to tidy the viewport.

> Rotating a helper bone at `influence = 1` stacks your manual rotation on top of the full automatic result. At `influence = 0` only your manual rotation is used.

**Import FBX Animation (Beta)**

Apply a MetaHuman animation exported from Unreal (FBX) straight onto this character — body and head animate together, automatically, even if the character's proportions don't exactly match the source animation.

1. Click **Import FBX Animation...** and pick the `.fbx` file.
2. Both the body and head are keyframed with the retargeted animation.

The button is greyed out while the control rig is connected to this character, because the rig would overwrite the imported animation every frame. Click **Remove Retarget** (and **Unlink Head Rig**) above, then import. Hover the greyed-out button to see this reminder.

**Retarget Rigify Animation (Beta)**

Copy an animation from another already-animated character onto this character's control rig. Use this when the animation lives on a rig rather than in an FBX file.

1. Open the **Retarget Rigify Animation (Beta)** panel.
2. **Source Rig** — the animated armature to copy from.
3. **Source Type** — which kind of rig that is:

   | Source Type | Use it for |
   |---|---|
   | **UE5 Mannequin** | Unreal's own mannequin |
   | **Fortnite** | Fortnite characters (same bone names as UE5) |
   | **MetaHuman** | another MetaHuman (same bone names as UE5) |
   | **Mixamo** | anything downloaded from Mixamo |
   | **Blender Rigify** | a rig made with Blender's own Rigify |

4. **Target Rig** — this character's Rigify control rig.
5. Click **Retarget**.

The animation is baked onto the target's controls, corrected for the two characters having different proportions and different rest poses.

**About Blender Rigify as a source:**

This addon's rig is *not* identical to a stock Rigify rig — its spine has six segments where Blender's has four — so an animation cannot simply be copied across. Picking **Blender Rigify** maps the two properly.

It works whether that animation was made with **IK or FK** arms and legs. You do not need to convert or bake the source rig first.

**Good to know:**

- Once Apply Retarget and Link Head Rig are set up, the connection is saved with your file — reopening it works without re-clicking Apply Retarget.
- The Rigify shoulder bone (`shoulder.L/R`) must be manually elevated when raising the arm. Key the shoulder bone alongside the arm for the most natural shoulder deformation.

---

## 6. Body Blend (experimental)
![Body_blend.gif](assets/Body_blend.gif)

Combine two or more MetaHuman body types — and their matching heads — into a brand-new blended character. Found in its own **Body Blend (experimental)** panel, collapsed by default.

**Adding sources:**
- **Use Base DNA** — adds the addon's own reference character from the `base_dna/` folder.
- **Add Folder...** — adds every character in a folder at once. **This is how you build a library.** See below.
- **Add Body DNA** — add one specific `.dna` file by hand.
- **Load Library...** — load a compact archetype library and add every archetype in it as a source.

**Add Folder... — building a library**
![Body_blend02.gif](assets/Body_blend02.gif)
Point this at a folder holding **the original `.dna` files of several characters**, with each character's head and body sitting side by side:

```
MyBodies\
   Boy01_body.dna    Boy01_head.dna
   Boy02_body.dna    Boy02_head.dna
   Boy03_body.dna    Boy03_head.dna
   ...
```

Every character in that folder is added in one click, and each body is paired with its own head automatically. That folder is now your library — collect the characters you blend with into one place and you can load them all whenever you start a new blend.

**Important:**

- Both files must be in the **same folder**, named so they match (`Name_body.dna` and `Name_head.dna`). A body with no matching head is still added, but it can only contribute a body shape.
- Only the folder you pick is read — characters in **sub-folders are not** included. Point it at the folder that directly holds the `.dna` files.
- The addon's own `base_dna/` folder holds a single reference character, so picking it adds only that one. That is expected — use **Use Base DNA** for it instead.

Weights don't need to add up to anything in particular — they're normalized automatically. **Use Base DNA** starts at `1.0`; all other sources start at `0.0`.

**The primary row:**

The **highlighted row** is the primary source — it supplies the topology, skin weights and face rig. Every other row just contributes its shape. If you only add library entries (no real `.dna` row), the addon quietly uses its own reference character as the primary behind the scenes, so you can build purely from a library.

**Building:**

1. Add and weight your sources.
2. Click a row to make it the primary.
3. Pick a **LOD** level.
4. Give it a **Name**.
5. Click **Build Blended Body**.

**Replace:**

Turn on **Replace** to overwrite your last Body Blend character in place instead of adding a new slot every time.

**Live Preview:**

After a Build, dragging any weight slider re-blends and updates the character already on screen. Turn Live Preview off if it slows things down.

**Good to know:**

- The head only blends if every weighted row has head data. If one is missing, the body still blends but the head is skipped and a note explains why.
- **Textures**: after building, the addon looks for a `Maps` folder next to the primary DNA, then falls back to `base_dna/Maps`.
- Shape keys on the blended head are copied from the primary head source only.
- Posing/expressions work normally on a blended character, and stay correct even after you go back and adjust the weight sliders.

**The `base_dna/` folder:**

Put your own reference `Body.dna` and matching `Head.dna` here (`metabridge_dna/base_dna/`). This is what **Use Base DNA** adds, and what Build falls back to when nothing else is weighted.

**Compact archetype libraries:**

Two libraries ship with the addon, both in the `base_dna/` folder:

| File | What is in it |
|---|---|
| `MH_All_Body.json` | The **28 standard** MetaHuman body types, each with matching head data |
| `MH_Boy.json` | **10 custom child bodies**, for smaller/younger proportions |

- **Load Library...** — loads a library, one row per archetype. The file browser opens on `MH_All_Body.json`; pick `MH_Boy.json` from the same folder for the child bodies.
- **Both can be loaded at once.** Load one, then load the other, and all 38 stay in the list — so an adult body type and a child body type can go into the same blend. Loading the same library a second time just refreshes its own rows; nothing doubles up.
- Your own `.dna` rows are never touched by either.
- **Export...** — packs exactly the sources currently listed in the panel into one compact `.json` library. If the list is empty, it instead scans a folder you pick (including subfolders). You don't need to keep the original `.dna` files around once you have a library.
- A library built from a different skeleton cannot be mixed with one already loaded — the addon says so when you try, rather than letting it fail at Build.

---

## 7. Wearables (experimental)

**Beta** — weights can still look off during animation/posing in some cases. Being actively improved; touch up in Weight Paint mode if needed.

Attach clothing (FBX) and hair/grooms (Alembic `.abc`) to the *active* character — found in its own **Wearables (experimental)** panel, collapsed by default. Works on any assembled or Body-Blend-built character.

There are two ways to dress a character: import a **clothing FBX** built for a MetaHuman skeleton, or **rig any mesh already in your scene** yourself. Both end up following the character the same way afterward.

**Clothing (FBX):**
![cloth_FBX.gif](assets/cloth_FBX.gif)
- **Top... / Bottom... / Full...** — import a MetaHuman-compatible clothing `.fbx` and attach it to the body, tagged with that category.
- **Head Accessory...** — same idea, for things that attach to the head instead (glasses, earrings, ...).
- **Retarget To Body Proportions** (on by default): fits the garment to this character's own proportions instead of the body it was originally made for — without going skin-tight, so a loose shirt stays loose.
- Clothing automatically avoids clipping into the character's skin.
- **Clothing Offset** slider — floats all worn clothing slightly off the skin, if you want extra breathing room. Updates live.
- **Categories replace what they conflict with**: a new Top clears any worn Top/Full; a new Bottom clears Bottom/Full; a new Full clears both. Head accessories never auto-remove anything.
- **LOD0 only**: if the FBX bundles multiple LODs, only LOD0 is kept.

**Scene Mesh Garment (Make + Bind):**
![scene_garment.gif](assets/scene_garment.gif)
For a mesh already in your scene that doesn't have a MetaHuman skeleton of its own.

1. Select the garment mesh and click **Make Top / Bottom / Full / Shoes / Gloves / Head Acc** — this fits it to the character and rigs it to move with the character's skeleton. Works best on a garment already modeled to roughly fit the character.
2. Click **Bind Garment To Character** — attaches it to the active character, exactly like an imported clothing FBX from here on (category replacement, Body Blend live follow, Refit, Clothing Offset all apply).

If deformation looks off in an extreme pose at a tight spot (armpits, between the thighs), touch it up in Weight Paint mode — everything else is unaffected.

**Hair (Alembic):**

- **Import Hair...** — imports a `.abc` groom and parents it to the head. Defaults are tuned for MetaHuman groom exports (**Scale 0.01**, **Rotation X -90°, Z -180°**) — adjust in the operator panel (bottom-left after import) if your source is different.
- **Bind To Head Surface** (on by default) — hair follows the head as it deforms, including through Body Blend changes, without collapsing onto the scalp.
- **Bind Hair To Head** — for hair that came from somewhere else: a groom already in your scene, a beard that came with the character, or anything imported outside this addon. Select it and click. It then follows the head exactly like hair imported here, Body Blend included. Hair already attached is simply re-attached to where the head is now.
- If hair sits still while the character's shape changes, the reason is written to the console — usually that it was never bound. Select it and use **Bind Hair To Head**.

**Good to know:**

- Clothing FBX placement depends on the file sharing bone names with a MetaHuman skeleton.
- Imported/rigged wearables aren't tracked as part of the character slot the way body/head meshes are — rename, move, or export them like any other Blender object.

---

## 8. Live Corrective Sculpting (Beta)
![Live_corrective.gif](assets/Live_corrective.gif)
**Beta** — a correction sculpted with only one pose holds steady if you pose further than that; sculpt more than one pose for the same correction if you want it to keep changing shape further into the pose. Head corrections can be written back into the character's `.dna` and used in Unreal — see **Sending a correction to Unreal** below. Body corrections stay inside Blender.

Pose the character, then sculpt directly on top of that pose — the sculpt becomes a correction that fades in and out automatically from then on, every time the character moves toward and away from that pose. No keyframing needed. Works on both the face and the body, and automatically carries over to any clothing worn on the character.

**Steps:**

1. Open the **Live Corrective Sculpting (Beta)** panel.
2. Pose the character the way you want to fix or add detail to (a bent elbow, a stretched shoulder, an expression...).
3. Type a name for the correction in the **Corrective** field.
4. For a body correction, also pick which bone should trigger it from the **Body Driver Bone** list.
5. For a face correction, you can also pick a **Head Driver Bone**. Do this when the character has a custom head that breaks as the controls move — the correction then follows that bone as well as the expression.
6. Click **Begin (Face)** or **Begin (Body)** — this enters Sculpt Mode on a fresh shape key, already at full strength.
7. Sculpt the correction.
8. Click **Finish Sculpt**.

**If a correction doesn't fade all the way out:**

Return the character to its rest position and click **Set Neutral** on that correction. It then reads 0 at rest. A custom head often needs this.

**Editing an existing correction:**

Click the sculpt icon next to a correction's slider to re-enter Sculpt Mode on it directly and refine it further. Pose the character close to where it was originally sculpted first, for the most accurate result — this doesn't return the character to that pose for you automatically.

**Manual mode:**

Click the tool icon next to a correction to switch it to **Manual** — its slider can then be dragged by hand instead of following the pose. Useful for previewing a correction at any strength, or hand-animating it. Click it again to go back to automatic.

**Clothing:**

A correction sculpted on the skin automatically carries over to any clothing worn on that character. This happens on its own whenever you finish a sculpt or import one — click **Sync to Wearables** if you add new clothing afterward and want it to catch up. Each garment gets its own copy of the correction, with the same Manual/slider/edit controls as the skin's, listed right underneath it.

**Sharing corrections:**

- **Export...** saves every correction on a character to a `.json` file.
- **Import...** brings corrections from a file onto another character. It only works if that character has the same body/head as the one the file was exported from (built by this addon at the same LOD) — importing onto a mismatched character is rejected rather than corrupting the mesh.

**Sending a correction to Unreal (head only):**

Use the **Write to DNA (head only)** box. It writes a new `.dna` file and leaves the original untouched. There is no equivalent for the body — a MetaHuman body has no expression shapes to write into, so body corrections stay in Blender.

There are two ways to do it.

### Fixing an expression that breaks — Export Edited Shape Keys
![export_shapekey.gif](assets/export_shapekey.gif)
This is the one to use when a face folds, spikes or collapses on a particular expression. You fix the character's own expression by hand and send that fix back into the `.dna`.

1. **Make the expression with the face controls.** Move the controls until the problem is on screen — for example open the jaw until the mesh breaks.

2. **Find the shape key that expression is using.** With the head mesh selected, look at its shape key list: the ones the controls are driving are the ones whose **value is above 0**. Opening the jaw, for instance, puts a jaw shape key at **1.0**. That is the one to fix.

   > Leave the face controls where they are. The shape key you are about to sculpt is only showing its shape because the controls are holding it there.

3. **Sculpt it.** With that shape key active, enter **Sculpt Mode** and shape the face the way it should look. You are editing the character's own expression, not adding a new one.

4. **Check it with the controls.** Leave Sculpt Mode and move the face controls through the expression again. The fix should follow the controls in and out. Keep sculpting until it does.

5. **Click Export Edited Shape Keys** and save. Every expression you changed goes into the new `.dna`; the ones you didn't touch are left exactly as they were.

**Good to know:**

- You can fix several expressions in one session — pose, sculpt, pose the next, sculpt — and one click sends them all.
- The button refuses to export if you haven't actually changed any of the character's expressions, so it never writes an empty file.
- With more than one character loaded, the **active character** is the one exported — the one with the filled dot next to it in **Assembled Characters**.

### Sending your own corrections

Click the ⇱ button on a correction and choose which expression it should ride along with. **Bake All Correctives** then writes every assigned correction at once. Always use this rather than sending them one at a time.

**In Unreal:** bring the new `.dna` in with **MetaHuman Creator ▸ From DNA**, and choose **Replace** with **Import Whole Rig** turned on. **Mesh Fit** rebuilds the expressions from scratch and will discard your edits.

---

## 9. Exporting

- **DNA**: separate **Head** and **Body** buttons (head and body are always two separate `.dna` files). To send a sculpted correction into the head `.dna` instead, use **Write to DNA** in [section 8](#8-live-corrective-sculpting-beta).
- **FBX / glTF**: **Full / Head / Body** buttons. Choose whether to include the control rig and animation in the export dialog.

**Batch Tools:**

- **Assemble All Characters** — loads every character found in your folder in one go.
- **Export All Slots** — exports every loaded character at once.

---

## 10. Opening a File Someone Else Saved

A `.blend` remembers where each character's `.dna` files were on the computer that saved it. On your machine those files are somewhere else, so the character appears but nothing about it responds.

You'll see this in **MetaHuman Assembler ▸ Assembled Characters** — the character is marked with a warning instead of a checkmark, and shows the file it's looking for:

> ⚠ Head DNA not found:
> `D:\SomeoneElse\MetaHumans\Bob\head.dna`
> **Relink Head DNA...**

Click **Relink Head DNA...** (or **Relink Body DNA...**) and pick the same file on your own machine. The character comes back to life immediately, and the warning disappears. Save the file afterwards so you only do this once.

If you pick the wrong file, nothing is broken — it's refused and the character stays as it was.

**To avoid this when sending a file to someone**, send the `.dna` files along with the `.blend`. They still need to relink once, but they'll have the files to point at.

---

## 11. MD Live (Marvelous Designer)

Make clothes on *this* character in Marvelous Designer, and bring them back already wearing.

MD Live is its own panel in the sidebar, next to **MetaBridge DNA**.

**Set up once**

1. Pick a **Shared Folder** — any empty folder both programs can reach.
2. Click **Open MD Plug-in Folder**.
3. In Marvelous Designer: **Plug-in ▸ Plug-in Manager ▸ Add**, and choose that folder. Two new entries appear in the Plug-in menu.

The folder and every setting are remembered, so this is a one-time step.

**Sending the character**

1. Click **Send Body to MD**.
2. In Marvelous Designer, click the MetaBridge avatar entry in the **Plug-in** menu.

The character appears as the avatar. No import window, no settings to fill in. Change the body in Blender, press **Send Body to MD** again, click the same menu entry again — the avatar is replaced, and you never end up with two.

**Include Head** is on by default — Marvelous Designer refuses an avatar without a head, and hats and collars need it too.

**Bringing the clothes back**

1. In Marvelous Designer, click the MetaBridge garment entry in the **Plug-in** menu.
2. In Blender, click **Import Garment from MD**.

The garment arrives at the right size, is fitted to the character, and follows the rig straight away — the same as any other clothing in [section 7](#7-wearables-experimental). Pick the **Category** so it replaces what it should.

**Skip Stitches & Trims** (on by default) leaves out the topstitch, button and zipper meshes. They carry most of the file's weight and none of it is needed to wear the garment.

**If the import takes a while**

Reading the file is quick even at 600 MB. The wait is the fitting: every vertex of the garment has to be matched to the body so it moves with the character. A garment carrying its topstitches can reach three million vertices, and almost all of them are stitching.

**Hide the topstitches, buttons and zippers in Marvelous Designer before you export.** Hidden objects are left out of the file, and the import goes from about a minute to a few seconds. Nothing is lost — they aren't needed to wear the garment, and they're still in your Marvelous Designer project.

You can also lower **Particle Distance** in Marvelous Designer if the garment is denser than it needs to be.

**Good to know**

- The panel shows the garment waiting to be imported and how big it is. Above 100 MB it warns you.
- **Send Scale** and **Import Scale** are already correct. Only touch them if what arrives is obviously the wrong size; Blender tells you the size it imported in the status bar.
- Marvelous Designer's own **Auto Fit** expects avatars from its library. **Prepare for Auto-Fit** (on by default) asks it to treat this character the same way.

---

## 12. Send to Cascadeur

Put this character into Cascadeur, ready to animate.

**Before the first time**

The Cascadeur plug-in comes with this addon, in the `third_party` folder described under [Installing](#installing).

1. Unzip **`KimodoCascadeurPlugin_free.zip`** anywhere.
2. Right-click **`install_plugin.bat`** ▸ **Run as administrator**. Cascadeur normally lives under `C:\Program Files`, and without that the installer stops with an access error.
3. It offers `C:\Program Files\Cascadeur`. Press Enter to accept, or type the path if Cascadeur is elsewhere.
4. It then asks for a **KimodoEngine folder** — leave it empty and press Enter. That is for a separate product, and nothing here uses it.
5. Restart Cascadeur.

**Animation Scripts ▸ Receive Poses (Blender)** now appears in the menu. The plug-in brings a few extra tools of its own along with it; ignore them.

There are two things you can send, chosen at the top of the panel.

**The first time — Character and Bones**

1. In Cascadeur: **Animation Scripts ▸ Receive Poses (Blender)**.
2. In Blender: open **Send to Cascadeur** in the sidebar and click **Send Character**.

The character opens in a new Cascadeur tab with its rig, its meshes and whatever animation is on it. Head and body arrive as one character, so the face stays on the body when you move it.

**Include Head** is on by default. Turn it off to send the body alone.

**Face Bones** is off by default, and should stay off. On, the face's 843 joints go too. Off, the face rides the head joint and only the body skeleton is sent — a quarter of the character, and all Cascadeur needs to animate a body. Turn it on only if you want to pose the face there.

**Include Animation** is on by default. Turn it off to send the character standing in its rest pose.

**After that — Keyframes Only**

Once the character is in Cascadeur, switch to **Keyframes Only** and click **Send Frame Range** to send a new pose or animation onto it. Nothing is created in Cascadeur; the character already there simply takes the motion.

**Current Frame** sends just the pose you are looking at.

**Append** adds after what Cascadeur already received. Off starts again from frame 0.

**Send the character again after restarting Cascadeur**

Keyframes only land correctly on a character Cascadeur received in that session. If you restart Cascadeur, press **Send Character** once more before sending keyframes. Skip it and the limbs come out turned the wrong way, with nothing reporting an error.

**Good to know**

- The character on screen is the one that goes — whichever slot is active.
- **Cascadeur Status** tells you whether Cascadeur is listening.
- Only change **Port** if Receive Poses was started on a different one.

**Bringing the work back**

Animate in Cascadeur, then press **Receive from Cascadeur**. It comes back onto
the same character, in the same scene, with nothing to import by hand.

**Animation Only** keys onto the character already here. Nothing new is
created.

**Mesh + Animation** brings the character back as new objects instead, for when
the mesh changed over there too.

**Onto Rigify Controls** puts the animation on the control rig rather than the
deform bones, so it can be adjusted, offset and layered like anything you keyed
by hand. The body rig goes back to being driven by the controls, so nothing
fights for the same bone.

**Whole Take** reads every frame Cascadeur holds. Turn it off to read only the
scene's frame range.

Reading a full MetaHuman take takes under a second, and root motion comes with
it — the character travels instead of walking on the spot.

---

## 13. Unreal Engine

![unreal_plugin_panel.jpg](assets/unreal_plugin_panel.jpg)

There is **one plugin** on the Unreal side. Which of Blender's features it is
talking to is decided by the **port**, so the port is the setting to get right.

| Port | Direction | What is using it |
| --- | --- | --- |
| **9560** | Blender → Unreal | **MotionForge** body motion, as a Live Link source |
| **9561** | Blender → Unreal | **Unreal Live** — this character's face and body |
| **9562** | Unreal → Blender | **Follow Unreal** — Unreal's character drives this one |
| **11111** | iPhone → Blender | **ARKit Live**, from the Live Link Face app |

Two of these can run at once — sending the face on 9561 while a body stream
uses 9560 — as long as they are on different ports.

**ARKit Live on 11111 is the exception** — it listens for the iPhone directly and needs no plugin in Unreal at all.

---

### Installing the Unreal plugin

It comes with this addon, in the `third_party` folder described under [Installing](#installing).

1. Unzip **`MotionForgeLiveLink_UE5.8.zip`** into your Unreal project's `Plugins` folder, so you end up with:

```
<YourProject>\Plugins\MotionForgeLiveLink\MotionForgeLiveLink.uplugin
```

Create the `Plugins` folder yourself if the project has none.

2. Restart the editor. Unreal builds the plugin as it opens, so the first launch takes longer than usual and needs a C++ project or the build tools installed.
3. Enable **Live Link** in **Edit ▸ Plugins** — this plugin extends it rather than replacing it.

One plugin covers all three ports. Install it once, whichever direction you are working in.

Its own `guide.md`, inside the zip, goes through the Unreal side in more detail.

---

### Unreal Live — the face performs in Unreal as you work

![unreal_live_panel.jpg](assets/unreal_live_panel.jpg)

A MetaHuman face animated in Blender performs on the MetaHuman in Unreal, live,
with nothing exported.

1. **Port** — leave it at **9561** unless something else has it.
2. **Rate** — frames a second to send. It is sent at a steady rate whether the
   face is moving or not, because Live Link treats a source that goes quiet as
   a source that died.
3. Press **Start Unreal Live**. The panel then says how many controls are ready
   and how many listeners are attached.
4. In Unreal, add a **MotionForge source** in the Live Link window, pointed at
   that port.

**Mirror** settles the handedness difference between Blender and Unreal. Y is
the default and is right for a normal MetaHuman; change it only for a rig built
the other way round.

Press **Stop Unreal Live** to end it. This one cannot be undone with Ctrl+Z —
use the panel's own Stop.

---

### Follow Unreal — the character here copies the one in Unreal

![follow_unreal_panel.jpg](assets/follow_unreal_panel.jpg)

The mirror of Unreal Live. Whatever is moving the character in Unreal — a
Control Rig in a sequence, a baked animation — arrives here and drives this
character.

1. **Host** and **Port** — `127.0.0.1` and **9562** for Unreal on the same
   machine.
2. **Apply Rate** — how many times a second the pose is applied here.
3. **Body** and **Face** — follow one, the other, or both.
4. Press **Follow Unreal**, then run **MotionForge.Send.Start** in Unreal.

While following, the panel shows the skeleton's name, its bone and curve counts
and how many frames have arrived.

**Rigify is stood down while following.** Its constraints exist to drive this
character, and the pose is now arriving from somewhere else. They come back
exactly as they were when you press **Stop Following**.

---

## 14. Other Useful Tools

![other_tools_panels.jpg](assets/other_tools_panels.jpg)

- **DNA RC Inspector**: shows how the control bones are connected to the character's DNA data. Mainly for troubleshooting a specific control.
- **DNA Validation**: **Validate DNA File** checks a `.dna` on disk before you
  use it; **Validate Active Slot** checks the character already loaded.
- **Pose Reset**: **Reset Face Pose** puts the whole face back to neutral.
  **Reset Selected Controls** does only the controls you have selected.
- **Animation Baker**: **Bake Face Animation** turns a live or keyframed facial
  performance into permanent, exportable keys. **Clear Baked Animation**
  removes them again.
- **Export Face CSV**: writes the face's shape values over the frame range to a
  spreadsheet file, one file per mesh. Useful for taking a performance to
  another program.

**Batch Tools** — for a folder of characters rather than one.

- **Assemble All Characters** builds every character in the scanned folder,
  each into its own slot. On a large folder this takes a long time.
- **Export All Slots** writes every assembled slot out to a folder, as FBX or
  glTF.

**External Preset Converter** — for expression presets that came from
somewhere else.

- **Convert & Import (Maya/Houdini)...** takes a preset JSON from Maya or
  Houdini and renames its bones to the ones this add-on uses. Anything it
  cannot match is reported rather than dropped silently.
- **Convert ARKit Payload...** turns an ARKit remap payload into a board-pose
  preset.
- **Edit Name Mapping** is where you fix a name it could not match by hand.

---

## Bake to DNA

A correction you sculpted lives in the scene. **Bake to DNA** writes it into the
character's `.dna` file instead, so it belongs to the character from then on —
in a new scene, on another machine, or in Unreal.

**Bake Corrective to DNA** does one correction. **Bake All to DNA** does every
correction on the character at once.

The original `.dna` is not overwritten; a new file is written and you choose
where.

---

## Undo

**Ctrl+Z** works on the steps that build or remove things:

Assemble · New · Delete Slot · Load Head DNA · Load Body DNA · Build Meta-Rig · Generate Rigify Rig · Apply Retarget · Link Head Rig · Unlink Head Rig · Remove Rigify Rig · Reload Materials

Undo a step and the face rig follows it — undo past an Assemble and it switches off with the character, redo and it comes back on. **Ctrl+Shift+Z** redoes.

Some things are one-way, because Undo cannot put them back:

- **Saving** a `.dna`, an FBX, a glTF or a CSV — the file is already written. Delete it yourself if you did not mean to.
- **Save / Reset Material Defaults** — same reason.
- **Connecting ARKit Live**, **Start Unreal Live**, **Follow Unreal**, **Send to Cascadeur** — these talk to something outside Blender. Use the panel's own Stop or Disconnect.
- **Face Rig ON/OFF** and the **Rig ON/OFF** on each character — just press the button again.

## Quick Tips

- **LOD 0** is always the highest quality — use it unless you need better performance. It is also the only level that carries facial expressions; see [section 1](#1-loading-a-character).
- You can combine **live ARKit tracking** with **manual Preset Sliders** — nudge sliders by hand if the tracking doesn't quite nail an expression.
- If something that used to work suddenly doesn't move, check that **Face Rig** or the character's **Rig ON/OFF** isn't accidentally switched off.
- For the most realistic shoulder deformation when raising the arm, key both the arm control and the `shoulder.L/R` bone together.
- **ARKit Smoothing**: low is raw and immediate, high is smooth and slightly behind. If you are coming from an older version, note that this slider used to behave the opposite way round — see [What's New](#whats-new).

## Panel Reference

Every button and option, panel by panel, under the name it carries
on screen.

### MetaBridge DNA

The main panel. The DNA inspector rows near the bottom are for troubleshooting one control's wiring and are not part of normal use.

- **Append GUIArmature** — From gui_mapping.blend (resets existing GUIArmature)
- **Toggle Face Rig** — Enable or disable RigLogic face evaluation for this
  character slot
- **Refresh Character List** — Re-scan the MetaHumans directory to refresh the
  character list
- **Head**
- **Body**
- **Textures**
- **LOD** — RigLogic evaluation LOD (0 = full detail). Applied when DNA is
  loaded or re-assembled, and immediately to the active slot
- **Re-Assemble** — Load selected MetaHuman into the active slot (replaces
  existing)
- **Assemble** — Load selected MetaHuman into the active slot (replaces
  existing)
- **New** — Add the selected character as a new slot (keeps existing slots)
- **Load Head DNA...** — Import head .dna (face mesh + face rig controls)
- **Load Body DNA...** — Import body .dna (body mesh only, no face controls)
- **Activate Slot** — Set this character slot as the active one for editing
- **Rig: ON** — Enable or disable RigLogic face evaluation for this character
  slot
- **Delete Slot** — Remove this character slot and all its objects
- **Relink DNA** — Point this character at a .dna file that has moved. Use this
  after opening a .blend saved on another computer
- **Rebuild Meta-Rig** — Create the Rigify meta-rig with bones aligned to the
  MetaHuman skeleton. Inspect and tweak bone positions, then click '2.
  Generate Rigify Rig'.
- **Regenerate Rigify Rig** — Generate the Rigify control rig from the meta-rig.
  Run AFTER '1. Build Meta-Rig' and any manual bone adjustments. MetaHuman
  meshes are protected during generation.
- **Remove Retarget** — Reverse Apply Retarget: restore original MetaHuman
  Armature modifier
- **3. Apply Retarget** — Copy vertex weights from MetaHuman bone names to
  Rigify DEF- bone names and redirect the Armature modifier to Rigify_Ctrl.
  Animate with Rigify FK/IK controls — the body mesh follows directly.
- **Unlink Head Rig** — Remove retarget constraints from the Head Rig shared
  bones
- **Link Head Rig** — Apply Rigify retarget to the MetaHuman Head Rig shared
  bones (spine_04, spine_05, clavicle_l/r, neck_01, etc.) so head mesh stays
  attached to the body animation.
- **Toggle RBF** — Enable/disable the RBF solver pass within Body Correctives
  (Twist/Swing always stay active)
- **Body Correctives: none in this DNA** — Enable/disable the RBF solver pass
  within Body Correctives (Twist/Swing always stay active)
- **Driver Bone**
- **Show RBF Controls** — Reveal and select the manual RBF controller bones
  linked to the currently selected Rigify control (e.g. shoulder.L), so their
  corrective bulge/twist can be hand-tuned.
- **Hide** — All manual RBF controller bones again
- **Import FBX Animation...**
- **Remove Rigify Rig** — Delete Rigify objects and clean up
  constraints/modifiers for this slot
- **Toggle IK Stretch** — Allow or prevent the leg/arm IK controls from
  stretching the limb
- **Toggle Heel Pivot** — Pivot the toe around the heel when foot_spin_ik is
  rotated backwards. Keep this OFF while rotating the foot_ik controller -
  when ON, the foot leaves the controller on one rotation direction
- **Toggle Finger IK** — Pose the fingers by dragging a target at each fingertip
  instead of rotating each joint. Stock Rigify has no finger IK. Switching it
  on keeps the fingers exactly where they are
- **IK to FK** — Hand the fingers' current pose over to the other set of
  controls without changing how they look
- **FK to IK** — Hand the fingers' current pose over to the other set of
  controls without changing how they look
- **Snap Fingertip Targets to Pose** — Move every fingertip target onto where
  that finger is right now, without changing the pose
- **Show** — Filter which DNA channels are listed
- **Parent**
- **Re-Auto Link** — Reload gui_mapping.json and rebuild all bone to RC
  connections
- **Clear All** — Reset runtime connections: clears manual_map and bone ml_rc
  tags. gui_mapping.json is NEVER modified. Use Re-Auto Link to restore.
- **Print Full Map (console)** — Print the complete bone to RC mapping to the
  system console
- **< Prev** — Navigate pages in the DNA RC channel list
- **Next >** — Navigate pages in the DNA RC channel list
- **Change Bone** — Open a dialog to assign a GUIArmature bone to a DNA raw-
  control channel
- **Edit Bone Mapping** — Edit the RC channel, axis, and directional mapping for
  this bone
- **Connect** — Open a dialog to assign a GUIArmature bone to a DNA raw-control
  channel
- **Add Bone to JSON** — Add a new bone-to-RC-channel entry to
  custom_mapping.json
- **Assign Bone to RC Channel** — Open a dialog to assign a GUIArmature bone to
  a DNA raw-control channel
- **Disconnect Bone** — Remove manual RC override for this bone

### Expression Presets

- **Save Current Expression** — Overwrite the preset selected in the dropdown
  with the current face board pose
- **Save As Current Expression...** — Save the current face board pose as a NEW
  preset file. Opens a file dialog so you can pick the location and type a
  file name
- **Delete Expression Preset** — Delete the selected preset file
- **Apply Preset** — Add this preset as a 0-1 slider (see 'Preset Sliders'
  below) instead of snapping instantly. It starts at 1.0 so the pose shows
  right away, and can be dialed back or blended with other active presets
  afterward
- **Import...** — Copy a preset .json file from anywhere into the addon presets
  folder so it appears in the preset list
- **Set Folder...** — Choose the folder where presets are stored and listed.
  Select the addon's own presets folder to return to the default
- **Open Presets Folder** — Open the current presets folder in the system file
  browser

### ARKit Live

- **Disconnect** — Start or stop listening for Apple Live Link Face UDP data
- **Stop Recording** — Record the live stream as keyframes starting at the
  current frame - one frame per received tick (~30fps) - instead of only being
  able to load a CSV exported after the fact. Keyframes the Preset Sliders,
  and head rotation too if that's enabled
- **Track Head Rotation**
- **Invert Pitch**
- **Invert Yaw**
- **Invert Roll**
- **Load Live Link Face CSV...** — Load a Live Link Face CSV recording and bake
  it as keyframes onto the Preset Sliders (the same controllers you can drag
  by hand), starting at the current frame
- **Export Face CSV...** — Write the evaluated shape key values over the frame
  range as CSV - one file per mesh, ready for Cascadeur's MetaArKit importer
- **Rebuild Name Mapping** — Rebuild the ARKit-name lookup tables and reload
  preset bone data from disk. Use after regenerating ARKit presets (Convert
  ARKit Payload), hand-editing a preset JSON file, or editing gui_mapping.json

### Retarget Rigify Animation (Beta)

- **Retarget Rigify Animation** — Bake the source armature's animation onto the
  target Rigify control rig

### Body Blend (experimental)

- **Use Base DNA** — Add the Body.dna (+ matching Head.dna) from the addon's
  base_dna/ folder as a source - this is meant to always be your PRIMARY row,
  since library entries can never supply RigLogic/correctives data on their
  own
- **Add Folder...** — Scan a folder for *_Body.dna files (Epic's own body-
  archetype naming) and add every one found as a blend source, auto-matching
  each with its *_Head.dna. Remembers the folder for next time
- **Add Body DNA** — Add a body.dna file as a blend source
- **Load Library...** — Load a compact .json archetype library (see Export
  Archetype Library) and add every archetype in it as a blend source. These
  can only be used as NON-primary sources - keep at least one real .dna file
  (e.g. your own character) as the primary/highlighted row
- **Export...** — Export the CURRENT Body Blend source list (added .dna rows and
  loaded library entries - exactly what you see, nothing else) as ONE compact
  .json library. With an empty list, falls back to scanning the chosen folder
  (including subfolders) for body .dna files instead
- **Name**
- **LOD**
- **Build Blended Body** — Blend the listed body DNA files (weighted) into a
  character. WARNING: adjusting blend weight sliders AFTER building may cause
  face rig errors - if the face misbehaves after changing weights, click Build
  again (with Replace on) to rebuild it cleanly
- **Replace** — Build overwrites the last Body Blend character slot in place
  instead of adding a new one (falls back to adding if there's nothing to
  replace yet, e.g. the first Build this session)
- **Live Preview** — After a Build, dragging a weight slider re-blends and
  updates the built character live instead of requiring another Build click

### Wearables (experimental)

- **Import Clothing (FBX)...** — Import a MetaHuman-compatible clothing FBX
  (same skeleton bone names) and attach it to the active character - reuses
  the character's OWN skeleton, and retargets the garment's rest shape to this
  character's actual bone proportions (not a Shrinkwrap - loose clothing stays
  loose)
- **Head Accessory...** — Import a MetaHuman-compatible clothing FBX (same
  skeleton bone names) and attach it to the active character - reuses the
  character's OWN skeleton, and retargets the garment's rest shape to this
  character's actual bone proportions (not a Shrinkwrap - loose clothing stays
  loose)
- **Refit Clothing To Body** — Re-run the bone-position retarget for every worn
  clothing item on the active character. For a Body Blend character, this also
  forces the body/head armature itself fully up to date first (bypassing Live
  Preview's mode-safety pause), so this is the reliable manual fallback when
  live tracking didn't already catch a shape change
- **Clothing Offset** — Pushes ALL currently worn clothing outward along its own
  surface normal by this distance, uniformly everywhere - not a scale, so it
  floats just slightly off the body instead of clipping into skin. Adjustable
  anytime, not just at import time - applies live to everything already worn
  on this character
- **Make Garment Rig** — Rig the SELECTED mesh as a garment for the active
  character: transfers skin weights from the character's own body mesh
  (nearest-face projection - the same technique MetaHuman clothing uses in
  Unreal), limits/normalizes them, and adds an Armature modifier driving it
  with the character's own skeleton - the mesh then deforms exactly as if the
  character were wearing it. Follow with Bind Garment To Character
- **Bind Garment To Character** — Attach the selected Made garment (see Make
  Garment Rig) to the active character, exactly like an imported clothing FBX:
  replaces whatever worn category it conflicts with, records the character's
  CURRENT shape as the garment's reference fit, and from then on it follows
  Body Blend weight changes live and the Refit button - the same pipeline as
  FBX clothing
- **Import Hair...** — Import a MetaHuman-compatible hair/groom Alembic (.abc)
  and parent it to the active character's head. Defaults are tuned for
  MetaHuman groom exports (Scale 0.01, since Blender's Alembic importer
  doesn't do the cm-to-meter conversion this addon's own DNA pipeline does
  elsewhere) - use the Scale/Rotation options (bottom-left after importing) to
  adjust for a different source
- **Bind Hair To Head** — Make the selected hair/beard follow the active
  character's head when Body Blend changes its shape. Needed for grooms that
  came in without Bind To Head Surface, or from outside this addon - hair
  already bound is simply re-bound to where the head is now
- **Align Active Mesh to DNA Head** — Move the selected mesh's points onto the
  character's own head shape, so a head made elsewhere matches this character
- **Retarget Hair to Selected Mesh** — Re-attach the selected hair to the mesh
  you pick, so it follows this character's head instead of the one it came
  with

### Live Corrective Sculpting (Beta)

- **Corrective** — Name of the corrective to sculpt - reuse an existing name to
  add another anchor pose to it, or type a new name to start a new one
- **Begin (Face)** — Enter Sculpt Mode on a new correction for the pose the
  character is in right now. Sculpt the fix, then click Finish Sculpt
- **Body Driver Bone** — Body armature bone whose rotation this corrective
  should react to - only bones that actually drive a Twist/Swing/RBF
  corrective are listed
- **Begin (Body)** — Enter Sculpt Mode on a new correction for the pose the
  character is in right now. Sculpt the fix, then click Finish Sculpt
- **Finish Sculpt** — Leave Sculpt Mode and start playing this correction back
  automatically whenever the character returns to that pose
- **Export Edited Shape Keys** — Write every DNA blend shape key you sculpted
  back into the .dna, replacing that channel
- **Bake All to DNA** — Write every corrective that has a blend shape target
  assigned, in one pass
- **Export...** — Save every correction on this character to a .json file to
  reuse or share
- **Import...** — Load corrections from a .json file. Only works on a character
  with the same body and head as the one they were saved from
- **Sync to Wearables** — Copy the skin's corrections onto the clothing worn on
  this character, so a sleeve bulges with the arm underneath it. Use after
  adding new clothing
- **Set Neutral** — Record the CURRENT pose as this corrective's neutral (weight
  0). Put the character back to rest first. Use this when the corrective does
  not fall all the way to 0 at rest - on a custom head the driver bone does
  not sit exactly on its rest pose at neutral, and the assumed neutral leaves
  a constant offset
- **Toggle Manual Override** — Switch between following the pose automatically
  and being dragged by hand with the slider
- **Remove Corrective** — Delete this correction and its shape key. The
  character keeps its shape; only the correction is removed
- **value**
- **Edit Sculpt** — Go back into Sculpt Mode on this correction to refine it.
  Pose the character close to where it was first sculpted for the best result
- **Bake Corrective to DNA** — Write this corrective into the .dna as blend
  shape deltas

### Export (DNA / FBX / glTF)

- **Head** — Save the active slot's head.dna, including any Blender mesh edits
- **Body** — Save the active slot's body.dna, including any Blender mesh edits

### MD Live

- **Shared Folder** — The folder Blender writes avatars to and Marvelous
  Designer exports garments into. Remembered for the next file
- **Open Shared Folder** — Open the shared folder in the system file browser
- **Send Scale** — Marvelous Designer units per Blender metre when SENDING.
  Blender works in metres, so 1000 sends millimetres and 100 sends centimetres
  - it has to match the unit picked in Marvelous Designer's own import dialog.
  Remembered for the next file
- **Include Head** — Send the head mesh along with the body. Marvelous Designer
  refuses an avatar with no head, so this is on by default; it is also what
  hats and collars need. Remembered for the next file
- **Prepare for Auto-Fit** — Ask Marvelous Designer to build arrangement points
  and a fitting suit while it loads the avatar. A plain OBJ has neither, and
  the tools that expect a prepared avatar turn it away. Turn off if the import
  misbehaves
- **Send Body to MD** — Write the active character's body out to the shared
  folder as an OBJ avatar for Marvelous Designer at the Send Scale. Always the
  same filename, so reshaping the character and pressing this again is the
  whole round trip - then run the MetaBridge plug-in in Marvelous Designer
- **Import Scale** — Marvelous Designer units per Blender metre when RECEIVING a
  garment. This is a separate number from the send scale because Marvelous
  Designer's export settings need not match its import dialog. The size of
  what arrives is reported so this can be checked
- **Import Garment from MD...** — Bring a garment Marvelous Designer exported
  back in, scaled from centimetres to metres. With Rig To Character on it goes
  straight through the normal clothing pipeline - skin weights from the
  character's own body, then worn as a garment that follows the rig
- **Open MD Plug-in Folder** — Open the folder holding the Marvelous Designer
  plug-in script. Register this folder once in Marvelous Designer under Plug-
  in > Plug-in Manager > Add, and a menu entry there will load whatever Send
  Body to MD last wrote

### Send to Cascadeur

- **Send**
- **Include Head** — Merge the head rig and its meshes into the body skeleton on
  the way out. Off sends the body alone
- **Face Bones** — Send the 843 facial joints too. Off keeps the face on the
  head joint and sends the body skeleton alone, which is a quarter of the
  character and all Cascadeur needs to animate a body. Turn on only to pose
  the face there
- **Include Animation** — Bake whatever animation is on the rig into the FBX.
  Off sends the character in its rest pose
- **Append** — Add after whatever Cascadeur already received. Off starts again
  from frame 0
- **Send Frame Range**
- **Current Frame**
- **Port** — The port Cascadeur's Receive Poses command listens on. Change it
  only if that command was started on another one. Remembered for the next
  file
- **Cascadeur Status**
- **Receive** — **Animation Only** keys onto the rig already here.
  **Mesh + Animation** brings Cascadeur's scene back as new objects.
- **Onto Rigify Controls** — Put what comes back on the control rig instead of
  the deform bones, so it can be adjusted there.
- **Whole Take** — Read every frame Cascadeur holds. Off reads the scene frame
  range instead.
- **Receive from Cascadeur** — Bring the work back.

### Unreal Live

- **Port** — Loopback port Unreal's Live Link source connects to. Keep it off
  the port a body stream is using, so the two can be attached at once
- **Rate** — Frames a second to send. Live Link reads a source that goes quiet
  as a source that died, so this is sent at a steady rate whether the face is
  moving or not
- **Start Unreal Live**
- **Stop Unreal Live**
- **Mirror** — Blender and Unreal disagree on handedness, and Y is the
  reflection that settles it - derived from Unreal's own bone transforms and
  confirmed on the character. Left as a switch for a rig built the other way
  round

### Follow Unreal

- **Host** — Where Unreal is. `127.0.0.1` when it is on this machine.
- **Port** — 9562. This is what tells the Unreal plug-in it is sending here
  rather than to one of the other features.
- **Apply Rate** — How many times a second the arriving pose is applied.
- **Body** — Follow the body bones.
- **Face** — Follow the face.
- **Follow Unreal** — Start. Then run **MotionForge.Send.Start** in Unreal.
- **Stop Following** — Stop, and give Rigify back its constraints.

### Animation Baker

- **Bake Face Animation** — Evaluate the face board over the frame range and
  bake the result into keyframes on the head rig bones and shape keys
- **Clear Baked Animation** — Remove baked actions from the head rig and shape
  keys of the active slot

### Pose Reset

- **Reset All Controls** — Reset all face board controls of the active slot to
  the neutral pose
- **Reset Selected (Pose Mode)** — Reset only the selected face board bones to
  neutral (Pose Mode)

### DNA Validation

- **Validate DNA File...** — Check a .dna file for corruption and print a
  content report to the console
- **Validate Active Slot** — Validate the head and body DNA files of the active
  slot

### Batch Tools

- **Assemble All Characters** — Assemble every character found in the scanned
  directory into its own slot. This can take a long time for many characters
- **Export All Slots** — Export every assembled slot to a directory as FBX or
  glTF

### External Preset Converter

- **Convert & Import (Maya/Houdini)...** — Import a Maya/Houdini preset JSON,
  converting its bone names to the GUI board names. Unmatched names are
  written to name_mapping.json for manual editing
- **Convert ARKit Payload...** — Convert an ARKit remap payload JSON (arkit52
  target/contributor weights) into one board-pose preset per ARKit target
- **Edit Name Mapping**
