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
        // Motion E 2026-11-27: BWK_PLAY_OUT (optional) sends a specialist's run to its own folder so the lead's
        // Captures/playmode files are never overwritten; unset = unchanged.
        static string OutDir => Path.GetFullPath(Env("BWK_PLAY_OUT", Path.Combine(Application.dataPath, "..", "Captures", "playmode")));

        // Motion E 2026-11-27 pass 7 (owner 09:20 s8 / brief s19: "he must not fill half the frame", "the first ~3.5 s must not
        // make the mascot excessively large ... keep it consistent"): the mascot's on-screen box (his skinned geometry projected
        // through the gameplay camera, portrait 720x1280) is measured every 0.5 s and asserted.
        const float MaxBoxHeight = 0.42f, MinBoxHeight = 0.12f, MaxOpeningSizeRatio = 1.35f;

        /// <summary>Viewport box (x0, y0, x1, y1; y up) of every skinned mesh under <paramref name="root"/>, false if none is in front.</summary>
        static bool MascotScreenBox(Camera cam, Transform root, Mesh bake, out Vector4 box)
        {
            float x0 = float.MaxValue, y0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue;
            int n = 0;
            foreach (var smr in root.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                if (!smr.enabled || !smr.gameObject.activeInHierarchy) continue;
                smr.BakeMesh(bake, true);
                var m = Matrix4x4.TRS(smr.transform.position, smr.transform.rotation, Vector3.one);
                var vs = bake.vertices;
                for (int i = 0; i < vs.Length; i++)
                {
                    Vector3 p = cam.WorldToViewportPoint(m.MultiplyPoint3x4(vs[i]));
                    if (p.z < 0.05f) continue;
                    x0 = Mathf.Min(x0, p.x); x1 = Mathf.Max(x1, p.x); y0 = Mathf.Min(y0, p.y); y1 = Mathf.Max(y1, p.y); n++;
                }
            }
            box = new Vector4(Mathf.Clamp01(x0), Mathf.Clamp01(y0), Mathf.Clamp01(x1), Mathf.Clamp01(y1));
            return n > 0;
        }

        [UnityTest, Timeout(900000)]
        public IEnumerator A_RecordAutopilotRun()
        {
            Directory.CreateDirectory(OutDir);
            GameManager.CaptureMode = true;
            // Lead 5190fd9a 2026-11-27: portrait from the FIRST frame (the opening snap in GameManager.Start reads it), so the
            // recording no longer starts with one landscape-framed frame (mascot ~2x large) - see RunnerCameraRig.ForcedAspect.
            RunnerCameraRig.ForcedAspect = 720f / 1280f;
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
            // Lead cd16e551 2026-11-27 07:58: in batchmode the screen is NOT portrait, so Camera.main.aspect was landscape and
            // RunnerCameraRig used its LANDSCAPE framing (2.9 back / 1.6 up / pitch 9 / FOV 52) while the frames were rendered
            // 720x1280 - every recording (and the owner's review of them: "the mascot fills half the screen around 3 s") showed
            // the mascot about twice as large as a portrait phone does. Force the phone's portrait aspect on the camera and the rig.
            cam.aspect = (float)w / h;
            foreach (var r in Object.FindObjectsByType<RunnerCameraRig>(FindObjectsInactive.Include, FindObjectsSortMode.None)) r.aspectOverride = (float)w / h;
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
            // 2026-11-26 21:40 lead: the v4 FBX arrived with a 180 deg test yaw and the rear camera saw the mascot's FACE while
            // sliding (and its back in the celebration) although every other assert passed. While running, the eyes must sit
            // AHEAD of the body along the travel direction (the camera sees the back of the hat, the pom-pom and the soles).
            Transform eyeL = null;
            foreach (var t in runner.GetComponentsInChildren<Transform>(true)) if (t.name == "eye.L") { eyeL = t; break; }
            int faceChecks = 0, faceBackward = 0;
            // mascot on-screen size (motion E pass 7)
            var bake = new Mesh();
            var driver = runner.GetComponent<MascotAnimatorDriver>();
            var sizeCsv = new System.Text.StringBuilder("t,distance,state,boxH,boxW,top,bottom,left,right,camDist,fov,armHold,seatW,raiseL,foreL,raiseR,foreR,clearMin\n");
            int sizeSamples = 0, bigSamples = 0, smallSamples = 0;
            float gameMinH = float.MaxValue, gameMaxH = 0f, openMinH = float.MaxValue, openMaxH = 0f;
            // Motion E pass 9 (owner brief s18 / reference 01 + crop 23b): seated arms raised up-outward beside the brim
            int armSamples = 0, armSolved = 0;
            float armForeMin = float.MaxValue, armForeMax = float.MinValue, armClearMin = float.MaxValue;
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
                if (frames % 15 == 0 && mascotAnim != null && MascotScreenBox(cam, mascotAnim.transform, bake, out var box))
                {
                    float tv = frames / 30f, bh = box.w - box.y, bw = box.z - box.x;
                    bool play = gm.RunStarted && !gm.Celebrating && runner.State == RunnerState.Running && runner.Distance > startDistance + 4f;
                    sizeCsv.AppendLine(string.Format(System.Globalization.CultureInfo.InvariantCulture,
                        "{0:F2},{1:F1},{2},{3:F3},{4:F3},{5:F3},{6:F3},{7:F3},{8:F3},{9:F2},{10:F1},{11:F2}", tv, runner.Distance,
                        gm.Celebrating ? "finish" : play ? "play" : gm.RunStarted ? "start" : "intro", bh, bw, 1f - box.w, 1f - box.y,
                        box.x, box.z, Vector3.Distance(cam.transform.position, runner.visual != null ? runner.visual.position : runner.transform.position),
                        cam.fieldOfView, driver != null ? driver.ArmHoldWeight : -1f) + ArmCsv(driver));
                    if (play && driver != null && driver.ArmSolver != null && driver.SeatedArmsWeight > 0.5f)
                    {
                        var so = driver.ArmSolver;
                        armSamples++;
                        bool ok = true;
                        for (int k = 0; k < 2; k++)
                        {
                            if (float.IsNaN(so.LastElevation[k]) || so.LastClearance[k] < -1e-4f) { ok = false; continue; }
                            armForeMin = Mathf.Min(armForeMin, so.LastForearm[k]); armForeMax = Mathf.Max(armForeMax, so.LastForearm[k]);
                            armClearMin = Mathf.Min(armClearMin, so.LastClearance[k]);
                        }
                        if (ok) armSolved++;
                    }
                    if (play)
                    {
                        sizeSamples++;
                        gameMinH = Mathf.Min(gameMinH, bh); gameMaxH = Mathf.Max(gameMaxH, bh);
                        if (bh > MaxBoxHeight) bigSamples++;
                        if (bh < MinBoxHeight) smallSamples++;
                    }
                    if (tv >= 0.5f && tv <= 4.0f) { openMinH = Mathf.Min(openMinH, bh); openMaxH = Mathf.Max(openMaxH, bh); }
                    if (tv <= 5.01f) File.WriteAllBytes(Path.Combine(OutDir, $"open_{tv:00.0}s.png"), tex.EncodeToPNG());
                }
                if (gm.RunStarted && !gm.Celebrating && runner.State == RunnerState.Running && runner.Distance > startDistance + 4f)
                {
                    rearChecks++;
                    if (Vector3.Dot(cam.transform.forward, runner.transform.forward) < 0.35f) rearViolations++;
                    if (eyeL != null && runner.visual != null)
                    {
                        faceChecks++;
                        if (Vector3.Dot(eyeL.position - runner.visual.position, runner.transform.forward) < 0f) faceBackward++;
                    }
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
            RunnerCameraRig.ForcedAspect = 0f;
            File.WriteAllText(Path.Combine(OutDir, "run_summary.txt"),
                $"frames={frames}\nstart={startDistance:F1}\nend={runner.Distance:F1}\ntrack={runner.track.Length:F1}\n" +
                $"coins={gm.items.Coins}\ngems={gm.items.Gems}\nrearChecks={rearChecks}\nrearViolations={rearViolations}\nfinished={gm.Celebrating}\n" +
                $"celebrationPose={runner.InCelebrationPose}\nfinishRest={runner.FinishRestDistance:F1}\nmaxCameraPastPortal={maxCamPastPortal:F2}\n");
            runner.LaneChanged -= onLane; runner.Jumped -= onJump; runner.Landed -= onLand; runner.Bumped -= onBump;
            // celebration: the mascot has turned to the camera, so its eyes must now point toward the camera
            bool faceToCameraAtEnd = eyeL == null || runner.visual == null ||
                Vector3.Dot(eyeL.position - runner.visual.position, cam.transform.position - runner.visual.position) > 0f;
            File.AppendAllText(Path.Combine(OutDir, "run_summary.txt"),
                $"laneChanges={laneChanges}\nlanesVisited={minLane}..{maxLane}\njumps={jumps}\nlandings={landings}\nbumps={bumps}\n" +
                $"animatorStates={animStates.Count}\nfaceChecks={faceChecks}\nfaceBackward={faceBackward}\nfaceToCameraAtEnd={faceToCameraAtEnd}\n");
            File.WriteAllText(Path.Combine(OutDir, "mascot_size.csv"), sizeCsv.ToString());
            File.AppendAllText(Path.Combine(OutDir, "run_summary.txt"), string.Format(System.Globalization.CultureInfo.InvariantCulture,
                "sizeSamples={0}\nboxHeightPlay={1:F3}..{2:F3}\nboxHeightOpening0p5to4s={3:F3}..{4:F3} (ratio {5:F2})\nboxTooBig={6}\nboxTooSmall={7}\n",
                sizeSamples, gameMinH, gameMaxH, openMinH, openMaxH, openMinH > 0f ? openMaxH / openMinH : 0f, bigSamples, smallSamples));
            File.AppendAllText(Path.Combine(OutDir, "run_summary.txt"), string.Format(System.Globalization.CultureInfo.InvariantCulture,
                "seatedArmSamples={0}\nseatedArmSolved={1}\nseatedArmForearmDeg={2:F1}..{3:F1}\nseatedArmClearanceMin={4:F3}\n",
                armSamples, armSolved, armSamples > 0 ? armForeMin : 0f, armSamples > 0 ? armForeMax : 0f, armSamples > 0 ? armClearMin : 0f));
            Object.Destroy(bake);
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
            Assert.LessOrEqual(faceBackward, faceChecks / 20, "the mascot faced the rear camera instead of the travel direction");
            Assert.IsTrue(faceToCameraAtEnd, "the celebration did not turn the mascot's face toward the camera");
            // Motion E 2026-11-27 pass 7: on-screen size in portrait gameplay (owner s8 / s19).
            Assert.Greater(sizeSamples, 20, "the mascot's on-screen size was not measured during gameplay");
            Assert.AreEqual(0, bigSamples, $"the mascot filled too much of the portrait frame (box height > {MaxBoxHeight} in {bigSamples} samples, max {gameMaxH:F3})");
            Assert.AreEqual(0, smallSamples, $"the mascot was too small to read (box height < {MinBoxHeight} in {smallSamples} samples, min {gameMinH:F3})");
            Assert.LessOrEqual(openMaxH / Mathf.Max(1e-3f, openMinH), MaxOpeningSizeRatio,
                $"the opening changed the mascot's on-screen size too much (0.5-4 s box height {openMinH:F3}..{openMaxH:F3})");
            // Motion E 2026-11-27 pass 9: the seated up-outward arm pose is engaged in normal play and clears the hat.
            Assert.Greater(armSamples, 10, "the seated raised-arm pose never engaged during gameplay (solver missing or weight 0)");
            Assert.GreaterOrEqual(armSolved, armSamples * 9 / 10,
                $"the seated arms found no hat-clear raise in {armSamples - armSolved} of {armSamples} gameplay samples");
        }

        /// <summary>Motion E pass 9: seated-arm weight and last solve (deg / m) as extra mascot_size.csv columns.</summary>
        static string ArmCsv(MascotAnimatorDriver d)
        {
            if (d == null || d.ArmSolver == null) return ",-1,,,,,";
            var s = d.ArmSolver;
            return string.Format(System.Globalization.CultureInfo.InvariantCulture, ",{0:F2},{1:F1},{2:F1},{3:F1},{4:F1},{5:F3}",
                d.SeatedArmsWeight, s.LastElevation[0], s.LastForearm[0], s.LastElevation[1], s.LastForearm[1],
                Mathf.Min(s.LastClearance[0], s.LastClearance[1]));
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
            // Lead cd16e551 2026-11-27 07:58: in batchmode the screen is NOT portrait, so Camera.main.aspect was landscape and
            // RunnerCameraRig used its LANDSCAPE framing (2.9 back / 1.6 up / pitch 9 / FOV 52) while the frames were rendered
            // 720x1280 - every recording (and the owner's review of them: "the mascot fills half the screen around 3 s") showed
            // the mascot about twice as large as a portrait phone does. Force the phone's portrait aspect on the camera and the rig.
            cam.aspect = (float)w / h;
            foreach (var r in Object.FindObjectsByType<RunnerCameraRig>(FindObjectsInactive.Include, FindObjectsSortMode.None)) r.aspectOverride = (float)w / h;
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
