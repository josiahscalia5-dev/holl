using System;
using UnityEngine;

namespace BubbleWash
{
    public enum RunnerState { Waiting, Running, Finished }

    public interface IRunnerBrain
    {
        void Tick(RunnerController runner, float dt);
    }

    /// <summary>
    /// Moves the mascot along the <see cref="TrackPath"/>: forward speed with downhill acceleration and boosts,
    /// three lanes with smooth lane changes, outward drift up the slide wall in curves, jumping with gravity, and
    /// orientation that always faces the direction of travel (never backwards, never toward the camera).
    /// </summary>
    [DefaultExecutionOrder(-50)]
    public class RunnerController : MonoBehaviour
    {
        [Header("References")]
        public TrackPath track;
        public SwipeInput input;
        public TrackItemRegistry items;
        [Tooltip("Visual child that receives lean/pitch; the root follows the track frame.")]
        public Transform visual;

        [Header("Speed (m/s)")]
        public float baseSpeed = 12f;
        public float maxSpeed = 21f;
        [Tooltip("How strongly slopes change speed (fraction of g).")]
        public float slopeFactor = 0.45f;
        [Tooltip("Rate at which speed returns to the target speed (1/s).")]
        public float speedRecovery = 0.9f;
        public float boostSpeed = 6.5f;
        public float boostDuration = 2.4f;
        public float startDistance = 3f;
        public float finishMargin = 6f;

        [Header("Lanes")]
        public float laneWidth = 1.15f;
        public int lanesEachSide = 1;
        public float laneChangeTime = 0.14f;

        [Header("Slide cross-section (must match SM_Slide_Module)")]
        public float flatHalfWidth = 1.25f;
        public float wallCurve = 0.9f;
        [Tooltip("Outward drift up the wall in curves: meters per (curvature * speed^2).")]
        public float driftGain = 0.012f;
        public float maxDrift = 0.55f;

        [Header("Jump")]
        public float jumpVelocity = 6.6f;
        public float gravity = 21f;

        [Header("Visual")]
        public float maxLean = 20f;
        public float curveLean = 10f;
        public float leanResponse = 10f;

        public RunnerState State { get; private set; } = RunnerState.Waiting;
        public float Distance { get; private set; }
        public float Lateral { get; private set; }
        public float Height { get; private set; }
        public float Speed { get; private set; }
        public int Lane { get; private set; }
        public float Steer { get; private set; }
        public float CurveSteer { get; private set; }
        public float BoostTime { get; private set; }
        public bool Grounded => Height <= 0f && verticalVel <= 0f;
        public bool Boosting => BoostTime > 0f;
        public bool Stumbling => stumble > 0f;
        public float Progress => track != null && track.Length > 0f ? Distance / track.Length : 0f;
        public TrackFrame Frame { get; private set; }

        public IRunnerBrain brain;
        public event Action Jumped, Landed, BoostStarted, Bumped, FinishedRun, LaneChanged;
        public event Action<TrackItem> Collected;

        float latVel, verticalVel, drift, stumble, lean, pitch;

        void Awake()
        {
            if (track == null) track = FindFirstObjectByType<TrackPath>();
            Distance = startDistance;
            SnapToTrack();
        }

        void OnEnable() { if (input != null) input.Swiped += OnSwipe; }
        void OnDisable() { if (input != null) input.Swiped -= OnSwipe; }

        public void Begin()
        {
            if (State == RunnerState.Running) return;
            State = RunnerState.Running;
            Speed = baseSpeed * 0.8f;
        }

        public void ResetRun()
        {
            State = RunnerState.Waiting;
            Distance = startDistance;
            Lane = 0; Lateral = 0f; Height = 0f; verticalVel = 0f; Speed = 0f; BoostTime = 0f; stumble = 0f; drift = 0f;
            items?.ResetAll();
            SnapToTrack();
        }

        void OnSwipe(SwipeDir dir)
        {
            if (State != RunnerState.Running) return;
            switch (dir)
            {
                case SwipeDir.Left: ChangeLane(-1); break;
                case SwipeDir.Right: ChangeLane(+1); break;
                case SwipeDir.Up: Jump(); break;
            }
        }

        public void ChangeLane(int delta)
        {
            int target = Mathf.Clamp(Lane + delta, -lanesEachSide, lanesEachSide);
            if (target == Lane) return;
            Lane = target;
            LaneChanged?.Invoke();
        }

        public void Jump()
        {
            if (!Grounded || State != RunnerState.Running) return;
            verticalVel = jumpVelocity;
            Height = 0.001f;
            Jumped?.Invoke();
        }

        public void StartBoost()
        {
            BoostTime = boostDuration;
            Speed = Mathf.Max(Speed, baseSpeed + boostSpeed * 0.7f);
            BoostStarted?.Invoke();
        }

