#include "MBForgeGroomExportLibrary.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "GroomAsset.h"
#include "HairAttributes.h"
#include "HairDescription.h"
#include "Misc/FileHelper.h"
#include "Serialization/ArchiveReplaceObjectRef.h"
#include "Serialization/BufferArchive.h"
#include "UObject/Package.h"
#include "UObject/UObjectHash.h"

UGroomAsset* UMBForgeGroomExportLibrary::CreateGroomFromStrands(const FString& FilePath, const FString& PackagePath, const FString& AssetName, FString& OutInfo)
{
#if WITH_EDITORONLY_DATA
	TArray<uint8> Bytes;
	if (!FFileHelper::LoadFileToArray(Bytes, *FilePath) || Bytes.Num() < 16 || FMemory::Memcmp(Bytes.GetData(), "MBGS", 4) != 0)
	{
		OutInfo = FString::Printf(TEXT("%s is not a strand file"), *FilePath);
		return nullptr;
	}
	const int32* Header = reinterpret_cast<const int32*>(Bytes.GetData() + 4);
	const int32 NumStrands = Header[1];
	const int32 NumVertices = Header[2];
	const int64 Expected = 16 + int64(NumStrands) * (4 * 3 + 8) + int64(NumVertices) * (12 + 4);
	if (Header[0] != 1 || NumStrands <= 0 || NumVertices <= 0 || Expected != Bytes.Num())
	{
		OutInfo = FString::Printf(TEXT("strand file size %d does not match its header (%d strands, %d points)"), Bytes.Num(), NumStrands, NumVertices);
		return nullptr;
	}
	const uint8* Cursor = Bytes.GetData() + 16;
	const int32* Counts = reinterpret_cast<const int32*>(Cursor); Cursor += 4 * NumStrands;
	const int32* Groups = reinterpret_cast<const int32*>(Cursor); Cursor += 4 * NumStrands;
	const int32* Guides = reinterpret_cast<const int32*>(Cursor); Cursor += 4 * NumStrands;
	const float* UVs = reinterpret_cast<const float*>(Cursor); Cursor += 8 * NumStrands;
	const float* Positions = reinterpret_cast<const float*>(Cursor); Cursor += 12 * NumVertices;
	const float* Widths = reinterpret_cast<const float*>(Cursor);

	int64 Total = 0;
	bool bHasGuides = false;
	TSet<int32> UniqueGroups;
	for (int32 S = 0; S < NumStrands; ++S)
	{
		if (Counts[S] < 2)
		{
			OutInfo = FString::Printf(TEXT("strand %d has %d points"), S, Counts[S]);
			return nullptr;
		}
		Total += Counts[S];
		bHasGuides |= Guides[S] != 0;
		UniqueGroups.Add(Groups[S]);
	}
	if (Total != NumVertices)
	{
		OutInfo = FString::Printf(TEXT("vertex counts add up to %lld, not %d"), Total, NumVertices);
		return nullptr;
	}

	FHairDescription Description;
	Description.StrandAttributes().RegisterAttribute<int>(HairAttribute::Strand::VertexCount);
	Description.StrandAttributes().RegisterAttribute<int>(HairAttribute::Strand::GroupID);
	Description.StrandAttributes().RegisterAttribute<FVector2f>(HairAttribute::Strand::RootUV);
	Description.StrandAttributes().RegisterAttribute<float>(HairAttribute::Strand::Width);
	if (bHasGuides)
	{
		Description.StrandAttributes().RegisterAttribute<int>(HairAttribute::Strand::Guide);
	}
	Description.VertexAttributes().RegisterAttribute<FVector3f>(HairAttribute::Vertex::Position);
	Description.VertexAttributes().RegisterAttribute<float>(HairAttribute::Vertex::Width);

	TStrandAttributesRef<int> CountRef = Description.StrandAttributes().GetAttributesRef<int>(HairAttribute::Strand::VertexCount);
	TStrandAttributesRef<int> GroupRef = Description.StrandAttributes().GetAttributesRef<int>(HairAttribute::Strand::GroupID);
	TStrandAttributesRef<FVector2f> UVRef = Description.StrandAttributes().GetAttributesRef<FVector2f>(HairAttribute::Strand::RootUV);
	TStrandAttributesRef<float> StrandWidthRef = Description.StrandAttributes().GetAttributesRef<float>(HairAttribute::Strand::Width);
	TVertexAttributesRef<FVector3f> PositionRef = Description.VertexAttributes().GetAttributesRef<FVector3f>(HairAttribute::Vertex::Position);
	TVertexAttributesRef<float> WidthRef = Description.VertexAttributes().GetAttributesRef<float>(HairAttribute::Vertex::Width);

	int32 Vertex = 0;
	for (int32 S = 0; S < NumStrands; ++S)
	{
		const FStrandID Strand = Description.AddStrand();
		CountRef[Strand] = Counts[S];
		GroupRef[Strand] = Groups[S];
		UVRef[Strand] = FVector2f(UVs[2 * S], UVs[2 * S + 1]);
		StrandWidthRef[Strand] = Widths[Vertex];
		if (bHasGuides)
		{
			Description.StrandAttributes().GetAttributesRef<int>(HairAttribute::Strand::Guide)[Strand] = Guides[S];
		}
		for (int32 I = 0; I < Counts[S]; ++I, ++Vertex)
		{
			const FVertexID Id = Description.AddVertex();
			PositionRef[Id] = FVector3f(Positions[3 * Vertex], Positions[3 * Vertex + 1], Positions[3 * Vertex + 2]);
			WidthRef[Id] = Widths[Vertex];
		}
	}

	UPackage* Package = CreatePackage(*(PackagePath / AssetName));
	UGroomAsset* Groom = NewObject<UGroomAsset>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
	Groom->SetNumGroup(UniqueGroups.Num());
	Groom->CommitHairDescription(MoveTemp(Description), EHairDescriptionType::Source);
	if (!Groom->CacheDerivedDatas())
	{
		OutInfo = TEXT("the groom could not be built from these strands");
		return nullptr;
	}
	FAssetRegistryModule::AssetCreated(Groom);
	Package->MarkPackageDirty();
	OutInfo = FString::Printf(TEXT("%d strands, %d points, %d group(s)%s"), NumStrands, NumVertices, UniqueGroups.Num(), bHasGuides ? TEXT(", guides") : TEXT(""));
	return Groom;
#else
	OutInfo = TEXT("editor only");
	return nullptr;
#endif
}

