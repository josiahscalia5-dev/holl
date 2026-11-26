using System.Collections.Generic;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Brightens the end-of-tunnel golden portal as the mascot approaches. Owner 2026-11-26: "controlled golden starburst,
    /// never white" - the old version scaled the WHOLE portal (bulb rings included) up to 1.6x and pushed its light to 14,
    /// which clipped to white and let the ring grow into the tunnel walls. Now only the glow pieces (core, ray quad,
    /// starburst) swell a little, the bulb rings keep their size, and the warm light stays moderate.
    /// </summary>
    public class PortalGlow : MonoBehaviour
    {
        public RunnerController runner;
        public float trackDistance;
        public float startGlowDistance = 80f;
        public Renderer[] rays;
        public Light portalLight;
        public float maxScale = 1.6f;
        public float raySpin = 12f;
        [Tooltip("Growth of the glow pieces (core / rays / starburst) at the finish; the bulb rings never scale.")]
        public float glowMaxScale = 1.18f;
        public float lightMin = 2f;
        public float lightMax = 6.5f;

        static readonly int IntensityId = Shader.PropertyToID("_Intensity");
        MaterialPropertyBlock mpb;
        readonly List<(Transform t, Vector3 baseScale)> glowParts = new List<(Transform, Vector3)>();

        void Awake()
        {
            mpb = new MaterialPropertyBlock();
            foreach (Transform c in transform)
            {
                string n = c.name.ToLowerInvariant();
                if (n == "core" || n == "rays" || n.Contains("starburst")) glowParts.Add((c, c.localScale));
            }
        }

        void Update()
        {
            if (runner == null) return;
            float remaining = trackDistance - runner.Distance;
            float k = Mathf.Clamp01(1f - remaining / startGlowDistance);
            float s = Mathf.Lerp(1f, glowMaxScale, k * k);
            foreach (var (t, baseScale) in glowParts) if (t != null) t.localScale = baseScale * s;
            if (portalLight) portalLight.intensity = Mathf.Lerp(lightMin, lightMax, k);
            if (rays != null)
                foreach (var r in rays)
                {
                    if (r == null) continue;
                    r.GetPropertyBlock(mpb);
                    mpb.SetFloat(IntensityId, Mathf.Lerp(0.6f, 1.4f, k));
                    r.SetPropertyBlock(mpb);
                    r.transform.Rotate(0f, 0f, raySpin * Time.deltaTime, Space.Self);
                }
        }
    }
}