        public void Bump()
        {
            if (stumble > 0f) return;
            stumble = 0.7f;
            Speed *= 0.55f;
            BoostTime = 0f;
            Bumped?.Invoke();
        }

        void Update()
        {
            if (track == null) return;
            float dt = Mathf.Min(Time.deltaTime, 0.05f);
            brain?.Tick(this, dt);

            TrackFrame f = track.Evaluate(Distance);
            if (State == RunnerState.Running)
            {
                float target = baseSpeed + (BoostTime > 0f ? boostSpeed : 0f);
                Speed = Mathf.Lerp(Speed, target, 1f - Mathf.Exp(-speedRecovery * dt));
                Speed += -Mathf.Sin(f.slope * Mathf.Deg2Rad) * 9.81f * slopeFactor * dt;
                if (stumble > 0f) Speed = Mathf.Min(Speed, baseSpeed * 0.6f);
                Speed = Mathf.Clamp(Speed, 4f, maxSpeed);
                Distance += Speed * dt;
                BoostTime = Mathf.Max(0f, BoostTime - dt);
                stumble = Mathf.Max(0f, stumble - dt);
                if (Distance >= track.Length - finishMargin)
                {
                    Distance = track.Length - finishMargin;
                    State = RunnerState.Finished;
                    FinishedRun?.Invoke();
                }
            }
            else if (State == RunnerState.Finished)
            {
                Speed = Mathf.MoveTowards(Speed, 0f, 14f * dt);
                Distance = Mathf.Min(Distance + Speed * dt, track.Length - 0.5f);
            }

            // Lateral: lane target plus outward drift up the wall in curves.
            float targetDrift = Mathf.Clamp(-f.curvature * Speed * Speed * driftGain, -maxDrift, maxDrift);
            drift = Mathf.Lerp(drift, targetDrift, 1f - Mathf.Exp(-3f * dt));
            float prevLat = Lateral;
            Lateral = Mathf.SmoothDamp(Lateral, Lane * laneWidth + drift, ref latVel, laneChangeTime, Mathf.Infinity, dt);

            // Vertical (jump).
            if (Height > 0f || verticalVel > 0f)
            {
                verticalVel -= gravity * dt;
                Height += verticalVel * dt;
                if (Height <= 0f)
                {
                    Height = 0f;
                    verticalVel = 0f;
                    Landed?.Invoke();
                }
            }

            SnapToTrack();

            // Steering signals for animation and lean.
            float lateralSpeed = dt > 0f ? (Lateral - prevLat) / dt : 0f;
            Steer = Mathf.Clamp(lateralSpeed / (laneWidth / Mathf.Max(0.05f, laneChangeTime * 2.2f)), -1f, 1f);
            CurveSteer = Mathf.Clamp(Frame.curvature * Speed * Speed / 9.81f, -1f, 1f);

            if (items != null && State == RunnerState.Running) items.CheckHits(this);
        }

        public float SurfaceHeight(float x)
        {
            float a = Mathf.Abs(x) - flatHalfWidth;
            return a > 0f ? wallCurve * a * a : 0f;
        }

        Vector3 SurfaceNormal(TrackFrame f, float x)
        {
            float a = Mathf.Abs(x) - flatHalfWidth;
            if (a <= 0f) return f.up;
            float slope = 2f * wallCurve * a * Mathf.Sign(x); // dy/dx
            return (f.up - f.right * slope).normalized;
        }

        void SnapToTrack()
        {
            if (track == null) return;
            TrackFrame f = track.Evaluate(Distance);
            Frame = f;
            Vector3 normal = SurfaceNormal(f, Lateral);
            Vector3 pos = f.position + f.right * Lateral + f.up * (SurfaceHeight(Lateral) + Height);
            Vector3 up = Vector3.Slerp(f.up, normal, 0.7f);
            transform.SetPositionAndRotation(pos, Quaternion.LookRotation(f.forward, up));

            if (visual != null)
            {
                float dt = Application.isPlaying ? Time.deltaTime : 1f;
                float targetLean = -Steer * maxLean - CurveSteer * curveLean;
                lean = Mathf.Lerp(lean, targetLean, 1f - Mathf.Exp(-leanResponse * dt));
                float targetPitch = Boosting ? 10f : Mathf.Clamp(-f.slope * 0.35f, -6f, 10f);
                pitch = Mathf.Lerp(pitch, targetPitch, 1f - Mathf.Exp(-5f * dt));
                visual.localRotation = Quaternion.Euler(pitch, 0f, lean);
            }
        }

        internal void NotifyCollected(TrackItem item) => Collected?.Invoke(item);
    }
}
