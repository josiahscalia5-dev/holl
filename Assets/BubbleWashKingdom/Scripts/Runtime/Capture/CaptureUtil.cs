using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash
{
    /// <summary>Renders a camera into a RenderTexture through the full URP stack (including post-processing).</summary>
    public static class CaptureUtil
    {
        public static void Render(Camera cam, RenderTexture rt)
        {
            var request = new RenderPipeline.StandardRequest();
            if (RenderPipeline.SupportsRenderRequest(cam, request))
            {
                request.destination = rt;
                RenderPipeline.SubmitRenderRequest(cam, request);
            }
            else
            {
                var prev = cam.targetTexture;
                cam.targetTexture = rt;
                cam.Render();
                cam.targetTexture = prev;
            }
        }

        /// <summary>
        /// Renders through an HDR intermediate, then converts into the given LDR (sRGB) target. URP uses a render-request
        /// target's own format as its colour buffer, so rendering straight into an ARGB32 texture clamped the scene to
        /// [0,1] before bloom and tonemapping: no glow halos, hot emissives flat white, unlike the device screen.
        /// </summary>
        public static void RenderHdr(Camera cam, RenderTexture ldrTarget)
        {
            var hdr = RenderTexture.GetTemporary(ldrTarget.width, ldrTarget.height, 24, RenderTextureFormat.DefaultHDR,
                RenderTextureReadWrite.Linear, Mathf.Max(1, ldrTarget.antiAliasing));
            Render(cam, hdr);
            Graphics.Blit(hdr, ldrTarget);   // linear -> sRGB on write
            RenderTexture.ReleaseTemporary(hdr);
        }

        public static Texture2D ReadBack(RenderTexture rt, Texture2D reuse = null, TextureFormat format = TextureFormat.RGBA32)
        {
            var tex = reuse != null && reuse.width == rt.width && reuse.height == rt.height ? reuse : new Texture2D(rt.width, rt.height, format, false);
            var active = RenderTexture.active;
            RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            tex.Apply(false);
            RenderTexture.active = active;
            return tex;
        }
    }
}
