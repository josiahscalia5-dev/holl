using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// 3D milk crown splashes at the mascot's feet (reference 1.75-3.0 s): each crown flips through a seamless loop of
    /// Blender metaball frames (Art/Models/FX/SM_FX_Crown_xx) like stop-motion liquid, gets a small scale / yaw jitter
    /// every cycle, grows with speed and collapses while airborne. Frames are swapped on shared MeshFilters (no allocations).
    /// In edit mode (still captures) the authored frame stays.
    /// </summary>
    public class SplashCrowns : MonoBehaviour
    {
        public RunnerController runner;
        public Mesh[] frames;
        public MeshFilter[] crowns;
        [Tooltip("Frame offset per crown so the two sides never match.")]
        public int[] phase;
        [Tooltip("Authored local scale per crown (x < 0 = mirrored right-side crown).")]
        public Vector3[] baseScale;
        public Quaternion[] baseRotation;
        public float fps = 15f;
        public float collapseSpeed = 7f;

        float clock;
        float[] presence, jitter, yaw;
        int[] cycle;
        Renderer[] renderers;

        void OnEnable()
        {
            int n = crowns != null ? crowns.Length : 0;
            presence = new float[n]; jitter = new float[n]; yaw = new float[n]; cycle = new int[n];
            renderers = new Renderer[n];
            for (int i = 0; i < n; i++)
            {
                presence[i] = 1f; jitter[i] = 1f; cycle[i] = -1;
                if (crowns[i] != null) renderers[i] = crowns[i].GetComponent<Renderer>();
            }
        }

        void Update()
        {
            if (frames == null || frames.Length == 0 || crowns == null) return;
            bool sliding = runner == null || (runner.Grounded && runner.Speed > 1f);
            float speedK = runner == null ? 1f : Mathf.Clamp(runner.Speed / Mathf.Max(1f, runner.baseSpeed), 0.5f, 1.7f);
            clock += Time.deltaTime * fps * Mathf.Lerp(0.85f, 1.2f, Mathf.InverseLerp(0.5f, 1.7f, speedK));
            for (int i = 0; i < crowns.Length; i++)
            {
                var mf = crowns[i];
                if (mf == null) continue;
                presence[i] = Mathf.MoveTowards(presence[i], sliding ? 1f : 0f, Time.deltaTime * collapseSpeed);
                int off = phase != null && i < phase.Length ? phase[i] : 0;
                int step = Mathf.FloorToInt(clock) + off;
                int f = ((step % frames.Length) + frames.Length) % frames.Length;
                int c = Mathf.FloorToInt((float)step / frames.Length);
                if (c != cycle[i])
                {
                    cycle[i] = c;
                    jitter[i] = Random.Range(0.88f, 1.12f);
                    yaw[i] = Random.Range(-7f, 7f);
                }
                if (mf.sharedMesh != frames[f]) mf.sharedMesh = frames[f];
                float s = presence[i] * jitter[i] * Mathf.Lerp(0.85f, 1.15f, Mathf.InverseLerp(0.5f, 1.7f, speedK));
                var bs = baseScale != null && i < baseScale.Length ? baseScale[i] : Vector3.one;
                mf.transform.localScale = new Vector3(bs.x * s, bs.y * s * Mathf.Lerp(0.9f, 1.1f, jitter[i] - 0.88f), bs.z * s);
                var br = baseRotation != null && i < baseRotation.Length ? baseRotation[i] : Quaternion.identity;
                mf.transform.localRotation = br * Quaternion.Euler(0f, yaw[i], 0f);
                if (renderers[i] != null) renderers[i].enabled = presence[i] > 0.02f;
            }
        }
    }
}
