using UnityEditor;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>Prints how Blender FBX files arrive in Unity (node rotation/scale and mesh bounds).</summary>
    public static class AxisProbe
    {
        public static void RunBatch()
        {
            foreach (var p in new[] { "Characters/SK_Mascot_model", "Machinery/SM_Porthole" })
            {
                string path = $"Assets/BubbleWashKingdom/Art/Models/{p}.fbx";
                var mi = AssetImporter.GetAtPath(path) as ModelImporter;
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (go == null) { Debug.Log($"[BWK-AXIS] {p}: missing"); continue; }
                Debug.Log($"[BWK-AXIS] {p}: bakeAxis={mi?.bakeAxisConversion} root rot={go.transform.localRotation.eulerAngles} scale={go.transform.localScale}");
                foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true))
                    Debug.Log($"[BWK-AXIS]   {mf.name} parent={mf.transform.parent?.name}: localPos={mf.transform.localPosition} localRot={mf.transform.localRotation.eulerAngles} localScale={mf.transform.localScale} bounds c={mf.sharedMesh.bounds.center} s={mf.sharedMesh.bounds.size} mats={string.Join(",", System.Array.ConvertAll(mf.GetComponent<MeshRenderer>().sharedMaterials, m => m ? m.name : "null"))}");
            }
            EditorApplication.Exit(0);
        }
    }
}
