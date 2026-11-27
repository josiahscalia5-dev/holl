using System.Collections.Generic;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Code-generated meshes: fallbacks for track modules while Blender assets are missing, plus simple shapes the
    /// scene needs (bulkhead annulus, portal disc, quad). Modules follow the same contract as the Blender ones:
    /// straight along +Z from 0 to length, cross-section in XY, slide floor centre at the origin.
    /// </summary>
    public static class ProceduralModules
    {
        public static Mesh SlideModule(float length = 4f, int rings = 24)
        {
            // Profile (left to right) matching RunnerController: flat floor |x|<=1.25, walls z = 0.9(|x|-1.25)^2 to |x|=2.1.
            var waterPts = new List<Vector2>();
            int wallSeg = 10;
            for (int i = wallSeg; i >= 0; i--) { float a = 0.85f * i / wallSeg; float x = -(1.25f + a); waterPts.Add(new Vector2(x, 0.9f * a * a)); }
            for (int i = 1; i < 6; i++) waterPts.Add(new Vector2(-1.25f + 2.5f * i / 6f, 0f));
            for (int i = 0; i <= wallSeg; i++) { float a = 0.85f * i / wallSeg; float x = 1.25f + a; waterPts.Add(new Vector2(x, 0.9f * a * a)); }
            var mesh = new Mesh { name = "SM_Slide_Module_Procedural" };
            var verts = new List<Vector3>(); var uvs = new List<Vector2>(); var tris0 = new List<int>(); var tris1 = new List<int>(); var tris2 = new List<int>();
            Extrude(waterPts, length, rings, verts, uvs, tris0, true);
            // rails: tubes at +-2.22, 0.72
            for (int side = -1; side <= 1; side += 2)
            {
                var circle = new List<Vector2>();
                for (int k = 0; k <= 12; k++) { float ang = k / 12f * Mathf.PI * 2f; circle.Add(new Vector2(side * SlideProfile.RailX + Mathf.Cos(ang) * SlideProfile.RailR, SlideProfile.RailZ + Mathf.Sin(ang) * SlideProfile.RailR)); }
                circle.Reverse(); // clockwise profile -> outward normals
                Extrude(circle, length, rings, verts, uvs, tris1, false);
            }
            // outer shell (simple U)
            var shell = new List<Vector2> { new Vector2(2.3f, 0.7f), new Vector2(2.25f, -0.15f), new Vector2(1.2f, -0.3f), new Vector2(-1.2f, -0.3f), new Vector2(-2.25f, -0.15f), new Vector2(-2.3f, 0.7f) };
            Extrude(shell, length, rings, verts, uvs, tris2, false);
            mesh.SetVertices(verts); mesh.SetUVs(0, uvs);
            mesh.subMeshCount = 3;
            mesh.SetTriangles(tris0, 0); mesh.SetTriangles(tris1, 1); mesh.SetTriangles(tris2, 2);
            mesh.RecalculateNormals(); mesh.RecalculateTangents(); mesh.RecalculateBounds();
            return mesh; // submeshes: M_Water, M_RailPink, M_SlideShell
        }

        public static Mesh TunnelModule(float radius = 4.2f, float centerY = 2.3f, float length = 4f, int seg = 64, int rings = 24)
        {
            var pts = new List<Vector2>();
            for (int i = 0; i <= seg; i++)
            {
                float a = -Mathf.PI / 2f + i / (float)seg * Mathf.PI * 2f; // start at the bottom
                pts.Add(new Vector2(Mathf.Cos(a) * radius, centerY + Mathf.Sin(a) * radius));
            }
            var verts = new List<Vector3>(); var uvs = new List<Vector2>(); var tris = new List<int>();
            Extrude(pts, length, rings, verts, uvs, tris, true, flip: false);
            var mesh = new Mesh { name = "SM_Tunnel_Module_Procedural" };
            mesh.SetVertices(verts); mesh.SetUVs(0, uvs); mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals(); mesh.RecalculateTangents(); mesh.RecalculateBounds();
            return mesh;
        }

        static void Extrude(List<Vector2> profile, float length, int rings, List<Vector3> verts, List<Vector2> uvs, List<int> tris, bool uAcross, bool flip = false)
        {
            int start = verts.Count;
            int n = profile.Count;
            float total = 0f; var acc = new float[n];
            for (int i = 1; i < n; i++) { total += Vector2.Distance(profile[i - 1], profile[i]); acc[i] = total; }
            for (int r = 0; r <= rings; r++)
            {
                float z = length * r / rings;
                for (int i = 0; i < n; i++)
                {
                    verts.Add(new Vector3(profile[i].x, profile[i].y, z));
                    uvs.Add(new Vector2(total > 0 ? acc[i] / total : 0, z / 4f));
                }
            }
            for (int r = 0; r < rings; r++)
                for (int i = 0; i < n - 1; i++)
                {
                    int a = start + r * n + i, b = a + 1, c = a + n, d = c + 1;
                    if (!flip) { tris.Add(a); tris.Add(c); tris.Add(b); tris.Add(b); tris.Add(c); tris.Add(d); }
                    else { tris.Add(a); tris.Add(b); tris.Add(c); tris.Add(b); tris.Add(d); tris.Add(c); }
                }
        }

        /// <summary>Flat ring (annulus) in the XY plane facing -Z, used as the hall bulkhead around the tunnel mouth.</summary>
        public static Mesh Annulus(float inner, float outer, int seg = 72)
        {
            var mesh = new Mesh { name = "Annulus" };
            var v = new List<Vector3>(); var uv = new List<Vector2>(); var t = new List<int>();
            for (int i = 0; i <= seg; i++)
            {
                float a = i / (float)seg * Mathf.PI * 2f;
                var dir = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f);
                v.Add(dir * inner); v.Add(dir * outer);
                uv.Add(new Vector2(dir.x * inner, dir.y * inner) / 4f); uv.Add(new Vector2(dir.x * outer, dir.y * outer) / 4f);
            }
            for (int i = 0; i < seg; i++)
            {
                int a = i * 2;
                t.Add(a); t.Add(a + 1); t.Add(a + 2);
                t.Add(a + 1); t.Add(a + 3); t.Add(a + 2);
            }
            mesh.SetVertices(v); mesh.SetUVs(0, uv); mesh.SetTriangles(t, 0);
            mesh.RecalculateNormals(); mesh.RecalculateTangents(); mesh.RecalculateBounds();
            return mesh;
        }

        public static Mesh Quad(float size)
        {
            var m = new Mesh { name = "Quad" };
            float h = size * 0.5f;
            m.SetVertices(new List<Vector3> { new Vector3(-h, -h, 0), new Vector3(h, -h, 0), new Vector3(-h, h, 0), new Vector3(h, h, 0) });
            m.SetUVs(0, new List<Vector2> { new Vector2(0, 0), new Vector2(1, 0), new Vector2(0, 1), new Vector2(1, 1) });
            m.SetTriangles(new List<int> { 0, 2, 1, 1, 2, 3 }, 0);
            m.RecalculateNormals(); m.RecalculateBounds();
            return m;
        }
    }
}
