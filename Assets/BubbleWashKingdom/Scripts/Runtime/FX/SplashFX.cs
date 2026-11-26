using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Water effects around the mascot: continuous side spray and foam trail while sliding (scaled by speed), a
    /// crown splash on landings and boosts, speed streaks during boosts, and sparkle bursts on pickups.
    /// </summary>
    public class SplashFX : MonoBehaviour
    {
        public RunnerController runner;
        public TrackItemRegistry items;
        public ParticleSystem spray;
        public ParticleSystem foamTrail;
        public ParticleSystem crown;
        public ParticleSystem speedStreaks;
        public ParticleSystem pickupSparkles;
        public ParticleSystem gemSparkles;
        [Tooltip("Milky crown splash sheets flanking the mascot (reference 1.75-7.5 s).")]
        public ParticleSystem[] sheets;
        public float sprayRateAtBase = 46f;
        public float sheetRateAtBase = 11f;
        public float trailRateAtBase = 14f;
        [Tooltip("Extra speed-scaled emitters (3D milk droplets, splash bubbles, speed lines); rate at base speed per entry.")]
        public ParticleSystem[] extra;
        public float[] extraRates;
        [Tooltip("Hand-placed glassy bubbles around the mascot (hero composition, reference f_003.00s). In play they bob, drift " +
                 "back toward the camera, pop and re-form at their spot; edit-mode still captures keep the authored layout.")]
        public Transform[] heroBubbles;
        Vector3[] hbBase, hbScale;
        float[] hbPhase;

        void OnEnable()
        {
            if (runner != null)
            {
                runner.Landed += OnLand;
                runner.BoostStarted += OnBoost;
                runner.Bumped += OnLand;
            }
            if (items != null) items.OnCollected += OnPickup;
            if (heroBubbles != null && hbBase == null)
            {
                int n = heroBubbles.Length;
                hbBase = new Vector3[n]; hbScale = new Vector3[n]; hbPhase = new float[n];
                for (int i = 0; i < n; i++)
                {
                    if (heroBubbles[i] == null) continue;
                    hbBase[i] = heroBubbles[i].localPosition;
                    hbScale[i] = heroBubbles[i].localScale;
                    hbPhase[i] = Mathf.Repeat(i * 0.618f, 1f);
                }
            }
        }

        void AnimateHeroBubbles(bool sliding)
        {
            if (heroBubbles == null || hbBase == null) return;
            float t = Time.time;
            for (int i = 0; i < heroBubbles.Length; i++)
            {
                var b = heroBubbles[i];
                if (b == null) continue;
                float ph = hbPhase[i];
                float cyc = Mathf.Repeat(t * 0.2f + ph, 1f);                       // 5 s life: form, drift back, pop
                float grow = Mathf.SmoothStep(0f, 1f, cyc / 0.12f) * (1f - Mathf.SmoothStep(0f, 1f, (cyc - 0.9f) / 0.1f));
                var wobble = new Vector3(Mathf.Sin(t * 1.3f + ph * 6.2f) * 0.03f, Mathf.Sin(t * 1.7f + ph * 9.1f) * 0.035f + cyc * 0.1f,
                                         sliding ? -cyc * 0.3f : 0f);
                b.localPosition = hbBase[i] + wobble;
                b.localScale = hbScale[i] * Mathf.Max(0.001f, grow);
            }
        }

        void OnDisable()
        {
            if (runner != null)
            {
                runner.Landed -= OnLand;
                runner.BoostStarted -= OnBoost;
                runner.Bumped -= OnLand;
            }
            if (items != null) items.OnCollected -= OnPickup;
        }

        void OnLand()
        {
            if (crown) crown.Emit(18);
            if (sheets != null) foreach (var sh in sheets) if (sh) sh.Emit(3);
        }

        void OnBoost()
        {
            if (crown) crown.Emit(14);
            if (speedStreaks) speedStreaks.Play();
        }

        void OnPickup(TrackItem item)
        {
            if (item.kind == TrackItemKind.Coin && pickupSparkles) Burst(pickupSparkles, item.transform.position, 14);
            else if (item.kind == TrackItemKind.Gem && gemSparkles) Burst(gemSparkles, item.transform.position, 22);
        }

        static void Burst(ParticleSystem ps, Vector3 position, int count)
        {
            var ep = new ParticleSystem.EmitParams { position = position, applyShapeToPosition = true };
            ps.Emit(ep, count);
        }

        void Update()
        {
            if (runner == null) return;
            bool sliding = runner.Grounded && runner.Speed > 1f;
            float speedK = runner.Speed / Mathf.Max(1f, runner.baseSpeed);
            if (spray)
            {
                var em = spray.emission;
                em.rateOverTime = sliding ? sprayRateAtBase * speedK : 0f;
            }
            if (foamTrail)
            {
                var em = foamTrail.emission;
                em.rateOverTime = sliding ? trailRateAtBase * speedK : 0f;
            }
            if (sheets != null)
                foreach (var sh in sheets)
                {
                    if (sh == null) continue;
                    var em = sh.emission;
                    em.rateOverTime = sliding ? sheetRateAtBase * speedK : 0f;
                }
            if (extra != null)
                for (int i = 0; i < extra.Length; i++)
                {
                    if (extra[i] == null) continue;
                    var em = extra[i].emission;
                    float baseRate = extraRates != null && i < extraRates.Length ? extraRates[i] : 0f;
                    em.rateOverTime = sliding ? baseRate * speedK : 0f;
                }
            if (speedStreaks && !runner.Boosting && speedStreaks.isPlaying) speedStreaks.Stop();
            AnimateHeroBubbles(sliding);
        }
    }
}
