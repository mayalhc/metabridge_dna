"""Headless jobs for MetaBridge DNA: build a MetaHuman Package from Blender's
export, or open one and hand its contents back to Blender.

Run by the commandlet, never from a menu:

    UnrealEditor-Cmd <project> -run=pythonscript -script="<this>/../../mbforge_job.py <job.json>"

A job is a JSON file; the answer is written next to it as <job>.result.json.
Verification and packaging are MetaHuman Manager's own steps in its own
order (see SMetaHumanManagerWindow::VerifyItems / PackageItems), so a package
made here is the one the Package button would have made.
"""
import json
import os
import traceback

import unreal

from . import config, duplicate_build, groom, importer, wardrobe

_TYPES = {
    "GROOM": "GROOM",
    "OUTFIT": "OUTFIT_CLOTHING",
}


def _asset_type(kind):
    return getattr(unreal.MetaHumanAssetType, _TYPES[kind])


def _description(kind, name):
    # Listed under the main asset's name: GB_<name> for a groom (its binding),
    # OA_<name> for an outfit.
    wanted = {name, "GB_" + name, "OA_" + name}
    for desc in unreal.MetaHumanAssetManager.find_assets_for_packaging(_asset_type(kind)):
        if str(desc.get_editor_property("name")) in wanted:
            return desc
    return None


def _updated(answer):
    """By-reference UFUNCTIONs come back as a tuple (return value, the ref)."""
    if isinstance(answer, tuple):
        for item in answer:
            if isinstance(item, unreal.MetaHumanAssetDescription):
                return item
    return answer


def _rules(kind):
    rules = unreal.MetaHumanVerificationRuleCollection()
    rules.add_verification_rule(unreal.VerifyObjectValid())
    rules.add_verification_rule(unreal.VerifyMetaHumanPackageSource())
    if kind == "GROOM":
        rules.add_verification_rule(unreal.VerifyMetaHumanGroom())
    else:
        rules.add_verification_rule(unreal.VerifyMetaHumanOutfitClothing())
    return rules


def _report(report):
    """(errors, warnings) as MetaHuman Manager shows them."""
    data = json.loads(report.generate_json_report() or "{}")
    def texts(key):
        return [str(item.get("message", item)) for item in data.get(key) or []]
    return texts("errors"), texts("warnings")


def package(kind, name, out_path):
    """Verify and package one asset found by MetaHuman Manager's own scan."""
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    desc = _description(kind, name)
    if desc is None:
        found = [str(d.get_editor_property("name"))
                 for d in unreal.MetaHumanAssetManager.find_assets_for_packaging(_asset_type(kind))]
        raise RuntimeError("MetaHuman Manager does not list %s '%s' (it lists: %s)"
                           % (kind, name, ", ".join(found) or "nothing"))
    # Saved packages are only seen with their references after a forced
    # rescan - without it the dependencies were the binding and the
    # Wardrobe Item alone, and the groom itself was left out of the package.
    folder = str(desc.get_editor_property("asset_data").package_path)
    unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([folder], True)
    desc = _updated(unreal.MetaHumanAssetManager.update_asset_dependencies(desc))
    asset = desc.get_editor_property("asset_data").get_asset()
    report = unreal.MetaHumanAssetReport()
    options = unreal.MetaHumanVerificationOptions()
    _rules(kind).apply_all_rules(asset, report, options)
    errors, warnings = _report(report)
    if errors:
        return {"ok": False, "stage": "verify", "errors": errors, "warnings": warnings}
    desc.set_editor_property("verification_report", report)
    desc = _updated(unreal.MetaHumanAssetManager.update_asset_details(desc))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    if not unreal.MetaHumanAssetManager.create_archive([desc], out_path):
        return {"ok": False, "stage": "package", "errors": ["CreateArchive failed"],
                "warnings": warnings}
    return {"ok": os.path.isfile(out_path), "path": out_path, "warnings": warnings,
            "bytes": os.path.getsize(out_path) if os.path.isfile(out_path) else 0}


def _fresh(folder):
    """Start a build from nothing. A second binding made beside an old one is
    given a unique name - GB_Hair_MyGroom4 became GB_Hair_MyGroom5 - and both
    then show up as separate grooms."""
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)


