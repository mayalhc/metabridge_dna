// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class MetaBridgeForge : ModuleRules
{
	public MetaBridgeForge(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				// FChaosSizedOutfitSource is part of our own public UFUNCTION signatures,
				// so this needs to be a public (not private) dependency.
				"ChaosOutfitAssetEngine",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				// UChaosClothAssetBase (the type SizedOutfitSource.SourceAsset points at).
				"ChaosClothAssetEngine",
				// FDataflowInstance, FDataflowVariableOverrides, IDataflowInstanceInterface, UDataflow.
				"DataflowEngine",
				// FDataflowNode, UE::Dataflow::FGraph (used directly in SetDataflowNodeObjectProperty).
				"DataflowCore",
				// FHairDescription, for handing a package's strands to Blender.
				"HairStrandsCore",
			}
		);
	}
}
