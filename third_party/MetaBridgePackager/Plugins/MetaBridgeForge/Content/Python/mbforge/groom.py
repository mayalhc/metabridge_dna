"""Groom (Alembic hair) import automation - mirrors importer.py's outfit
workflow: create /Game/Grooms/<name>/<name>/{GroomMesh,Materials}/, clone
the reference head mesh + material template files from an existing groom
folder (every groom in this project shares identically-named files there,
e.g. SK_MH_Groom_Head - see config.GROOM_TEMPLATE_FOLDER), then import
the .abc as the groom asset itself, bind it to that same cloned reference
head, and wire up its Wardrobe Item (see finish_groom_setup()). Fully
one-shot, no Content Browser selection needed for any of it.

NOTE: the Alembic groom import options class (unreal.GroomImportOptions
below) was not confirmed against a live console during scoping - if the
import step itself errors, check `[x for x in dir(unreal) if 'Groom' in x
and 'Import' in x]` in the UE Python console for the real class name.

Unlike outfits, a groom's Wardrobe Item principal_asset is NOT the raw
GroomAsset - it's a GroomBindingAsset (Groom + a SkeletalMesh to bind
onto). Confirmed both against MetaHumanDefaultEditorPipeline's C++ source
(Cast<UGroomBindingAsset>(WardrobeItem->PrincipalAsset.LoadSynchronous()))
and against a real, hand-built example already in this project
(/Game/Grooms/Beard_A/{GB_Beard_A,Wi_Beard_A}). That same example is also
what corrected an earlier, wrong version of this module: the binding's
SourceSkeletalMesh and TargetSkeletalMesh are the SAME object (the
cloned generic reference head, not some specific MetaHuman's actual
face) - see create_groom_binding()'s docstring.

CRASH HISTORY: an earlier version of create_groom_binding() crashed the
editor (confirmed: UnrealEditor-HairStrandsCore.dll, background worker
thread, array-index-out-of-bounds during an async binding rebuild -
caused by driving unreal.GroomBindingFactory via 3 separate
set_editor_property() calls instead of the engine's own
unreal.GroomLibrary.create_new_groom_binding_asset_with_path(), which
sets everything through non-reflection setters and calls Build() exactly
once). See create_groom_binding()'s docstring for the full root-cause
writeup. Do not reintroduce set_editor_property() on a
GroomBindingAsset's Groom/SourceSkeletalMesh/TargetSkeletalMesh fields.
"""
import unreal

from . import config, dialogs


def _ensure_groom_folders(groom_name: str) -> None:
    lib = unreal.EditorAssetLibrary
    for folder in (
        config.groom_folder(groom_name),
        config.groom_deps_folder(groom_name),
        config.groom_mesh_folder(groom_name),
        config.groom_materials_folder(groom_name),
    ):
        if not lib.does_directory_exist(folder):
            lib.make_directory(folder)


def _clone_template_folder(src_folder: str, dst_folder: str) -> list:
    """Duplicates every asset directly inside src_folder into dst_folder,
    keeping exact names (case-sensitive) - same self-contained-package
    reasoning as importer.py's skeleton/body-mesh duplication. Skips
    (doesn't overwrite) anything already present at the destination.
    Returns the list of destination asset paths.
    """
    lib = unreal.EditorAssetLibrary
    copied = []
    for src_path in lib.list_assets(src_folder, recursive=False, include_folder=False):
        # list_assets returns "/Game/.../Name.Name" - strip to the bare
        # package path for both source and destination.
        pkg_path = src_path.split(".")[0]
        name = pkg_path.split("/")[-1]
        dst_path = f"{dst_folder}/{name}"
        if lib.does_asset_exist(dst_path):
            copied.append(dst_path)
            continue
        new_asset = lib.duplicate_asset(pkg_path, dst_path)
        if new_asset is not None:
            lib.save_loaded_asset(new_asset)
            copied.append(dst_path)
        else:
            unreal.log_error(
                f"MetaBridge Forge: failed to duplicate {src_path} to {dst_path}"
            )
    return copied


