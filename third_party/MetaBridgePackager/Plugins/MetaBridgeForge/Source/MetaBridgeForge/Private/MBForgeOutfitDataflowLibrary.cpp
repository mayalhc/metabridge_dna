// Copyright Epic Games, Inc. All Rights Reserved.

#include "MBForgeOutfitDataflowLibrary.h"

#include "ChaosClothAsset/ClothAssetBase.h"
#include "Dataflow/DataflowGraph.h"
#include "Dataflow/DataflowInstance.h"
#include "Dataflow/DataflowNode.h"
#include "Dataflow/DataflowObject.h"
#include "Engine/SkeletalMesh.h"
#include "StructUtils/PropertyBag.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogMBForgeOutfitDataflow, Log, All);

bool UMBForgeOutfitDataflowLibrary::OverrideSizedOutfitSourceVariable(
	UObject* TargetAsset,
	FName VariableName,
	const TArray<FChaosSizedOutfitSource>& SizedOutfitSources)
{
	if (!TargetAsset)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error, TEXT("OverrideSizedOutfitSourceVariable: TargetAsset is null."));
		return false;
	}

	IDataflowInstanceInterface* Interface = UE::Dataflow::InstanceUtils::GetDataflowInterfaceFromObject(TargetAsset);
	if (!Interface)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("OverrideSizedOutfitSourceVariable: '%s' does not implement IDataflowInstanceInterface."),
			*TargetAsset->GetPathName());
		return false;
	}

	TargetAsset->Modify();

	FDataflowInstance& Instance = Interface->GetDataflowInstance();
	const bool bSuccess = Instance.GetVariableOverrides().OverrideVariableStructArray<FChaosSizedOutfitSource>(VariableName, SizedOutfitSources);
	if (!bSuccess)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("OverrideSizedOutfitSourceVariable: variable '%s' was not found on '%s's Dataflow asset ")
			TEXT("(wrong name, or not a struct-array variable of a compatible type)."),
			*VariableName.ToString(), *TargetAsset->GetPathName());
		return false;
	}

#if WITH_EDITOR
	TargetAsset->PostEditChange();
#endif
	TargetAsset->MarkPackageDirty();
	return true;
}

bool UMBForgeOutfitDataflowLibrary::ReplaceSizedOutfitSourceAsset(
	UObject* TargetAsset,
	FName VariableName,
	UChaosClothAssetBase* NewClothAsset,
	USkeletalMesh* NewBodyMesh)
{
	if (!TargetAsset)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error, TEXT("ReplaceSizedOutfitSourceAsset: TargetAsset is null."));
		return false;
	}
	if (!NewClothAsset)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error, TEXT("ReplaceSizedOutfitSourceAsset: NewClothAsset is null."));
		return false;
	}

	IDataflowInstanceInterface* Interface = UE::Dataflow::InstanceUtils::GetDataflowInterfaceFromObject(TargetAsset);
	if (!Interface)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("ReplaceSizedOutfitSourceAsset: '%s' does not implement IDataflowInstanceInterface."),
			*TargetAsset->GetPathName());
		return false;
	}

	FDataflowInstance& Instance = Interface->GetDataflowInstance();
	FDataflowVariableOverrides& Overrides = Instance.GetVariableOverrides();

	// Start from the current per-asset override if there is one, otherwise from the owning
	// Dataflow asset's default value - either way, this preserves SizeName/SourceBodyParts on
	// every existing entry, we only touch SourceAsset below.
	const FInstancedPropertyBag* SourceBag = nullptr;
	if (Overrides.IsVariableOverridden(VariableName))
	{
		SourceBag = &Overrides.GetVariables();
	}
	else if (const UDataflow* DataflowAsset = Instance.GetDataflowAsset())
	{
		SourceBag = &DataflowAsset->Variables;
	}

	if (!SourceBag)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("ReplaceSizedOutfitSourceAsset: '%s' has no Dataflow asset assigned."),
			*TargetAsset->GetPathName());
		return false;
	}

	TArray<FChaosSizedOutfitSource> SizedOutfitSources;
	const TValueOrError<const FPropertyBagArrayRef, EPropertyBagResult> ArrayResult = SourceBag->GetArrayRef(VariableName);
	if (ArrayResult.HasValue())
	{
		const FPropertyBagArrayRef& ArrayRef = ArrayResult.GetValue();
		for (int32 Index = 0; Index < ArrayRef.Num(); ++Index)
		{
			const TValueOrError<FChaosSizedOutfitSource*, EPropertyBagResult> ElementResult =
				ArrayRef.GetValueStruct<FChaosSizedOutfitSource>(Index);
			if (ElementResult.HasValue())
			{
				SizedOutfitSources.Add(*ElementResult.GetValue());
			}
		}
	}

	if (SizedOutfitSources.IsEmpty())
	{
		// Nothing to copy forward (variable not found, or currently empty) - start a single
		// fresh entry. GetBodySizeName() falls back to the first body part name, or "Default".
		SizedOutfitSources.AddDefaulted();
	}

	for (FChaosSizedOutfitSource& Source : SizedOutfitSources)
	{
		Source.SourceAsset = NewClothAsset;
		if (NewBodyMesh)
		{
			Source.SourceBodyParts = { NewBodyMesh };
		}
	}

	return OverrideSizedOutfitSourceVariable(TargetAsset, VariableName, SizedOutfitSources);
}

