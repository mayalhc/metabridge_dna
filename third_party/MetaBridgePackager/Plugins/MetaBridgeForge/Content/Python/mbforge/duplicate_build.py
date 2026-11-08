"""Safe CA_/OA_ creation by duplicating an existing, known-good outfit as
a template - the crash-free alternative to dataflow_build.py's
build_cloth_asset()/build_outfit_asset() (which pop an interactive
ChaosClothAssetFactory dialog that crashes the engine when driven from
Python - see dataflow_build.py's module docstring).

Every operation here is unreal.EditorAssetLibrary.duplicate_asset() +
get_editor_property()/set_editor_property() - the same pattern already
proven safe everywhere else in this plugin (skeleton/body-mesh
duplication in importer.py, GroomMesh/Materials cloning in groom.py).
No factory is ever called, so this cannot hit the same crash.

Scope: duplicates OA_<template> and every CA_ under its ClothAssets/
folder (plus each one's own backing Dataflow graph, so editing a copy
never affects the template) into /Game/Outfits/<new_outfit_name>/,
renamed to match. The duplicated CA_'s two mesh references (garment
static mesh, reference body skeletal mesh), and the duplicated OA_'s
SizedOutfitSource (which still points at the TEMPLATE's original CA_,
not the new one), still need retargeting after this function returns -
this function does NOT attempt it, by design (it's a separate,
independently-useful "clone as-is" primitive, also used as-is by the
"Duplicate Outfit Template..." menu action for manual editing
afterward). See retarget_duplicated_outfit() for the automated fix,
used by importer.run_import_outfit_fbx()'s one-shot pipeline - proven
crash-free and correct end-to-end by hand before being wired in (see
that function's docstring, and MBForgeOutfitDataflowLibrary.h/.cpp's
comments, for the real engine bugs worked around along the way: the
built-in SetDataflowNodeProperty's missing cache invalidation, and a
confirmed HairStrandsCore crash - unrelated to this outfit code, but
the same root cause class - from firing PostEditChangeProperty once
per property instead of once after all properties are set; see
groom.py's module docstring for that one).
"""
import unreal

from . import config, dialogs


def _dup(src_path: str, dst_path: str):
    """Duplicates src_path to dst_path, unconditionally overwriting
    anything already there (deletes the old asset first) - always a
    fresh copy from the template, since this is meant to be re-run
    repeatedly during testing without manual cleanup between runs."""
    lib = unreal.EditorAssetLibrary
    if lib.does_asset_exist(dst_path):
        lib.delete_asset(dst_path)
    new_asset = lib.duplicate_asset(src_path, dst_path)
    if new_asset is not None:
        lib.save_loaded_asset(new_asset)
    return new_asset


def _renamed(name: str, template_name: str, new_name: str) -> str:
    """CA_ names sometimes carry a size suffix (CA_BasicOutfit_Bof2) - a
    substring replace handles that and the plain OA_/DF_ cases alike."""
    return name.replace(template_name, new_name) if template_name in name else name


def _duplicate_with_own_dataflow(src_asset, dst_path: str, template_name: str, new_name: str):
    """Duplicates src_asset to dst_path, then ALSO duplicates whatever
    Dataflow graph its dataflow_instance points at and re-points the
    duplicate at that copy - so later edits (manual or scripted) to one
    outfit's graph never bleed into another outfit sharing the same
    template. Returns the new asset, or None on failure."""
    new_asset = _dup(src_asset.get_path_name(), dst_path)
    if new_asset is None:
        return None

    src_instance = src_asset.get_editor_property("dataflow_instance")
    src_dataflow = src_instance.get_editor_property("dataflow_asset")
    if src_dataflow is None:
        return new_asset  # nothing to re-point, plain duplicate is enough

    dst_folder = dst_path.rsplit("/", 1)[0]
    new_dataflow_name = _renamed(src_dataflow.get_name(), template_name, new_name)
    new_dataflow = _dup(src_dataflow.get_path_name(), f"{dst_folder}/{new_dataflow_name}")
    if new_dataflow is None:
        unreal.log_warning(
            f"MetaBridge Forge: duplicated {new_asset.get_path_name()} but "
            f"could not duplicate its Dataflow graph {src_dataflow.get_path_name()} "
            f"- it still shares the TEMPLATE's graph. Don't edit it, or the "
            f"template outfit will change too."
        )
        return new_asset

    new_instance = new_asset.get_editor_property("dataflow_instance")
    new_instance.set_editor_property("dataflow_asset", new_dataflow)
    new_asset.set_editor_property("dataflow_instance", new_instance)
    unreal.EditorAssetLibrary.save_loaded_asset(new_asset)
    return new_asset


