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

            const int w = 540, h = 960;
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
            while (frames < 30 * 75)
            {
                yield return null;
                CaptureUtil.Render(cam, rt);
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
                if (gm.Celebrating && ++celebrateFrames > 120) break;
                frames++;
            }
#if UNITY_EDITOR
            encoder.Dispose();
#endif
            Time.captureFramerate = 0;
            File.WriteAllText(Path.Combine(OutDir, "run_summary.txt"),
                $"frames={frames}\nstart={startDistance:F1}\nend={runner.Distance:F1}\ntrack={runner.track.Length:F1}\n" +
                $"coins={gm.items.Coins}\ngems={gm.items.Gems}\nrearChecks={rearChecks}\nrearViolations={rearViolations}\nfinished={gm.Celebrating}\n");
            Assert.Greater(runner.Distance - startDistance, runner.track.Length * 0.8f, "mascot did not travel the section");
            Assert.AreEqual(0, rearViolations, "camera was not behind the mascot during gameplay");
            Assert.IsTrue(gm.Celebrating, "run did not reach the finish");
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
    }
}