bool UMBForgeOutfitDataflowLibrary::SetDataflowNodeObjectProperty(
	UDataflow* Dataflow,
	FName NodeName,
	FName PropertyName,
	UObject* NewValue)
{
	if (!Dataflow)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error, TEXT("SetDataflowNodeObjectProperty: Dataflow is null."));
		return false;
	}

	const TSharedPtr<UE::Dataflow::FGraph> Graph = Dataflow->GetDataflow();
	if (!Graph)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("SetDataflowNodeObjectProperty: '%s' has no graph."), *Dataflow->GetPathName());
		return false;
	}

	const TSharedPtr<FDataflowNode> Node = Graph->FindBaseNode(NodeName);
	if (!Node)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("SetDataflowNodeObjectProperty: node '%s' not found in '%s'."),
			*NodeName.ToString(), *Dataflow->GetPathName());
		return false;
	}

	const UScriptStruct* NodeStruct = Node->TypedScriptStruct();
	const FProperty* Property = NodeStruct ? NodeStruct->FindPropertyByName(PropertyName) : nullptr;
	const FObjectPropertyBase* ObjectProperty = CastField<FObjectPropertyBase>(Property);
	if (!ObjectProperty)
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("SetDataflowNodeObjectProperty: property '%s' not found on node '%s', or is not an object-reference property."),
			*PropertyName.ToString(), *NodeName.ToString());
		return false;
	}

	if (NewValue && !NewValue->IsA(ObjectProperty->PropertyClass))
	{
		UE_LOG(LogMBForgeOutfitDataflow, Error,
			TEXT("SetDataflowNodeObjectProperty: '%s' is a %s, but node '%s's property '%s' expects a %s."),
			*NewValue->GetPathName(), *NewValue->GetClass()->GetName(),
			*NodeName.ToString(), *PropertyName.ToString(), *ObjectProperty->PropertyClass->GetName());
		return false;
	}

	Dataflow->Modify();

	// NewStructOnScope() wraps the node's own live memory rather than copying it (see the
	// DATAFLOW_NODE_DEFINE_INTERNAL macro), so writing through it mutates the real node in place.
	const TUniquePtr<FStructOnScope> StructOnScope(Node->NewStructOnScope());
	void* PropertyAddress = ObjectProperty->ContainerPtrToValuePtr<void>(StructOnScope->GetStructMemory());
	ObjectProperty->SetObjectPropertyValue(PropertyAddress, NewValue);

	// The built-in UDataflowEditorBlueprintLibrary::SetDataflowNodeProperty skips this step,
	// which leaves the node's cached output stale - RegenerateAssetFromDataflow silently keeps
	// using the old value without it.
	Node->Invalidate();
	Dataflow->RefreshEdNodeByGuid(Node->GetGuid());
	Dataflow->MarkPackageDirty();
	return true;
}
