using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Import rules for Blender FBX under Art/Models: bake Blender's axis conversion (front = +Z, up = +Y),
    /// keep authored normals, readable track modules for spline bending, generic rig and named, looping clips
    /// for characters ("Armature|Slide" -> "Slide").
    /// </summary>
    public class ModelImportRules : AssetPostprocessor
    {
        public const string ModelsRoot = "Assets/BubbleWashKingdom/Art/Models/";

        static readonly HashSet<string> LoopClips = new HashSet<string>
        {
            "Idle", "Slide", "LeanLeft", "LeanRight", "TurnLeft", "TurnRight", "Swim", "Balance", "Accelerate", "Celebrate"
        };

        void OnPreprocessModel()
        {
            if (!assetPath.StartsWith(ModelsRoot)) return;
            var mi = (ModelImporter)assetImporter;
            bool character = assetPath.Contains("/Characters/");
            bool track = assetPath.Contains("/Track/");
            mi.bakeAxisConversion = true;
            mi.globalScale = 1f;
            mi.useFileScale = true;
            mi.importCameras = false;
            mi.importLights = false;
            mi.importVisibility = false;
            mi.importNormals = ModelImporterNormals.Import;
            mi.importTangents = ModelImporterTangents.CalculateMikk;
            mi.meshCompression = ModelImporterMeshCompression.Off;
            mi.isReadable = track || character;
            mi.optimizeMeshPolygons = true;
            mi.optimizeMeshVertices = true;
            mi.weldVertices = true;
            mi.importBlendShapes = character;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            mi.materialLocation = ModelImporterMaterialLocation.InPrefab;
            mi.animationType = character ? ModelImporterAnimationType.Generic : ModelImporterAnimationType.None;
            mi.importAnimation = character;
            mi.generateSecondaryUV = false;
        }

        void OnPreprocessAnimation()
        {
            if (!assetPath.StartsWith(ModelsRoot) || !assetPath.Contains("/Characters/")) return;
            var mi = (ModelImporter)assetImporter;
            var defaults = mi.defaultClipAnimations;
            if (defaults == null || defaults.Length == 0) return;
            var clips = new List<ModelImporterClipAnimation>();
            foreach (var c in defaults)
            {
                string name = c.takeName;
                int bar = name.LastIndexOf('|');
                if (bar >= 0) name = name.Substring(bar + 1);
                c.name = name;
                c.loopTime = LoopClips.Contains(name);
                c.loopPose = false;
                c.lockRootRotation = true;
                c.lockRootHeightY = true;
                c.lockRootPositionXZ = true;
                c.keepOriginalOrientation = true;
                c.keepOriginalPositionY = true;
                c.keepOriginalPositionXZ = true;
                clips.Add(c);
            }
            mi.clipAnimations = clips.ToArray();
        }

        /// <summary>Remaps every embedded FBX material to the project material of the same name (M_*).</summary>
        public static void RemapAllMaterials()
        {
            foreach (string guid in AssetDatabase.FindAssets("t:Model", new[] { ModelsRoot.TrimEnd('/') }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (AssetImporter.GetAtPath(path) is ModelImporter mi)
                {
                    mi.materialLocation = ModelImporterMaterialLocation.InPrefab;
                    mi.SearchAndRemapMaterials(ModelImporterMaterialName.BasedOnMaterialName, ModelImporterMaterialSearch.Everywhere);
                    mi.SaveAndReimport();
                }
            }
        }
    }
}
