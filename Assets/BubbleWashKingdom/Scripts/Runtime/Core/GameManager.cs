using System.Collections;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Level flow: opening crane on the rear camera (mascot waiting in the hall) -> run -> the mascot brakes to a stop in
    /// front of the golden portal, turns to face the camera and celebrates (front-facing) -> soft fade -> restart.
    /// Also applies mobile frame-rate settings and the optional autopilot.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public RunnerController runner;
        public CameraDirector director;
        public HUDController hud;
        public TrackItemRegistry items;
        public AutopilotBrain autopilot;

        public float introDuration = 2.4f;
        public float blendToGameplay = 1.4f;
        public float celebrationDuration = 6f;
        public bool loopAfterCelebration = true;
        [Tooltip("Enabled by capture runs or the -bwkAutopilot command-line flag.")]
        public bool useAutopilot;

        public static bool CaptureMode;
        public bool RunStarted { get; private set; }
        public bool Celebrating { get; private set; }

        void Awake()
        {
            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount = 0;
            var args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "-bwkAutopilot") useAutopilot = true;
                if (args[i] == "-bwkPerf" && i + 1 < args.Length) { perfOutput = args[i + 1]; useAutopilot = true; }
            }
            if (autopilot != null) autopilot.enabled = useAutopilot || CaptureMode;
        }

        void OnEnable() { if (runner != null) runner.FinishedRun += OnFinished; }
        void OnDisable() { if (runner != null) runner.FinishedRun -= OnFinished; }

        IEnumerator Start()
        {
            yield return RunIntro();
        }

        IEnumerator RunIntro()
        {
            RunStarted = false;
            Celebrating = false;
            if (hud) { hud.ShowComplete(false, 0, 0); hud.ShowHint(true); }
            // Opening crane on the rear camera: settles into the frozen gameplay framing just before the run starts.
            if (director) director.Show(CameraDirector.Shot.Intro, introDuration + blendToGameplay * 0.8f);
            if (hud) hud.Fade(0f, 0.6f);
            yield return new WaitForSeconds(introDuration);
            if (director) director.Show(CameraDirector.Shot.Gameplay);
            yield return new WaitForSeconds(blendToGameplay);
            runner.Begin();
            RunStarted = true;
            yield return new WaitForSeconds(3f);
            if (hud) hud.ShowHint(false);
        }

        void OnFinished() { StartCoroutine(Celebrate()); }

        string perfOutput;

        IEnumerator Celebrate()
        {
            Celebrating = true;
            if (!string.IsNullOrEmpty(perfOutput) && PerfStats.Instance != null)
            {
                PerfStats.Instance.WriteSummary(perfOutput, "standalone-autopilot-run");
                Application.Quit();
            }
            // Continuous finish: the camera eases into the finale framing while the mascot brakes in front of the portal;
            // the banner appears once the mascot has turned to face the camera.
            if (director) director.Show(CameraDirector.Shot.Celebrate);
            float t = 0f;
            while (!runner.InCelebrationPose && t < 4f) { t += Time.deltaTime; yield return null; }
            if (hud && items) hud.ShowComplete(true, items.Coins, items.Gems);
            yield return new WaitForSeconds(celebrationDuration);
            if (loopAfterCelebration && !CaptureMode)
            {
                if (hud) hud.Fade(1f, 0.6f);
                yield return new WaitForSeconds(0.65f);
                runner.ResetRun();
                yield return RunIntro();
            }
        }
    }
}