def duplicate_outfit_template(template_outfit_name: str, new_outfit_name: str):
    """Duplicates OA_<template_outfit_name> and its CA_(s) - each with
    its own independent copy of its backing Dataflow graph - into
    /Game/Outfits/<new_outfit_name>/. Returns the new OA_ asset, or None
    on failure (errors logged via unreal.log_error).

    Mesh references inside the duplicated CA_ still point at the
    template's original meshes - this is a known, deliberate limitation
    (see module docstring). Swap them by hand afterward.
    """
    # Template source paths resolve project-first with a plugin-bundled
    # fallback (see config.template_outfit_folder) - so this works even in
    # a fresh project that has no /Game/Outfits/<template>/ of its own.
    src_folder = config.template_outfit_folder(template_outfit_name)
    dst_folder = config.outfit_folder(new_outfit_name)

    if not unreal.EditorAssetLibrary.does_directory_exist(src_folder):
        unreal.log_error(
            f"MetaBridge Forge: template folder {src_folder} not found "
            f"(checked the project first, then the plugin's bundled "
            f"Templates content)."
        )
        return None
    # No "already exists" guard: this always overwrites (see _dup) so the
    # one-shot pipeline can be re-run freely during testing without manual
    # cleanup - dst_folder existing already is also expected regardless,
    # since importer.py's garment import creates it moments earlier in
    # the same run.

    src_oa_path = config.template_outfit_asset_path(template_outfit_name)
    if not unreal.EditorAssetLibrary.does_asset_exist(src_oa_path):
        unreal.log_error(f"MetaBridge Forge: template OA_ not found at {src_oa_path}.")
        return None
    src_oa = unreal.load_asset(src_oa_path)

    if not unreal.EditorAssetLibrary.does_directory_exist(dst_folder):
        unreal.EditorAssetLibrary.make_directory(dst_folder)

    new_oa = _duplicate_with_own_dataflow(
        src_oa, config.outfit_asset_path(new_outfit_name),
        template_outfit_name, new_outfit_name,
    )
    if new_oa is None:
        unreal.log_error(f"MetaBridge Forge: failed to duplicate {src_oa_path}.")
        return None

    src_ca_folder = f"{config.template_outfit_deps_folder(template_outfit_name)}/{config.CLOTH_ASSETS_SUBDIR}"
    new_ca_folder = f"{config.outfit_deps_folder(new_outfit_name)}/{config.CLOTH_ASSETS_SUBDIR}"
    if not unreal.EditorAssetLibrary.does_directory_exist(new_ca_folder):
        unreal.EditorAssetLibrary.make_directory(new_ca_folder)

    new_ca_count = 0
    for src_ca_listing in unreal.EditorAssetLibrary.list_assets(
        src_ca_folder, recursive=False, include_folder=False
    ):
        src_ca_path = src_ca_listing.split(".")[0]
        src_ca = unreal.load_asset(src_ca_path)
        if not isinstance(src_ca, unreal.ChaosClothAsset):
            # ClothAssets/ also holds each CA_'s own backing Dataflow
            # graph as a sibling asset - _duplicate_with_own_dataflow
            # already handles duplicating that when it processes the
            # actual CA_, so skip it here rather than trying (and failing:
            # a Dataflow asset has no dataflow_instance property of its
            # own) to treat it as a CA_ in its own right.
            continue
        ca_name = _renamed(src_ca_path.split("/")[-1], template_outfit_name, new_outfit_name)
        new_ca = _duplicate_with_own_dataflow(
            src_ca, f"{new_ca_folder}/{ca_name}", template_outfit_name, new_outfit_name
        )
        if new_ca is not None:
            new_ca_count += 1
        else:
            unreal.log_error(f"MetaBridge Forge: failed to duplicate {src_ca_path}.")

    unreal.log(
        f"MetaBridge Forge: duplicated template '{template_outfit_name}' -> "
        f"'{new_outfit_name}': {new_oa.get_path_name()} + {new_ca_count} "
        f"ClothAsset(s). Mesh references still point at the TEMPLATE's "
        f"original meshes - open the new CA_ in the Chaos Cloth Asset "
        f"Editor and swap the Static Mesh / Skeletal Mesh fields to this "
        f"outfit's own meshes in {config.outfit_meshes_folder(new_outfit_name)}."
    )
    return new_oa