def import_groom_abc(abc_path: str, groom_name: str) -> "unreal.Object | None":
    """Sets up /Game/Grooms/<groom_name>/, clones the GroomMesh/Materials
    template contents from config.GROOM_TEMPLATE_FOLDER into it, and
    imports abc_path as the groom asset itself (named after groom_name,
    no prefix). Returns the imported groom asset, or None on failure.
    """
    _ensure_groom_folders(groom_name)

    # Resolves project-first with a plugin-bundled fallback (see
    # config.resolve_groom_template_folder).
    template = config.resolve_groom_template_folder()
    mesh_copied = _clone_template_folder(
        f"{template}/{config.GROOM_MESH_SUBDIR}", config.groom_mesh_folder(groom_name)
    )
    mat_copied = _clone_template_folder(
        f"{template}/{config.MATERIALS_SUBDIR}", config.groom_materials_folder(groom_name)
    )
    unreal.log(
        f"MetaBridge Forge: cloned {len(mesh_copied)} GroomMesh + "
        f"{len(mat_copied)} Materials asset(s) from template {template}"
    )

    options = unreal.GroomImportOptions()

    task = unreal.AssetImportTask()
    task.filename = abc_path
    task.destination_path = config.groom_mesh_folder(groom_name)
    task.destination_name = groom_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = list(task.imported_object_paths)
    if not imported_paths:
        unreal.log_error(
            f"MetaBridge Forge: groom import produced no assets for "
            f"{abc_path} - check the Output Log for the Alembic "
            f"importer's own errors."
        )
        return None

    groom_asset = None
    for p in imported_paths:
        obj = unreal.load_asset(p)
        if isinstance(obj, unreal.GroomAsset):
            groom_asset = obj
            break

    if groom_asset is None:
        kinds = ", ".join(type(unreal.load_asset(p)).__name__ for p in imported_paths)
        unreal.log_error(
            f"MetaBridge Forge: groom import of {abc_path} produced no "
            f"GroomAsset (got: {kinds})."
        )
        return None

    unreal.log(f"MetaBridge Forge: imported groom {groom_asset.get_path_name()}")
    return groom_asset


# ── Groom binding + Wardrobe Item (Step 2) ──────────────────────────────

GROOM_SLOT_NAMES = ("Hair", "Eyebrows", "Beard", "Mustache", "Eyelashes", "Peachfuzz")


def _find_skeletal_mesh_in_folder(folder: str) -> "unreal.SkeletalMesh | None":
    for listing in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
        obj = unreal.load_asset(listing.split(".")[0])
        if isinstance(obj, unreal.SkeletalMesh):
            return obj
    return None


def create_groom_binding(
    groom_name: str,
    groom_asset: "unreal.GroomAsset",
) -> "unreal.GroomBindingAsset | None":
    """Creates GB_<groom_name> under /Game/Grooms/<groom_name>/, binding
    groom_asset onto the SkeletalMesh cloned from the template into this
    groom's own GroomMesh/ folder (see import_groom_abc /
    config.GROOM_TEMPLATE_FOLDER) - used as BOTH SourceSkeletalMesh and
    TargetSkeletalMesh.

    Confirmed against a real, hand-built example already in this project
    (/Game/Grooms/Beard_A/GB_Beard_A): SourceSkeletalMesh and
    TargetSkeletalMesh are the same object
    (GroomMesh/SKM_MH_Groom_Head) - grooms don't bind to a specific
    MetaHuman's actual face at the binding-asset level the way outfits
    bind to a specific reference body; the shared generic head is enough,
    and per-character fitting happens elsewhere in the MetaHuman groom
    pipeline.

    CRASH HISTORY: an earlier version of this function created the asset
    via unreal.GroomBindingFactory + three separate set_editor_property()
    calls (groom, then source_skeletal_mesh, then target_skeletal_mesh).
    That crashed the editor (UnrealEditor-HairStrandsCore.dll, background
    worker thread, "Array index out of bounds: -1 into an array of size
    1"), confirmed via the crash log (Saved/Logs/*-backup-*.log) and the
    engine source: UGroomBindingAsset::PostEditChangeProperty
    (GroomBindingAsset.cpp) unconditionally kicks off an async rebuild
    (BeginCacheDerivedDatas) on EVERY set_editor_property() call, with no
    check that Groom/Source/Target are all populated yet - so the 3 calls
    raced 3 overlapping, transiently-invalid async builds against each
    other. This version instead uses the engine's own
    UGroomBlueprintLibrary::CreateNewGroomBindingAssetWithPath() (Python:
    unreal.GroomLibrary - note the ScriptName override, it is NOT
    unreal.GroomBindingFactory or unreal.GroomBlueprintLibrary), which
    sets Groom/Source/Target via their non-reflection C++ setters (no
    PostEditChangeProperty involved) and calls Build() exactly once at
    the end - confirmed by reading GroomBlueprintLibrary.cpp directly, do
    not replace this with manual set_editor_property() calls again.

    Returns the binding asset, or None on failure (errors logged via
    unreal.log_error).
    """
    reference_head = _find_skeletal_mesh_in_folder(config.groom_mesh_folder(groom_name))
    if reference_head is None:
        unreal.log_error(
            f"MetaBridge Forge: no SkeletalMesh found in "
            f"{config.groom_mesh_folder(groom_name)} to use as the "
            f"binding's Source/TargetSkeletalMesh - check "
            f"config.GROOM_TEMPLATE_FOLDER and that 'Import Groom ABC...' "
            f"actually cloned it there."
        )
        return None

    # GB_ sits at the top-level groom folder (/Game/Grooms/<name>/), same
    # level as WI_ - confirmed against the real Beard_A example
    # (/Game/Grooms/Beard_A/GB_Beard_A, /Game/Grooms/Beard_A/Wi_Beard_A).
    # Only GroomMesh/Materials/the raw GroomAsset live one level deeper,
    # under groom_deps_folder() (/Game/Grooms/<name>/<name>/).
    gb_folder = config.groom_folder(groom_name)
    gb_path = f"{gb_folder}/GB_{groom_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(gb_path):
        unreal.EditorAssetLibrary.delete_asset(gb_path)
    if not unreal.EditorAssetLibrary.does_directory_exist(gb_folder):
        unreal.EditorAssetLibrary.make_directory(gb_folder)

    binding = unreal.GroomLibrary.create_new_groom_binding_asset_with_path(
        gb_path, groom_asset, reference_head, 100, reference_head, 0
    )
    if binding is None:
        unreal.log_error(
            f"MetaBridge Forge: create_new_groom_binding_asset_with_path "
            f"returned None for {gb_path} - check the Output Log for "
            f"LogHairStrands errors."
        )
        return None

    # CreateNewGroomBindingAssetWithPath already calls FHairStrandsCore::
    # SaveAsset internally, but that's a synchronous save at Build() time -
    # save again to be safe/explicit, matching this codebase's convention
    # everywhere else.
    unreal.EditorAssetLibrary.save_loaded_asset(binding)
    unreal.log(f"MetaBridge Forge: created groom binding {binding.get_path_name()}")
    return binding


