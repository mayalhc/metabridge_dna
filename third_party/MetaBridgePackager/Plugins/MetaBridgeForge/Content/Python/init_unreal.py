"""Auto-executed by UE's PythonScriptPlugin on editor startup for every
enabled plugin's Content/Python folder. Registers MetaBridge Forge's menu
actions under Tools > MetaBridge Forge in the main editor toolbar.

Kept deliberately small: "Import Outfit FBX..." is the one-shot pipeline
(import -> duplicate OA_/CA_ template -> WI_ + verify, see importer.py's
module docstring) with no intermediate steps to run by hand, and
"Import Groom ABC..." is the separate groom workflow. The old
"Finish Outfit Setup..." / "Duplicate Outfit Template..." entries were
folded into the one-shot flow rather than staying as separate menu
items - their underlying functions (wardrobe.finish_outfit_setup,
duplicate_build.duplicate_outfit_template) are still directly callable
from the Python console if you ever need to re-run just one piece.
"""
import unreal

_MENU_OWNER = "MetaBridgeForge"


def _make_entry(name: str, label: str, tooltip: str, module: str, func: str) -> "unreal.ToolMenuEntry":
    entry = unreal.ToolMenuEntry(
        name=name,
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    entry.set_label(label)
    entry.set_tool_tip(tooltip)
    entry.set_string_command(
        unreal.ToolMenuStringCommandType.PYTHON,
        "",
        string=f"import {module}; {module}.{func}()",
    )
    return entry


def _register_menus() -> None:
    menus = unreal.ToolMenus.get()

    tools_menu = menus.find_menu("LevelEditor.MainMenu.Tools")
    if tools_menu is None:
        unreal.log_error(
            "MetaBridge Forge: could not find LevelEditor.MainMenu.Tools - "
            "menu registration skipped. Run mbforge.importer.run_import_outfit_fbx() "
            "directly from the Python console instead."
        )
        return

    sub_menu = tools_menu.add_sub_menu(
        owner=_MENU_OWNER,
        section_name="",
        name="MetaBridgeForge",
        label="MetaBridge Forge",
        tool_tip="Fab outfit prep automation",
    )

    sub_menu.add_menu_entry(
        _MENU_OWNER,
        _make_entry(
            "ImportOutfitFbx",
            "Import Outfit FBX...",
            "Full pipeline in one shot: import the garment, duplicate the "
            "OA_/CA_ template, create the Wardrobe Item, and verify. No "
            "further steps to run by hand.",
            "mbforge.importer",
            "run_import_outfit_fbx",
        ),
    )
    sub_menu.add_menu_entry(
        _MENU_OWNER,
        _make_entry(
            "ImportGroomAbc",
            "Import Groom ABC...",
            "Set up /Game/Grooms/<name>/, clone the GroomMesh/Materials "
            "template files, import a groom Alembic (.abc), bind it to "
            "the reference head, and create its Wardrobe Item. No further "
            "steps to run by hand.",
            "mbforge.groom",
            "run_import_groom_abc",
        ),
    )

    menus.refresh_all_widgets()
    unreal.log("MetaBridge Forge: menu registered under Tools > MetaBridge Forge")


_register_menus()