_TEMPLATE_ROOTS = ("/MetaBridgeForge/",)


def _folder_assets(folder):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    reg.scan_paths_synchronous([folder], True)
    return {str(d.asset_name): str(d.package_name)
            for d in reg.get_assets_by_path(folder, recursive=True)}


def _outside(folder):
    """{package in folder: [template packages it still points at]}."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True, include_hard_package_references=True)
    found = {}
    for package in _folder_assets(folder).values():
        deps = [str(d) for d in reg.get_dependencies(package, options) or []]
        bad = [d for d in deps if d.startswith(_TEMPLATE_ROOTS)]
        if bad:
            found[package] = bad
    return found


def _load(package):
    return unreal.load_asset(package + "." + package.rsplit("/", 1)[-1])


def make_self_contained(folder):
    """Point everything in the folder at the folder's own copies.

    The template is cloned one asset at a time, so every copy still pointed
    at the plugin's template: the head's skeleton and physics asset, every
    material function. A buyer without this plugin would open broken assets.
    A template asset with no copy here yet is copied in first.
    """
    for _round in range(4):
        outside = _outside(folder)
        if not outside:
            return 0
        local = _folder_assets(folder)
        mapping = {}
        for refs in outside.values():
            for ref in refs:
                name = ref.rsplit("/", 1)[-1]
                if name not in local:
                    copy = unreal.EditorAssetLibrary.duplicate_asset(ref, folder + "/" + name)
                    if copy is None:
                        raise RuntimeError("could not copy %s into %s" % (ref, folder))
                    unreal.EditorAssetLibrary.save_loaded_asset(copy)
                    local[name] = folder + "/" + name
                source, target = _load(ref), _load(local[name])
                if source is not None and target is not None:
                    mapping[source] = target
        assets = [a for a in (_load(p) for p in local.values()) if a is not None]
        unreal.MBForgeGroomExportLibrary.remap_references(assets, mapping)
        for asset in assets:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    left = _outside(folder)
    if left:
        raise RuntimeError("still pointing outside the package: %s" % left)
    return 0


def _import_files(paths, folder, static=True):
    tasks = []
    for path in paths:
        task = unreal.AssetImportTask()
        task.filename = path
        task.destination_path = folder
        task.automated = True
        task.save = True
        task.replace_existing = True
        if static and path.lower().endswith(".fbx"):
            options = unreal.FbxImportUI()
            options.set_editor_property("import_mesh", True)
            options.set_editor_property("import_as_skeletal", False)
            options.set_editor_property("import_materials", False)
            options.set_editor_property("import_textures", False)
            options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
            options.static_mesh_import_data.set_editor_property("combine_meshes", True)
            task.options = options
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    out = []
    for task in tasks:
        paths_done = [str(p) for p in task.imported_object_paths]
        if not paths_done:
            raise RuntimeError("could not import %s" % task.filename)
        out.append(unreal.load_asset(paths_done[0]))
    return out


def _struct(cls, text):
    value = cls()
    value.import_text(text)
    return value


def _ref(asset):
    return "None" if asset is None else "\"%s'%s'\"" % (
        asset.get_class().get_path_name(), asset.get_path_name())


def dress_groom(name, cards=(), card_textures=(), helmet=None):
    """Materials, strand rendering and card LODs as the published grooms have them."""
    deps = config.groom_deps_folder(name)
    materials = config.groom_materials_folder(name)
    asset = unreal.load_asset(config.groom_mesh_folder(name) + "/" + name)
    slots = []
    for slot in ("MI_Hair", "MI_Hair_Cards", "MI_Hair_Helmet"):
        material = unreal.load_asset(materials + "/" + slot)
        if material is None:
            raise RuntimeError("the template has no %s" % slot)
        slots.append(_struct(unreal.HairGroupsMaterial,
                             '(Material=%s,SlotName="%s")' % (_ref(material), slot)))
    asset.set_editor_property("hair_groups_materials", slots)
    groups = len(asset.get_editor_property("hair_groups_rendering")) or 1
    asset.set_editor_property("hair_groups_rendering", [_struct(
        unreal.HairGroupsRendering,
        '(MaterialSlotName="MI_Hair",GeometrySettings=(HairWidth=0.013000,'
        'HairWidth_Override=True,HairRootScale=1.000000,HairTipScale=0.850000),'
        'ShadowSettings=(HairShadowDensity=0.350000,HairRaytracingRadiusScale=1.000000,'
        'bUseHairRaytracingGeometry=False,bVoxelize=True),'
        'AdvancedSettings=(bUseStableRasterization=True,bScatterSceneLighting=False))')
        for _g in range(groups)])

    textures = _import_files(card_textures, deps + "/Textures", static=False) if card_textures else []
    tex = ",".join([_ref(x) for x in textures] + ["None"] * (6 - len(textures)))
    meshes = _import_files(cards, deps) if cards else []
    asset.set_editor_property("hair_groups_cards", [_struct(
        unreal.HairGroupsCardsSourceDescription,
        '(MaterialSlotName="MI_Hair_Cards",bInvertUV=False,GuideType=Generated,'
        'ImportedMesh=%s,Textures=(Layout=Layout0,Textures=(%s)),GroupIndex=0,LODIndex=%d)'
        % (_ref(mesh), tex, lod)) for lod, mesh in enumerate(meshes)])
    if helmet:
        mesh = _import_files([helmet], deps)[0]
        asset.set_editor_property("hair_groups_meshes", [_struct(
            unreal.HairGroupsMeshesSourceDescription,
            '(MaterialSlotName="MI_Hair_Helmet",ImportedMesh=%s,'
            'Textures=(Layout=Layout0,Textures=(None,None,None,None,None,None)),'
            'GroupIndex=0,LODIndex=%d)' % (_ref(mesh), len(meshes)))])
    unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    return {"cards": len(meshes), "card_textures": len(textures), "helmet": bool(helmet)}


def import_groom_strands(strands_path, name):
    """import_groom_abc's steps, with the groom built from a strand file."""
    groom._ensure_groom_folders(name)
    template = config.resolve_groom_template_folder()
    groom._clone_template_folder(f"{template}/{config.GROOM_MESH_SUBDIR}", config.groom_mesh_folder(name))
    groom._clone_template_folder(f"{template}/{config.MATERIALS_SUBDIR}", config.groom_materials_folder(name))
    asset = unreal.MBForgeGroomExportLibrary.create_groom_from_strands(
        strands_path, config.groom_mesh_folder(name), name)
    if isinstance(asset, tuple):
        asset, info = asset
    if asset is None:
        raise RuntimeError("the strands could not be built into a groom")
    asset.set_editor_property("hair_groups_interpolation", [_struct(
        unreal.HairGroupsInterpolation,
        "(DecimationSettings=(CurveDecimation=1.000000,VertexDecimation=1.000000),"
        "InterpolationSettings=(GuideType=Imported,HairToGuideDensity=0.100000,"
        "RiggedGuideNumCurves=10,RiggedGuideNumPoints=4,InterpolationQuality=High,"
        "InterpolationDistance=Parametric,bRandomizeGuide=False,bUseUniqueGuide=False),"
        "RiggingSettings=())")
        for _g in range(len(asset.get_editor_property("hair_groups_interpolation")) or 1)])
    unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    return asset