def finish_groom_setup(
    groom_name: str,
    slot_name: str = "Hair",
) -> tuple[bool, str]:
    """Step 2 for grooms, mirroring wardrobe.finish_outfit_setup(): binds
    the already-imported groom (create_groom_binding()) and creates/wires
    WI_<groom_name>, with principal_asset set to the GroomBindingAsset
    (NOT the raw GroomAsset - see module docstring) and pipeline set to a
    MetaHumanDefaultGroomPipeline instance.

    Does NOT add the resulting Wardrobe Item to any character - that's a
    separate, per-character step
    (MetaHumanCharacter.internal_collection.try_add_item_from_wardrobe_item(
    slot_name=..., wardrobe_item=...), confirmed against
    Content/Python/test_set_character_grooms.py in MetaHumanCharacter) -
    slot_name here is only recorded in the returned message as a reminder
    of which slot this item is meant for.

    Returns (ok, message).
    """
    if slot_name not in GROOM_SLOT_NAMES:
        return False, f"'{slot_name}' isn't a known groom slot ({', '.join(GROOM_SLOT_NAMES)})."

    groom_asset_path = f"{config.groom_mesh_folder(groom_name)}/{groom_name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(groom_asset_path):
        return False, (
            f"No GroomAsset found at {groom_asset_path} - run "
            f"'Import Groom ABC...' for '{groom_name}' first."
        )
    groom_asset = unreal.load_asset(groom_asset_path)

    binding = create_groom_binding(groom_name, groom_asset)
    if binding is None:
        return False, "Groom binding creation failed - check the Output Log."

    wi_path = f"{config.groom_folder(groom_name)}/WI_{groom_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(wi_path):
        wi_asset = unreal.load_asset(wi_path)
        unreal.log(f"MetaBridge Forge: WI_{groom_name} already exists, re-wiring it.")
    else:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        wi_asset = asset_tools.create_asset(
            asset_name=f"WI_{groom_name}",
            package_path=config.groom_folder(groom_name),
            asset_class=unreal.MetaHumanWardrobeItem,
            factory=unreal.MetaHumanWardrobeItemFactory(),
        )
        if wi_asset is None:
            return False, f"Failed to create Wardrobe Item at {wi_path}."

    # See module docstring: a groom's principal_asset is the
    # GroomBindingAsset, not the raw GroomAsset.
    asset_ref = unreal.EditorOnlyAssetReference()
    asset_ref.set_editor_property("asset", binding)
    wi_asset.set_editor_property("principal_asset", asset_ref)
    actual = wi_asset.get_editor_property("principal_asset")
    if isinstance(actual, unreal.EditorOnlyAssetReference):
        actual = actual.get_editor_property("asset")
    if actual != binding:
        return False, (
            f"Created WI_{groom_name} but principal_asset did not stick "
            f"(read back: {actual!r}, expected: {binding.get_path_name()}). "
            f"This is a bug in groom.py, not something to retry - report "
            f"this back with the Output Log content."
        )

    if wi_asset.get_editor_property("pipeline") is None:
        pipeline = unreal.new_object(unreal.MetaHumanDefaultGroomPipeline, outer=wi_asset)
        wi_asset.set_editor_property("pipeline", pipeline)
        if wi_asset.get_editor_property("pipeline") is None:
            return False, (
                f"Created WI_{groom_name} and linked principal_asset, but "
                f"could not create/assign its pipeline "
                f"(MetaHumanDefaultGroomPipeline). This is a bug in "
                f"groom.py, not something to retry - report this back with "
                f"the Output Log content."
            )

    try:
        wi_asset.set_editor_property("thumbnail_name", unreal.Text(groom_name))
    except Exception as e:
        unreal.log_warning(f"MetaBridge Forge: could not set thumbnail_name: {e}")

    unreal.EditorAssetLibrary.save_loaded_asset(wi_asset)
    unreal.EditorAssetLibrary.save_loaded_asset(binding)

    unreal.log(
        f"MetaBridge Forge: WI_{groom_name} created and linked to "
        f"{binding.get_path_name()} (slot: {slot_name})"
    )
    return True, (
        f"WI_{groom_name} created and linked to {binding.get_path_name()}.\n\n"
        f"Slot: {slot_name} - not auto-assigned to any character. Add it "
        f"yourself via a MetaHumanCharacter's "
        f"internal_collection.try_add_item_from_wardrobe_item("
        f"slot_name='{slot_name}', wardrobe_item=wi_asset) when ready."
    )


