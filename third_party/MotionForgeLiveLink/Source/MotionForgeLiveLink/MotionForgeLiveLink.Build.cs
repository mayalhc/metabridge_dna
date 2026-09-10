// Copyright 2026 Chamiseul. All Rights Reserved.
using UnrealBuildTool;

public class MotionForgeLiveLink : ModuleRules
{
	public MotionForgeLiveLink(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				// ILiveLinkSource and ULiveLinkSourceFactory are part of the
				// types this module publicly derives from.
				"LiveLinkInterface",
				// ULiveLinkRetargetAsset, which the body path subclasses so a
				// streamed pose can be added to a character's own rest pose.
				"LiveLinkAnimationCore",
			}
		);

		if (Target.bBuildEditor)
		{
			// The sender follows whatever is selected in the editor, and puts
			// its own entry in the Tools menu.
			PrivateDependencyModuleNames.AddRange(
				new string[] { "UnrealEd", "ToolMenus" });
		}

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				// The reader thread owns a TCP socket of its own.
				"Sockets",
				"Networking",
				// The wire format is one JSON object per line.
				"Json",
				// IModularFeatures / the Live Link client feature name.
				"Projects",
				// The factory's "add source" panel.
				"Slate",
				"SlateCore",
				"InputCore",
			}
		);
	}
}
