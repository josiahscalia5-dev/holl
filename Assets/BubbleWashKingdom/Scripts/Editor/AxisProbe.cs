using UnityEditor;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>Prints how Blender FBX files arrive in Unity (node rotation/scale and mesh bounds).</summary>
    public static class AxisProbe
    {
        public static void RunBatch()
        {
            foreach (var p in new[] { "_Test/SM_AxisMarker", "Track/SM_Ring", "Track/SM_Slide_Module", "Track/SM_GlassPipe_Module" })
            {
                string path = $"Assets/BubbleWashKingdom/Art/Models/{p}.fbx";
                var mi = AssetImporter.GetAtPath(path) as ModelImporter;
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (go == null) { Debug.Log($"[BWK-AXIS] {p}: missing"); continue; }
                Debug.Log($"[BWK-AXIS] {p}: bakeAxis={mi?.bakeAxisConversion} root rot={go.transform.localRotation.eulerAngles} scale={go.transform.localScale}");
                foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true))
                    Debug.Log($"[BWK-AXIS]   {mf.name}: localRot={mf.transform.localRotation.eulerAngles} localScale={mf.transform.localScale} meshBounds center={mf.sharedMesh.bounds.center} size={mf.sharedMesh.bounds.size}");
            }
            EditorApplication.Exit(0);
        }
    }
}
