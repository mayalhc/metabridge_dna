// Copyright 2026 Chamiseul. All Rights Reserved.
#include "MotionForgeSender.h"

#include "Animation/AnimInstance.h"
#include "Common/TcpListener.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/Skeleton.h"
#include "Engine/SkinnedAssetCommon.h"
#include "GameFramework/Actor.h"
#include "HAL/IConsoleManager.h"
#include "Sockets.h"

#if WITH_EDITOR
#include "Editor.h"
#include "Selection.h"
#endif

DEFINE_LOG_CATEGORY_STATIC(LogMotionForgeSend, Log, All);

namespace
{
	/** Unreal is left handed and Blender is not, so one axis is reflected on
	 *  the way out. A point moves by the reflection and a rotation against it,
	 *  a rotation being a pseudovector - the same rule the incoming stream
	 *  uses, and its own inverse. */
	FVector MirrorPoint(const FVector& V)
	{
		return FVector(V.X, -V.Y, V.Z);
	}

	FVector MirrorTurn(const FQuat& Q)
	{
		FVector Axis;
		float Angle = 0.0f;
		Q.ToAxisAndAngle(Axis, Angle);
		if (Angle < KINDA_SMALL_NUMBER)
		{
			return FVector::ZeroVector;
		}
		const FVector Turn = Axis * Angle;
		return FVector(-Turn.X, Turn.Y, -Turn.Z);
	}

	FString Triple(const FVector& V)
	{
		return FString::Printf(TEXT("[%.6f,%.6f,%.6f]"), V.X, V.Y, V.Z);
	}
}

FMotionForgeSender& FMotionForgeSender::Get()
{
	static FMotionForgeSender Instance;
	return Instance;
}

bool FMotionForgeSender::Start(uint16 InPort)
{
	Stop();

#if WITH_EDITOR
	// Whatever is selected, so there is nothing to configure and nothing to
	// get out of step with the level.
	if (GEditor != nullptr)
	{
		for (FSelectionIterator It(GEditor->GetSelectedActorIterator()); It; ++It)
		{
			AActor* Actor = Cast<AActor>(*It);
			if (Actor == nullptr)
			{
				continue;
			}
			TArray<USkeletalMeshComponent*> Found;
			Actor->GetComponents(Found);
			for (USkeletalMeshComponent* Component : Found)
			{
				const FString Name = Component->GetName();
				if (Name.Contains(TEXT("Face")))
				{
					Face = Component;
				}
				else if (Name.Contains(TEXT("Body")) || !Body.IsValid())
				{
					Body = Component;
				}
			}
		}
	}
#endif

	if (!Body.IsValid() && !Face.IsValid())
	{
		UE_LOG(LogMotionForgeSend, Warning,
		       TEXT("Nothing to send: select the MetaHuman in the level first."));
		return false;
	}

	Listener = new FTcpListener(FIPv4Endpoint(FIPv4Address(127, 0, 0, 1), InPort));
	if (!Listener->IsActive())
	{
		delete Listener;
		Listener = nullptr;
		UE_LOG(LogMotionForgeSend, Error, TEXT("Could not listen on port %d."), InPort);
		return false;
	}
	Listener->OnConnectionAccepted().BindRaw(this, &FMotionForgeSender::OnConnection);

	Describe();
	FrameIndex = 0;
	Accumulated = 0.0f;
	TickHandle = FTSTicker::GetCoreTicker().AddTicker(
		TEXT("MotionForgeSender"), 0.0f,
		[this](float DeltaTime) { return Tick(DeltaTime); });

	UE_LOG(LogMotionForgeSend, Log,
	       TEXT("Sending on 127.0.0.1:%d - %d bones, %d curves."),
	       InPort, BoneNames.Num(), CurveNames.Num());
	return true;
}

void FMotionForgeSender::Stop()
{
	if (TickHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
		TickHandle.Reset();
	}
	if (Listener != nullptr)
	{
		Listener->Stop();
		delete Listener;
		Listener = nullptr;
	}
	FScopeLock Lock(&ClientLock);
	for (FSocket* Client : Clients)
	{
		Client->Close();
	}
	Clients.Reset();
	Body.Reset();
	Face.Reset();
	BoneNames.Reset();
	BoneParents.Reset();
	CurveNames.Reset();
	Hello.Reset();
}

bool FMotionForgeSender::OnConnection(FSocket* InSocket, const FIPv4Endpoint& Endpoint)
{
	{
		FScopeLock Lock(&ClientLock);
		Clients.Add(InSocket);
	}
	// A joiner needs the names before any numbers mean anything.
	if (!Hello.IsEmpty())
	{
		Broadcast(Hello);
	}
	return true;
}

