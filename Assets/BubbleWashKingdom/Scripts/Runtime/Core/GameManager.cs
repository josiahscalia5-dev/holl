using System.Collections;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Level flow: front-facing intro (mascot waiting) -> blend to the rear gameplay camera -> run -> celebration
    /// (front-facing) -> restart. Also applies mobile frame-rate settings and the optional autopilot.
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
            if (director) director.Show(CameraDirector.Shot.Intro);
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
            yield return new WaitForSeconds(0.8f);
            if (director) director.Show(CameraDirector.Shot.Celebrate);
            if (hud && items) hud.ShowComplete(true, items.Coins, items.Gems);
            yield return new WaitForSeconds(celebrationDuration);
            if (loopAfterCelebration && !CaptureMode)
            {
                runner.ResetRun();
                yield return RunIntro();
            }
        }
    }
}
