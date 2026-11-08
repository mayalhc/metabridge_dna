"""DO NOT USE build_cloth_asset()/build_outfit_asset() below - CONFIRMED
TO CRASH THE ENGINE (EXCEPTION_ACCESS_VIOLATION). unreal.ChaosClothAssetFactory()
pops an interactive "choose creation template" dialog when driven via
create_asset() from Python, and that dialog crashes when a template is
picked outside of normal editor-driven interaction. Use
duplicate_build.py instead, which never calls this factory at all.

Kept here only as a record of what was tried and why it's unsafe - do
not resurrect this path without first confirming (in a disposable test
project) that the factory dialog issue is actually fixed.

Fully-automated CA_ (ChaosClothAsset) / OA_ (ChaosOutfitAsset) creation
via Dataflow graph templates.

The templates below were captured by hand: build one real CA_/OA_ once
using Epic's own Outfit Asset wizard, open its Dataflow graph, select all
nodes, Ctrl+C, and paste that text here. Replaying it via
unreal.DataflowEditorBlueprintLibrary.add_dataflow_from_clipboard_content()
reproduces the exact same graph in a fresh Dataflow asset - no need to
reconstruct nodes/connections by hand, which is the piece that isn't
exposed to Python at all (see mbforge module docstrings elsewhere).

Confirmed against this project's real CA_test_jeket / OA_test_jeket:
- CA_'s graph has exactly two per-outfit-varying values, both literal
  asset-reference strings baked into node Properties text: the garment
  Static Mesh and the reference body Skeletal Mesh. _ca_template_text()
  substitutes those.
- OA_'s graph has ZERO baked-in paths - its only per-outfit input is a
  Dataflow VARIABLE named "SizedOutfitSource" (TArray<FChaosSizedOutfitSource>),
  read via a FGetDataflowVariableNode. The OA_ template is pasted
  unchanged for every outfit; only the variable value differs.

RESOLVED: override_dataflow_variable_object_array (Array[Object]) is NOT
the right call for a TArray<FChaosSizedOutfitSource> (struct, not Object)
variable - confirmed against the engine source (DataflowBlueprintLibrary
only exposes Bool/Int/Float/Object overrides, no Struct/StructArray one).
The engine does have the right mechanism -
FDataflowVariableOverrides::OverrideVariableStructArray<T>() - it's just a
C++ template with no Blueprint/Python exposure. MetaBridgeForge's own
C++ module (Source/MetaBridgeForge/.../MBForgeOutfitDataflowLibrary.h)
wraps it as unreal.MBForgeOutfitDataflowLibrary.override_sized_outfit_source_variable(),
used below.
"""
import unreal

from . import config

# ── CA_ (ChaosClothAsset) template ──────────────────────────────────────────
# Captured from a real, hand-built CA_test_jeket. The two asset references
# below (in their exact escaped form, as pasted from the Dataflow editor)
# are substituted per-outfit; everything else is fixed graph structure.

_CA_TEMPLATE = (
    r'(NodeData=((Type="FChaosClothAssetTerminalNode_v2",Name="ClothAssetTerminal",'
    r'Properties="(CollectionLods=(()),LODTransitionDataCache=(()),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=5274.000000,Y=1107.000000)),'
    r'(Type="FChaosClothAssetStaticMeshImportNode_v2",Name="StaticMeshImport",'
    r'Properties="(Collection=(),StaticMesh=\"/Script/Engine.StaticMesh\'/Game/Outfits/test_jeket/'
    r'test_jeket/Meshes/test_jeket.test_jeket\'\",Reimport=(),bImportSimMesh=False,'
    r'bImportRenderMesh=True,LODIndex=0,SimMeshSection=-1,RenderMeshSection=-1,UVChannel=0,'
    r'UVScale=(X=1.000000,Y=1.000000),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=4570.000000,Y=1107.000000)),'
    r'(Type="FChaosClothAssetTransferSkinWeightsNode",Name="TransferSkinWeights",'
    r'Properties="(Collection=(),TargetMeshType=Render,SimMeshSourceTypeHint=\"Skeletal Mesh\",'
    r'RenderMeshSourceType=SkeletalMesh,SkeletalMesh=\"/Script/Engine.SkeletalMesh\'/Game/Outfits/'
    r'test_jeket/test_jeket/Meshes/Blended_Body_01_Body.Blended_Body_01_Body\'\",SimCollection=(),'
    r'LodIndex=0,Transform=(Rotation=(X=0.000000,Y=-0.000000,Z=0.000000,W=1.000000),'
    r'Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),'
    r'TransferMethodHint=\"Closest Point On Surface\",TransferMethod=ClosestPointOnSurface,'
    r'RadiusPercentage=0.050000,NormalThreshold=30.000000,LayeredMeshSupport=True,'
    r'NumSmoothingIterations=10,SmoothingStrength=0.100000,InpaintMask=(WeightMap=\"InpaintMask\"),'
    r'MaxNumInfluences=Eight,bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=4906.000000,Y=1107.000000))),'
    r'ConnectionData=((Out="/TransferSkinWeights:Collection|FManagedArrayCollection",'
    r'In="/ClothAssetTerminal:CollectionLods[0]|FManagedArrayCollection"),'
    r'(Out="/StaticMeshImport:Collection|FManagedArrayCollection",'
    r'In="/TransferSkinWeights:Collection|FManagedArrayCollection")))'
)
_CA_TERMINAL_NODE = "ClothAssetTerminal"

