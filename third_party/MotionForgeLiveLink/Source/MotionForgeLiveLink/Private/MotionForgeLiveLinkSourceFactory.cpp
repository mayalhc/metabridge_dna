// Copyright 2026 Chamiseul. All Rights Reserved.
#include "MotionForgeLiveLinkSourceFactory.h"

#include "MotionForgeLiveLinkSource.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "MotionForgeLiveLinkSourceFactory"

namespace
{
	const FString DefaultConnection = TEXT("127.0.0.1:9560");

	/** "host:port" -> the two halves, with the defaults when it is malformed. */
	void ParseConnection(const FString& Connection, FString& OutHost, uint16& OutPort)
	{
		OutHost = TEXT("127.0.0.1");
		OutPort = 9560;

		FString Host;
		FString Port;
		if (Connection.Split(TEXT(":"), &Host, &Port))
		{
			Host.TrimStartAndEndInline();
			Port.TrimStartAndEndInline();
			if (!Host.IsEmpty())
			{
				OutHost = Host;
			}
			const int32 Number = FCString::Atoi(*Port);
			if (Number > 0 && Number <= 65535)
			{
				OutPort = static_cast<uint16>(Number);
			}
		}
		else if (!Connection.IsEmpty())
		{
			OutHost = Connection;
		}
	}
}

FText UMotionForgeLiveLinkSourceFactory::GetSourceDisplayName() const
{
	return LOCTEXT("DisplayName", "MotionForge");
}

FText UMotionForgeLiveLinkSourceFactory::GetSourceTooltip() const
{
	return LOCTEXT("Tooltip",
		"Motion streamed from MotionForge in Blender, as it is generated.");
}

ULiveLinkSourceFactory::EMenuType UMotionForgeLiveLinkSourceFactory::GetMenuType() const
{
	return EMenuType::SubPanel;
}

TSharedPtr<SWidget> UMotionForgeLiveLinkSourceFactory::BuildCreationPanel(
	FOnLiveLinkSourceCreated OnSourceCreated) const
{
	TSharedRef<SEditableTextBox> AddressBox = SNew(SEditableTextBox)
		.Text(FText::FromString(DefaultConnection))
		.MinDesiredWidth(180.0f);

	return SNew(SBox)
		.Padding(8.0f)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("Address", "Address of the MotionForge stream"))
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 4.0f)
			[
				AddressBox
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SNew(STextBlock)
				.Text(LOCTEXT("Hint",
					"Turn on Stream to Unreal in Blender's Live Path panel."))
				.AutoWrapText(true)
			]
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 8.0f, 0.0f, 0.0f)
			[
				SNew(SButton)
				.Text(LOCTEXT("Add", "Add"))
				.OnClicked_Lambda([this, AddressBox, OnSourceCreated]() -> FReply
				{
					const FString Connection = AddressBox->GetText().ToString();
					FString Host;
					uint16 Port = 9560;
					ParseConnection(Connection, Host, Port);
					OnSourceCreated.ExecuteIfBound(
						MakeShared<FMotionForgeLiveLinkSource>(Host, Port),
						Connection);
					return FReply::Handled();
				})
			]
		];
}

TSharedPtr<ILiveLinkSource> UMotionForgeLiveLinkSourceFactory::CreateSource(
	const FString& ConnectionString) const
{
	FString Host;
	uint16 Port = 9560;
	ParseConnection(ConnectionString.IsEmpty() ? DefaultConnection : ConnectionString,
	                Host, Port);
	return MakeShared<FMotionForgeLiveLinkSource>(Host, Port);
}

#undef LOCTEXT_NAMESPACE
