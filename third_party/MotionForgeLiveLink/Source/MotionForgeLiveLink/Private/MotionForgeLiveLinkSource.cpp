// Copyright 2026 Chamiseul. All Rights Reserved.
#include "MotionForgeLiveLinkSource.h"

#include "Common/TcpSocketBuilder.h"
#include "Dom/JsonObject.h"
#include "HAL/RunnableThread.h"
#include "ILiveLinkClient.h"
#include "Roles/LiveLinkAnimationRole.h"
#include "Roles/LiveLinkAnimationTypes.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "SocketSubsystem.h"
#include "Sockets.h"

#define LOCTEXT_NAMESPACE "MotionForgeLiveLink"

DEFINE_LOG_CATEGORY_STATIC(LogMotionForge, Log, All);

namespace
{
	/** MotionForge streams metres, Y up, right handed. Unreal is centimetres,
	 *  Z up, left handed. Swapping Y and Z does both at once. */
	constexpr float MetresToCentimetres = 100.0f;

	FVector ToUnrealPosition(double X, double Y, double Z)
	{
		return FVector(static_cast<float>(X) * MetresToCentimetres,
		               static_cast<float>(Z) * MetresToCentimetres,
		               static_cast<float>(Y) * MetresToCentimetres);
	}

	/** The same swap, applied to a rotation rather than a point. */
	FQuat ToUnrealRotation(double AxisX, double AxisY, double AxisZ)
	{
		const FVector Axis(AxisX, AxisY, AxisZ);
		const double Angle = Axis.Size();
		if (Angle < UE_DOUBLE_SMALL_NUMBER)
		{
			return FQuat::Identity;
		}

		const FVector Unit = Axis / Angle;
		// Conjugating by the axis swap is the same as swapping the axis and
		// reversing the angle, which is cheaper and avoids a matrix round trip.
		const FVector Swapped(Unit.X, Unit.Z, Unit.Y);
		return FQuat(Swapped, static_cast<float>(-Angle));
	}

	/** Axis-angle straight to a quaternion, for a sender already in our axes. */
	FQuat FromAxisAngle(double X, double Y, double Z)
	{
		const FVector Axis(X, Y, Z);
		const double Angle = Axis.Size();
		if (Angle < UE_DOUBLE_SMALL_NUMBER)
		{
			return FQuat::Identity;
		}
		return FQuat(Axis / Angle, static_cast<float>(Angle));
	}

	bool ReadVector(const TArray<TSharedPtr<FJsonValue>>* Values, FVector& Out)
	{
		if (Values == nullptr || Values->Num() < 3)
		{
			return false;
		}
		Out = ToUnrealPosition((*Values)[0]->AsNumber(),
		                       (*Values)[1]->AsNumber(),
		                       (*Values)[2]->AsNumber());
		return true;
	}
}

const FName FMotionForgeLiveLinkSource::DefaultSubjectName(TEXT("MotionForge"));

FMotionForgeLiveLinkSource::FMotionForgeLiveLinkSource(const FString& InHost, uint16 InPort)
	: Host(InHost)
	, Port(InPort)
{
	SetStatus(TEXT("Not connected"));
}

FMotionForgeLiveLinkSource::~FMotionForgeLiveLinkSource()
{
	RequestSourceShutdown();
}

void FMotionForgeLiveLinkSource::ReceiveClient(ILiveLinkClient* InClient, FGuid InSourceGuid)
{
	Client = InClient;
	SourceGuid = InSourceGuid;
	// A placeholder until the stream says what it is; the hello renames it.
	SubjectKey = FLiveLinkSubjectKey(InSourceGuid, DefaultSubjectName);

	bRunning = true;
	Thread = FRunnableThread::Create(this, TEXT("MotionForgeLiveLink"), 128 * 1024,
	                                 TPri_BelowNormal);
}

bool FMotionForgeLiveLinkSource::IsSourceStillValid() const
{
	return Client != nullptr && bRunning;
}

bool FMotionForgeLiveLinkSource::RequestSourceShutdown()
{
	bRunning = false;
	if (Thread != nullptr)
	{
		Thread->WaitForCompletion();
		delete Thread;
		Thread = nullptr;
	}
	Disconnect();
	Client = nullptr;
	return true;
}

FText FMotionForgeLiveLinkSource::GetSourceType() const
{
	return LOCTEXT("SourceType", "MotionForge");
}

FText FMotionForgeLiveLinkSource::GetSourceMachineName() const
{
	return FText::FromString(FString::Printf(TEXT("%s:%d"), *Host, Port));
}

FText FMotionForgeLiveLinkSource::GetSourceStatus() const
{
	FScopeLock Lock(&StatusLock);
	return FText::FromString(StatusText);
}

