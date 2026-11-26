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

        void OnEnable()
        {
            if (runner != null)
            {
                runner.Landed += OnLand;
                runner.BoostStarted += OnBoost;
                runner.Bumped += OnLand;
            }
            if (items != null) items.OnCollected += OnPickup;
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
            if (speedStreaks && !runner.Boosting && speedStreaks.isPlaying) speedStreaks.Stop();
        }
    }
}
