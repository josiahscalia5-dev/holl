using System.Collections.Generic;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>Holds all track items sorted by distance and performs cheap distance-based hit tests.</summary>
    public class TrackItemRegistry : MonoBehaviour
    {
        public List<TrackItem> items = new List<TrackItem>();
        [Tooltip("Coins and gems within this radius of the mascot are pulled in.")]
        public float magnetRadius = 0.0f;

        public int Coins { get; private set; }
        public int Gems { get; private set; }
        public System.Action<TrackItem> OnCollected;
        int cursor;

        void Awake() { Sort(); }

        /// <summary>Lateral reach of a hit (item half-width + 0.3 m body), capped at 0.62 lane widths. lead 3c2b09a2
        /// 2026-11-27: since the 11:00 corridor narrowing (lanes 1.15 -> 0.90 m) the uncapped 0.6 + 0.3 = 0.9 m equalled the
        /// lane spacing, so a mascot in the centre lane also collected the coins (and boost pads) of BOTH side lanes and
        /// lane choice stopped mattering. Capped: 0.56 m with 0.90 m lanes - own lane only, either lane mid-change.</summary>
        public static float HitHalfWidth(TrackItem it, float laneWidth) => Mathf.Min(it.halfWidth + 0.3f, laneWidth * 0.62f);

        public void Sort()
        {
            items.RemoveAll(i => i == null);
            items.Sort((a, b) => a.distance.CompareTo(b.distance));
            cursor = 0;
        }

        public void ResetAll()
        {
            foreach (var i in items) if (i != null) i.ResetItem();
            Coins = Gems = 0;
            cursor = 0;
        }

        public void CheckHits(RunnerController r)
        {
            float d = r.Distance;
            while (cursor < items.Count && items[cursor].distance + items[cursor].halfLength < d - 2f) cursor++;
            for (int k = cursor; k < items.Count; k++)
            {
                var it = items[k];
                if (it.distance - it.halfLength > d + 1.0f) break;
                if (it.Consumed) continue;
                if (Mathf.Abs(it.distance - d) > it.halfLength + 0.35f) continue;
                if (Mathf.Abs(it.lateral - r.Lateral) > HitHalfWidth(it, r.laneWidth)) continue;
                switch (it.kind)
                {
                    case TrackItemKind.Coin:
                    case TrackItemKind.Gem:
                        float itemH = it.height;
                        float runnerTop = r.Height + 1.1f;
                        if (itemH > runnerTop + 0.2f || itemH < r.Height - 0.4f) continue;
                        it.Consume(r.transform);
                        if (it.kind == TrackItemKind.Coin) Coins += it.value; else Gems += it.value;
                        r.NotifyCollected(it);
                        OnCollected?.Invoke(it);
                        break;
                    case TrackItemKind.Boost:
                        if (r.Height > 0.4f) continue;
                        it.Consume(null);
                        r.StartBoost();
                        r.NotifyCollected(it);
                        OnCollected?.Invoke(it);
                        break;
                    case TrackItemKind.Obstacle:
                        if (it.jumpable && r.Height >= it.clearHeight) continue;
                        it.Consume(null);
                        r.Bump();
                        r.NotifyCollected(it);
                        OnCollected?.Invoke(it);
                        break;
                }
            }
        }

        /// <summary>Items ahead of a distance within a window (for the autopilot).</summary>
        public IEnumerable<TrackItem> Ahead(float from, float to)
        {
            for (int k = cursor; k < items.Count; k++)
            {
                var it = items[k];
                if (it.distance < from) continue;
                if (it.distance > to) yield break;
                if (!it.Consumed) yield return it;
            }
        }
    }
}