_CA_TEMPLATE_GARMENT_PATH = "/Game/Outfits/test_jeket/test_jeket/Meshes/test_jeket"
_CA_TEMPLATE_BODY_PATH = (
    "/Game/Outfits/test_jeket/test_jeket/Meshes/Blended_Body_01_Body"
)


def _escaped_ref(class_name: str, path: str) -> str:
    """Builds the same \\"/Script/Engine.<Class>\\'<path>.<name>\\'\\"
    literal form found embedded in the captured template text."""
    name = path.rstrip("/").split("/")[-1]
    return f'\\"/Script/Engine.{class_name}\\\'{path}.{name}\\\'\\"'


def _ca_template_text(garment_mesh_path: str, body_mesh_path: str) -> str:
    old_static = _escaped_ref("StaticMesh", _CA_TEMPLATE_GARMENT_PATH)
    new_static = _escaped_ref("StaticMesh", garment_mesh_path)
    old_skel = _escaped_ref("SkeletalMesh", _CA_TEMPLATE_BODY_PATH)
    new_skel = _escaped_ref("SkeletalMesh", body_mesh_path)

    if old_static not in _CA_TEMPLATE:
        raise ValueError(
            "CA_ template's garment StaticMesh reference pattern not found - "
            "the template text in dataflow_build.py doesn't match what's "
            "expected, this needs re-capturing."
        )
    if old_skel not in _CA_TEMPLATE:
        raise ValueError(
            "CA_ template's reference body SkeletalMesh pattern not found - "
            "the template text in dataflow_build.py doesn't match what's "
            "expected, this needs re-capturing."
        )

    return _CA_TEMPLATE.replace(old_static, new_static).replace(old_skel, new_skel)


# ── OA_ (ChaosOutfitAsset) template ─────────────────────────────────────────
# Captured from a real, hand-built OA_test_jeket. Pasted UNCHANGED for every
# outfit - its only per-outfit input is the "SizedOutfitSource" Dataflow
# variable, set separately (see build_outfit_asset).

