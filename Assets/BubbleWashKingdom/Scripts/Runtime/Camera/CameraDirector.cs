using Unity.Cinemachine;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Switches between the three cameras. Front-facing shots are used ONLY for the opening (mascot waiting,
    /// not moving) and the celebration; normal gameplay always uses the rear <see cref="RunnerCameraRig"/>.
    /// Cinemachine's brain blends between them (no hard cuts).
    /// </summary>
    [DefaultExecutionOrder(110)]
    public class CameraDirector : MonoBehaviour
    {
        public enum Shot { Intro, Gameplay, Celebrate }

        public RunnerController runner;
        public CinemachineCamera introCam;
        public CinemachineCamera gameplayCam;
        public CinemachineCamera celebrateCam;

        [Header("Intro orbit (front-facing, mascot stationary)")]
        public float introDistance = 2.6f;
        public float introHeight = 0.95f;
        public float introStartAngle = 25f;
        public float introOrbitSpeed = 9f;

        [Header("Celebration (front-facing)")]
        public float celebrateDistance = 3.0f;
        public float celebrateHeight = 1.2f;
        public float celebrateOrbitSpeed = 14f;

        public Shot Current { get; private set; } = Shot.Intro;
        float shotTime;

        public void Show(Shot shot)
        {
            Current = shot;
            shotTime = 0f;
            if (introCam) introCam.gameObject.SetActive(shot == Shot.Intro);
            if (gameplayCam) gameplayCam.gameObject.SetActive(shot == Shot.Gameplay);
            if (celebrateCam) celebrateCam.gameObject.SetActive(shot == Shot.Celebrate);
            LateUpdate();
        }

        void LateUpdate()
        {
            if (runner == null) return;
            shotTime += Time.deltaTime;
            Transform r = runner.transform;
            Vector3 focus = r.position + r.up * 0.55f;
            if (Current == Shot.Intro && introCam)
            {
                float a = (introStartAngle + shotTime * introOrbitSpeed) * Mathf.Deg2Rad;
                Vector3 offset = (r.forward * Mathf.Cos(a) + r.right * Mathf.Sin(a)) * introDistance + r.up * introHeight;
                introCam.transform.position = r.position + offset;
                introCam.transform.rotation = Quaternion.LookRotation(focus - introCam.transform.position, r.up);
            }
            else if (Current == Shot.Celebrate && celebrateCam)
            {
                float a = (-30f + shotTime * celebrateOrbitSpeed) * Mathf.Deg2Rad;
                Vector3 offset = (r.forward * Mathf.Cos(a) + r.right * Mathf.Sin(a)) * celebrateDistance + r.up * celebrateHeight;
                celebrateCam.transform.position = r.position + offset;
                celebrateCam.transform.rotation = Quaternion.LookRotation(focus - celebrateCam.transform.position, r.up);
            }
        }
    }
}
