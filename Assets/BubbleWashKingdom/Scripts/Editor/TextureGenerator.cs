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
            Save("T_SplashCrown", SplashCrown(256, 7), TextureWrapMode.Clamp, true, true);
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
            // Cartoon milky water droplet: crisp round silhouette, white body, cool blue lower rim, hot highlight.
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, true);
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    float r = Mathf.Sqrt(u * u + v * v);
                    float a = Mathf.Clamp01((0.86f - r) * size * 0.12f);
                    float rimShade = Mathf.Clamp01((r - 0.35f) / 0.5f) * Mathf.Clamp01(0.6f - v * 0.6f);
                    float hl = Mathf.Pow(Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(-0.3f, 0.35f)) * 3.5f), 1.5f);
                    Color c = Color.Lerp(new Color(1f, 1f, 1f), new Color(0.72f, 0.86f, 1f), rimShade * 0.8f);
                    c = Color.Lerp(c, Color.white, hl);
                    tex.SetPixel(x, y, new Color(c.r, c.g, c.b, a));
                }
            tex.Apply();
            return tex;
        }

        /// <summary>
        /// Milky crown splash sheet (reference 1.75-7.5 s): a fan of rounded fingers rising from a pooled base, each ending
        /// in a droplet, plus a few detached drops. White body, cool blue shading toward the base, crisp cartoon edge.
        /// Signed-distance construction (capsules + circles, smooth union) so the silhouette stays clean at any size.
        /// </summary>
        static Texture2D SplashCrown(int size, int seed)
        {
            var rng = new System.Random(seed);
            var caps = new System.Collections.Generic.List<(Vector2 a, Vector2 b, float ra, float rb)>();
            var drops = new System.Collections.Generic.List<(Vector2 c, float r)>();
            Vector2 baseC = new Vector2(0f, -0.72f);
            int fingers = 7 + rng.Next(3);
            for (int i = 0; i < fingers; i++)
            {
                float t = fingers == 1 ? 0.5f : i / (float)(fingers - 1);
                float ang = Mathf.Lerp(-66f, 66f, t) + (float)(rng.NextDouble() * 20 - 10);
                float len = Mathf.Lerp(0.95f, 1.45f, 1f - Mathf.Abs(t - 0.5f) * 1.6f) * (0.8f + (float)rng.NextDouble() * 0.35f);
                Vector2 dir = new Vector2(Mathf.Sin(ang * Mathf.Deg2Rad), Mathf.Cos(ang * Mathf.Deg2Rad));
                Vector2 a = baseC + new Vector2(dir.x * 0.25f, 0.05f);
                Vector2 b = baseC + dir * len;
                float rb = 0.045f + (float)rng.NextDouble() * 0.03f;
                caps.Add((a, b, 0.09f + (float)rng.NextDouble() * 0.05f, rb));
                drops.Add((b + dir * (rb * 2.2f + 0.04f), rb * 1.35f));
                if (rng.NextDouble() < 0.55) drops.Add((b + dir * (0.2f + (float)rng.NextDouble() * 0.12f), rb * 0.8f));
            }
            for (int i = 0; i < 9; i++)
                drops.Add((new Vector2((float)(rng.NextDouble() * 1.4 - 0.7), (float)(rng.NextDouble() * 0.9 - 0.1)), 0.025f + (float)rng.NextDouble() * 0.03f));

            float Capsule(Vector2 p, Vector2 a, Vector2 b, float ra, float rb)
            {
                Vector2 pa = p - a, ba = b - a;
                float h = Mathf.Clamp01(Vector2.Dot(pa, ba) / Vector2.Dot(ba, ba));
                return (pa - ba * h).magnitude - Mathf.Lerp(ra, rb, h);
            }
            float SMin(float d1, float d2, float k)
            {
                float h = Mathf.Clamp01(0.5f + 0.5f * (d2 - d1) / k);
                return Mathf.Lerp(d2, d1, h) - k * h * (1f - h);
            }

            var tex = new Texture2D(size, size, TextureFormat.RGBA32, true);
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    Vector2 p = new Vector2((x + 0.5f) / size * 2f - 1f, (y + 0.5f) / size * 2f - 1f) * 1.08f;
                    // pooled base: flattened ellipse
                    Vector2 q = (p - baseC); q.x /= 1.9f; q.y /= 0.55f;
                    float d = (q.magnitude - 0.28f) * 0.55f;
                    foreach (var c in caps) d = SMin(d, Capsule(p, c.a, c.b, c.ra, c.rb), 0.09f);
                    float body = d;
                    foreach (var dr in drops) d = Mathf.Min(d, (p - dr.c).magnitude - dr.r);
                    float a = Mathf.Clamp01(-d * size * 0.5f);
                    float inner = Mathf.Clamp01(-body * 6f);
                    float baseShade = Mathf.Clamp01((-0.2f - p.y) / 0.6f);
                    Color c0 = Color.Lerp(new Color(0.84f, 0.93f, 1f), Color.white, Mathf.SmoothStep(0f, 1f, inner));
                    c0 = Color.Lerp(c0, new Color(0.74f, 0.88f, 1f), baseShade * 0.45f);
                    tex.SetPixel(x, y, new Color(c0.r, c0.g, c0.b, a));
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