void FMotionForgeLiveLinkSource::SetStatus(const FString& Text)
{
	FScopeLock Lock(&StatusLock);
	StatusText = Text;
}

bool FMotionForgeLiveLinkSource::Init()
{
	return true;
}

void FMotionForgeLiveLinkSource::Stop()
{
	bRunning = false;
}

void FMotionForgeLiveLinkSource::Exit()
{
}

bool FMotionForgeLiveLinkSource::Connect()
{
	ISocketSubsystem* Sockets = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (Sockets == nullptr)
	{
		SetStatus(TEXT("No socket subsystem"));
		return false;
	}

	TSharedRef<FInternetAddr> Address = Sockets->CreateInternetAddr();
	bool bValid = false;
	Address->SetIp(*Host, bValid);
	if (!bValid)
	{
		SetStatus(FString::Printf(TEXT("%s is not an address"), *Host));
		return false;
	}
	Address->SetPort(Port);

	Socket = FTcpSocketBuilder(TEXT("MotionForgeStream"))
		.AsBlocking()
		.WithReceiveBufferSize(1 << 20)
		.Build();
	if (Socket == nullptr)
	{
		SetStatus(TEXT("Could not make a socket"));
		return false;
	}

	if (!Socket->Connect(*Address))
	{
		Disconnect();
		SetStatus(FString::Printf(TEXT("Nothing listening on %s:%d"), *Host, Port));
		return false;
	}

	bConnected = true;
	UE_LOG(LogMotionForge, Log, TEXT("Connected to %s:%d, waiting for the skeleton."),
	       *Host, Port);
	SetStatus(TEXT("Connected, waiting for the skeleton"));
	return true;
}

void FMotionForgeLiveLinkSource::Disconnect()
{
	bConnected = false;
	if (Socket != nullptr)
	{
		Socket->Close();
		if (ISocketSubsystem* Sockets = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM))
		{
			Sockets->DestroySocket(Socket);
		}
		Socket = nullptr;
	}
}

uint32 FMotionForgeLiveLinkSource::Run()
{
	FString Pending;
	TArray<uint8> Buffer;
	Buffer.SetNumUninitialized(1 << 16);

	while (bRunning)
	{
		if (!bConnected)
		{
			if (!Connect())
			{
				// Blender may not be streaming yet; keep trying quietly.
				FPlatformProcess::Sleep(1.0f);
				continue;
			}
		}

		// Wait rather than block in Recv: a blocking read cannot be
		// interrupted, so removing the source would hang the editor until the
		// next frame happened to arrive.
		if (!Socket->Wait(ESocketWaitConditions::WaitForRead,
		                  FTimespan::FromMilliseconds(200)))
		{
			continue;
		}

		int32 Read = 0;
		if (!Socket->Recv(Buffer.GetData(), Buffer.Num(), Read) || Read <= 0)
		{
			Disconnect();
			UE_LOG(LogMotionForge, Log, TEXT("Stream closed; reconnecting."));
			SetStatus(TEXT("Stream closed, reconnecting"));
			FPlatformProcess::Sleep(1.0f);
			continue;
		}

		// Recv gives raw bytes, and a read can stop mid-line, so decode exactly
		// what arrived and let the loop below take whole lines off the front.
		const FUTF8ToTCHAR Decoded(
			reinterpret_cast<const ANSICHAR*>(Buffer.GetData()), Read);
		Pending.AppendChars(Decoded.Get(), Decoded.Length());

		int32 Newline = INDEX_NONE;
		while (Pending.FindChar(TEXT('\n'), Newline))
		{
			const FString Line = Pending.Left(Newline);
			Pending.RightChopInline(Newline + 1, EAllowShrinking::No);
			if (!Line.IsEmpty())
			{
				HandleLine(Line);
			}
		}
	}

	Disconnect();
	return 0;
}

void FMotionForgeLiveLinkSource::HandleLine(const FString& Line)
{
	TSharedPtr<FJsonObject> Object;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Line);
	if (!FJsonSerializer::Deserialize(Reader, Object) || !Object.IsValid())
	{
		return;
	}

	const FString Type = Object->GetStringField(TEXT("type"));
	if (Type == TEXT("hello"))
	{
		HandleHello(Object);
	}
	else if (Type == TEXT("frame"))
	{
		HandleFrame(Object);
	}
	else if (Type == TEXT("end"))
	{
		SetStatus(FString::Printf(TEXT("%s, %d frames, take finished"),
		                          *Skeleton, FramesReceived.GetValue()));
	}
}

