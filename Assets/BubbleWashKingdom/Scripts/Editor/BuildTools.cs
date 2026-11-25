using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Player builds. Windows development build is used for real frame-rate measurement on this PC
    /// (run: Builds/Windows/BubbleWashKingdom.exe -bwkPerf Captures/perf_standalone.json -screen-width 540 -screen-height 960).
    /// Android needs the Android Build Support module (not installed yet).
    /// </summary>
    public static class BuildTools
    {
        public const string WindowsExe = "Builds/Windows/BubbleWashKingdom.exe";

        [MenuItem("Bubble Wash/Build/Windows (development)")]
        public static void BuildWindowsDev() => Build(true);

        public static void BuildWindowsDevBatch()
        {
            bool ok = Build(true);
            EditorApplication.Exit(ok ? 0 : 1);
        }

        static bool Build(bool development)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(WindowsExe));
            var opts = new BuildPlayerOptions
            {
                scenes = new[] { SceneBuilder.ScenePath },
                locationPathName = WindowsExe,
                target = BuildTarget.StandaloneWindows64,
                options = development ? BuildOptions.Development : BuildOptions.None,
            };
            var report = BuildPipeline.BuildPlayer(opts);
            Debug.Log($"[BWK] Windows build: {report.summary.result}, {report.summary.totalSize / 1048576f:F1} MB, {report.summary.totalTime}");
            return report.summary.result == BuildResult.Succeeded;
        }
    }
}
