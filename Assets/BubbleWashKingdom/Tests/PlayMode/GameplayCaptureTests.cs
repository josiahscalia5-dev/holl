using System.Collections;
using System.IO;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
#if UNITY_EDITOR
using UnityEditor.Media;
#endif

namespace BubbleWash.Tests
{
    /// <summary>
    /// Plays the Level 01 section in Play Mode with the autopilot (it uses the same lane/jump API as swipes),
    /// records a portrait gameplay video + periodic stills, and checks: the run completes, the mascot moves forward,
    /// and during gameplay the camera always looks the same way the mascot faces (rear-facing camera).
    /// Also measures real-time frame rate in a second pass (editor numbers, not device numbers).
    /// </summary>
    public class GameplayCaptureTests
    {
        const string Scene = "Level01_RainbowRush";
        static string OutDir => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Captures", "playmode"));

        [UnityTest, Timeout(900000)]
        public IEnumerator A_RecordAutopilotRun()
        {
            Directory.CreateDirectory(OutDir);
            GameManager.CaptureMode = true;
            yield return SceneManager.LoadSceneAsync(Scene);
            yield return null;
            var gm = Object.FindFirstObjectByType<GameManager>();
            Assert.IsNotNull(gm, "GameManager missing");
            var runner = gm.runner;
            gm.autopilot.enabled = true;
            var cam = Camera.main;
            foreach (var canvas in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None))
            {
                canvas.renderMode = RenderMode.ScreenSpaceCamera; // so the HUD appears in captured frames
                canvas.worldCamera = cam;
                canvas.planeDistance = 0.5f;
            }

