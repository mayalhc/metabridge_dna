"""Step 2: create the WI_<name> Wardrobe Item for an already hand-built
OA_<name> Outfit Asset, wire it up, and run verification.
"""
import unreal

from . import config, dialogs, verify


def finish_outfit_setup(outfit_name: str) -> tuple[bool, str]:
    """Returns (ok, message)."""
    oa_path = config.outfit_asset_path(outfit_name)
    if not unreal.EditorAssetLibrary.does_asset_exist(oa_path):
        return False, (
            f"No Outfit Asset found at {oa_path}.\n\n"
            f"Build OA_{outfit_name} first using Epic's Outfit Asset "
            f"creation wizard (Step 1's Skeletal Mesh import should already "
            f"be sitting in {config.outfit_meshes_folder(outfit_name)}), "
            f"then run 'Finish Outfit Setup...' again."
        )

    oa_asset = unreal.load_asset(oa_path)
    if oa_asset is None:
        return False, f"Found {oa_path} but could not load it."

    wi_path = config.wardrobe_item_path(outfit_name)
    if unreal.EditorAssetLibrary.does_asset_exist(wi_path):
        wi_asset = unreal.load_asset(wi_path)
        unreal.log(f"MetaBridge Forge: WI_{outfit_name} already exists, re-wiring it.")
    else:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        wi_asset = asset_tools.create_asset(
            asset_name=f"WI_{outfit_name}",
            package_path=config.outfit_folder(outfit_name),
            asset_class=unreal.MetaHumanWardrobeItem,
            factory=unreal.MetaHumanWardrobeItemFactory(),
        )
        if wi_asset is None:
            return False, f"Failed to create Wardrobe Item at {wi_path}."

    # principal_asset looks like a plain Object property in the docs, but
    # is actually an EditorOnlyAssetReference struct (a TSoftObjectPtr
    # wrapper) - passing the OA_ object directly raises "Cannot nativize
    # ChaosOutfitAsset as EditorOnlyAssetReference". Wrap it - construct
    # empty then set the field (the struct's own __init__ doesn't take
    # constructor kwargs, unlike most other UE Python structs).
    asset_ref = unreal.EditorOnlyAssetReference()
    asset_ref.set_editor_property("asset", oa_asset)
    wi_asset.set_editor_property("principal_asset", asset_ref)
    # Read the property straight back rather than assuming the set() call
    # stuck - a silent no-op here (wrong property name/type mismatch that
    # doesn't raise) would otherwise only surface as "the WI_ file exists
    # but nothing is wired up" with no clue why.
    actual = wi_asset.get_editor_property("principal_asset")
    # get_editor_property() has been observed to sometimes return the raw
    # referenced Object directly (WI_BasicOutfit, already-loaded/legacy
    # data) and sometimes the EditorOnlyAssetReference struct itself
    # (freshly created here) - unwrap defensively instead of assuming one
    # shape.
    if isinstance(actual, unreal.EditorOnlyAssetReference):
        actual = actual.get_editor_property("asset")
    if actual != oa_asset:
        return False, (
            f"Created WI_{outfit_name} but principal_asset did not stick "
            f"(read back: {actual!r}, expected: {oa_asset.get_path_name()}). "
            f"This is a bug in wardrobe.py, not something to retry - report "
            f"this back with the Output Log content."
        )

    # pipeline (MetaHumanItemPipeline) isn't auto-created by the factory
    # for an asset made via a raw create_asset() call, unlike the real
    # WI_BasicOutfit example (whose pipeline subobject was presumably
    # created by whatever editor-UI path made it). Create one and parent
    # it to the Wardrobe Item if it's missing.
    if wi_asset.get_editor_property("pipeline") is None:
        pipeline = unreal.new_object(unreal.MetaHumanOutfitPipeline, outer=wi_asset)
        wi_asset.set_editor_property("pipeline", pipeline)
        if wi_asset.get_editor_property("pipeline") is None:
            return False, (
                f"Created WI_{outfit_name} and linked principal_asset, but "
                f"could not create/assign its pipeline (MetaHumanOutfitPipeline). "
                f"This is a bug in wardrobe.py, not something to retry - report "
                f"this back with the Output Log content."
            )

    try:
        wi_asset.set_editor_property("thumbnail_name", unreal.Text(outfit_name))
    except Exception as e:
        # Non-critical - the wardrobe item still works without a thumbnail name.
        unreal.log_warning(f"MetaBridge Forge: could not set thumbnail_name: {e}")

    unreal.EditorAssetLibrary.save_loaded_asset(wi_asset)
    unreal.EditorAssetLibrary.save_loaded_asset(oa_asset)

    ok, report_text = verify.run_verification(oa_asset)

    status = "PASSED (best-effort read of the report)" if ok else "reported issues"
    message = (
        f"WI_{outfit_name} created and linked to OA_{outfit_name}.\n\n"
        f"Verification {status}:\n{report_text}"
    )
    return True, message


def run_finish_outfit_setup() -> None:
    """Entry point wired to the "Finish Outfit Setup..." menu action."""
    outfit_name = dialogs.ask_outfit_name()
    if not outfit_name:
        return

    try:
        ok, message = finish_outfit_setup(outfit_name)
    except Exception as e:
        unreal.log_error(f"MetaBridge Forge: exception during Finish Outfit Setup: {e}")
        dialogs.show_result(
            "MetaBridge Forge - Step 2 failed",
            f"Finish Outfit Setup failed for '{outfit_name}':\n\n{e}\n\n"
            f"(Full traceback in the Output Log.)",
            is_error=True,
        )
        return

    dialogs.show_result(
        "MetaBridge Forge - Step 2" if ok else "MetaBridge Forge - Step 2 failed",
        message,
        is_error=not ok,
    )
