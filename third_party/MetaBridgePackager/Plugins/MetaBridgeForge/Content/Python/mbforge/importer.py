"""One-shot Fab outfit prep: pick an FBX, everything else happens
automatically - no confirmation dialogs, no follow-up steps to run by
hand. Only a popup on failure.

Pipeline, all using config.OUTFIT_TEMPLATE_DEFAULT (BasicOutfit) as the
fixed reference body + OA_/CA_ template:
  1. Import the garment FBX as a Static Mesh (raw geometry only - no
     skeleton at this stage; matches the real BasicOutfit example,
     where the garment geometry is a plain static mesh, not skeletal)
     into Meshes/, and duplicate the template's reference body
     SkeletalMesh into the same folder (self-contained package, same
     reasoning as the rest of this plugin).
  2. Duplicate the template's OA_/CA_ (+ their own Dataflow graph
     copies) into the new outfit's folder, renamed
     (duplicate_build.duplicate_outfit_template - proven crash-free,
     see that module's docstring for why the factory-based alternative
     is NOT used).
  3. Retarget the duplicated CA_'s Dataflow mesh references and the
     duplicated OA_'s SizedOutfitSource at this outfit's own meshes
     instead of the template's (duplicate_build.retarget_duplicated_outfit
     - confirmed crash-free and correct end-to-end by hand before being
     wired in here; see that function's docstring and
     MBForgeOutfitDataflowLibrary.h/.cpp for the engine bugs it works
     around).
  4. Create/wire WI_, run verification (wardrobe.finish_outfit_setup).
"""
import unreal

from . import config, dialogs, duplicate_build, wardrobe


def _ensure_folders(outfit_name: str) -> None:
    lib = unreal.EditorAssetLibrary
    for folder in (
        config.outfit_folder(outfit_name),
        config.outfit_deps_folder(outfit_name),
        config.outfit_meshes_folder(outfit_name),
        f"{config.outfit_deps_folder(outfit_name)}/{config.MATERIALS_SUBDIR}",
        f"{config.outfit_deps_folder(outfit_name)}/{config.CLOTH_ASSETS_SUBDIR}",
    ):
        if not lib.does_directory_exist(folder):
            lib.make_directory(folder)


def _find_skeletal_mesh_in_folder(folder: str) -> "unreal.SkeletalMesh | None":
    for listing in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
        obj = unreal.load_asset(listing.split(".")[0])
        if isinstance(obj, unreal.SkeletalMesh):
            return obj
    return None


def import_outfit_fbx(
    fbx_path: str, outfit_name: str, reference_body: "unreal.SkeletalMesh"
) -> "unreal.StaticMesh | None":
    """Imports fbx_path as a Static Mesh under
    /Game/Outfits/<outfit_name>/<outfit_name>/Meshes/, and duplicates
    `reference_body` into the same folder. Returns the imported
    StaticMesh, or None if the import failed (errors logged via
    unreal.log_error).
    """
    _ensure_folders(outfit_name)

    dest_folder = config.outfit_meshes_folder(outfit_name)
    dest_name = config.garment_mesh_name(outfit_name)

    local_body_path = f"{dest_folder}/{reference_body.get_name()}"
    if unreal.EditorAssetLibrary.does_asset_exist(local_body_path):
        local_body = unreal.load_asset(local_body_path)
    else:
        local_body = unreal.EditorAssetLibrary.duplicate_asset(
            reference_body.get_path_name(), local_body_path
        )
    if local_body is None:
        unreal.log_error(
            f"MetaBridge Forge: failed to duplicate reference body "
            f"{reference_body.get_path_name()} into {local_body_path}."
        )
        return None
    unreal.EditorAssetLibrary.save_loaded_asset(local_body)

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = True
    options.import_textures = True
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH

    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = dest_folder
    task.destination_name = dest_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = list(task.imported_object_paths)
    if not imported_paths:
        unreal.log_error(
            f"MetaBridge Forge: import produced no assets for {fbx_path} "
            f"- check the Output Log for the FBX importer's own errors."
        )
        return None

    mesh = None
    for p in imported_paths:
        obj = unreal.load_asset(p)
        if isinstance(obj, unreal.StaticMesh):
            mesh = obj
            break

    if mesh is None:
        kinds = ", ".join(type(unreal.load_asset(p)).__name__ for p in imported_paths)
        unreal.log_error(
            f"MetaBridge Forge: import of {fbx_path} produced no Static "
            f"Mesh (got: {kinds})."
        )
        return None

    unreal.log(
        f"MetaBridge Forge: imported {mesh.get_path_name()} (garment "
        f"geometry) + reference body {local_body.get_path_name()}"
    )
    return mesh


def _default_outfit_name_from_fbx(fbx_path: str) -> str:
    import os

    stem = os.path.splitext(os.path.basename(fbx_path))[0]
    safe = "".join(c if (c.isalnum() or c == "_") else "_" for c in stem)
    return safe


def run_import_outfit_fbx() -> None:
    """Entry point wired to the "Import Outfit FBX..." menu action - the
    only step in the whole plugin that shows any UI, and only the native
    file picker. No name prompt, no confirmations, no follow-up
    instructions. Only pops a message box if something failed."""
    fbx_path = dialogs.pick_fbx_file()
    if not fbx_path:
        return

    outfit_name = _default_outfit_name_from_fbx(fbx_path)
    template_name = config.OUTFIT_TEMPLATE_DEFAULT

    try:
        # Template source resolves project-first with a plugin-bundled
        # fallback (see config.template_outfit_meshes_folder).
        template_meshes = config.template_outfit_meshes_folder(template_name)
        reference_body = _find_skeletal_mesh_in_folder(template_meshes)
        if reference_body is None:
            raise RuntimeError(
                f"No reference body Skeletal Mesh found in "
                f"{template_meshes} (template outfit: '{template_name}') "
                f"- check config.OUTFIT_TEMPLATE_DEFAULT, and that the "
                f"plugin's bundled Templates content is present."
            )

        mesh = import_outfit_fbx(fbx_path, outfit_name, reference_body)
        if mesh is None:
            raise RuntimeError(
                "Garment import failed - check the Output Log "
                "(Window > Developer Tools > Output Log)."
            )

        oa = duplicate_build.duplicate_outfit_template(template_name, outfit_name)
        if oa is None:
            raise RuntimeError(
                "OA_/CA_ template duplication failed - check the Output Log."
            )

        local_body = _find_skeletal_mesh_in_folder(config.outfit_meshes_folder(outfit_name))
        if local_body is None:
            raise RuntimeError(
                f"No SkeletalMesh found in {config.outfit_meshes_folder(outfit_name)} "
                f"to retarget against - import_outfit_fbx() should have "
                f"duplicated the reference body there."
            )

        if not duplicate_build.retarget_duplicated_outfit(outfit_name, mesh, local_body):
            raise RuntimeError(
                "Mesh/SizedOutfitSource retargeting failed - check the "
                "Output Log."
            )

        ok, message = wardrobe.finish_outfit_setup(outfit_name)
        if not ok:
            raise RuntimeError(message)
    except Exception as e:
        unreal.log_error(f"MetaBridge Forge: full-auto import failed for '{outfit_name}': {e}")
        dialogs.show_result("MetaBridge Forge - Failed", str(e), is_error=True)
        return

    unreal.log(f"MetaBridge Forge: '{outfit_name}' fully set up - {oa.get_path_name()}.")
