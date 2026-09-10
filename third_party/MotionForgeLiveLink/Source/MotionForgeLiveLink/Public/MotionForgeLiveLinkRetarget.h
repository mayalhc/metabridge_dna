// Copyright 2026 Chamiseul. All Rights Reserved.
// Applies MotionForge's pose as a change to the character's own rest pose.

#pragma once

#include "CoreMinimal.h"
#include "LiveLinkRetargetAsset.h"

#include "MotionForgeLiveLinkRetarget.generated.h"

/**
 * A retargeter that adds to the reference pose instead of replacing it.
 *
 * The stock remapper writes each streamed transform straight into the bone's
 * local slot, which is only right when the sending and receiving skeletons
 * hold their bones the same way round. MotionForge's driver rig is built for
 * that; a MetaHuman is not - its bones carry real orientations, and writing
 * over them pulls the character apart.
 *
 * So the body stream sends a change from rest rather than a pose: how far each
 * bone has turned from where it sits in the reference pose. Live Link hands
 * this class a pose that already holds the reference, so applying the change
 * is a multiply, and the character keeps its own proportions and its own bone
 * orientations. It also means a pose made on one body drives another - the
 * same way the face stream carries expressions rather than geometry.
 *
 * Curves pass through unchanged, so one subject can carry a face and a body.
 */
UCLASS(Blueprintable)
class MOTIONFORGELIVELINK_API UMotionForgeLiveLinkRetarget : public ULiveLinkRetargetAsset
{
	GENERATED_UCLASS_BODY()

public:
	virtual void BuildPoseFromAnimationData(
		float DeltaTime,
		const FLiveLinkSkeletonStaticData* InSkeletonData,
		const FLiveLinkAnimationFrameData* InFrameData,
		FCompactPose& OutPose) override;

	virtual void BuildPoseAndCurveFromBaseData(
		float DeltaTime,
		const FLiveLinkBaseStaticData* InBaseStaticData,
		const FLiveLinkBaseFrameData* InBaseFrameData,
		FCompactPose& OutPose,
		FBlendedCurve& OutCurve) override;

	/**
	 * Move the bones as well as turn them.
	 *
	 * On, because a pose is not rotation alone: dropping the hips moves the
	 * pelvis down and bends the knees, and with only the bend arriving the
	 * character keeps its hips where they were and lifts its feet instead. A
	 * bone that merely turns sends no movement, so this costs those nothing.
	 *
	 * Turn it off to carry a pose onto a body of a different build, where the
	 * sender's bone positions would stretch the receiver to match.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MotionForge")
	bool bApplyTranslation = true;

private:
	/** Bone name to index in the receiving skeleton, worked out once. */
	TMap<FName, int32> BoneIndexCache;
};