def export_groom(abc_path, name, out_path, slot="Hair", cards=(), card_textures=(), helmet=None):
    _fresh(config.groom_folder(name))
    if abc_path.lower().endswith(".mbgs"):
        asset = import_groom_strands(abc_path, name)
    else:
        asset = groom.import_groom_abc(abc_path, name)
    if asset is None:
        raise RuntimeError("the Alembic import made no groom - see the log")
    make_self_contained(config.groom_folder(name))
    dressed = dress_groom(name, cards, card_textures, helmet)
    ok, message = groom.finish_groom_setup(name, slot)
    if not ok:
        raise RuntimeError(message)
    make_self_contained(config.groom_folder(name))
    result = package("GROOM", name, out_path)
    result.update(dressed)
    return result


def export_outfit(fbx_path, name, out_path):
    """The Import Outfit FBX menu action, without its file picker."""
    _fresh(config.outfit_folder(name))
    template = config.OUTFIT_TEMPLATE_DEFAULT
    reference_body = importer._find_skeletal_mesh_in_folder(
        config.template_outfit_meshes_folder(template))
    if reference_body is None:
        raise RuntimeError("no reference body in the outfit template")
    mesh = importer.import_outfit_fbx(fbx_path, name, reference_body)
    if mesh is None:
        raise RuntimeError("the garment import failed - see the log")
    oa = duplicate_build.duplicate_outfit_template(template, name)
    if oa is None:
        raise RuntimeError("the OA_/CA_ template could not be duplicated")
    body = importer._find_skeletal_mesh_in_folder(config.outfit_meshes_folder(name))
    if body is None or not duplicate_build.retarget_duplicated_outfit(name, mesh, body):
        raise RuntimeError("the outfit could not be retargeted to the garment")
    ok, message = wardrobe.finish_outfit_setup(name)
    if not ok:
        raise RuntimeError(message)
    make_self_contained(config.outfit_folder(name))
    return package("OUTFIT", name, out_path)


