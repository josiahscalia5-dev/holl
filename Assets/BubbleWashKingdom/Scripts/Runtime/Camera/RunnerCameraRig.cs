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
        [Tooltip("Owner requirement: rear follow camera slightly above and behind; back of hat, pom-pom, arms and paws visible, route and tunnel visible ahead above the pom-pom.")]
        public float distanceBackPortrait = 2.55f;
        public float heightPortrait = 1.5f;
        public float fovPortrait = 58f;

        [Header("Aim")]
        public float lookAhead = 10f;
        [Tooltip("Downward pitch from the track direction (reference: about 8.5 degrees at 16:9).")]
        public float pitchDown = 9f;
        public float pitchDownPortrait = 10f;
        public float lookHeight = 0.6f;
        [Range(0f, 1f)] public float lookAtRunnerWeight = 0.08f;
        [Range(0f, 1f)] public float lateralFollow = 0.55f;
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

        Vector3 posVel, lookVel, smoothedLook;
        float smLat, smH, latV, hV;
        float dutch, dutchVel, fov, fovVel;
        bool initialized;
        Camera outputCamera;

        void OnEnable() { initialized = false; }

        void LateUpdate()
        {
            if (runner == null || runner.track == null) return;
            Step(Time.deltaTime, !initialized);
            initialized = true;
        }

        public void Snap()
        {
            if (runner == null || runner.track == null) return;
            Step(0f, true);
            initialized = true;
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

            float d = runner.Distance;
            TrackFrame fc = track.Evaluate(d - back);
            TrackFrame fr = runner.Frame;
            TrackFrame fl = track.Evaluate(d + lookAhead);

            // Along-track distance follows exactly (no lag at speed); only lateral and height offsets are smoothed.
            float targetLat = runner.Lateral * lateralFollow;
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
            if (dir.sqrMagnitude > 1e-4f) transform.rotation = Quaternion.LookRotation(dir, fc.flatUp) * Quaternion.Euler(Mathf.Lerp(pitchDown, pitchDownPortrait, portrait), 0f, 0f);

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
