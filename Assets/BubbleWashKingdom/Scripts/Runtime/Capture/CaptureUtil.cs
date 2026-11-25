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