            const int w = 720, h = 1280;
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 2 };
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            Time.captureFramerate = 30;
#if UNITY_EDITOR
            var attrs = new VideoTrackAttributes
            {
                frameRate = new MediaRational(30), width = (uint)w, height = (uint)h, includeAlpha = false,
                bitRateMode = UnityEditor.VideoBitrateMode.High,
            };
            var encoder = new MediaEncoder(Path.Combine(OutDir, "gameplay_autopilot_9x16.mp4"), attrs);
#endif
            float startDistance = runner.Distance;
            int frames = 0, rearChecks = 0, rearViolations = 0, celebrateFrames = 0, stills = 0;
            // portal plane (LightPortal sits at track end - 12 m, facing along the track)
            var portalGo = GameObject.Find("LightPortal");
            Transform portal = portalGo != null ? portalGo.transform : runner.transform;
            float maxCamPastPortal = float.NegativeInfinity;
            // 2026-11-26 owner: verify the real controls in the recording - lane changes to both sides, jumps + landings,
            // and that the mascot's animator really cycles through several states (slide / swim, jump, land, celebrate)
            int laneChanges = 0, jumps = 0, landings = 0, bumps = 0, minLane = 0, maxLane = 0;
            System.Action onLane = () => { laneChanges++; minLane = Mathf.Min(minLane, runner.Lane); maxLane = Mathf.Max(maxLane, runner.Lane); };
            System.Action onJump = () => jumps++, onLand = () => landings++, onBump = () => bumps++;
            runner.LaneChanged += onLane; runner.Jumped += onJump; runner.Landed += onLand; runner.Bumped += onBump;
            var mascotAnim = runner.GetComponentInChildren<Animator>();
            var animStates = new System.Collections.Generic.HashSet<int>();
            while (frames < 30 * 75)
            {
                yield return null;
                CaptureUtil.RenderHdr(cam, rt);
                CaptureUtil.ReadBack(rt, tex);
#if UNITY_EDITOR
                encoder.AddFrame(tex);
#endif
                if (frames % 60 == 0 && stills < 40)
                    File.WriteAllBytes(Path.Combine(OutDir, $"play_{stills++:00}_d{runner.Distance:000}.png"), tex.EncodeToPNG());
                if (gm.RunStarted && !gm.Celebrating && runner.State == RunnerState.Running && runner.Distance > startDistance + 4f)
                {
                    rearChecks++;
                    if (Vector3.Dot(cam.transform.forward, runner.transform.forward) < 0.35f) rearViolations++;
                }
                if (mascotAnim != null && frames % 3 == 0) animStates.Add(mascotAnim.GetCurrentAnimatorStateInfo(0).shortNameHash);
                // 2026-11-26 finishing sequence: brake in front of the portal, turn, banner, slow push-in (~7 s recorded)
                if (gm.Celebrating && ++celebrateFrames > 210) break;
                maxCamPastPortal = Mathf.Max(maxCamPastPortal, Vector3.Dot(cam.transform.position - portal.position, portal.forward));
                frames++;
            }
#if UNITY_EDITOR
            encoder.Dispose();
#endif
            Time.captureFramerate = 0;
            File.WriteAllText(Path.Combine(OutDir, "run_summary.txt"),
                $"frames={frames}\nstart={startDistance:F1}\nend={runner.Distance:F1}\ntrack={runner.track.Length:F1}\n" +
                $"coins={gm.items.Coins}\ngems={gm.items.Gems}\nrearChecks={rearChecks}\nrearViolations={rearViolations}\nfinished={gm.Celebrating}\n" +
                $"celebrationPose={runner.InCelebrationPose}\nfinishRest={runner.FinishRestDistance:F1}\nmaxCameraPastPortal={maxCamPastPortal:F2}\n");
            runner.LaneChanged -= onLane; runner.Jumped -= onJump; runner.Landed -= onLand; runner.Bumped -= onBump;
            File.AppendAllText(Path.Combine(OutDir, "run_summary.txt"),
                $"laneChanges={laneChanges}\nlanesVisited={minLane}..{maxLane}\njumps={jumps}\nlandings={landings}\nbumps={bumps}\n" +
                $"animatorStates={animStates.Count}\n");
            Assert.Greater(runner.Distance - startDistance, runner.track.Length * 0.8f, "mascot did not travel the section");
            Assert.AreEqual(0, rearViolations, "camera was not behind the mascot during gameplay");
            Assert.IsTrue(gm.Celebrating, "run did not reach the finish");
            Assert.IsTrue(runner.InCelebrationPose, "finishing sequence did not reach the front-facing celebration pose");
            Assert.Less(maxCamPastPortal, -2f, "camera flew into / past the portal (empty space behind it)");
            Assert.GreaterOrEqual(laneChanges, 2, "no lane changes in the run");
            Assert.IsTrue(minLane < 0 && maxLane > 0, "the run did not use both the left and the right lane");
            Assert.GreaterOrEqual(jumps, 1, "the mascot never jumped");
            Assert.GreaterOrEqual(landings, 1, "the mascot never landed after a jump");
            Assert.GreaterOrEqual(animStates.Count, 3, "the mascot animator did not cycle through slide / jump / celebration states");
        }

        [UnityTest, Timeout(600000)]
        public IEnumerator B_MeasureEditorFrameRate()
        {
            Directory.CreateDirectory(OutDir);
            GameManager.CaptureMode = true;
            yield return SceneManager.LoadSceneAsync(Scene);
            yield return null;
            var gm = Object.FindFirstObjectByType<GameManager>();
            gm.autopilot.enabled = true;
            float t0 = Time.realtimeSinceStartup;
            while (!gm.Celebrating && Time.realtimeSinceStartup - t0 < 120f) yield return null;
            Assert.IsNotNull(PerfStats.Instance);
            PerfStats.Instance.WriteSummary(Path.Combine(OutDir, "perf_editor_playmode.json"), "editor-playmode-batch (not a device measurement)");
        }

        static string Env(string key, string fallback)
        {
            var v = System.Environment.GetEnvironmentVariable(key);
            return string.IsNullOrEmpty(v) ? fallback : v;
        }

        static float EnvF(string key, float fallback) =>
            float.TryParse(Env(key, ""), System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out var f) ? f : fallback;

        /// <summary>
        /// Real-time gameplay recording of one track segment in ANY scene (for example the round-6 test scene
        /// Assets/BubbleWashKingdom/Scenes/Test_S5_Shot0825.unity), which does not need to be in the build settings.
        /// Runs only when BWK_PLAY_SCENE is set (ignored otherwise, so the default test run is unchanged):
        ///   BWK_PLAY_SCENE=<scene path>  BWK_PLAY_START=190  BWK_PLAY_END=250  BWK_PLAY_NAME=s5_shot0825
        /// The intro plays normally, then the runner is placed at START and the autopilot plays to END under the frozen
        /// rear gameplay camera. Output: Captures/playmode/<name>_9x16.mp4, stills every 0.5 s, <name>_summary.txt.
        /// </summary>
        [UnityTest, Timeout(900000)]
        public IEnumerator C_RecordSegmentFromEnv()
        {
            string scenePath = Env("BWK_PLAY_SCENE", "");
            if (scenePath.Length == 0)
            {
                Assert.Ignore("segment recording runs only with BWK_PLAY_SCENE set");
                yield break;
            }
            float start = EnvF("BWK_PLAY_START", 190f), end = EnvF("BWK_PLAY_END", 250f);
            string name = Env("BWK_PLAY_NAME", "segment");
            Directory.CreateDirectory(OutDir);
            GameManager.CaptureMode = true;
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                scenePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            yield return null;
            var gm = Object.FindFirstObjectByType<GameManager>();
            Assert.IsNotNull(gm, "GameManager missing in " + scenePath);
            var runner = gm.runner;
            gm.autopilot.enabled = true;
            float t0 = Time.realtimeSinceStartup;
            while (!gm.RunStarted && Time.realtimeSinceStartup - t0 < 60f) yield return null;
            Assert.IsTrue(gm.RunStarted, "intro did not hand over to gameplay");
            runner.TeleportTo(start);
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>();
            if (rig) rig.Snap();
            yield return null;
            if (rig) rig.Snap();

            var cam = Camera.main;
            foreach (var canvas in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None))
            {
                canvas.renderMode = RenderMode.ScreenSpaceCamera;
                canvas.worldCamera = cam;
                canvas.planeDistance = 0.5f;
            }
            const int w = 720, h = 1280;
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 2 };
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            Time.captureFramerate = 30;
#if UNITY_EDITOR
            var attrs = new VideoTrackAttributes
            {
                frameRate = new MediaRational(30), width = (uint)w, height = (uint)h, includeAlpha = false,
                bitRateMode = UnityEditor.VideoBitrateMode.High,
            };
            var encoder = new MediaEncoder(Path.Combine(OutDir, name + "_9x16.mp4"), attrs);
