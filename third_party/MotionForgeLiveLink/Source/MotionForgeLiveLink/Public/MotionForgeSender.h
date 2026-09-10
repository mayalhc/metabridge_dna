// Copyright 2026 Chamiseul. All Rights Reserved.
// Sends a MetaHuman's evaluated pose back out, for Blender to follow.

#pragma once

#include "CoreMinimal.h"
#include "UObject/WeakObjectPtr.h"
#include "Containers/Ticker.h"
#include "Interfaces/IPv4/IPv4Endpoint.h"

class FSocket;
class FTcpListener;
class USkeletalMeshComponent;

/**
 * Reads the character Unreal is showing and hands it to whoever connects.
 *
 * Live Link only carries data into Unreal, so the way back is a socket of our
 * own. The wire format is the one the Blender add-on already speaks - a JSON
 * object per line, a hello then a frame each tick - so the receiving end is
 * the mirror of the sending end rather than a second protocol.
 *
 * The evaluated bones are read, not the Control Rig's controls. Whatever moved
 * the character - a control rig in a sequence, a baked animation, Live Link
 * coming the other way - ends up in the same bones, so reading those works for
 * all of it and needs no knowledge of a MetaHuman's several hundred controls.
 */
class FMotionForgeSender
{
public:
	static FMotionForgeSender& Get();

	/** Listen, and follow the actor currently selected in the editor. */
	bool Start(uint16 InPort);
	void Stop();
	bool IsRunning() const { return Listener != nullptr; }

private:
	bool OnConnection(FSocket* InSocket, const FIPv4Endpoint& Endpoint);
	bool Tick(float DeltaTime);
	void Describe();
	void SendFrame();
	void Broadcast(const FString& Line);

	FTcpListener* Listener = nullptr;
	TArray<FSocket*> Clients;
	FCriticalSection ClientLock;
	FTSTicker::FDelegateHandle TickHandle;

	TWeakObjectPtr<USkeletalMeshComponent> Body;
	TWeakObjectPtr<USkeletalMeshComponent> Face;

	TArray<FName> BoneNames;
	TArray<int32> BoneParents;
	TArray<FName> CurveNames;
	FString Hello;

	int32 FrameIndex = 0;
	float Accumulated = 0.0f;
	float Interval = 1.0f / 30.0f;
};