def _export_asset(asset, path):
    task = unreal.AssetExportTask()
    task.object = asset
    task.filename = path
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    if isinstance(asset, unreal.StaticMesh):
        options = unreal.FbxExportOption()
        options.set_editor_property("collision", False)
        options.set_editor_property("level_of_detail", False)
        task.options = options
    ok = unreal.Exporter.run_asset_export_task(task)
    return ok and os.path.isfile(path)


_PINS = (("base_color", "MP_BASE_COLOR"), ("normal", "MP_NORMAL"), ("roughness", "MP_ROUGHNESS"),
         ("metallic", "MP_METALLIC"), ("ao", "MP_AMBIENT_OCCLUSION"), ("opacity", "MP_OPACITY"),
         ("opacity_mask", "MP_OPACITY_MASK"), ("emissive", "MP_EMISSIVE_COLOR"))


def describe_material(mat):
    """Which texture (and channel) or colour feeds each pin, read off the graph.

    Read from the expressions, not from GetUsedTextures: that one answers from
    compiled shaders, and a commandlet compiles none, so it returned nothing.
    A material instance's texture overrides win over the parent's defaults.
    """
    lib = unreal.MaterialEditingLibrary
    base = mat if isinstance(mat, unreal.Material) else mat.get_base_material()
    out = {}
    if base is None:
        return out
    for pin, prop in _PINS:
        prop = getattr(unreal.MaterialProperty, prop)
        node = lib.get_material_property_input_node(base, prop)
        if node is None:
            continue
        try:
            channel = str(lib.get_material_property_input_node_output_name(base, prop) or "")
        except Exception:
            channel = ""
        entry, seen, queue = {"channel": channel}, set(), [node]
        while queue and "texture" not in entry:
            n = queue.pop(0)
            if n is None or n.get_name() in seen:
                continue
            seen.add(n.get_name())
            cls = n.get_class().get_name()
            if "TextureSample" in cls:
                param = None
                try:
                    param = str(n.get_editor_property("parameter_name"))
                except Exception:
                    pass
                tex = n.get_editor_property("texture")
                if param and isinstance(mat, unreal.MaterialInstance):
                    tex = lib.get_material_instance_texture_parameter_value(mat, param) or tex
                # A mask that only blends tints is not the colour itself.
                if tex is not None and not (param and "mask" in param.lower()):
                    entry["texture"] = tex.get_outermost().get_name()
                    if n is not node:
                        entry["channel"] = ""
                    continue
            elif cls in ("MaterialExpressionConstant3Vector", "MaterialExpressionConstant4Vector"):
                c = n.get_editor_property("constant")
                entry.setdefault("color", [c.r, c.g, c.b])
            elif cls == "MaterialExpressionConstant":
                entry.setdefault("value", n.get_editor_property("r"))
            try:
                queue.extend(lib.get_inputs_for_material_expression(base, n))
            except Exception:
                pass
        out[pin] = entry
    return out


def _export_texture(asset, out_dir, rel):
    """(file, [udim tiles]) - PNG first; linear float textures have no PNG exporter.

    A UDIM texture comes out as one file per tile (<name>.1002.png, ...), and
    its exporter reports failure even when it has written them.
    """
    for ext in (".png", ".exr", ".tga"):
        path = os.path.join(out_dir, rel + ext)
        ok = _export_asset(asset, path)
        tiles = sorted(f for f in os.listdir(out_dir)
                       if f.startswith(rel + ".") and f.endswith(ext) and f[len(rel) + 1:-len(ext)].isdigit())
        if tiles:
            return os.path.join(out_dir, tiles[0]), [os.path.join(out_dir, f) for f in tiles]
        if ok:
            return path, []
    return None, []


