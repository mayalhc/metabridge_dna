// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "ChaosOutfitAsset/SizedOutfitSource.h"
#include "MBForgeOutfitDataflowLibrary.generated.h"

class UChaosClothAssetBase;
class UDataflow;
class USkeletalMesh;

/**
 * Fixes the gap noted in dataflow_build.py: the outfit asset's "SizedOutfitSource" Dataflow
 * variable is a TArray<FChaosSizedOutfitSource> (a struct array), and
 * UDataflowBlueprintLibrary::OverrideDataflowVariableObjectArray only accepts UObject arrays,
 * so it silently doesn't apply to this variable. The engine already has the right mechanism for
 * struct-array variables - FDataflowVariableOverrides::OverrideVariableStructArray<T>() - it is
 * just a C++ template, so it has never been exposed to Blueprint/Python. These two functions wrap it.
 */
UCLASS()
class METABRIDGEFORGE_API UMBForgeOutfitDataflowLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Overrides a struct-array Dataflow variable (e.g. "SizedOutfitSource",
	 * TArray<FChaosSizedOutfitSource>) on TargetAsset's own DataflowInstance.
	 * TargetAsset must implement IDataflowInstanceInterface (UChaosOutfitAsset and
	 * UChaosClothAsset both do, via UChaosClothAssetBase).
	 *
	 * This only stores the override; call
	 * UDataflowBlueprintLibrary::RegenerateAssetFromDataflow() afterward to re-run the
	 * Dataflow graph and rebuild the asset's simulation data from the new value.
	 *
	 * @return true if the variable was found and overridden.
	 */
	UFUNCTION(BlueprintCallable, Category = "OutfitAutomation")
	static bool OverrideSizedOutfitSourceVariable(
		UObject* TargetAsset,
		FName VariableName,
		const TArray<FChaosSizedOutfitSource>& SizedOutfitSources);

	/**
	 * Convenience wrapper for the common "duplicated template, now point it at the freshly
	 * imported garment" case: takes every existing FChaosSizedOutfitSource entry for
	 * VariableName (from the current override if TargetAsset already has one, otherwise from
	 * the owning Dataflow asset's default value), replaces SourceAsset on each entry with
	 * NewClothAsset, and - if NewBodyMesh is non-null - replaces SourceBodyParts on each entry
	 * with a single-element array containing NewBodyMesh (pass nullptr to leave
	 * SourceBodyParts untouched). SizeName is always left untouched. Applies the result via
	 * OverrideSizedOutfitSourceVariable(). If there are no existing entries, creates a single
	 * new one with SizeName left empty (GetBodySizeName() will fall back to the first body
	 * part / "Default").
	 *
	 * NewClothAsset must be a ChaosClothAssetBase (e.g. a CA_ built by build_cloth_asset() /
	 * BuildClothAsset from a Static Mesh import) - it is the FChaosSizedOutfitSource garment
	 * reference, NOT a Groom/hair asset. Groom assets attach to a MetaHuman through a separate
	 * binding step and are not part of this Dataflow variable.
	 *
	 * NewBodyMesh should normally be the SAME reference body mesh NewClothAsset's own Dataflow
	 * graph was built/retargeted against (e.g. via SetDataflowNodeObjectProperty on its
	 * TransferSkinWeights node) - OA_'s resizing interpolation is computed against this body,
	 * so it needs to match the body the garment was actually fitted to, not the template's.
	 *
	 * @return true if the variable was found and overridden.
	 */
	UFUNCTION(BlueprintCallable, Category = "OutfitAutomation")
	static bool ReplaceSizedOutfitSourceAsset(
		UObject* TargetAsset,
		FName VariableName,
		UChaosClothAssetBase* NewClothAsset,
		USkeletalMesh* NewBodyMesh);

	/**
	 * Sets a single object-reference property (e.g. StaticMesh, SkeletalMesh) on a named node
	 * inside Dataflow's graph, in place - for baked-in literal node properties like the
	 * ones the CA_ template's StaticMeshImport/TransferSkinWeights nodes carry, which (unlike
	 * "SizedOutfitSource") are NOT Dataflow variables, so DataflowInstance overrides don't apply
	 * to them.
	 *
	 * This is the fixed equivalent of the engine's own
	 * UDataflowEditorBlueprintLibrary::SetDataflowNodeProperty(): that function does write into
	 * the node's live memory (NewStructOnScope() wraps it, not a copy), but never calls
	 * Node->Invalidate(), so the node's cached output stays stale and
	 * RegenerateAssetFromDataflow() silently keeps using the old value. This version calls
	 * Invalidate() and marks the Dataflow asset dirty. It also type-checks NewValue against the
	 * property before writing, and takes NewValue as a real UObject* instead of a stringified
	 * export-text blob.
	 *
	 * @return true if the node and a compatible object property were found and set.
	 */
	UFUNCTION(BlueprintCallable, Category = "OutfitAutomation")
	static bool SetDataflowNodeObjectProperty(
		UDataflow* Dataflow,
		FName NodeName,
		FName PropertyName,
		UObject* NewValue);
};
