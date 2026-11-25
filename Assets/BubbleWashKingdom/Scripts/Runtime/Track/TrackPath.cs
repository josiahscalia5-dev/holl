using System.Collections.Generic;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.Splines;

namespace BubbleWash
{
    /// <summary>One sampled point of the track: position on the slide-floor centre line plus a banked and
    /// an un-banked orthonormal frame.</summary>
    public struct TrackFrame
    {
        public float distance;
        public Vector3 position;
        public Vector3 forward;
        public Vector3 up;        // banked up (slide surface normal at the centre line)
        public Vector3 right;     // banked right
        public Vector3 flatUp;    // world-up projected perpendicular to forward (no banking) - tunnels, rings
        public Vector3 flatRight;
        public float roll;        // degrees, positive = banked into a right-hand turn
        public float curvature;   // signed 1/m, positive = turning right
        public float slope;       // degrees, positive = uphill

        public Quaternion Rotation => Quaternion.LookRotation(forward, up);
        public Quaternion FlatRotation => Quaternion.LookRotation(forward, flatUp);
        public Vector3 Point(float lateral, float height) => position + right * lateral + up * height;
        public Vector3 FlatPoint(float lateral, float height) => position + flatRight * lateral + flatUp * height;
    }

    /// <summary>
    /// Arc-length parameterised view of a <see cref="SplineContainer"/>. Builds a lookup table of frames every
    /// <see cref="sampleSpacing"/> meters with automatic, smoothed banking computed from curvature, so gameplay,
    /// camera and mesh bending all agree on exactly the same frames.
    /// </summary>
    [ExecuteAlways]
    [RequireComponent(typeof(SplineContainer))]
    public class TrackPath : MonoBehaviour
    {
        [Tooltip("Distance between lookup-table frames in meters.")]
        public float sampleSpacing = 0.25f;
        [Tooltip("Speed used to compute coordinated-turn banking (m/s).")]
        public float referenceSpeed = 13f;
        [Range(0f, 1.5f)] public float bankStrength = 0.75f;
        public float maxBank = 24f;
        [Tooltip("Gaussian smoothing of the bank angle along the track, in meters.")]
        public float bankSmoothing = 5f;

        readonly List<TrackFrame> frames = new List<TrackFrame>();
        float length;
        bool built;

        public float Length { get { EnsureBuilt(); return length; } }
        public int FrameCount { get { EnsureBuilt(); return frames.Count; } }

        void OnEnable() { built = false; }
        void OnValidate() { built = false; }

        public void EnsureBuilt()
        {
            if (!built || frames.Count < 2) Rebuild();
        }