_OA_TEMPLATE = (
    r'(NodeData=((Type="FGetDataflowVariableNode",Name="SizedOutfitSource",'
    r'Properties="(Value=(),VariablePropertyBag=(Value=/Engine/Transient.'
    r'PropertyBag_c1366741c9dd34f9(SizedOutfitSource=)),VariableName=\"SizedOutfitSource\",'
    r'Category=\"\",Description=\"\",bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-6496.000000,Y=256.000000)),'
    r'(Type="FChaosOutfitAssetMakeSizedOutfitNode",Name="MakeSizedOutfit",'
    r'Properties="(Outfit=None,OutfitCollection=(),SizedOutfitSources=(()),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-6272.000000,Y=256.000000)),'
    r'(Type="FChaosGetOutfitClothCollectionsNode",Name="GetOutfitClothCollections",'
    r'Properties="(Outfit=None,ClothCollections=,LodIndex=-1,NumLods=0,NumPieces=0,'
    r'bOverrideColor=False,OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),'
    r'bActive=True,FrozenProperties=(Value=None),bIsFrozen=False)",'
    r'Position=(X=-5888.000000,Y=256.000000)),'
    r'(Type="FDataflowCallSubGraphNode",Name="PrepareClothCollections_0",'
    r'Properties="(SubGraphGuid=72383383426B393393742FA8418F7DE1,'
    r'SubGraphName=\"PrepareClothCollections\",DynamicInputs=(DynamicProperties=((),(),())),'
    r'InputsPropertyBag=(Value=/Engine/Transient.PropertyBag_638a58098cf39f94'
    r'(Collection=,Outfit=None,NumLODs=0)),DynamicOutputs=(DynamicProperties=(())),'
    r'OutputsPropertyBag=(Value=/Engine/Transient.PropertyBag_20d37448538073c6(Outfit=None)),'
    r'bOverrideColor=False,OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),'
    r'bActive=True,FrozenProperties=(Value=None),bIsFrozen=False)",'
    r'Position=(X=-5472.000000,Y=272.000000)),'
    r'(Type="FChaosOutfitAssetTerminalNode",Name="OutfitAssetTerminal",'
    r'Properties="(Outfit=None,ConvertToSkeletalMesh=(),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-5184.000000,Y=272.000000))),'
    r'ConnectionData=('
    r'(Out="/SizedOutfitSource:Value|TArray<FChaosSizedOutfitSource>",'
    r'In="/MakeSizedOutfit:SizedOutfitSources[0]|TArray<FChaosSizedOutfitSource>"),'
    r'(Out="/MakeSizedOutfit:Outfit|TObjectPtr<UChaosOutfit>",'
    r'In="/GetOutfitClothCollections:Outfit|TObjectPtr<UChaosOutfit>"),'
    r'(Out="/GetOutfitClothCollections:ClothCollections|TArray<FManagedArrayCollection>",'
    r'In="/PrepareClothCollections_0:Collection|TArray<FManagedArrayCollection>"),'
    r'(Out="/GetOutfitClothCollections:Outfit|TObjectPtr<UChaosOutfit>",'
    r'In="/PrepareClothCollections_0:Outfit|TObjectPtr<UChaosOutfit>"),'
    r'(Out="/GetOutfitClothCollections:NumLods|int32",'
    r'In="/PrepareClothCollections_0:NumLODs|int32"),'
    r'(Out="/PrepareClothCollections_0:Outfit|TObjectPtr<UChaosOutfit>",'
    r'In="/OutfitAssetTerminal:Outfit|TObjectPtr<UChaosOutfit>")),'
    r'SubGraphData=('
    r'(SubGraphGuid=72383383426B393393742FA8418F7DE1,Name="PrepareClothCollections",'
    r'bIsForEach=True,NodeData=('
    r'(Type="FDataflowSubGraphInputNode",Name="Input",'
    r'Properties="(DynamicConnections=(DynamicProperties=((),(),())),'
    r'PropertyBag=(Value=/Engine/Transient.PropertyBag_638a58098cf39f94'
    r'(Collection=,Outfit=None,NumLODs=0)),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-336.000000,Y=-64.000000)),'
    r'(Type="FDataflowSubGraphOutputNode",Name="Output",'
    r'Properties="(DynamicConnections=(DynamicProperties=(())),'
    r'PropertyBag=(Value=/Engine/Transient.PropertyBag_20d37448538073c6(Outfit=None)),'
    r'bOverrideColor=False,OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),'
    r'bActive=True,FrozenProperties=(Value=None),bIsFrozen=False)",'
    r'Position=(X=1536.000000,Y=-32.000000)),'
    r'(Type="FDataflowGetArrayElementNode",Name="GetArrayElement",'
    r'Properties="(Array=(),Index=0,Element=(),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-128.000000,Y=16.000000)),'
    r'(Type="FDataflowSubGraphGetCurrentIndexNode",Name="GetCurrentIndex",'
    r'Properties="(Index=0,bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-336.000000,Y=96.000000)),'
    r'(Type="FChaosClothAssetCollectionQueryNode",Name="ClothCollectionQuery",'
    r'Properties="(Collection=(),bIsClothCollection=False,bHasClothSimMesh=False,'
    r'bHasClothRenderMesh=False,bHasClothProxyDeformer=False,'
    r'BooleanPropertyName=\"PropertyName\",bBooleanPropertyValue=False,bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=128.000000,Y=48.000000)),'
    r'(Type="FChaosSetOutfitClothCollectionNode",Name="SetOutfitClothCollection",'
    r'Properties="(Outfit=None,ClothCollection=(),PieceIndex=0,LODIndex=0,bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=880.000000,Y=-32.000000)),'
    r'(Type="FDataflowCallSubGraphNode",Name="GetClothCollectionIndex_0",'
    r'Properties="(SubGraphGuid=A2DCA79A4D5984EFA08563874560E8D1,'
    r'SubGraphName=\"GetClothCollectionIndex\",DynamicInputs=(DynamicProperties=((),())),'
    r'InputsPropertyBag=(Value=/Engine/Transient.PropertyBag_3fdaf188cb0e2d77'
    r'(CollectionIndex=0,NumLODs=0)),DynamicOutputs=(DynamicProperties=((),(),())),'
    r'OutputsPropertyBag=(Value=/Engine/Transient.PropertyBag_44e5073b26702fa9'
    r'(PieceIndex=0,LODIndex=0,ReturnValue=0)),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-128.000000,Y=512.000000)),'
    r'(Type="FDataflowBranchNode",Name="Branch_0",'
    r'Properties="(TrueValue=(),FalseValue=(),bCondition=True,Result=(),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=1216.000000,Y=-32.000000)),'
    r'(Type="FChaosClothAssetProxyDeformerNode_v3",Name="ProxyDeformer_0",'
    r'Properties="(Collection=(),SelectionFilterSets=(()),bUseMultipleInfluences=False,'
    r'InfluenceRadius=5.000000,bPreserveRenderTangents=True,bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=512.000000,Y=48.000000))),'
    r'ConnectionData=('
    r'(Out="/Branch_0:Result|TObjectPtr<UChaosOutfit>",In="/Output:Outfit|TObjectPtr<UChaosOutfit>"),'
    r'(Out="/Input:Collection|TArray<FManagedArrayCollection>",'
    r'In="/GetArrayElement:Array|TArray<FManagedArrayCollection>"),'
    r'(Out="/GetCurrentIndex:Index|int32",In="/GetArrayElement:Index|int32"),'
    r'(Out="/GetArrayElement:Element|FManagedArrayCollection",'
    r'In="/ClothCollectionQuery:Collection|FManagedArrayCollection"),'
    r'(Out="/Input:Outfit|TObjectPtr<UChaosOutfit>",'
    r'In="/SetOutfitClothCollection:Outfit|TObjectPtr<UChaosOutfit>"),'
    r'(Out="/ProxyDeformer_0:Collection|FManagedArrayCollection",'
    r'In="/SetOutfitClothCollection:ClothCollection|FManagedArrayCollection"),'
    r'(Out="/GetClothCollectionIndex_0:PieceIndex|int32",'
    r'In="/SetOutfitClothCollection:PieceIndex|int32"),'
    r'(Out="/GetClothCollectionIndex_0:LODIndex|int32",'
    r'In="/SetOutfitClothCollection:LODIndex|int32"),'
    r'(Out="/GetCurrentIndex:Index|int32",In="/GetClothCollectionIndex_0:CollectionIndex|int32"),'
    r'(Out="/Input:NumLODs|int32",In="/GetClothCollectionIndex_0:NumLODs|int32"),'
    r'(Out="/Input:Outfit|TObjectPtr<UChaosOutfit>",In="/Branch_0:TrueValue|TObjectPtr<UChaosOutfit>"),'
    r'(Out="/SetOutfitClothCollection:Outfit|TObjectPtr<UChaosOutfit>",'
    r'In="/Branch_0:FalseValue|TObjectPtr<UChaosOutfit>"),'
    r'(Out="/ClothCollectionQuery:bHasClothProxyDeformer|bool",In="/Branch_0:bCondition|bool"),'
    r'(Out="/ClothCollectionQuery:Collection|FManagedArrayCollection",'
    r'In="/ProxyDeformer_0:Collection|FManagedArrayCollection"))),'
    r'(SubGraphGuid=A2DCA79A4D5984EFA08563874560E8D1,Name="GetClothCollectionIndex",'
    r'NodeData=('
    r'(Type="FDataflowSubGraphInputNode",Name="Input_0",'
    r'Properties="(DynamicConnections=(DynamicProperties=((),())),'
    r'PropertyBag=(Value=/Engine/Transient.PropertyBag_3fdaf188cb0e2d77'
    r'(CollectionIndex=0,NumLODs=0)),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-384.000000,Y=-32.000000)),'
    r'(Type="FDataflowSubGraphOutputNode",Name="Output_0",'
    r'Properties="(DynamicConnections=(DynamicProperties=((),(),())),'
    r'PropertyBag=(Value=/Engine/Transient.PropertyBag_44e5073b26702fa9'
    r'(PieceIndex=0,LODIndex=0,ReturnValue=0)),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=352.000000,Y=-48.000000)),'
    r'(Type="FMathExpressionDataflowNode",Name="MathExpression_1",'
    r'Properties="(A=(Value=0.000000),B=(Value=0.000000),C=(Value=0.000000),D=(Value=0.000000),'
    r'Expression=\"{A}%{B}\",ReturnValue=(Value=0.000000),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-176.000000,Y=112.000000)),'
    r'(Type="FDataflowMathDivideNode",Name="Divide",'
    r'Properties="(Fallback=(Value=0.000000),A=(Value=0.000000),B=(Value=0.000000),'
    r'Result=(Value=0.000000),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=-192.000000,Y=-80.000000)),'
    r'(Type="FDataflowMathFloorNode",Name="Floor",'
    r'Properties="(A=(Value=0.000000),Result=(Value=0.000000),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=64.000000,Y=-80.000000)),'
    r'(Type="FConvertNumericTypesDataflowNode",Name="ConvertNumericTypes",'
    r'Properties="(In=(Value=0.000000),Out=(Value=0.000000),bOverrideColor=False,'
    r'OverrideColor=(R=1.000000,G=1.000000,B=1.000000,A=1.000000),bActive=True,'
    r'FrozenProperties=(Value=None),bIsFrozen=False)",Position=(X=48.000000,Y=0.000000))),'
    r'ConnectionData=('
    r'(Out="/ConvertNumericTypes:Out|int32",In="/Output_0:PieceIndex|int32"),'
    r'(Out="/MathExpression_1:ReturnValue|int32",In="/Output_0:LODIndex|int32"),'
    r'(Out="/Input_0:CollectionIndex|int32",In="/MathExpression_1:A|int32"),'
    r'(Out="/Input_0:NumLODs|int32",In="/MathExpression_1:B|int32"),'
    r'(Out="/Input_0:CollectionIndex|int32",In="/Divide:A|int32"),'
    r'(Out="/Input_0:NumLODs|int32",In="/Divide:B|int32"),'
    r'(Out="/Divide:Result|float",In="/Floor:A|float"),'
    r'(Out="/Floor:Result|float",In="/ConvertNumericTypes:In|float")))))'
)
_OA_TERMINAL_NODE = "OutfitAssetTerminal"
_OA_VARIABLE_NAME = "SizedOutfitSource"


