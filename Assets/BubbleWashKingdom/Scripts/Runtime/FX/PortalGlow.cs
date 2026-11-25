using UnityEngine;

namespace BubbleWash
{
    /// <summary>Brightens and scales the end-of-tunnel light portal as the mascot approaches.</summary>
    public class PortalGlow : MonoBehaviour
    {
        public RunnerController runner;
        public float trackDistance;
        public float startGlowDistance = 80f;
        public Renderer[] rays;
        public Light portalLight;
        public float maxScale = 1.6f;
        public float raySpin = 12f;
        static readonly int IntensityId = Shader.PropertyToID("_Intensity");
        MaterialPropertyBlock mpb;
        Vector3 baseScale;

        void Awake() { mpb = new MaterialPropertyBlock(); baseScale = transform.localScale; }

        void Update()
        {
            if (runner == null) return;
            float remaining = trackDistance - runner.Distance;
            float k = Mathf.Clamp01(1f - remaining / startGlowDistance);
            transform.localScale = baseScale * Mathf.Lerp(1f, maxScale, k * k);
            if (portalLight) portalLight.intensity = Mathf.Lerp(2f, 14f, k);
            if (rays != null)
                foreach (var r in rays)
                {
                    if (r == null) continue;
                    r.GetPropertyBlock(mpb);
                    mpb.SetFloat(IntensityId, Mathf.Lerp(0.6f, 2.2f, k));
                    r.SetPropertyBlock(mpb);
                    r.transform.Rotate(0f, 0f, raySpin * Time.deltaTime, Space.Self);
                }
        }
    }
}
