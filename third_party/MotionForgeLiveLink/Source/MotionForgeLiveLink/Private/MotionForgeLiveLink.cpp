// Copyright 2026 Chamiseul. All Rights Reserved.
#include "MotionForgeLiveLink.h"

#if WITH_EDITOR
#include "MotionForgeSender.h"
#include "ToolMenus.h"
#endif

#define LOCTEXT_NAMESPACE "FMotionForgeLiveLinkModule"

#if WITH_EDITOR
namespace
{
	/** Start against the selection, or stop if it is already going. */
	void ToggleSending()
	{
		FMotionForgeSender& Sender = FMotionForgeSender::Get();
		if (Sender.IsRunning())
		{
			Sender.Stop();
		}
		else
		{
			Sender.Start(9562);
		}
	}

	void BuildMenu()
	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu(TEXT("LevelEditor.MainMenu.Tools"));
		if (Menu == nullptr)
		{
			return;
		}

		FToolMenuSection& Section = Menu->FindOrAddSection(
			TEXT("MotionForge"), LOCTEXT("SectionLabel", "MotionForge"));

		Section.AddDynamicEntry(TEXT("MotionForgeSend"),
			FNewToolMenuSectionDelegate::CreateLambda(
				[](FToolMenuSection& InSection)
				{
					const bool bRunning = FMotionForgeSender::Get().IsRunning();
					InSection.AddMenuEntry(
						TEXT("MotionForgeSendToggle"),
						bRunning
							? LOCTEXT("StopLabel", "Stop Sending to Blender")
							: LOCTEXT("StartLabel", "Send Selected to Blender"),
						bRunning
							? LOCTEXT("StopTip", "Stop the stream Blender is following.")
							: LOCTEXT("StartTip",
							          "Send the selected MetaHuman's pose and "
							          "expression on port 9562, for Blender's "
							          "Follow Unreal panel to pick up."),
						FSlateIcon(),
						FUIAction(FExecuteAction::CreateStatic(&ToggleSending)));
				}));
	}
}
#endif

void FMotionForgeLiveLinkModule::StartupModule()
{
#if WITH_EDITOR
	// A menu entry rather than a console command: the same thing, reachable
	// without remembering its name or which mode the console is in.
	UToolMenus::RegisterStartupCallback(
		FSimpleMulticastDelegate::FDelegate::CreateStatic(&BuildMenu));
#endif
}

void FMotionForgeLiveLinkModule::ShutdownModule()
{
#if WITH_EDITOR
	UToolMenus::UnRegisterStartupCallback(this);
	UToolMenus::UnregisterOwner(this);
	FMotionForgeSender::Get().Stop();
#endif
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMotionForgeLiveLinkModule, MotionForgeLiveLink)