        public void Rebuild()
        {
            frames.Clear();
            built = true;
            var container = GetComponent<SplineContainer>();
            if (container == null || container.Spline == null || container.Spline.Count < 2)
            {
                length = 0f;
                return;
            }

            // 1. Dense uniform-t sampling with cumulative arc length.
            float approx = Mathf.Max(1f, container.CalculateLength());
            int n = Mathf.Clamp(Mathf.CeilToInt(approx / 0.04f), 500, 200000);
            var pts = new Vector3[n + 1];
            var cum = new float[n + 1];
            for (int i = 0; i <= n; i++)
            {
                float t = i / (float)n;
                float3 p = container.EvaluatePosition(t);
                pts[i] = p;
                if (i > 0) cum[i] = cum[i - 1] + Vector3.Distance(pts[i - 1], pts[i]);
            }
            length = cum[n];

            // 2. Resample at uniform distance.
            int count = Mathf.Max(2, Mathf.FloorToInt(length / sampleSpacing) + 1);
            var pos = new Vector3[count];
            int seg = 0;
            for (int k = 0; k < count; k++)
            {
                float d = Mathf.Min(k * sampleSpacing, length);
                while (seg < n - 1 && cum[seg + 1] < d) seg++;
                float segLen = Mathf.Max(1e-6f, cum[seg + 1] - cum[seg]);
                pos[k] = Vector3.Lerp(pts[seg], pts[seg + 1], (d - cum[seg]) / segLen);
            }

            // 3. Frames, curvature, raw bank.
            var fwd = new Vector3[count];
            var flatUp = new Vector3[count];
            var curv = new float[count];
            var rawRoll = new float[count];
            Vector3 prevUp = Vector3.up;
            for (int k = 0; k < count; k++)
            {
                Vector3 a = pos[Mathf.Max(0, k - 1)];
                Vector3 b = pos[Mathf.Min(count - 1, k + 1)];
                Vector3 f = (b - a);
                fwd[k] = f.sqrMagnitude > 1e-10f ? f.normalized : (k > 0 ? fwd[k - 1] : Vector3.forward);
                Vector3 u = Vector3.up - fwd[k] * Vector3.Dot(Vector3.up, fwd[k]);
                flatUp[k] = u.sqrMagnitude > 1e-6f ? u.normalized : prevUp;
                prevUp = flatUp[k];
            }
            for (int k = 0; k < count; k++)
            {
                Vector3 fa = fwd[Mathf.Max(0, k - 2)];
                Vector3 fb = fwd[Mathf.Min(count - 1, k + 2)];
                float ds = sampleSpacing * (Mathf.Min(count - 1, k + 2) - Mathf.Max(0, k - 2));
                Vector3 flatRight = Vector3.Cross(flatUp[k], fwd[k]);
                curv[k] = ds > 0f ? Vector3.Dot((fb - fa) / ds, flatRight) : 0f;
                float bank = Mathf.Atan(referenceSpeed * referenceSpeed * curv[k] / 9.81f) * Mathf.Rad2Deg * bankStrength;
                rawRoll[k] = Mathf.Clamp(bank, -maxBank, maxBank);
            }

            // 4. Gaussian-smoothed bank (avoids sudden camera/slide roll changes).
            int radius = Mathf.CeilToInt(bankSmoothing * 2.5f / sampleSpacing);
            float sigma = Mathf.Max(0.01f, bankSmoothing / sampleSpacing);
            var kernel = new float[radius * 2 + 1];
            for (int i = -radius; i <= radius; i++) kernel[i + radius] = Mathf.Exp(-0.5f * i * i / (sigma * sigma));
            for (int k = 0; k < count; k++)
            {
                float sum = 0f, wsum = 0f;
                for (int i = -radius; i <= radius; i++)
                {
                    int j = Mathf.Clamp(k + i, 0, count - 1);
                    float w = kernel[i + radius];
                    sum += rawRoll[j] * w;
                    wsum += w;
                }
                float roll = sum / wsum;
                Vector3 fRight = Vector3.Cross(flatUp[k], fwd[k]);
                // Positive roll tilts "up" toward the inside (right) of a right-hand turn.
                Vector3 up = Quaternion.AngleAxis(-roll, fwd[k]) * flatUp[k];
                frames.Add(new TrackFrame
                {
                    distance = Mathf.Min(k * sampleSpacing, length),
                    position = pos[k],
                    forward = fwd[k],
                    up = up,
                    right = Vector3.Cross(up, fwd[k]),
                    flatUp = flatUp[k],
                    flatRight = fRight,
                    roll = roll,
                    curvature = curv[k],
                    slope = Mathf.Asin(Mathf.Clamp(Vector3.Dot(fwd[k], Vector3.up), -1f, 1f)) * Mathf.Rad2Deg,
                });
            }
        }

        /// <summary>Interpolated frame at a distance (meters) along the track; clamped to [0, Length].</summary>
        public TrackFrame Evaluate(float distance)
        {
            EnsureBuilt();
            if (frames.Count == 0) return new TrackFrame { forward = Vector3.forward, up = Vector3.up, right = Vector3.right, flatUp = Vector3.up, flatRight = Vector3.right };
            float x = Mathf.Clamp(distance, 0f, length) / sampleSpacing;
            int i = Mathf.Clamp(Mathf.FloorToInt(x), 0, frames.Count - 1);
            int j = Mathf.Min(i + 1, frames.Count - 1);
            float t = Mathf.Clamp01(x - i);
            TrackFrame a = frames[i], b = frames[j];
            Vector3 f = Vector3.Slerp(a.forward, b.forward, t).normalized;
            Vector3 u = Vector3.Slerp(a.up, b.up, t);
            u = (u - f * Vector3.Dot(u, f)).normalized;
            Vector3 fu = Vector3.Slerp(a.flatUp, b.flatUp, t);
            fu = (fu - f * Vector3.Dot(fu, f)).normalized;
            return new TrackFrame
            {
                distance = Mathf.Lerp(a.distance, b.distance, t),
                position = Vector3.Lerp(a.position, b.position, t),
                forward = f,
                up = u,
                right = Vector3.Cross(u, f),
                flatUp = fu,
                flatRight = Vector3.Cross(fu, f),
                roll = Mathf.Lerp(a.roll, b.roll, t),
                curvature = Mathf.Lerp(a.curvature, b.curvature, t),
                slope = Mathf.Lerp(a.slope, b.slope, t),
            };
        }

#if UNITY_EDITOR
        void OnDrawGizmosSelected()
        {
            EnsureBuilt();
            Gizmos.color = Color.cyan;
            for (int k = 0; k + 8 < frames.Count; k += 8)
            {
                Gizmos.DrawLine(frames[k].position, frames[k + 8].position);
                Gizmos.DrawLine(frames[k].position, frames[k].position + frames[k].up * 1.5f);
            }
        }
#endif
    }
}