def _default_groom_name_from_abc(abc_path: str) -> str:
    import os

    stem = os.path.splitext(os.path.basename(abc_path))[0]
    return "".join(c if (c.isalnum() or c == "_") else "_" for c in stem)


def run_import_groom_abc() -> None:
    """Entry point wired to the "Import Groom ABC..." menu action. Mirrors
    importer.run_import_outfit_fbx()'s one-shot style: only the native
    file picker shows up front, the groom name is auto-derived from the
    .abc filename (no name prompt), and success is silent (logged only) -
    a dialog only appears on failure."""
    abc_path = dialogs.pick_abc_file()
    if not abc_path:
        return

    groom_name = _default_groom_name_from_abc(abc_path)

    try:
        asset = import_groom_abc(abc_path, groom_name)
    except Exception as e:
        unreal.log_error(f"MetaBridge Forge: exception during groom import: {e}")
        dialogs.show_result(
            "MetaBridge Forge",
            f"Groom import failed for '{groom_name}':\n\n{e}\n\n"
            f"(Full traceback in the Output Log.)",
            is_error=True,
        )
        return

    if asset is None:
        dialogs.show_result(
            "MetaBridge Forge",
            f"Groom import failed for '{groom_name}'. Check the Output "
            f"Log (Window > Developer Tools > Output Log) for details.",
            is_error=True,
        )
        return

    # Binding + Wardrobe Item wiring (create_groom_binding /
    # finish_groom_setup) needs nothing beyond what's already on disk at
    # this point (the just-imported GroomAsset + the reference head cloned
    # into this groom's own GroomMesh/ folder), so a failure here is a
    # real error, not a "missing selection" situation - don't swallow it.
    try:
        ok, message = finish_groom_setup(groom_name)
    except Exception as e:
        unreal.log_error(f"MetaBridge Forge: exception during groom binding/wardrobe setup: {e}")
        dialogs.show_result(
            "MetaBridge Forge - Groom imported, binding failed",
            f"Imported: {asset.get_path_name()}\n\n"
            f"Binding/Wardrobe Item setup raised an exception:\n{e}\n\n"
            f"(Full traceback in the Output Log.) Run "
            f"mbforge.groom.finish_groom_setup('{groom_name}') from the "
            f"Python console to retry.",
            is_error=True,
        )
        return

    if not ok:
        dialogs.show_result(
            "MetaBridge Forge - Groom imported, binding failed",
            f"Imported: {asset.get_path_name()}\n\n"
            f"Binding/Wardrobe Item setup did not complete:\n{message}\n\n"
            f"Run mbforge.groom.finish_groom_setup('{groom_name}') from "
            f"the Python console to retry.",
            is_error=True,
        )
        return

    unreal.log(
        f"MetaBridge Forge: '{groom_name}' fully set up - {asset.get_path_name()}. "
        f"{message}"
    )
