using Unity.Cinemachine;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Gameplay camera: stays behind and slightly above the mascot (who faces the direction of travel), follows the
    /// track through curves, drops with downhill sections and banks a controlled fraction of the slide's roll.
    /// Lives on the gameplay CinemachineCamera, which has no procedural Position/Rotation components, so this
    /// transform is the camera pose; Cinemachine handles lens, blending and shake.
    /// </summary>
    [DefaultExecutionOrder(100)]
    public class RunnerCameraRig : MonoBehaviour
    {
        public RunnerController runner;
        public CinemachineCamera vcam;

        [Header("Landscape 16:9 framing (matches the reference rear view)")]
        public float distanceBack = 2.9f;
        public float height = 1.6f;
        public float fovLandscape = 52f;

        [Header("Portrait 9:16 framing")]
        [Tooltip("Owner requirement: rear follow camera slightly above and behind; back of hat, pom-pom, arms and paws visible, route and tunnel visible ahead above the pom-pom. " +
                 "Owner-approved camera: 2026-11-25 2.75 back / 1.3 up / pitch 10 / FOV 58; 2026-11-26 21:50 (owner: reveal more scenery, keep portrait) 3.1 / 1.45 / 7 / 70 = SceneBuilder.HeroCam*. Change only with the owner's explicit approval.")]
        public float distanceBackPortrait = 3.1f;
        public float heightPortrait = 1.45f;
        public float fovPortrait = 70f;

        [Header("Aim")]
        public float lookAhead = 10f;
        [Tooltip("Downward pitch from the track direction (reference: about 8.5 degrees at 16:9).")]
        public float pitchDown = 9f;
        public float pitchDownPortrait = 7f;
        public float lookHeight = 0.6f;
        [Range(0f, 1f)] public float lookAtRunnerWeight = 0.08f;
        [Range(0f, 1f)] public float lateralFollow = 0.55f;
        [Tooltip("Portrait screens are narrow: follow more of the lane change so the mascot never drifts to the screen edge.")]
        [Range(0f, 1f)] public float lateralFollowPortrait = 0.8f;
        [Range(0f, 1f)] public float jumpFollow = 0.35f;
        [Tooltip("On slopes the track point behind the mascot is higher/lower than the mascot: remove this fraction of the " +
                 "difference so the camera stays level with the hat band (reference) instead of looking down on downhills.")]
        [Range(0f, 1f)] public float slopeCompensation = 0.85f;
        [Tooltip("Same for the look-ahead point, so the gaze runs along the slide instead of diving on long downhills.")]
        [Range(0f, 1f)] public float lookSlopeCompensation = 0.5f;

        [Header("Banking")]
        [Range(0f, 1f)] public float bankFactor = 0.5f;
        public float maxDutch = 11f;

        [Header("Dynamics")]
        public float boostFovKick = 7f;
        public float positionSmoothTime = 0.09f;
        public float lookSmoothTime = 0.07f;
        public float dutchSmoothTime = 0.3f;
        [Tooltip("> 0 forces an aspect (used by capture tools); otherwise the output camera aspect is used.")]
        public float aspectOverride = 0f;

        // Owner 2026-11-26 (review of the round-7 recording): the old front-facing intro orbit crowded the mascot and its hat
        // and its blend to this rig passed through the hat; the celebration orbit flew past the portal into empty space.
        // Both are now offsets on THIS rear rig (no camera switch, no blend through the mascot). They are zero in gameplay and
        // in every capture (Snap() clears them), so the frozen hero framing 2.75 / 1.3 / 10 / 58 is unchanged.
        [Header("Opening crane (rear, eases into the gameplay framing)")]
        [Tooltip("The opening starts this much further back than the gameplay framing (metres along the track).")]
        public float introExtraBack = 4.4f;
        [Tooltip("...and this much higher (metres).")]
        public float introExtraHeight = 1.7f;
        [Tooltip("...and pitched this much further down (degrees), so the shot reveals the hall and the slide ahead.")]
        public float introExtraPitch = 7f;

        [Header("Finale (rear camera, mascot turned to face it, golden portal behind the mascot)")]
        public float finaleExtraBack = 1.4f;
        public float finaleExtraHeight = 0.15f;
        [Tooltip("Degrees of LESS downward pitch, so the top of the portal's bulb ring is in frame.")]
        public float finalePitchUp = 5f;
        public float finaleFovDelta = 5f;
        public float finaleBlendTime = 1.7f;
        [Tooltip("Slow push-in after the finale blend (metres over finalePushTime seconds).")]
        public float finalePushIn = 0.45f;
        public float finalePushTime = 5f;

        Vector3 posVel, lookVel, smoothedLook;
        float smLat, smH, latV, hV;
        float dutch, dutchVel, fov, fovVel;
        float introTime = -1f, introDuration = 1f, finaleTime = -1f;
        bool initialized;
        Camera outputCamera;

        /// <summary>0..1 weight of the opening crane (1 = start pose, 0 = gameplay framing).</summary>
        public float IntroWeight => introTime < 0f ? 0f : 1f - SmootherStep(introTime / Mathf.Max(0.01f, introDuration));
        /// <summary>0..1 weight of the finale framing.</summary>
        public float FinaleWeight => finaleTime < 0f ? 0f : SmootherStep(finaleTime / Mathf.Max(0.01f, finaleBlendTime));

        static float SmootherStep(float x) { x = Mathf.Clamp01(x); return x * x * x * (x * (x * 6f - 15f) + 10f); }

        /// <summary>Starts the opening crane: the camera begins further back / higher and eases into the gameplay framing.</summary>
        public void PlayIntro(float duration)
        {
            introDuration = Mathf.Max(0.1f, duration);
            introTime = 0f;
            finaleTime = -1f;
            initialized = false; // snap to the crane's start pose (new run / loop restart)
        }

        /// <summary>Eases into (true) or clears (false, immediate) the finale framing.</summary>
        public void SetFinale(bool on) { finaleTime = on ? Mathf.Max(0f, finaleTime) : -1f; }

        void OnEnable() { initialized = false; }

        void LateUpdate()
        {
            if (runner == null || runner.track == null) return;
            float dt = Time.deltaTime;
            if (introTime >= 0f) { introTime += dt; if (introTime >= introDuration) introTime = -1f; }
            if (finaleTime >= 0f) finaleTime += dt;
            Step(dt, !initialized);
            initialized = true;
        }

        /// <summary>Jumps straight to the plain gameplay framing (capture tools, tests): cancels the opening / finale offsets.</summary>
        public void Snap()
        {
            if (runner == null || runner.track == null) return;
            introTime = -1f;
            finaleTime = -1f;
            Step(0f, true);
            initialized = true;
        }

        /// <summary>Capture tools: jumps straight to the settled finale framing (before the slow push-in). Call Snap() after.</summary>
        public void SnapFinale()
        {
            if (runner == null || runner.track == null) return;
            introTime = -1f;
            finaleTime = finaleBlendTime;
            Step(0f, true);
            initialized = true;
        }

        /// <summary>Track frame that continues straight beyond the ends of the track (the opening crane may start behind 0 m).</summary>
        static TrackFrame EvaluateExtended(TrackPath track, float d)
        {
            if (d >= 0f && d <= track.Length) return track.Evaluate(d);
            float edge = d < 0f ? 0f : track.Length;
            TrackFrame f = track.Evaluate(edge);
            f.position += f.forward * (d - edge);
            f.distance = d;
            return f;
        }

        public float CurrentAspect()
        {
            if (aspectOverride > 0f) return aspectOverride;
            if (outputCamera == null) outputCamera = Camera.main;
            return outputCamera != null ? outputCamera.aspect : (float)Screen.width / Mathf.Max(1, Screen.height);
        }

        void Step(float dt, bool snap)
        {
            var track = runner.track;
            float aspect = CurrentAspect();
            float portrait = Mathf.InverseLerp(1.2f, 0.6f, aspect); // 0 = landscape, 1 = portrait
            float back = Mathf.Lerp(distanceBack, distanceBackPortrait, portrait);
            float h = Mathf.Lerp(height, heightPortrait, portrait);
            float baseFov = Mathf.Lerp(fovLandscape, fovPortrait, portrait);
            float pitch = Mathf.Lerp(pitchDown, pitchDownPortrait, portrait);

            // Opening crane / finale framing (both 0 during gameplay and captures).
            float wi = IntroWeight, wf = FinaleWeight;
            if (wi > 0f || wf > 0f)
            {
                float push = finaleTime > finaleBlendTime ? finalePushIn * SmootherStep((finaleTime - finaleBlendTime) / Mathf.Max(0.1f, finalePushTime)) : 0f;
                back += wi * introExtraBack + wf * finaleExtraBack - push;
                h += wi * introExtraHeight + wf * finaleExtraHeight;
                pitch += wi * introExtraPitch - wf * finalePitchUp;
                baseFov += wf * finaleFovDelta;
            }

            float d = runner.Distance;
            TrackFrame fc = EvaluateExtended(track, d - back);
            TrackFrame fr = runner.Frame;
            TrackFrame fl = track.Evaluate(d + lookAhead);

            // Along-track distance follows exactly (no lag at speed); only lateral and height offsets are smoothed.
            float targetLat = runner.Lateral * Mathf.Lerp(lateralFollow, lateralFollowPortrait, portrait);
            float targetH = h + runner.Height * jumpFollow;
            if (snap) { smLat = targetLat; smH = targetH; latV = hV = 0f; }
            else
            {
                smLat = Mathf.SmoothDamp(smLat, targetLat, ref latV, 0.12f, Mathf.Infinity, dt);
                smH = Mathf.SmoothDamp(smH, targetH, ref hV, 0.15f, Mathf.Infinity, dt);
            }
            Vector3 desiredPos = fc.position + fc.flatRight * smLat + fc.flatUp * smH;
            desiredPos -= Vector3.up * ((fc.position.y - fr.position.y) * slopeCompensation);
            Vector3 aheadPoint = fl.position + fl.flatRight * (runner.Lateral * 0.3f) + fl.flatUp * (h + runner.Height * jumpFollow);
            aheadPoint += Vector3.up * ((fr.position.y - fl.position.y) * lookSlopeCompensation);
            Vector3 runnerPoint = runner.transform.position + fr.flatUp * 0.45f;
            Vector3 desiredLook = Vector3.Lerp(aheadPoint, runnerPoint, lookAtRunnerWeight);

            if (snap)
            {
                transform.position = desiredPos;
                smoothedLook = desiredLook;
                posVel = lookVel = Vector3.zero;
            }
            else
            {
                transform.position = desiredPos;
                smoothedLook = Vector3.SmoothDamp(smoothedLook, desiredLook, ref lookVel, lookSmoothTime, Mathf.Infinity, dt);
            }

            Vector3 dir = smoothedLook - transform.position;
            if (dir.sqrMagnitude > 1e-4f) transform.rotation = Quaternion.LookRotation(dir, fc.flatUp) * Quaternion.Euler(pitch, 0f, 0f);

            // Bank with the slide (a fraction of its roll) so curves read clearly without making players dizzy.
            float targetDutch = Mathf.Clamp(-fr.roll * bankFactor, -maxDutch, maxDutch);
            float targetFov = baseFov + (runner.Boosting ? boostFovKick : 0f);
            if (snap) { dutch = targetDutch; fov = targetFov; }
            else
            {
                dutch = Mathf.SmoothDamp(dutch, targetDutch, ref dutchVel, dutchSmoothTime, Mathf.Infinity, dt);
                fov = Mathf.SmoothDamp(fov, targetFov, ref fovVel, 0.35f, Mathf.Infinity, dt);
            }
            if (vcam != null)
            {
                vcam.Lens.FieldOfView = fov;
                vcam.Lens.Dutch = dutch;
            }
        }
    }
}