def import_package(mhpkg_path, out_dir):
    """Open a package in this project, then write out what Blender can read."""
    os.makedirs(out_dir, exist_ok=True)
    task = unreal.AssetImportTask()
    task.filename = mhpkg_path
    stem = os.path.splitext(os.path.basename(mhpkg_path))[0]
    destination = "/Game/MetaBridgeImport/" + "".join(
        c if c.isalnum() or c == "_" else "_" for c in stem)
    _fresh(destination)
    task.destination_path = destination
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [str(p) for p in task.imported_object_paths]
    if not imported:
        raise RuntimeError("the package imported nothing - see the log")

    main = unreal.load_asset(imported[0])
    root = main.get_path_name().rsplit("/", 1)[0]
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    found = registry.get_assets_by_path(root, recursive=True)

    out = {"ok": True, "main": main.get_path_name(), "main_class": main.get_class().get_name(),
           "grooms": [], "meshes": [], "textures": [], "references": [], "materials": {}}
    for data in found:
        cls = str(data.asset_class_path.asset_name)
        if cls in ("Material", "MaterialInstanceConstant"):
            try:
                out["materials"][str(data.asset_name)] = describe_material(data.get_asset())
            except Exception as error:
                unreal.log_warning("MetaBridge Forge: could not read %s: %s" % (data.asset_name, error))
            continue
        if cls not in ("GroomAsset", "StaticMesh", "SkeletalMesh", "Texture2D"):
            continue
        asset = data.get_asset()
        rel = str(data.package_name)[len(root):].strip("/").replace("/", "__")
        if cls == "GroomAsset":
            path = os.path.join(out_dir, rel + ".mbgs")
            # A bool UFUNCTION with an out parameter comes back as the out value
            # when it succeeded and as None when it did not.
            info = unreal.MBForgeGroomExportLibrary.export_groom_strands(asset, path)
            ok = info is not None
            out["grooms"].append({"name": str(data.asset_name), "path": path, "ok": ok, "info": info})
        elif cls == "SkeletalMesh":
            # The MetaHuman reference head or body the item binds to. Its FBX
            # export bakes from render data and asserts in a commandlet, and
            # Blender already has this MetaHuman, so it is only named.
            out["references"].append({"name": str(data.asset_name),
                                      "path": str(data.package_name)})
        elif cls == "StaticMesh":
            path = os.path.join(out_dir, rel + ".fbx")
            out["meshes"].append({"name": str(data.asset_name), "class": cls, "path": path,
                                  "ok": _export_asset(asset, path)})
        else:
            done, tiles = _export_texture(asset, out_dir, rel)
            srgb = True
            try:
                srgb = bool(asset.get_editor_property("srgb"))
            except Exception:
                pass
            out["textures"].append({"name": str(data.asset_name), "package": str(data.package_name),
                                    "path": done, "tiles": tiles, "srgb": srgb,
                                    "ok": done is not None})
    return out


def run(job_path):
    with open(job_path, encoding="utf-8") as handle:
        job = json.load(handle)
    # A commandlet starts with the asset registry unscanned: the plugin's
    # bundled templates and MetaHuman Manager's own scan both see nothing.
    unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    try:
        mode = job["mode"]
        if mode == "export_groom":
            result = export_groom(job["source"], job["name"], job["output"], job.get("slot", "Hair"),
                                  job.get("cards") or (), job.get("card_textures") or (),
                                  job.get("helmet"))
        elif mode == "export_outfit":
            result = export_outfit(job["source"], job["name"], job["output"])
        elif mode == "import":
            result = import_package(job["source"], job["output"])
        else:
            raise ValueError("unknown mode %r" % mode)
    except Exception as error:
        result = {"ok": False, "error": "%s: %s" % (type(error).__name__, error),
                  "trace": traceback.format_exc()}
    with open(job_path + ".result.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1)
    return result
