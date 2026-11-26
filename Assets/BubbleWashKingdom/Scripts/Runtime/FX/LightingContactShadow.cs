using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// OWNER: Agent 4 (lighting). Keeps the mascot's soft contact-shadow card on the slide surface while he jumps
    /// (the runner transform rises with RunnerController.Height) and lets it shrink / fade with height.
    /// </summary>
    public class LightingContactShadow : MonoBehaviour
    {
        public RunnerController runner;
        public float surfaceOffset = 0.035f;
        public Vector3 baseScale = new Vector3(1.25f, 1.6f, 1f);
        public float fadeHeight = 2.2f;
        Renderer rend;
        MaterialPropertyBlock mpb;
        static readonly int StrengthId = Shader.PropertyToID("_Strength");
        float baseStrength = -1f;

        void LateUpdate()
        {
            if (runner == null) return;
            if (rend == null) rend = GetComponent<Renderer>();
            if (mpb == null) mpb = new MaterialPropertyBlock();
            if (baseStrength < 0f && rend != null && rend.sharedMaterial != null && rend.sharedMaterial.HasProperty(StrengthId))
                baseStrength = rend.sharedMaterial.GetFloat(StrengthId);
            float h = Mathf.Max(0f, runner.Height);
            var p = transform.localPosition;
            p.y = surfaceOffset - h;
            transform.localPosition = p;
            float k = Mathf.Clamp01(h / fadeHeight);
            transform.localScale = baseScale * Mathf.Lerp(1f, 0.6f, k);
            if (rend != null && baseStrength >= 0f)
            {
                rend.GetPropertyBlock(mpb);
                mpb.SetFloat(StrengthId, baseStrength * (1f - 0.75f * k));
                rend.SetPropertyBlock(mpb);
            }
        }
    }
}
