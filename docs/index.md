# MetaBridge Forge — User Guide (v1.1)

![MetaBridgeForge04.png](assets/MetaBridgeForge04.png)

<<<<<<< HEAD
An editor plugin that automates MetaHuman outfit (clothing) and groom (hair) preparation. Aside from picking one FBX/Alembic file, everything from import through Wardrobe Item creation and verification happens automatically, with no manual steps in between.

**Zero setup required** — the template assets the pipelines are built on are bundled inside the plugin itself, so it works out of the box even in a brand-new project with an empty `Content/` folder. Just install the plugin and use the menu.

## Menu Location

Editor top menu: **Tools > MetaBridge Forge**

- **Import Outfit FBX...** — full outfit (clothing) pipeline
- **Import Groom ABC...** — full groom (hair) pipeline

Both menu items only show a file-picker dialog; everything else is automatic. A popup only appears on failure.

## Templates: Bundled, No Project Setup Needed

**This plugin doesn't generate content from scratch — it duplicates a template and retargets it.** In earlier versions (v1.0) the templates had to already exist in the project's own `Content/` folder; **since v1.1 that is no longer required.** The template assets (a working OA_/CA_ outfit set, and a groom's GroomMesh/Materials set) are **bundled inside the plugin's own content** under `/MetaBridgeForge/Templates/` (both fully self-contained — verified to have zero external `/Game/` dependencies, and verified end-to-end by running both pipelines cloning from the bundled copies), so in a fresh project the plugin works out of the box with no setup.

Template resolution order (automatic, per run):

1. **Project override first** — if the project has its own template at `/Game/Outfits/<OUTFIT_TEMPLATE_DEFAULT>/` (with a real OA_ inside) or at `GROOM_TEMPLATE_FOLDER`, that one is used.
2. **Plugin fallback** — otherwise the bundled copy under `/MetaBridgeForge/Templates/` is used. (Leftover redirectors from moving templates around do not count as a project override — the resolver checks for real assets.)

| Setting (`Content/Python/mbforge/config.py`) | Purpose |
=======
**v1.6.0 — Rigify retarget overhaul + body correctives polish**

- **Spine hierarchy fix**: upper body no longer follows hip FK rotation incorrectly — `spine_fk.001` is re-parented to `torso` automatically after rig generation.
- **Foot IK gap fixed**: `heel.02` is now placed directly under the ankle at the true ground level, so the foot stays flush with the floor when `foot_ik` moves.
- **Foot follows torso fix**: `foot_l/r` now use a world-space COPY_LOCATION from the Rigify IK foot — moving torso no longer drags the feet along.
- **Smooth shading**: all MetaHuman meshes are automatically set to smooth shading on Assemble.
- **Material defaults**: place a `material_defaults.json` alongside the addon to bake preferred BSDF values into every fresh character assembly — other users get the same look without extra steps.
- **Body correctives lag fix**: a deferred timer re-evaluates correctives after the re-entrant depsgraph update, so the mesh never stays one tick behind when a controller stops moving.
- **RBF influence slider redesigned**: `0` = automatic corrective off (neutral rest), `1` = full automatic corrective applied. Rotating the controller bone manually adds an additional offset on top, independent of the slider.
- **RBF controllers — one driver per joint**: each corrective joint now belongs to exactly one primary driver bone (chosen by longest name-prefix match), so selecting `shoulder.L` shows only that shoulder's controllers, with no overlap from `upper_arm_ik.L`.
- **RBF slider now triggers live update**: changing the influence slider immediately re-evaluates the mesh — no need to move a bone to see the effect.

**v1.5.0 — Body Blend (experimental) + individual DNA loading**
- **NEW: Body Blend panel** — combine two or more MetaHuman body types (and their matching heads) into a brand-new blended character, with a per-source weight slider for each.
- **Live Preview** — dragging a weight slider updates the character on screen in real time.
- **Replace toggle** — overwrite your last Body Blend character in place instead of adding a new slot every time.
- **Load Library...** now defaults to `base_dna/`'s own library file when nothing's been loaded yet this session.
- **Compact archetype libraries** — pack many body/head archetypes into a single small `.json` file.
- **Individual DNA loading restored** — **Load Head DNA...** / **Load Body DNA...** buttons are back in the main panel.

**v1.3.0 — Body Correctives & auto-reconnect**
- **Body Correctives**: realistic secondary deformation (shoulder/hip muscle bulge, limb twist correction) powered by the character's own DNA file.
- **Manual fine-tuning (RBF Controllers)**: hand-adjust specific spots with helper bones and blend sliders.
- **The body rig reconnects itself automatically** when you reopen a saved file.

---

## What is this addon?

MetaBridge DNA lets you bring Epic Games **MetaHuman** characters into Blender, pose their faces in real time, and export them back out.

<div align="center"><iframe width="640" height="360" src="https://www.youtube.com/embed/rnNuLmuO7JE" title="Load MetaHuman DNA to Instant ARKit Controllers (No Shape Keys!)" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>

With it you can:

- Load a MetaHuman character (head + body) into Blender
- Move sliders or bones to make facial expressions — no shape key editing needed
- Save your favorite expressions as reusable presets, and blend several at once
- Drive the face **live from an iPhone** using Apple's Live Link Face app
- Build an animatable body rig (Rigify) for the character
- Export everything back to DNA, FBX, or glTF

Everything is in one place: open the **N panel** on the right side of the 3D Viewport, and look for the **MetaBridge DNA** tab.

![metabridge_dna01.png](assets/metabridge_dna01.png)

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
2. Click **Apply Preset** — it's added to the **Preset Sliders** list, already turned on.
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
>>>>>>> parent of 611460a (1.7)
|---|---|
| `OUTFIT_TEMPLATE_DEFAULT` | Name of the template outfit (default `"BasicOutfit"`) — used for both the project-override lookup and the plugin-bundled lookup |
| `GROOM_TEMPLATE_FOLDER` | Project-override path for the groom template (default `"/Game/Grooms/Beard_A/Beard_A"`) |
| `PLUGIN_GROOM_TEMPLATE_FOLDER` | Plugin-bundled groom template path — only change if you rebundle a different groom into the plugin |

To see the bundled templates in the Content Browser, enable **Settings > Show Plugin Content**.

If no template can be found in either location, nothing crashes — the run fails immediately with a "template not found" error in the log.

### How to edit config.py (optional — only for using your own project templates)

With the bundled templates, no config editing is required. Edit `Plugins/MetaBridgeForge/Content/Python/mbforge/config.py` only if you want a specific project template to take priority over the bundled one. Only the paths/names inside the quotes need to change.

```python
# 1) Outfit template name - if "/Game/Outfits/<this name>/" contains a real OA_, it wins over the bundled template
OUTFIT_TEMPLATE_DEFAULT = "BasicOutfit"        # → e.g. "MyTemplateOutfit"

# 2) Groom template folder - if this folder contains real assets, it wins over the bundled template
GROOM_TEMPLATE_FOLDER = "/Game/Grooms/Beard_A/Beard_A"   # → e.g. "/Game/Grooms/MyTemplateGroom/MyTemplateGroom"
```

Tip for finding the exact path: right-click the folder/asset in the Content Browser → **Copy Reference** to get the full, exact path.

You don't need to restart the editor after changing values — it may already be picked up the next time you click a menu item, but to be sure, reload it from the Python console:

```python
import importlib
from mbforge import config
importlib.reload(config)
```

## Import Outfit FBX...

1. Click the menu → pick the garment FBX file
2. What happens automatically:
   - Imports the garment as a Static Mesh + duplicates the template's reference body (`/Game/Outfits/<name>/<name>/Meshes/`)
   - Duplicates the template OA_/CA_ (+ their own Dataflow graphs) wholesale (`/Game/Outfits/<name>/`)
   - Retargets the duplicated CA_'s mesh references and the OA_'s `SizedOutfitSource` to point at the newly imported mesh
   - Creates `WI_<name>` Wardrobe Item + runs verification
3. The outfit name is auto-derived from the FBX filename (special characters replaced with `_`).
4. On success, only a log entry is written (Output Log) — no popup. On failure, an error popup appears with details in the Output Log.

<<<<<<< HEAD
## Import Groom ABC...
=======
1. **Build Meta-Rig** — creates a draft skeleton matching the body.
2. **Generate Rigify Rig** — turns the draft into a real, posable control rig. The spine hierarchy is patched automatically after generation (upper body isolated from hip FK rotation, tweak bones locked).
3. **Apply Retarget** — connects the control rig so it drives the MetaHuman body. Body correctives are registered at this step.
   > ⚠️ If the draft skeleton from step 1 wasn't positioned correctly, this can distort the mesh. Check that everything looks right after step 2, before applying.
4. **Link Head Rig** — connects the head so it moves with the body.
5. **Remove Rigify Rig** removes everything from steps 1–4 if you need to start over.
>>>>>>> parent of 611460a (1.7)

1. Click the menu → pick the hair Alembic (.abc) file
2. What happens automatically:
   - Clones the GroomMesh/Materials template files + imports the .abc as the groom asset (`/Game/Grooms/<name>/`)
   - Creates a binding (`GB_<name>`) onto the cloned reference head
   - Creates the `WI_<name>` Wardrobe Item
3. The groom name is auto-derived from the .abc filename.
4. On success, only a log entry is written — no popup. On failure, an error popup appears.

## Out of Automated Scope (manual work)

The following were deliberately left manual, since they need case-by-case judgment:

<<<<<<< HEAD
- Mesh retargeting for the compound case of an outfit with multiple CA_'s (call `duplicate_build.retarget_cloth_asset_meshes` / `retarget_outfit_source` directly from the Python console)
- Assigning a finished `WI_` to an actual MetaHuman character's slot (`character.internal_collection.try_add_item_from_wardrobe_item(slot_name=..., wardrobe_item=wi_asset)`)
- Groom hair color/material customization
=======
- **Body Correctives RBF: ON/OFF** — toggles the RBF solver layer. Leave it **ON** for the most realistic result. Basic twist/muscle correction stays active either way.
- If a character's DNA doesn't include this data, the button shows **"none in this DNA"** and is grayed out.
- Correctives update continuously as you pose — even when a controller stops moving, the mesh catches up via an automatic deferred re-evaluation.
>>>>>>> parent of 611460a (1.7)

## If Something Goes Wrong

1. Check the Output Log for lines starting with `MetaBridge Forge:` (**Window > Developer Tools > Output Log**)
2. Each pipeline function can be called directly from the Python console to re-run just one step, e.g.:
   ```python
   from mbforge import duplicate_build, groom, wardrobe
   duplicate_build.retarget_duplicated_outfit("MyOutfitName", garment_mesh, body_mesh)
   groom.finish_groom_setup("MyGroomName")
   wardrobe.finish_outfit_setup("MyOutfitName")
   ```

<<<<<<< HEAD
## Moving to Another Project/Computer

**Zipping up the plugin folder (`Plugins/MetaBridgeForge/`) is enough** — the template assets are bundled inside the plugin's `Content/Templates/` folder, so nothing else needs to be migrated. Checklist:

1. Copy the entire `Plugins/MetaBridgeForge/` folder into the target project's `Plugins/` folder.
   - If `Binaries/Win64/` is included, it works without a rebuild as long as the **engine version is exactly the same** (currently UE 5.8, same build as the Epic Games Launcher install).
   - `Intermediate/` and `Content/Python/**/__pycache__/` are build/runtime cache — no need to bring these along (safe to exclude from the zip).
   - If the engine version differs, `Source/` must be included, and the target machine will automatically trigger a one-time rebuild.
   - **Do include `Content/Templates/`** — that's the bundled template data the pipelines clone from.
2. Confirm the target project's `.uproject` has the `ChaosOutfitAsset` and `ChaosClothAsset` engine plugins set to `Enabled: true`.
3. (Optional) If the target project has its own, better-fitting template outfit/groom, point `config.py`'s `OUTFIT_TEMPLATE_DEFAULT` / `GROOM_TEMPLATE_FOLDER` at it — project templates always take priority over the bundled ones.

## Version

**v1.1** — Template content (`BasicOutfit` outfit set, `Beard_A` groom set) moved into the plugin's own `Content/Templates/`, with project-first/plugin-fallback resolution — pre-existing base templates in the project are no longer required; the plugin works out of the box in a fresh project. Both pipelines verified end-to-end cloning from the bundled templates. Candidates for the next version: multi-CA_ support, automatic character-slot assignment, head accessories.

**v1.0** — Outfit/groom one-shot import pipelines complete. Unused dead code removed (`BODY_SKELETON_PATH`/`HEAD_SKELETON_PATH` in `config.py`, `confirm()` in `dialogs.py`).
=======
1. In **Pose Mode**, select the control bone for the area you want to adjust (e.g. `shoulder.L`).
2. Click **Show RBF Controls** — small diamond-shaped helper bones appear, only for that driver's joints (no overlap with adjacent drivers).
3. Adjust the **influence slider** (0–1) per bone in the **Active RBF Controllers** list:
   - `0` = automatic corrective **off** (bone stays at rest/neutral)
   - `1` = automatic corrective **fully applied** (default)
   - Changing the slider immediately updates the mesh.
4. **Rotate** a helper bone by hand to add an extra manual correction on top of the automatic result — this is independent of the influence slider and is always applied at full strength.
5. Click **Hide** when done to tidy the viewport.

> Rotating a helper bone at `influence = 1` stacks your manual rotation on top of the full automatic result. At `influence = 0` only your manual rotation is used, with no automatic contribution.

**Good to know:**

- Once Apply Retarget and Link Head Rig are set up, the connection is saved with your file — reopening it works without re-clicking Apply Retarget.
- The Rigify shoulder bone (`shoulder.L/R`) must be manually elevated when raising the arm — unlike Unreal's Control Rig, Rigify does not auto-elevate the clavicle procedurally. Key the shoulder bone alongside the arm for the most natural shoulder deformation.

---

## 6. Body Blend (experimental)

Combine two or more MetaHuman body types — and their matching heads — into a brand-new blended character. Found in its own **Body Blend (experimental)** panel, collapsed by default.

**Adding sources:**

- **Use Base DNA** — adds the addon's own reference character from the `base_dna/` folder.
- **Add Folder...** — scans a folder for `*_Body.dna` files and adds every one it finds.
- **Add Body DNA** — add one specific `.dna` file by hand.
- **Load Library...** — load a compact archetype library and add every archetype in it as a source.

Weights don't need to add up to anything in particular — they're normalized automatically. **Use Base DNA** starts at `1.0`; all other sources start at `0.0`.

**The primary row:**

The **highlighted row** is the primary source — its DNA supplies the topology, skin weights, RigLogic and muscle-correctives data. This must be a real `.dna` file. Every other row contributes its shape to the blend.

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

**The `base_dna/` folder:**

Put your own reference `Body.dna` and matching `Head.dna` here (`metabridge_dna/base_dna/`). This is what **Use Base DNA** adds, and what Build falls back to when nothing else is weighted.

**Compact archetype libraries:**

- **Export...** — picks a folder of `*_Body.dna` files and writes one compact `.json` library.
- **Load Library...** — loads a library, adding one row per archetype. Library rows can only ever be non-primary sources.

---

## 7. Exporting

- **DNA**: separate **Head** and **Body** buttons (head and body are always two separate `.dna` files).
- **FBX / glTF**: **Full / Head / Body** buttons. Choose whether to include the control rig and animation in the export dialog.

**Batch Tools:**

- **Assemble All Characters** — loads every character found in your folder in one go.
- **Export All Slots** — exports every loaded character at once.

---

## 8. Other Useful Tools

- **DNA RC Inspector**: shows how the control bones are connected to the character's DNA data. Mainly for troubleshooting a specific control.
- **DNA Validation**: checks whether a `.dna` file is valid before you use it.
- **Pose Reset**: instantly resets the face back to neutral.
- **Animation Baker**: turns your live/keyframed facial performance into a permanent, exportable animation.

---

## Quick Tips

- **LOD 0** is always the highest quality — use it unless you need better performance.
- You can combine **live ARKit tracking** with **manual Preset Sliders** — nudge sliders by hand if the tracking doesn't quite nail an expression.
- If something that used to work suddenly doesn't move, check that **Face Rig** or the character's **Rig ON/OFF** isn't accidentally switched off.
- For the most realistic shoulder deformation when raising the arm, key both the arm control and the `shoulder.L/R` bone together.
>>>>>>> parent of 611460a (1.7)
