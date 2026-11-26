using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>Logs renderer / sub-mesh (approximate draw calls) / triangle counts per scene group and the worst offenders.</summary>
    public static class SceneStats
    {
        public static void Log()
        {
            var groups = new Dictionary<string, (int renderers, int submeshes, long tris, int shadowCasters)>();
            var heavy = new List<(string name, long tris)>();
            // LODGroups: count only LOD0 here (what is drawn up close); lower LODs are reported separately.
            var lowerLods = new HashSet<Renderer>();
            long lowerLodTris = 0;
            foreach (var lg in Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None))
            {
                var lods = lg.GetLODs();
                for (int li = 1; li < lods.Length; li++)
                    foreach (var lr in lods[li].renderers)
                        if (lr != null && lowerLods.Add(lr) && lr.GetComponent<MeshFilter>()?.sharedMesh is Mesh lm)
                            for (int s = 0; s < lm.subMeshCount; s++) lowerLodTris += (long)lm.GetIndexCount(s) / 3;
            }
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy || lowerLods.Contains(r)) continue;
                Mesh mesh = null;
                if (r is MeshRenderer) mesh = r.GetComponent<MeshFilter>()?.sharedMesh;
                else if (r is SkinnedMeshRenderer smr) mesh = smr.sharedMesh;
                long tris = 0;
                int subs = 1;
                if (mesh != null)
                {
                    subs = mesh.subMeshCount;
                    for (int s = 0; s < mesh.subMeshCount; s++) tris += (long)mesh.GetIndexCount(s) / 3;
                }
                string key = GroupOf(r.transform);
                groups.TryGetValue(key, out var g);
                g.renderers++; g.submeshes += subs; g.tris += tris;
                if (r.shadowCastingMode != UnityEngine.Rendering.ShadowCastingMode.Off) g.shadowCasters += subs;
                groups[key] = g;
                heavy.Add((r.name, tris));
            }
            var sb = new StringBuilder("[BWK-STATS] group | renderers | submeshes(draws) | tris | shadow-casting draws\n");
            foreach (var kv in groups.OrderByDescending(k => k.Value.tris))
                sb.AppendLine($"[BWK-STATS] {kv.Key} | {kv.Value.renderers} | {kv.Value.submeshes} | {kv.Value.tris} | {kv.Value.shadowCasters}");
            sb.AppendLine($"[BWK-STATS] TOTAL | {groups.Values.Sum(v => v.renderers)} | {groups.Values.Sum(v => v.submeshes)} | {groups.Values.Sum(v => v.tris)} | {groups.Values.Sum(v => v.shadowCasters)}");
            sb.AppendLine($"[BWK-STATS] (lower LOD levels, not counted above: {lowerLods.Count} renderers, {lowerLodTris} tris)");
            foreach (var h in heavy.OrderByDescending(h => h.tris).Take(8)) sb.AppendLine($"[BWK-STATS] heavy: {h.name} {h.tris}");
            Debug.Log(sb.ToString());
        }

        static string GroupOf(Transform t)
        {
            // second-level ancestor under the level root, e.g. Environment/Rings, TrackItems, Runner
            var chain = new List<string>();
            for (var p = t; p != null; p = p.parent) chain.Add(p.name);
            chain.Reverse();
            if (chain.Count >= 3 && chain[1] == "Environment") return "Environment/" + chain[2];
            return chain.Count >= 2 ? chain[1] : chain[0];
        }
    }
}