def run_duplicate_outfit_template() -> None:
    """Entry point wired to the "Duplicate Outfit Template..." menu
    action. Asks which existing outfit to use as a template and what to
    name the new one."""
    template_name = dialogs.ask_outfit_name(
        config.OUTFIT_TEMPLATE_DEFAULT, label="Template Outfit (existing)"
    )
    if not template_name:
        return

    new_name = dialogs.ask_outfit_name(label="New Outfit")
    if not new_name:
        return

    try:
        oa = duplicate_outfit_template(template_name, new_name)
    except Exception as e:
        unreal.log_error(f"MetaBridge Forge: exception during template duplication: {e}")
        dialogs.show_result(
            "MetaBridge Forge",
            f"Duplication failed:\n\n{e}\n\n(Full traceback in the Output Log.)",
            is_error=True,
        )
        return

    if oa is None:
        dialogs.show_result(
            "MetaBridge Forge",
            f"Duplication failed. Check the Output Log "
            f"(Window > Developer Tools > Output Log) for details.",
            is_error=True,
        )
        return

    dialogs.show_result(
        "MetaBridge Forge - Template duplicated",
        f"Created: {oa.get_path_name()}\n\n"
        f"Mesh references still point at '{template_name}''s original "
        f"meshes. Open the new CA_ in the Chaos Cloth Asset Editor and "
        f"swap the Static Mesh / Skeletal Mesh fields to this outfit's "
        f"own meshes in {config.outfit_meshes_folder(new_name)}.\n\n"
        f"Once that's done, run 'Finish Outfit Setup...' as usual.",
    )


# ── Mesh retargeting ─────────────────────────────────────────────────────
#
# Confirmed crash-free and correct end-to-end by hand (against the real
# test_jeketK CA_/OA_ in this project, including a re-run after an
# unrelated engine crash to rule out stale-cache false positives) before
# being wired into importer.run_import_outfit_fbx() below via
# retarget_duplicated_outfit(). NOT called by duplicate_outfit_template()
# itself or by the "Duplicate Outfit Template..." menu action - that one
# stays a plain "clone as-is" primitive for manual template duplication,
# on purpose (see duplicate_outfit_template()'s docstring).

_CA_STATIC_MESH_NODE = "StaticMeshImport"
_CA_STATIC_MESH_PROPERTY = "StaticMesh"
_CA_SKELETAL_MESH_NODE = "TransferSkinWeights"
_CA_SKELETAL_MESH_PROPERTY = "SkeletalMesh"
_OA_SIZED_OUTFIT_SOURCE_VARIABLE = "SizedOutfitSource"


def retarget_cloth_asset_meshes(
    ca_asset: "unreal.ChaosClothAsset",
    garment_mesh: "unreal.StaticMesh",
    body_mesh: "unreal.SkeletalMesh",
) -> bool:
    """Points ca_asset's own (already-duplicated, private) Dataflow graph
    at garment_mesh/body_mesh instead of whatever mesh the template it was
    copied from was using - the piece duplicate_outfit_template()
    deliberately leaves undone.

    Uses unreal.MBForgeOutfitDataflowLibrary.set_dataflow_node_object_property()
    (MetaBridgeForge's own C++ module, Source/MetaBridgeForge/...
    /MBForgeOutfitDataflowLibrary.h) rather than the engine's built-in
    unreal.DataflowEditorBlueprintLibrary.set_dataflow_node_property(): the
    built-in one does write the property into the node's live memory
    correctly, but never calls the node's Invalidate(), so its cached
    output stays stale and a following regenerate_asset_from_dataflow()
    silently keeps using the OLD mesh. Confirmed against the engine source
    (Dataflow/Source/DataflowEditor/.../DataflowEditorBlueprintLibrary.cpp)
    - not something hit by testing.

    Returns True on success (errors logged via unreal.log_error).
    """
    instance = ca_asset.get_editor_property("dataflow_instance")
    dataflow_asset = instance.get_editor_property("dataflow_asset")
    if dataflow_asset is None:
        unreal.log_error(
            f"MetaBridge Forge: {ca_asset.get_path_name()} has no Dataflow "
            f"asset assigned - can't retarget its meshes."
        )
        return False

    lib = unreal.MBForgeOutfitDataflowLibrary
    ok = lib.set_dataflow_node_object_property(
        dataflow_asset, _CA_STATIC_MESH_NODE, _CA_STATIC_MESH_PROPERTY, garment_mesh
    )
    ok = ok and lib.set_dataflow_node_object_property(
        dataflow_asset, _CA_SKELETAL_MESH_NODE, _CA_SKELETAL_MESH_PROPERTY, body_mesh
    )
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: failed to retarget meshes on "
            f"{dataflow_asset.get_path_name()} - node names "
            f"('{_CA_STATIC_MESH_NODE}' / '{_CA_SKELETAL_MESH_NODE}') may not "
            f"match this CA_'s actual graph (only confirmed against the "
            f"BasicOutfit-derived template captured in dataflow_build.py). "
            f"Check the Output Log."
        )
        return False

    ok = unreal.DataflowBlueprintLibrary.regenerate_asset_from_dataflow(ca_asset)
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: regenerate_asset_from_dataflow failed for "
            f"{ca_asset.get_path_name()} after mesh retarget."
        )
        return False

    unreal.EditorAssetLibrary.save_loaded_asset(ca_asset)
    unreal.EditorAssetLibrary.save_loaded_asset(dataflow_asset)
    unreal.log(f"MetaBridge Forge: retargeted meshes on {ca_asset.get_path_name()}")
    return True


