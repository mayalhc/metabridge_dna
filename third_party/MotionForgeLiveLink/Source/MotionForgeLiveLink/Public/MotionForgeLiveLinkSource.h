// Copyright 2026 Chamiseul. All Rights Reserved.
// MotionForge Live Link source: reads the motion stream and publishes it.

#pragma once

#include "CoreMinimal.h"
#include "HAL/Runnable.h"
#include "HAL/ThreadSafeBool.h"
#include "ILiveLinkSource.h"

class FRunnableThread;
class FSocket;

/**
 * Connects to MotionForge's motion stream and pushes what arrives into Live
 * Link as an animation subject.
 *
 * The stream is one JSON object per line over TCP: a "hello" describing the
 * skeleton, then a "frame" per frame of motion. Reading happens on its own
 * thread, because the generator emits a couple of seconds of motion in one go
 * and the game thread must not wait for it.
 */
class FMotionForgeLiveLinkSource : public ILiveLinkSource, public FRunnable
{
public:
	FMotionForgeLiveLinkSource(const FString& InHost, uint16 InPort);
	virtual ~FMotionForgeLiveLinkSource();

	// ILiveLinkSource
	virtual void ReceiveClient(ILiveLinkClient* InClient, FGuid InSourceGuid) override;
	virtual bool IsSourceStillValid() const override;
	virtual bool RequestSourceShutdown() override;
	virtual FText GetSourceType() const override;
	virtual FText GetSourceMachineName() const override;
	virtual FText GetSourceStatus() const override;

	// FRunnable
	virtual bool Init() override;
	virtual uint32 Run() override;
	virtual void Stop() override;
	virtual void Exit() override;

private:
	bool Connect();
	void Disconnect();
	void HandleLine(const FString& Line);
	void HandleHello(const TSharedPtr<class FJsonObject>& Object);
	void HandleFrame(const TSharedPtr<class FJsonObject>& Object);

	ILiveLinkClient* Client = nullptr;
	FGuid SourceGuid;
	/** Named after the stream's skeleton once the hello arrives. */
	FLiveLinkSubjectKey SubjectKey;
	static const FName DefaultSubjectName;

	FString Host;
	uint16 Port = 9560;

	FSocket* Socket = nullptr;
	FRunnableThread* Thread = nullptr;
	FThreadSafeBool bRunning = false;
	FThreadSafeBool bConnected = false;

	/** Joint names and parents from the hello, in stream order. */
	TArray<FName> BoneNames;
	TArray<int32> BoneParents;
	/** Rest position of each joint, already in Unreal's axes and units. */
	TArray<FVector> RestPositions;
	/** Each joint's offset from its parent's rest position. */
	TArray<FVector> BoneOffsets;

	/**
	 * Named float curves the stream carries alongside the pose, in stream
	 * order. A MetaHuman face is driven this way rather than by moving bones:
	 * a few hundred control values that Rig Logic evaluates into the rig at
	 * this end. Empty for a sender that only has a skeleton.
	 */
	TArray<FName> CurveNames;

	/**
	 * The stream sends each bone's change from its rest pose, in the skeleton's
	 * own space, rather than a pose in ARDY's. Set by the hello's "space"
	 * field. Nothing is converted in this mode - the sender is already
	 * speaking the receiver's language - and the frames are meant for
	 * UMotionForgeLiveLinkRetarget, which adds them to the reference pose.
	 */
	bool bLocalDelta = false;

	FThreadSafeCounter FramesReceived;
	FString Skeleton;
	double FrameRate = 0.0;

	mutable FCriticalSection StatusLock;
	FString StatusText;

	void SetStatus(const FString& Text);
};