# ── Shared plumbing ──────────────────────────────────────────────────────

def _paste_template_into_new_dataflow(
    template_text: str, dataflow_folder: str, dataflow_name: str
) -> "unreal.Dataflow | None":
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    dataflow_asset = asset_tools.create_asset(
        dataflow_name, dataflow_folder, unreal.Dataflow, unreal.DataflowAssetFactory()
    )
    if dataflow_asset is None:
        unreal.log_error(
            f"MetaBridge Forge: failed to create Dataflow asset "
            f"{dataflow_folder}/{dataflow_name}"
        )
        return None

    ok = unreal.DataflowEditorBlueprintLibrary.add_dataflow_from_clipboard_content(
        dataflow_asset, template_text, unreal.Vector2D(0, 0)
    )
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: add_dataflow_from_clipboard_content failed "
            f"for {dataflow_asset.get_path_name()}"
        )
        return None

    unreal.EditorAssetLibrary.save_loaded_asset(dataflow_asset)
    return dataflow_asset


def _wire_dataflow_instance(
    target_asset, dataflow_asset: "unreal.Dataflow", terminal_node: str
) -> None:
    instance = target_asset.get_editor_property("dataflow_instance")
    instance.set_editor_property("dataflow_asset", dataflow_asset)
    instance.set_editor_property("dataflow_terminal", terminal_node)
    target_asset.set_editor_property("dataflow_instance", instance)


