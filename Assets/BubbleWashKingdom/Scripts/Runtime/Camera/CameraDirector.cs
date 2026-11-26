using Unity.Cinemachine;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Drives the three level shots. Owner review 2026-11-26 of the round-7 recording: the old front-facing intro orbit got
    /// too close to the mascot and its hat (and its blend to the rear camera passed through the hat), and the old
    /// celebration orbit flew past the portal into empty space. All three shots now use the ONE rear gameplay camera
    /// (<see cref="RunnerCameraRig"/>), so there is never a blend through the mascot or a jump in perspective:
    ///  - Intro: an opening crane that starts behind / above and eases into the frozen gameplay framing while the mascot waits.
    ///  - Gameplay: the frozen rear framing (2.75 back / 1.3 up / pitch 10 / FOV 58 portrait).
    ///  - Celebrate: the mascot stops in front of the golden portal and turns to face the camera (front-facing celebration,
    ///    reference 14.5 s composition) while the camera eases back a little so the portal frames it.
    /// The old intro / celebrate CinemachineCameras stay in the scene (serialized references) but are no longer used.
    /// </summary>
    [DefaultExecutionOrder(110)]
    public class CameraDirector : MonoBehaviour
    {
        public enum Shot { Intro, Gameplay, Celebrate }

        public RunnerController runner;
        public CinemachineCamera introCam;
        public CinemachineCamera gameplayCam;
        public CinemachineCamera celebrateCam;

        public Shot Current { get; private set; } = Shot.Intro;
        RunnerCameraRig rig;

        void Awake()
        {
            // Only the rear gameplay camera is ever live, from the very first frame (no Cinemachine blend at start-up).
            if (introCam) introCam.gameObject.SetActive(false);
            if (celebrateCam) celebrateCam.gameObject.SetActive(false);
            if (gameplayCam) gameplayCam.gameObject.SetActive(true);
            rig = gameplayCam ? gameplayCam.GetComponent<RunnerCameraRig>() : null;
        }

        /// <summary>Switches the shot. <paramref name="duration"/> is the opening crane's length (Intro only).</summary>
        public void Show(Shot shot, float duration = 2.4f)
        {
            Current = shot;
            if (gameplayCam && !gameplayCam.gameObject.activeSelf) gameplayCam.gameObject.SetActive(true);
            if (rig == null && gameplayCam) rig = gameplayCam.GetComponent<RunnerCameraRig>();
            if (rig == null) return;
            switch (shot)
            {
                case Shot.Intro: rig.PlayIntro(duration); break;
                case Shot.Gameplay: rig.SetFinale(false); break;
                case Shot.Celebrate: rig.SetFinale(true); break;
            }
        }
    }
}