def retarget_outfit_source(
    oa_asset: "unreal.ChaosOutfitAsset",
    ca_asset: "unreal.ChaosClothAsset",
    body_mesh: "unreal.SkeletalMesh",
) -> bool:
    """Repoints oa_asset's SizedOutfitSource Dataflow variable at ca_asset
    (SourceAsset) and body_mesh (SourceBodyParts) - the piece
    duplicate_outfit_template() deliberately leaves undone: the
    duplicated OA_'s SizedOutfitSource still references the TEMPLATE's
    original CA_, not the new one duplicated alongside it.

    Uses unreal.MBForgeOutfitDataflowLibrary.replace_sized_outfit_source_asset()
    rather than unreal.DataflowBlueprintLibrary.override_dataflow_variable_object_array()
    - see dataflow_build.py's module docstring for why that one doesn't
    work (SizedOutfitSource is a struct array, not an object array).

    Returns True on success (errors logged via unreal.log_error).
    """
    ok = unreal.MBForgeOutfitDataflowLibrary.replace_sized_outfit_source_asset(
        oa_asset, _OA_SIZED_OUTFIT_SOURCE_VARIABLE, ca_asset, body_mesh
    )
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: replace_sized_outfit_source_asset failed "
            f"for {oa_asset.get_path_name()} -> {ca_asset.get_path_name()} "
            f"- check the Output Log."
        )
        return False

    ok = unreal.DataflowBlueprintLibrary.regenerate_asset_from_dataflow(oa_asset)
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: regenerate_asset_from_dataflow failed for "
            f"{oa_asset.get_path_name()} after SizedOutfitSource retarget."
        )
        return False

    unreal.EditorAssetLibrary.save_loaded_asset(oa_asset)
    unreal.log(
        f"MetaBridge Forge: retargeted {oa_asset.get_path_name()} -> "
        f"{ca_asset.get_path_name()}"
    )
    return True


def retarget_duplicated_outfit(
    outfit_name: str,
    garment_mesh: "unreal.StaticMesh",
    body_mesh: "unreal.SkeletalMesh",
) -> bool:
    """Full fix for what duplicate_outfit_template() deliberately leaves
    undone, run right after it for outfit_name:
      1. retarget_cloth_asset_meshes() - rewires the duplicated CA_'s own
         Dataflow graph (StaticMeshImport/TransferSkinWeights nodes) to
         garment_mesh/body_mesh.
      2. retarget_outfit_source() - repoints the duplicated OA_'s
         SizedOutfitSource at that same (now correctly retargeted) CA_
         and body_mesh.

    Expects exactly one ChaosClothAsset under
    <outfit_deps_folder(outfit_name)>/ClothAssets/ - the one-shot
    FBX-import pipeline (importer.run_import_outfit_fbx) only ever
    produces one per outfit. Errors out rather than guessing which CA_
    to retarget if there are zero or several - use
    retarget_cloth_asset_meshes()/retarget_outfit_source() directly for
    those cases.

    Returns True on success (errors logged via unreal.log_error).
    """
    ca_folder = f"{config.outfit_deps_folder(outfit_name)}/{config.CLOTH_ASSETS_SUBDIR}"
    ca_assets = [
        obj
        for p in unreal.EditorAssetLibrary.list_assets(ca_folder, recursive=False, include_folder=False)
        for obj in [unreal.load_asset(p.split(".")[0])]
        if isinstance(obj, unreal.ChaosClothAsset)
    ]
    if len(ca_assets) != 1:
        unreal.log_error(
            f"MetaBridge Forge: expected exactly 1 ChaosClothAsset under "
            f"{ca_folder}, found {len(ca_assets)} - can't auto-retarget "
            f"'{outfit_name}'. Use retarget_cloth_asset_meshes()/"
            f"retarget_outfit_source() directly, or swap meshes by hand "
            f"in the Chaos Cloth Asset Editor."
        )
        return False
    ca_asset = ca_assets[0]

    if not retarget_cloth_asset_meshes(ca_asset, garment_mesh, body_mesh):
        return False

    oa_path = config.outfit_asset_path(outfit_name)
    if not unreal.EditorAssetLibrary.does_asset_exist(oa_path):
        unreal.log_error(f"MetaBridge Forge: no OA_ found at {oa_path}.")
        return False
    oa_asset = unreal.load_asset(oa_path)

    return retarget_outfit_source(oa_asset, ca_asset, body_mesh)
