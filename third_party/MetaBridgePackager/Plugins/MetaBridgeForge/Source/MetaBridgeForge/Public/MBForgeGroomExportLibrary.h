#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MBForgeGroomExportLibrary.generated.h"

class UGroomAsset;

/**
 * Hands a groom's strands to MetaBridge DNA in Blender. Unreal has no groom
 * exporter, so a package's hair could not leave the engine any other way.
 */
UCLASS()
class METABRIDGEFORGE_API UMBForgeGroomExportLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Writes every strand of the groom's hair description to FilePath.
	 * Layout (little endian): "MBGS", int32 version, int32 strands, int32 vertices,
	 * int32[strands] vertex counts, int32[strands] group ids, int32[strands] guide flags,
	 * float[strands*2] root uvs, float[vertices*3] positions (cm), float[vertices] widths (cm).
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaBridge Forge|Groom")
	static bool ExportGroomStrands(UGroomAsset* Groom, const FString& FilePath, FString& OutInfo);

	/**
	 * Points every reference inside Assets (and their subobjects) at the
	 * replacement given for it. Duplicating a template asset by asset keeps
	 * each copy pointing at the template, so a package built that way refers
	 * outside itself; this is Consolidate's reference swap without deleting
	 * anything. Returns how many assets changed.
	 */
	/**
	 * Builds a GroomAsset at PackagePath/AssetName from a strand file in the
	 * layout ExportGroomStrands writes, the way the Alembic importer does:
	 * groups, hair description, derived data. Blender's own Alembic writer
	 * drops root UVs and widths, so strands come across this way instead.
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaBridge Forge|Groom")
	static UGroomAsset* CreateGroomFromStrands(const FString& FilePath, const FString& PackagePath, const FString& AssetName, FString& OutInfo);

	UFUNCTION(BlueprintCallable, Category = "MetaBridge Forge|Package")
	static int32 RemapReferences(const TArray<UObject*>& Assets, const TMap<UObject*, UObject*>& Replacements);
};
