"""Project-specific constants + template path resolution for MetaBridge
Forge.

Templates are resolved with a project-first fallback: if the project has
its own template (e.g. /Game/Outfits/BasicOutfit with a real OA_ in it),
that wins; otherwise the copy bundled inside this plugin's own Content
folder (/MetaBridgeForge/Templates/...) is used. This is what lets the
plugin work out-of-the-box in a fresh project that has no template
content of its own - see template_outfit_folder() /
resolve_groom_template_folder() below.

Note: this module imports unreal (for the existence checks in the
resolvers), so it can only be imported inside the Unreal editor's
embedded Python - same as every other module in this package.
"""
import unreal

# Root folder Fab-ready outfits live under. Matches Project Settings >
# MetaHuman Packaging Paths by default - change this if that setting has
# been changed for this project.
OUTFITS_ROOT = "/Game/Outfits"

# Where the plugin's own bundled template content lives (this plugin has
# CanContainContent=true, so anything under Plugins/MetaBridgeForge/
# Content/Templates/ mounts at this path in the editor).
PLUGIN_TEMPLATES_ROOT = "/MetaBridgeForge/Templates"

# Default suggestion for duplicate_build.py's "which existing outfit to
# clone" prompt. Pick any outfit that already has a working OA_/CA_.
OUTFIT_TEMPLATE_DEFAULT = "BasicOutfit"

# Naming pattern applied to the imported garment STATIC mesh (garment
# geometry only - no skeleton/skinning at this stage, see importer.py's
# module docstring). Matches the real BasicOutfit example, where the
# garment geometry is a plain static mesh named after the outfit itself
# ("BasicOutfit"), no prefix.
GARMENT_MESH_NAME_PATTERN = "{name}"

# Subfolder layout under OUTFITS_ROOT/<name>/<name>/, matching the real
# BasicOutfit example inspected in-editor.
MESHES_SUBDIR = "Meshes"
MATERIALS_SUBDIR = "Materials"
CLOTH_ASSETS_SUBDIR = "ClothAssets"


def outfit_folder(outfit_name: str) -> str:
    """Top-level folder for one outfit, e.g. /Game/Outfits/BasicOutfit."""
    return f"{OUTFITS_ROOT}/{outfit_name}"


def outfit_deps_folder(outfit_name: str) -> str:
    """Dependencies folder, e.g. /Game/Outfits/BasicOutfit/BasicOutfit."""
    return f"{outfit_folder(outfit_name)}/{outfit_name}"


def outfit_meshes_folder(outfit_name: str) -> str:
    return f"{outfit_deps_folder(outfit_name)}/{MESHES_SUBDIR}"


def outfit_asset_path(outfit_name: str) -> str:
    """Full package path to the OA_<name> Outfit Asset."""
    return f"{outfit_folder(outfit_name)}/OA_{outfit_name}"


def wardrobe_item_path(outfit_name: str) -> str:
    """Full package path to the WI_<name> Wardrobe Item."""
    return f"{outfit_folder(outfit_name)}/WI_{outfit_name}"


def garment_mesh_name(outfit_name: str) -> str:
    return GARMENT_MESH_NAME_PATTERN.format(name=outfit_name)


# ── Template resolution (project-first, plugin fallback) ─────────────────

def _package_asset_datas(package_path: str):
    """Asset registry lookup that stays SILENT when the package doesn't
    exist - unlike EditorAssetLibrary.find_asset_data, which logs a red
    "FindAssetData failed" error line for a plain miss (and a miss is the
    normal, expected case here whenever the project has no template
    override and the plugin-bundled copy should be used instead). Uses
    get_assets_by_package_name because this engine build's Python binding
    of get_asset_by_object_path is the deprecated Name-based overload
    that rejects SoftObjectPath arguments outright."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    return registry.get_assets_by_package_name(package_path) or []


def _is_real_asset(asset_path: str) -> bool:
    """True if asset_path (package path, e.g. /Game/X/OA_X) is an actual
    asset - NOT a redirector left behind by moving the templates into the
    plugin (a redirector would make does_asset_exist() return True,
    silently routing the pipeline through stale paths)."""
    for data in _package_asset_datas(asset_path):
        if str(data.asset_class_path.asset_name) != "ObjectRedirector":
            return True
    return False


def _dir_has_real_assets(folder: str) -> bool:
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        return False
    for listing in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
        if _is_real_asset(listing.split(".")[0]):
            return True
    return False


def template_outfit_folder(template_name: str) -> str:
    """Source folder to clone the outfit template FROM. The project's own
    copy (/Game/Outfits/<name>, containing a real OA_<name>) wins if it
    exists; otherwise falls back to the plugin's bundled copy."""
    project = f"{OUTFITS_ROOT}/{template_name}"
    if _is_real_asset(f"{project}/OA_{template_name}"):
        return project
    return f"{PLUGIN_TEMPLATES_ROOT}/Outfits/{template_name}"


def template_outfit_asset_path(template_name: str) -> str:
    return f"{template_outfit_folder(template_name)}/OA_{template_name}"


def template_outfit_deps_folder(template_name: str) -> str:
    return f"{template_outfit_folder(template_name)}/{template_name}"


def template_outfit_meshes_folder(template_name: str) -> str:
    return f"{template_outfit_deps_folder(template_name)}/{MESHES_SUBDIR}"


# ── Grooms ───────────────────────────────────────────────────────────────

GROOMS_ROOT = "/Game/Grooms"
GROOM_MESH_SUBDIR = "GroomMesh"

# Every existing groom folder in this project has identically-named files
# in its GroomMesh/ (e.g. SK_MH_Groom_Head) and Materials/ subfolders -
# unlike Outfits' per-character body, grooms all share the same head
# reference, so a fixed template folder to clone from (rather than a
# per-import Content Browser selection) is enough. Point this at any one
# existing /Game/Grooms/<Name>/<Name> folder. If it doesn't exist (or
# only holds redirectors), the plugin's bundled copy is used instead -
# see resolve_groom_template_folder().
GROOM_TEMPLATE_FOLDER = "/Game/Grooms/Beard_A/Beard_A"
PLUGIN_GROOM_TEMPLATE_FOLDER = f"{PLUGIN_TEMPLATES_ROOT}/Grooms/Beard_A/Beard_A"


def resolve_groom_template_folder() -> str:
    """Source folder to clone GroomMesh/Materials FROM. The project's own
    GROOM_TEMPLATE_FOLDER wins if it actually contains real assets;
    otherwise falls back to the plugin's bundled copy."""
    if _dir_has_real_assets(GROOM_TEMPLATE_FOLDER):
        return GROOM_TEMPLATE_FOLDER
    return PLUGIN_GROOM_TEMPLATE_FOLDER


def groom_folder(groom_name: str) -> str:
    """Top-level folder for one groom, e.g. /Game/Grooms/MyGroom."""
    return f"{GROOMS_ROOT}/{groom_name}"


def groom_deps_folder(groom_name: str) -> str:
    """Dependencies folder, e.g. /Game/Grooms/MyGroom/MyGroom."""
    return f"{groom_folder(groom_name)}/{groom_name}"


def groom_mesh_folder(groom_name: str) -> str:
    return f"{groom_deps_folder(groom_name)}/{GROOM_MESH_SUBDIR}"


def groom_materials_folder(groom_name: str) -> str:
    return f"{groom_deps_folder(groom_name)}/{MATERIALS_SUBDIR}"