# ── CA_ build ────────────────────────────────────────────────────────────

def build_cloth_asset(
    outfit_name: str, garment_mesh_path: str, body_mesh_path: str
) -> "unreal.ChaosClothAsset | None":
    """Creates CA_<outfit_name> under
    /Game/Outfits/<outfit_name>/<outfit_name>/ClothAssets/, fully
    automated - no manual wizard step. Returns the asset, or None on
    failure (errors logged via unreal.log_error)."""
    ca_folder = f"{config.outfit_deps_folder(outfit_name)}/{config.CLOTH_ASSETS_SUBDIR}"
    if not unreal.EditorAssetLibrary.does_directory_exist(ca_folder):
        unreal.EditorAssetLibrary.make_directory(ca_folder)

    ca_name = f"CA_{outfit_name}"
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    ca_asset = asset_tools.create_asset(
        ca_name, ca_folder, unreal.ChaosClothAsset, unreal.ChaosClothAssetFactory()
    )
    if ca_asset is None:
        unreal.log_error(f"MetaBridge Forge: failed to create {ca_folder}/{ca_name}")
        return None

    template_text = _ca_template_text(garment_mesh_path, body_mesh_path)
    dataflow_asset = _paste_template_into_new_dataflow(
        template_text, ca_folder, f"DF_{ca_name}"
    )
    if dataflow_asset is None:
        return None

    _wire_dataflow_instance(ca_asset, dataflow_asset, _CA_TERMINAL_NODE)

    ok = unreal.DataflowBlueprintLibrary.regenerate_asset_from_dataflow(ca_asset)
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: regenerate_asset_from_dataflow failed for "
            f"{ca_asset.get_path_name()}"
        )
        return None

    unreal.EditorAssetLibrary.save_loaded_asset(ca_asset)
    unreal.log(f"MetaBridge Forge: built {ca_asset.get_path_name()}")
    return ca_asset


