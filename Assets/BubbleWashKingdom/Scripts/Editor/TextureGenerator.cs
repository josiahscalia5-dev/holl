using System.IO;
using UnityEditor;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>Generates the small procedural textures the shaders and particles use (deterministic seeds).</summary>
    public static class TextureGenerator
    {
        public const string Dir = "Assets/BubbleWashKingdom/Art/Textures";

        [MenuItem("Bubble Wash/Setup/2 Generate Textures")]
        public static void Run()
        {
            Directory.CreateDirectory(Dir);
            Save("T_FurNoise", FurNoise(256), TextureWrapMode.Repeat, false, true);
            Save("T_SoftCircle", Radial(64, (r, a) => Mathf.Pow(Mathf.Clamp01(1f - r), 1.6f)), TextureWrapMode.Clamp, true, true);
            Save("T_Splash", Splash(128), TextureWrapMode.Clamp, true, true);
            Save("T_Sparkle", Sparkle(128), TextureWrapMode.Clamp, true, true);
            Save("T_Bubble", Bubble(128), TextureWrapMode.Clamp, true, true);
            Save("T_Streak", Streak(32, 256), TextureWrapMode.Clamp, true, true);
            AssetDatabase.Refresh();
            Debug.Log("[BWK] Textures generated.");
        }

        static Texture2D FurNoise(int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, true, true);
            var rng = new System.Random(1234);
            var px = new Color[size * size];
            for (int i = 0; i < px.Length; i++)
            {
                float v = (float)rng.NextDouble();
                v = Mathf.Pow(v, 0.7f);
                px[i] = new Color(v, v, v, 1f);
            }
            tex.SetPixels(px);
            tex.Apply();
            return tex;
        }

        delegate float RadialFn(float r, float angle);

        static Texture2D Radial(int size, RadialFn fn)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, true);
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    float a = fn(Mathf.Sqrt(u * u + v * v), Mathf.Atan2(v, u));
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, Mathf.Clamp01(a)));
                }
            tex.Apply();
            return tex;
        }

        static Texture2D Splash(int size)
        {
            // Cartoon water blob: bright white core, soft light-blue rim, wobbly silhouette.
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, true);
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    float r = Mathf.Sqrt(u * u + v * v);
                    float ang = Mathf.Atan2(v, u);
                    float edge = 0.78f + 0.12f * Mathf.Sin(ang * 5f) + 0.06f * Mathf.Sin(ang * 11f + 1.3f);
                    float a = Mathf.SmoothStep(1f, 0f, Mathf.InverseLerp(edge - 0.12f, edge, r));
                    float shade = Mathf.Lerp(1f, 0.82f, Mathf.Clamp01((r - 0.2f) / 0.6f));
                    tex.SetPixel(x, y, new Color(shade, Mathf.Lerp(1f, 0.93f, r), 1f, a));
                }
            tex.Apply();
            return tex;
        }

        static Texture2D Sparkle(int size)
        {
            return Radial(size, (r, ang) =>
            {
                float star = Mathf.Pow(Mathf.Abs(Mathf.Cos(ang * 2f)), 24f) * Mathf.Clamp01(1f - r) * 1.2f;
                float core = Mathf.Pow(Mathf.Clamp01(1f - r * 3f), 2f);
                float halo = Mathf.Pow(Mathf.Clamp01(1f - r), 3f) * 0.35f;
                return star + core + halo;
            });
        }

        static Texture2D Bubble(int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, true);
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    float r = Mathf.Sqrt(u * u + v * v);
                    if (r > 1f) { tex.SetPixel(x, y, Color.clear); continue; }
                    float rim = Mathf.Pow(r, 6f);
                    float ang = Mathf.Atan2(v, u);
                    Color film = Color.HSVToRGB(Mathf.Repeat(ang / (2f * Mathf.PI) + r * 0.6f, 1f), 0.55f, 1f);
                    float hl = Mathf.Pow(Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(-0.38f, 0.42f)) * 3.2f), 2f);
                    float aa = Mathf.SmoothStep(0f, 1f, (1f - r) * size * 0.25f);
                    Color c = Color.Lerp(film, Color.white, hl);
                    tex.SetPixel(x, y, new Color(c.r, c.g, c.b, Mathf.Clamp01((0.08f + rim * 0.85f + hl) * aa)));
                }
            tex.Apply();
            return tex;
        }

        static Texture2D Streak(int w, int h)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, true);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float u = (x + 0.5f) / w * 2f - 1f, v = (y + 0.5f) / h;
                    float a = Mathf.Pow(Mathf.Clamp01(1f - Mathf.Abs(u)), 2f) * Mathf.Sin(v * Mathf.PI);
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            tex.Apply();
            return tex;
        }

        static void Save(string name, Texture2D tex, TextureWrapMode wrap, bool alpha, bool mips)
        {
            string path = $"{Dir}/{name}.png";
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Default;
            ti.wrapMode = wrap;
            ti.alphaIsTransparency = alpha;
            ti.mipmapEnabled = mips;
            ti.sRGBTexture = name != "T_FurNoise";
            ti.filterMode = FilterMode.Bilinear;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;
            ti.SaveAndReimport();
        }
    }
}