int32 UMBForgeGroomExportLibrary::RemapReferences(const TArray<UObject*>& Assets, const TMap<UObject*, UObject*>& Replacements)
{
	TMap<UObject*, UObject*> Map;
	for (const TPair<UObject*, UObject*>& Pair : Replacements)
	{
		if (Pair.Key && Pair.Value && Pair.Key != Pair.Value)
		{
			Map.Add(Pair.Key, Pair.Value);
		}
	}
	int32 Changed = 0;
	for (UObject* Asset : Assets)
	{
		if (!Asset)
		{
			continue;
		}
		TArray<UObject*> Objects;
		GetObjectsWithPackage(Asset->GetPackage(), Objects, true);
		int64 Count = 0;
		for (UObject* Object : Objects)
		{
			FArchiveReplaceObjectRef<UObject> Replace(Object, Map,
				EArchiveReplaceObjectFlags::IgnoreOuterRef | EArchiveReplaceObjectFlags::IgnoreArchetypeRef);
			Count += Replace.GetCount();
		}
		if (Count > 0)
		{
			Asset->Modify();
			Asset->PostEditChange();
			Asset->MarkPackageDirty();
			++Changed;
		}
	}
	return Changed;
}

bool UMBForgeGroomExportLibrary::ExportGroomStrands(UGroomAsset* Groom, const FString& FilePath, FString& OutInfo)
{
#if WITH_EDITORONLY_DATA
	if (!Groom)
	{
		OutInfo = TEXT("no groom");
		return false;
	}
	const FHairDescription Description = Groom->GetHairDescription();
	const int32 NumStrands = Description.GetNumStrands();
	const int32 NumVertices = Description.GetNumVertices();
	if (NumStrands <= 0 || NumVertices <= 0)
	{
		OutInfo = TEXT("the groom has no hair description");
		return false;
	}

	TStrandAttributesConstRef<int> Counts = Description.StrandAttributes().GetAttributesRef<int>(HairAttribute::Strand::VertexCount);
	TStrandAttributesConstRef<int> Groups = Description.StrandAttributes().GetAttributesRef<int>(HairAttribute::Strand::GroupID);
	TStrandAttributesConstRef<int> Guides = Description.StrandAttributes().GetAttributesRef<int>(HairAttribute::Strand::Guide);
	TStrandAttributesConstRef<FVector2f> RootUVs = Description.StrandAttributes().GetAttributesRef<FVector2f>(HairAttribute::Strand::RootUV);
	TStrandAttributesConstRef<float> StrandWidths = Description.StrandAttributes().GetAttributesRef<float>(HairAttribute::Strand::Width);
	TVertexAttributesConstRef<FVector3f> Positions = Description.VertexAttributes().GetAttributesRef<FVector3f>(HairAttribute::Vertex::Position);
	TVertexAttributesConstRef<float> Widths = Description.VertexAttributes().GetAttributesRef<float>(HairAttribute::Vertex::Width);
	if (!Counts.IsValid() || !Positions.IsValid())
	{
		OutInfo = TEXT("the hair description has no vertex counts or positions");
		return false;
	}

	FBufferArchive Out;
	char Magic[4] = {'M', 'B', 'G', 'S'};
	Out.Serialize(Magic, 4);
	int32 Version = 1;
	int32 Strands = NumStrands;
	int32 Vertices = NumVertices;
	Out << Version << Strands << Vertices;

	int32 Total = 0;
	for (int32 S = 0; S < NumStrands; ++S)
	{
		int32 Count = Counts[FStrandID(S)];
		Total += Count;
		Out << Count;
	}
	if (Total != NumVertices)
	{
		OutInfo = FString::Printf(TEXT("vertex counts add up to %d, not %d"), Total, NumVertices);
		return false;
	}
	for (int32 S = 0; S < NumStrands; ++S)
	{
		int32 Group = Groups.IsValid() ? Groups[FStrandID(S)] : 0;
		Out << Group;
	}
	int32 GuideCount = 0;
	for (int32 S = 0; S < NumStrands; ++S)
	{
		int32 Guide = Guides.IsValid() ? Guides[FStrandID(S)] : 0;
		GuideCount += Guide ? 1 : 0;
		Out << Guide;
	}
	for (int32 S = 0; S < NumStrands; ++S)
	{
		FVector2f UV = RootUVs.IsValid() ? RootUVs[FStrandID(S)] : FVector2f::ZeroVector;
		Out << UV.X << UV.Y;
	}
	for (int32 V = 0; V < NumVertices; ++V)
	{
		FVector3f P = Positions[FVertexID(V)];
		Out << P.X << P.Y << P.Z;
	}
	int32 Offset = 0;
	for (int32 S = 0; S < NumStrands; ++S)
	{
		const int32 Count = Counts[FStrandID(S)];
		const float Fallback = StrandWidths.IsValid() ? StrandWidths[FStrandID(S)] : 0.f;
		for (int32 I = 0; I < Count; ++I)
		{
			float W = Widths.IsValid() ? Widths[FVertexID(Offset + I)] : Fallback;
			Out << W;
		}
		Offset += Count;
	}

	if (!FFileHelper::SaveArrayToFile(Out, *FilePath))
	{
		OutInfo = FString::Printf(TEXT("could not write %s"), *FilePath);
		return false;
	}
	OutInfo = FString::Printf(TEXT("%d strands, %d guides, %d points"), NumStrands, GuideCount, NumVertices);
	return true;
#else
	OutInfo = TEXT("editor only");
	return false;
#endif
}