# ── OA_ build ────────────────────────────────────────────────────────────

def build_outfit_asset(
    outfit_name: str, ca_asset: "unreal.ChaosClothAsset", body_mesh_path: str
):
    """Creates OA_<outfit_name> directly under
    /Game/Outfits/<outfit_name>/, wiring in `ca_asset` as the (sole) sized
    outfit source. UNVERIFIED: the SizedOutfitSource variable override
    call - see module docstring. Returns the asset, or None on failure.
    """
    oa_folder = config.outfit_folder(outfit_name)
    oa_name = f"OA_{outfit_name}"
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    oa_asset = asset_tools.create_asset(
        oa_name, oa_folder, unreal.ChaosOutfitAsset, unreal.ChaosOutfitAssetFactory()
    )
    if oa_asset is None:
        unreal.log_error(f"MetaBridge Forge: failed to create {oa_folder}/{oa_name}")
        return None

    dataflow_asset = _paste_template_into_new_dataflow(
        _OA_TEMPLATE, config.outfit_deps_folder(outfit_name), f"DF_{oa_name}"
    )
    if dataflow_asset is None:
        return None

    _wire_dataflow_instance(oa_asset, dataflow_asset, _OA_TERMINAL_NODE)

    body_mesh = unreal.load_asset(body_mesh_path)
    sized_source = unreal.ChaosSizedOutfitSource()
    sized_source.set_editor_property("size_name", outfit_name)
    sized_source.set_editor_property("source_asset", ca_asset)
    sized_source.set_editor_property("source_body_parts", [body_mesh])

    ok = unreal.MBForgeOutfitDataflowLibrary.override_sized_outfit_source_variable(
        oa_asset, _OA_VARIABLE_NAME, [sized_source]
    )
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: override_sized_outfit_source_variable "
            f"returned False for '{_OA_VARIABLE_NAME}' on "
            f"{oa_asset.get_path_name()} - check that the Dataflow graph "
            f"actually has a variable with this name."
        )
        return None

    ok = unreal.DataflowBlueprintLibrary.regenerate_asset_from_dataflow(oa_asset)
    if not ok:
        unreal.log_error(
            f"MetaBridge Forge: regenerate_asset_from_dataflow failed for "
            f"{oa_asset.get_path_name()}"
        )
        return None

    unreal.EditorAssetLibrary.save_loaded_asset(oa_asset)
    unreal.log(f"MetaBridge Forge: built {oa_asset.get_path_name()}")
    return oa_asset