void FMotionForgeLiveLinkSource::HandleHello(const TSharedPtr<FJsonObject>& Object)
{
	if (Client == nullptr)
	{
		return;
	}

	const TArray<TSharedPtr<FJsonValue>>* Joints = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* Parents = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* Rest = nullptr;
	if (!Object->TryGetArrayField(TEXT("joints"), Joints) ||
	    !Object->TryGetArrayField(TEXT("parents"), Parents))
	{
		SetStatus(TEXT("The stream did not describe a skeleton"));
		return;
	}
	Object->TryGetArrayField(TEXT("rest"), Rest);

	Skeleton = Object->GetStringField(TEXT("skeleton"));
	FrameRate = Object->HasField(TEXT("fps")) ? Object->GetNumberField(TEXT("fps")) : 0.0;

	FString Space;
	Object->TryGetStringField(TEXT("space"), Space);
	bLocalDelta = Space.Equals(TEXT("local-delta"), ESearchCase::IgnoreCase);

	// Name the subject after the skeleton the stream carries, so a body source
	// and a face source can be attached at once. A fixed name meant the second
	// one to connect quietly took over the first one's subject.
	const FName Wanted = Skeleton.IsEmpty() ? DefaultSubjectName : FName(*Skeleton);
	if (SubjectKey.SubjectName != Wanted)
	{
		if (!SubjectKey.SubjectName.IsNone())
		{
			Client->RemoveSubject_AnyThread(SubjectKey);
		}
		SubjectKey = FLiveLinkSubjectKey(SourceGuid, Wanted);
	}

	const int32 Count = Joints->Num();
	BoneNames.Reset(Count);
	BoneParents.Reset(Count);
	RestPositions.Reset(Count);
	BoneOffsets.Reset(Count);

	for (int32 Index = 0; Index < Count; ++Index)
	{
		BoneNames.Add(FName(*(*Joints)[Index]->AsString()));

		int32 Parent = INDEX_NONE;
		if (Parents->IsValidIndex(Index) && !(*Parents)[Index]->IsNull())
		{
			Parent = static_cast<int32>((*Parents)[Index]->AsNumber());
		}
		BoneParents.Add(Parent);

		FVector Position = FVector::ZeroVector;
		if (Rest != nullptr && Rest->IsValidIndex(Index))
		{
			const TArray<TSharedPtr<FJsonValue>>* Triple = nullptr;
			if ((*Rest)[Index]->TryGetArray(Triple))
			{
				ReadVector(Triple, Position);
			}
		}
		RestPositions.Add(Position);
	}

	// Live Link wants each bone relative to its parent, so turn the absolute
	// rest positions the stream sends into offsets once, here.
	BoneOffsets.SetNum(Count);
	for (int32 Index = 0; Index < Count; ++Index)
	{
		const int32 Parent = BoneParents[Index];
		BoneOffsets[Index] = RestPositions.IsValidIndex(Parent)
			? RestPositions[Index] - RestPositions[Parent]
			: FVector::ZeroVector;
	}

	// Curve names are optional, and are what a face stream carries instead of
	// - or as well as - a pose. Live Link calls them properties.
	CurveNames.Reset();
	const TArray<TSharedPtr<FJsonValue>>* Curves = nullptr;
	if (Object->TryGetArrayField(TEXT("curves"), Curves))
	{
		CurveNames.Reserve(Curves->Num());
		for (const TSharedPtr<FJsonValue>& Value : *Curves)
		{
			CurveNames.Add(FName(*Value->AsString()));
		}
	}

	FLiveLinkStaticDataStruct StaticData(FLiveLinkSkeletonStaticData::StaticStruct());
	FLiveLinkSkeletonStaticData& Skeleton_ = *StaticData.Cast<FLiveLinkSkeletonStaticData>();
	Skeleton_.SetBoneNames(BoneNames);
	Skeleton_.SetBoneParents(BoneParents);
	Skeleton_.PropertyNames = CurveNames;

	Client->PushSubjectStaticData_AnyThread(SubjectKey, ULiveLinkAnimationRole::StaticClass(),
	                                        MoveTemp(StaticData));
	FramesReceived.Reset();
	UE_LOG(LogMotionForge, Log,
	       TEXT("Subject published: skeleton '%s', %d joints, %d curves, %.1f fps."),
	       *Skeleton, Count, CurveNames.Num(), FrameRate);
	SetStatus(FString::Printf(TEXT("%s, %d joints, %d curves"),
	                          *Skeleton, Count, CurveNames.Num()));
}

