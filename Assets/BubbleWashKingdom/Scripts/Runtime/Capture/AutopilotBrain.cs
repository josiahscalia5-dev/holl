using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Simple autopilot used for automated play-tests and gameplay recordings: steers toward the lane with the most
    /// value ahead (coins, gems, boosts), away from obstacles, and jumps over jumpable obstacles or for raised gems.
    /// Uses the same lane/jump API as swipe input, so it exercises the real controls.
    /// </summary>
    public class AutopilotBrain : MonoBehaviour, IRunnerBrain
    {
        public RunnerController runner;
        public TrackItemRegistry items;
        public float lookAhead = 24f;
        public float decisionInterval = 0.18f;
        [Tooltip("Adds harmless lane changes so recordings show steering even on empty stretches.")]
        public bool showcaseSteering = true;

        float timer;
        float showcaseTimer = 2.5f;

        void OnEnable()
        {
            if (runner == null) runner = GetComponent<RunnerController>();
            if (runner != null) runner.brain = this;
        }

        void OnDisable()
        {
            if (runner != null && ReferenceEquals(runner.brain, this)) runner.brain = null;
        }

        public void Tick(RunnerController r, float dt)
        {
            if (r.State != RunnerState.Running || items == null) return;
            timer -= dt;
            showcaseTimer -= dt;
            if (timer > 0f) return;
            timer = decisionInterval;

            int lanes = r.lanesEachSide;
            var score = new float[lanes * 2 + 1];
            bool jumpNeeded = false;
            foreach (var it in items.Ahead(r.Distance + 1.5f, r.Distance + lookAhead))
            {
                int lane = Mathf.Clamp(Mathf.RoundToInt(it.lateral / r.laneWidth), -lanes, lanes);
                float ahead = it.distance - r.Distance;
                float w = Mathf.Lerp(1f, 0.25f, ahead / lookAhead);
                switch (it.kind)
                {
                    case TrackItemKind.Coin: score[lane + lanes] += 1f * w; break;
                    case TrackItemKind.Gem: score[lane + lanes] += 3f * w; break;
                    case TrackItemKind.Boost: score[lane + lanes] += 2f * w; break;
                    case TrackItemKind.Obstacle:
                        int span = Mathf.Max(0, Mathf.RoundToInt((it.halfWidth - 0.4f) / r.laneWidth));
                        for (int l = lane - span; l <= lane + span; l++)
                            if (l >= -lanes && l <= lanes) score[l + lanes] -= (it.jumpable ? 4f : 12f) * w;
                        if (it.jumpable && ahead < 5.5f && Mathf.Abs(it.lateral - r.Lateral) < TrackItemRegistry.HitHalfWidth(it, r.laneWidth)) jumpNeeded = true;
                        break;
                }
                if (it.kind == TrackItemKind.Gem && it.height > 1.0f && ahead < 4.5f && Mathf.Abs(it.lateral - r.Lateral) < 0.6f)
                    jumpNeeded = true;
            }

            int best = r.Lane;
            float bestScore = score[r.Lane + lanes] + 0.15f; // slight preference to stay
            for (int l = -lanes; l <= lanes; l++)
                if (score[l + lanes] > bestScore) { bestScore = score[l + lanes]; best = l; }

            if (best == r.Lane && showcaseSteering && showcaseTimer <= 0f && bestScore <= 0.2f)
            {
                best = r.Lane == 0 ? (Random.value < 0.5f ? -1 : 1) : 0;
                showcaseTimer = 3.5f;
            }

            if (best != r.Lane) r.ChangeLane(best > r.Lane ? 1 : -1);
            if (jumpNeeded) r.Jump();
        }
    }
}