#endif
            float d0 = runner.Distance;
            int frames = 0, stills = 0, rearChecks = 0, rearViolations = 0;
            float realStart = Time.realtimeSinceStartup;
            while (runner.Distance < end && !gm.Celebrating && frames < 30 * 30)
            {
                yield return null;
                CaptureUtil.RenderHdr(cam, rt);
                CaptureUtil.ReadBack(rt, tex);
#if UNITY_EDITOR
                encoder.AddFrame(tex);
#endif
                if (frames % 15 == 0 && stills < 60)
                    File.WriteAllBytes(Path.Combine(OutDir, $"{name}_{stills++:00}_d{runner.Distance:000}.png"), tex.EncodeToPNG());
                if (runner.State == RunnerState.Running)
                {
                    rearChecks++;
                    if (Vector3.Dot(cam.transform.forward, runner.transform.forward) < 0.35f) rearViolations++;
                }
                frames++;
            }
#if UNITY_EDITOR
            encoder.Dispose();
#endif
            Time.captureFramerate = 0;
            float realSeconds = Time.realtimeSinceStartup - realStart;
            File.WriteAllText(Path.Combine(OutDir, name + "_summary.txt"),
                $"scene={scenePath}\nframes={frames}\nvideoSeconds={frames / 30f:F2}\nstart={d0:F1}\nend={runner.Distance:F1}\n" +
                $"coins={gm.items.Coins}\ngems={gm.items.Gems}\nrearChecks={rearChecks}\nrearViolations={rearViolations}\n" +
                $"editorRenderFps={(realSeconds > 0f ? frames / realSeconds : 0f):F1} (editor batch, not a device measurement)\n");
            Assert.Greater(runner.Distance, start + (end - start) * 0.8f, "mascot did not travel the segment");
            Assert.AreEqual(0, rearViolations, "camera was not behind the mascot during gameplay");
        }
    }
}