void FMotionForgeLiveLinkSource::HandleFrame(const TSharedPtr<FJsonObject>& Object)
{
	if (Client == nullptr || (BoneNames.Num() == 0 && CurveNames.Num() == 0))
	{
		return;
	}

	// A pose is only expected from a sender that announced joints - a face
	// stream carries curves and nothing else.
	const TArray<TSharedPtr<FJsonValue>>* Pose = nullptr;
	const bool bHasPose = Object->TryGetArrayField(TEXT("pose"), Pose);
	if (BoneNames.Num() > 0)
	{
		if (!bHasPose)
		{
			UE_LOG(LogMotionForge, Warning, TEXT("A frame arrived with no pose."));
			return;
		}
		if (Pose->Num() != BoneNames.Num())
		{
			UE_LOG(LogMotionForge, Warning,
			       TEXT("A frame has %d joints but the skeleton has %d; ignoring it."),
			       Pose->Num(), BoneNames.Num());
			return;
		}
	}

	FVector RootTranslation = FVector::ZeroVector;
	const TArray<TSharedPtr<FJsonValue>>* Translation = nullptr;
	if (Object->TryGetArrayField(TEXT("translation"), Translation) &&
	    Translation->Num() >= 3)
	{
		if (bLocalDelta)
		{
			RootTranslation = FVector((*Translation)[0]->AsNumber(),
			                          (*Translation)[1]->AsNumber(),
			                          (*Translation)[2]->AsNumber());
		}
		else
		{
			ReadVector(Translation, RootTranslation);
		}
	}

	const TArray<TSharedPtr<FJsonValue>>* Moved = nullptr;
	Object->TryGetArrayField(TEXT("moved"), Moved);

	FLiveLinkFrameDataStruct FrameData(FLiveLinkAnimationFrameData::StaticStruct());
	FLiveLinkAnimationFrameData& Animation = *FrameData.Cast<FLiveLinkAnimationFrameData>();
	Animation.Transforms.SetNum(BoneNames.Num());

	for (int32 Index = 0; Index < BoneNames.Num(); ++Index)
	{
		const TArray<TSharedPtr<FJsonValue>>* AxisAngle = nullptr;
		FQuat Rotation = FQuat::Identity;
		if ((*Pose)[Index]->TryGetArray(AxisAngle) && AxisAngle->Num() >= 3)
		{
			Rotation = bLocalDelta
				? FromAxisAngle((*AxisAngle)[0]->AsNumber(),
				                (*AxisAngle)[1]->AsNumber(),
				                (*AxisAngle)[2]->AsNumber())
				: ToUnrealRotation((*AxisAngle)[0]->AsNumber(),
				                   (*AxisAngle)[1]->AsNumber(),
				                   (*AxisAngle)[2]->AsNumber());
		}

		const bool bIsRoot = !BoneParents.IsValidIndex(Index) ||
			BoneParents[Index] == INDEX_NONE;

		FVector Offset = bIsRoot ? RootTranslation : FVector::ZeroVector;
		if (!bLocalDelta && !bIsRoot)
		{
			Offset = BoneOffsets[Index];
		}
		else if (bLocalDelta && Moved != nullptr && Moved->IsValidIndex(Index))
		{
			// How far the bone itself shifted, which a pose is not free of:
			// dropping the hips moves the pelvis, and without it the knees
			// bend while the hips stay and the feet come up instead.
			const TArray<TSharedPtr<FJsonValue>>* Shift = nullptr;
			if ((*Moved)[Index]->TryGetArray(Shift) && Shift->Num() >= 3)
			{
				Offset = FVector((*Shift)[0]->AsNumber(),
				                 (*Shift)[1]->AsNumber(),
				                 (*Shift)[2]->AsNumber());
			}
		}

		Animation.Transforms[Index] = FTransform(Rotation, Offset,
		                                         FVector::OneVector);
	}

	// PropertyValues must stay the length the static data declared, whatever
	// the frame carries, or the receiver reads them against the wrong names.
	if (CurveNames.Num() > 0)
	{
		Animation.PropertyValues.SetNumZeroed(CurveNames.Num());
		const TArray<TSharedPtr<FJsonValue>>* Curves = nullptr;
		if (Object->TryGetArrayField(TEXT("curves"), Curves))
		{
			const int32 Shared = FMath::Min(Curves->Num(), CurveNames.Num());
			for (int32 Index = 0; Index < Shared; ++Index)
			{
				Animation.PropertyValues[Index] =
					static_cast<float>((*Curves)[Index]->AsNumber());
			}
		}
	}

	Client->PushSubjectFrameData_AnyThread(SubjectKey, MoveTemp(FrameData));

	const int32 Count = FramesReceived.Increment();
	if (Count == 1)
	{
		UE_LOG(LogMotionForge, Log, TEXT("First frame pushed to Live Link."));
	}
	if ((Count % 20) == 0)
	{
		UE_LOG(LogMotionForge, Verbose, TEXT("%d frames."), Count);
		SetStatus(FString::Printf(TEXT("%s, %d joints, %d frames"),
		                          *Skeleton, BoneNames.Num(), Count));
	}
}

#undef LOCTEXT_NAMESPACE
