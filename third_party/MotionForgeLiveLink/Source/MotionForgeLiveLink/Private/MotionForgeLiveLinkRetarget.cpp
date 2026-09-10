// Copyright 2026 Chamiseul. All Rights Reserved.
#include "MotionForgeLiveLinkRetarget.h"

#include "BonePose.h"
#include "Roles/LiveLinkAnimationTypes.h"

UMotionForgeLiveLinkRetarget::UMotionForgeLiveLinkRetarget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

void UMotionForgeLiveLinkRetarget::BuildPoseFromAnimationData(
	float DeltaTime,
	const FLiveLinkSkeletonStaticData* InSkeletonData,
	const FLiveLinkAnimationFrameData* InFrameData,
	FCompactPose& OutPose)
{
	if (InSkeletonData == nullptr || InFrameData == nullptr)
	{
		return;
	}

	const TArray<FName>& BoneNames = InSkeletonData->BoneNames;
	const int32 Count = FMath::Min(BoneNames.Num(), InFrameData->Transforms.Num());
	const FBoneContainer& Bones = OutPose.GetBoneContainer();

	for (int32 Index = 0; Index < Count; ++Index)
	{
		const FName BoneName = BoneNames[Index];

		int32* Cached = BoneIndexCache.Find(BoneName);
		if (Cached == nullptr)
		{
			Cached = &BoneIndexCache.Add(
				BoneName, Bones.GetPoseBoneIndexForBoneName(BoneName));
		}
		if (*Cached == INDEX_NONE)
		{
			continue;
		}

		const FCompactPoseBoneIndex PoseIndex =
			Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(*Cached));
		if (PoseIndex == INDEX_NONE)
		{
			continue;
		}

		FTransform Change = InFrameData->Transforms[Index];
		FTransform& Bone = OutPose[PoseIndex];

		const bool bIsRoot = PoseIndex == FCompactPoseBoneIndex(0);
		if (!bApplyTranslation && !bIsRoot)
		{
			Change.SetTranslation(FVector::ZeroVector);
		}

		// One composition rather than a rotation and a translation handled
		// separately: FQuat and FTransform read their operands in opposite
		// orders, and mixing them silently produced a pose that was almost
		// right. This follows the engine's own, where a component-space
		// transform is built as child-local times parent - so the change,
		// which is in the bone's frame, goes first and the rest carries it
		// into the parent's.
		Bone = Change * Bone;
		Bone.NormalizeRotation();
	}
}

void UMotionForgeLiveLinkRetarget::BuildPoseAndCurveFromBaseData(
	float DeltaTime,
	const FLiveLinkBaseStaticData* InBaseStaticData,
	const FLiveLinkBaseFrameData* InBaseFrameData,
	FCompactPose& OutPose,
	FBlendedCurve& OutCurve)
{
	if (InBaseStaticData == nullptr || InBaseFrameData == nullptr)
	{
		return;
	}

	// Names are already what the receiving skeleton calls them - the stream
	// sends Unreal's spelling - so there is nothing to remap on the way in.
	const TArray<FName>& CurveNames = InBaseStaticData->PropertyNames;
	if (CurveNames.Num() != InBaseFrameData->PropertyValues.Num())
	{
		return;
	}

	TMap<FName, float> CurveMap;
	CurveMap.Reserve(CurveNames.Num());
	for (int32 Index = 0; Index < CurveNames.Num(); ++Index)
	{
		const float Value = InBaseFrameData->PropertyValues[Index];
		if (FMath::IsFinite(Value))
		{
			CurveMap.Add(CurveNames[Index], Value);
		}
	}

	BuildCurveData(CurveMap, OutPose, OutCurve);
}
