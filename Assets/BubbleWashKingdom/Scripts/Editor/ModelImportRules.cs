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
                    RemapVersionedMaterials(mi, path);
                    mi.SaveAndReimport();
                }
            }
        }

        /// <summary>
        /// Lead 2026-11-27 06:45 (owner: v4 stays the COMPLETE fallback, including its materials): a versioned model export
        /// whose file name ends in "_v5", "_v6", ... keeps v4's FBX material names but uses its OWN project materials named
        /// "&lt;name&gt;_v5" wherever the character artist created them (MaterialLibrary.Character.cs); any name without a
        /// versioned material keeps the shared M_* material. Call after SearchAndRemapMaterials, before SaveAndReimport.
        /// </summary>
        public static int RemapVersionedMaterials(ModelImporter mi, string path)
        {
            var m = System.Text.RegularExpressions.Regex.Match(System.IO.Path.GetFileNameWithoutExtension(path), @"_(v\d+)$");
            if (!m.Success) return 0;
            string suffix = "_" + m.Groups[1].Value;
            int n = 0;
            foreach (var kv in mi.GetExternalObjectMap())
            {
                if (kv.Key.type != typeof(Material)) continue;
                string want = kv.Key.name + suffix;
                foreach (string guid in AssetDatabase.FindAssets(want + " t:Material"))
                {
                    string p = AssetDatabase.GUIDToAssetPath(guid);
                    if (System.IO.Path.GetFileNameWithoutExtension(p) != want) continue;
                    var mat = AssetDatabase.LoadAssetAtPath<Material>(p);
                    if (mat != null) { mi.AddRemap(kv.Key, mat); n++; }
                    break;
                }
            }
            if (n > 0) Debug.Log($"[BWK] {path}: {n} materials remapped to their {suffix} versions");
            return n;
        }
    }
}
