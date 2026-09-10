// Copyright 2026 Chamiseul. All Rights Reserved.
// Puts MotionForge in Live Link's "Add Source" list.

#pragma once

#include "CoreMinimal.h"
#include "LiveLinkSourceFactory.h"
#include "MotionForgeLiveLinkSourceFactory.generated.h"

UCLASS()
class MOTIONFORGELIVELINK_API UMotionForgeLiveLinkSourceFactory : public ULiveLinkSourceFactory
{
	GENERATED_BODY()

public:
	virtual FText GetSourceDisplayName() const override;
	virtual FText GetSourceTooltip() const override;
	virtual EMenuType GetMenuType() const override;
	virtual TSharedPtr<SWidget> BuildCreationPanel(
		FOnLiveLinkSourceCreated OnSourceCreated) const override;
	virtual TSharedPtr<ILiveLinkSource> CreateSource(
		const FString& ConnectionString) const override;
};