void FMotionForgeSender::Describe()
{
	BoneNames.Reset();
	BoneParents.Reset();
	CurveNames.Reset();

	if (Body.IsValid() && Body->GetSkinnedAsset() != nullptr)
	{
		const FReferenceSkeleton& Reference =
			Body->GetSkinnedAsset()->GetRefSkeleton();
		for (int32 Index = 0; Index < Reference.GetNum(); ++Index)
		{
			BoneNames.Add(Reference.GetBoneName(Index));
			BoneParents.Add(Reference.GetParentIndex(Index));
		}
	}

	// The face's curves are the raw controls Rig Logic reads, and their names
	// are the DNA's with the dot written as an underscore.
	if (Face.IsValid() && Face->GetSkinnedAsset() != nullptr)
	{
		if (USkeleton* Skeleton = Face->GetSkinnedAsset()->GetSkeleton())
		{
			Skeleton->ForEachCurveMetaData(
				[this](const FName& Name, const FCurveMetaData&)
				{
					if (Name.ToString().StartsWith(TEXT("CTRL_expressions_")))
					{
						CurveNames.Add(Name);
					}
				});
		}
	}

	FString Joints, Parents, Curves;
	for (int32 Index = 0; Index < BoneNames.Num(); ++Index)
	{
		Joints += FString::Printf(TEXT("%s\"%s\""), Index ? TEXT(",") : TEXT(""),
		                          *BoneNames[Index].ToString());
		Parents += (BoneParents[Index] == INDEX_NONE)
			? FString::Printf(TEXT("%snull"), Index ? TEXT(",") : TEXT(""))
			: FString::Printf(TEXT("%s%d"), Index ? TEXT(",") : TEXT(""),
			                  BoneParents[Index]);
	}
	for (int32 Index = 0; Index < CurveNames.Num(); ++Index)
	{
		Curves += FString::Printf(TEXT("%s\"%s\""), Index ? TEXT(",") : TEXT(""),
		                          *CurveNames[Index].ToString());
	}

	Hello = FString::Printf(
		TEXT("{\"type\":\"hello\",\"protocol\":1,\"skeleton\":\"unreal_metahuman\","
		     "\"joints\":[%s],\"parents\":[%s],\"rest\":[],\"space\":\"local\","
		     "\"fps\":%.1f,\"up\":\"z\",\"curves\":[%s]}"),
		*Joints, *Parents, 1.0f / Interval, *Curves);
}

bool FMotionForgeSender::Tick(float DeltaTime)
{
	Accumulated += DeltaTime;
	if (Accumulated < Interval)
	{
		return true;
	}
	Accumulated = 0.0f;

	{
		FScopeLock Lock(&ClientLock);
		if (Clients.Num() == 0)
		{
			return true;
		}
	}
	SendFrame();
	return true;
}

void FMotionForgeSender::SendFrame()
{
	FString Pose, Moved, Values;

	if (Body.IsValid())
	{
		// Bone space is parent relative, which is what the far end applies.
		const TArray<FTransform> Local = Body->GetBoneSpaceTransforms();
		for (int32 Index = 0; Index < BoneNames.Num(); ++Index)
		{
			const FTransform& Bone = Local.IsValidIndex(Index)
				? Local[Index] : FTransform::Identity;
			Pose += FString::Printf(TEXT("%s%s"), Index ? TEXT(",") : TEXT(""),
			                        *Triple(MirrorTurn(Bone.GetRotation())));
			Moved += FString::Printf(TEXT("%s%s"), Index ? TEXT(",") : TEXT(""),
			                         *Triple(MirrorPoint(Bone.GetTranslation())));
		}
	}

	if (Face.IsValid())
	{
		if (UAnimInstance* Instance = Face->GetAnimInstance())
		{
			for (int32 Index = 0; Index < CurveNames.Num(); ++Index)
			{
				Values += FString::Printf(TEXT("%s%.6f"), Index ? TEXT(",") : TEXT(""),
				                          Instance->GetCurveValue(CurveNames[Index]));
			}
		}
	}

	FString Line = FString::Printf(
		TEXT("{\"type\":\"frame\",\"index\":%d,\"time\":%.6f"),
		FrameIndex, FrameIndex * Interval);
	if (!Pose.IsEmpty())
	{
		Line += FString::Printf(TEXT(",\"pose\":[%s],\"moved\":[%s]"), *Pose, *Moved);
	}
	if (!Values.IsEmpty())
	{
		Line += FString::Printf(TEXT(",\"curves\":[%s]"), *Values);
	}
	Line += TEXT("}");

	Broadcast(Line);
	++FrameIndex;
}

void FMotionForgeSender::Broadcast(const FString& Line)
{
	const FTCHARToUTF8 Utf8(*(Line + TEXT("\n")));
	const uint8* Data = reinterpret_cast<const uint8*>(Utf8.Get());
	const int32 Length = Utf8.Length();

	FScopeLock Lock(&ClientLock);
	for (int32 Index = Clients.Num() - 1; Index >= 0; --Index)
	{
		int32 Written = 0;
		if (!Clients[Index]->Send(Data, Length, Written) || Written != Length)
		{
			Clients[Index]->Close();
			Clients.RemoveAt(Index);
		}
	}
}

static FAutoConsoleCommand StartCommand(
	TEXT("MotionForge.Send.Start"),
	TEXT("Send the selected MetaHuman's pose to Blender. Optional port, 9562 by default."),
	FConsoleCommandWithArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args)
		{
			const uint16 Port = Args.Num() > 0
				? static_cast<uint16>(FCString::Atoi(*Args[0])) : 9562;
			FMotionForgeSender::Get().Start(Port);
		}));

static FAutoConsoleCommand StopCommand(
	TEXT("MotionForge.Send.Stop"),
	TEXT("Stop sending."),
	FConsoleCommandDelegate::CreateStatic(
		[]() { FMotionForgeSender::Get().Stop(); }));
