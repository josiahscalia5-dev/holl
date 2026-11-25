using System.Collections.Generic;
using System.IO;
using System.Text;
using Unity.Profiling;
using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Runtime performance sampler (Unity Profiler counters via ProfilerRecorder): frame time / FPS, main-thread time,
    /// draw calls, batches, SetPass calls, triangles, vertices and memory. Writes a JSON summary for test reports.
    /// Press F1 (or tap with 4 fingers) to toggle the on-screen readout.
    /// </summary>
    public class PerfStats : MonoBehaviour
    {
        public bool showOverlay;
        public float warmupSeconds = 2f;

        ProfilerRecorder mainThread, drawCalls, batches, setPass, tris, verts, totalMem, gcMem;
        readonly List<float> frameMs = new List<float>(8192);
        float startTime;
        GUIStyle style;

        public static PerfStats Instance { get; private set; }

        void OnEnable()
        {
            Instance = this;
            mainThread = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 15);
            drawCalls = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count");
            batches = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count");
            setPass = ProfilerRecorder.StartNew(ProfilerCategory.Render, "SetPass Calls Count");
            tris = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count");
            verts = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Vertices Count");
            totalMem = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "Total Used Memory");
            gcMem = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Used Memory");
            startTime = Time.realtimeSinceStartup;
            frameMs.Clear();
        }

        void OnDisable()
        {
            mainThread.Dispose(); drawCalls.Dispose(); batches.Dispose(); setPass.Dispose();
            tris.Dispose(); verts.Dispose(); totalMem.Dispose(); gcMem.Dispose();
            if (Instance == this) Instance = null;
        }

        long maxDraw, maxBatches, maxSetPass, maxTris, maxVerts;

        void Update()
        {
            if (UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.f1Key.wasPressedThisFrame)
                showOverlay = !showOverlay;
            if (Time.realtimeSinceStartup - startTime < warmupSeconds) return;
            frameMs.Add(Time.unscaledDeltaTime * 1000f);
            maxDraw = System.Math.Max(maxDraw, drawCalls.LastValue);
            maxBatches = System.Math.Max(maxBatches, batches.LastValue);
            maxSetPass = System.Math.Max(maxSetPass, setPass.LastValue);
            maxTris = System.Math.Max(maxTris, tris.LastValue);
            maxVerts = System.Math.Max(maxVerts, verts.LastValue);
        }

        public string SummaryJson(string label)
        {
            var sorted = new List<float>(frameMs);
            sorted.Sort();
            float avg = 0f; foreach (var f in sorted) avg += f;
            avg = sorted.Count > 0 ? avg / sorted.Count : 0f;
            float P(float q) => sorted.Count == 0 ? 0f : sorted[Mathf.Clamp(Mathf.RoundToInt(q * (sorted.Count - 1)), 0, sorted.Count - 1)];
            var sb = new StringBuilder();
            sb.Append("{\n");
            sb.AppendFormat(System.Globalization.CultureInfo.InvariantCulture,
                "  \"label\": \"{0}\",\n  \"frames\": {1},\n  \"avg_ms\": {2:F2},\n  \"avg_fps\": {3:F1},\n  \"p50_ms\": {4:F2},\n  \"p95_ms\": {5:F2},\n  \"p99_ms\": {6:F2},\n  \"fps_1pct_low\": {7:F1},\n",
                label, sorted.Count, avg, avg > 0 ? 1000f / avg : 0f, P(0.5f), P(0.95f), P(0.99f), P(0.99f) > 0 ? 1000f / P(0.99f) : 0f);
            sb.AppendFormat("  \"main_thread_ms_last\": {0:F2},\n", mainThread.LastValue * 1e-6);
            sb.AppendFormat("  \"draw_calls_max\": {0},\n  \"batches_max\": {1},\n  \"setpass_max\": {2},\n  \"triangles_max\": {3},\n  \"vertices_max\": {4},\n",
                maxDraw, maxBatches, maxSetPass, maxTris, maxVerts);
            sb.AppendFormat("  \"total_used_memory_mb\": {0:F1},\n  \"gc_used_memory_mb\": {1:F1},\n", totalMem.LastValue / 1048576.0, gcMem.LastValue / 1048576.0);
            sb.AppendFormat("  \"screen\": \"{0}x{1}\",\n  \"device\": \"{2}\",\n  \"gpu\": \"{3}\",\n  \"platform\": \"{4}\"\n}}\n",
                Screen.width, Screen.height, SystemInfo.deviceModel, SystemInfo.graphicsDeviceName, Application.platform);
            return sb.ToString();
        }

        public void WriteSummary(string path, string label)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, SummaryJson(label));
        }

        void OnGUI()
        {
            if (!showOverlay) return;
            if (style == null) style = new GUIStyle(GUI.skin.label) { fontSize = 26, normal = { textColor = Color.white } };
            float ms = frameMs.Count > 0 ? frameMs[frameMs.Count - 1] : 0f;
            GUI.Label(new Rect(20, 20, 900, 200),
                $"{(ms > 0 ? 1000f / ms : 0):F0} fps  {ms:F1} ms\nDraw {drawCalls.LastValue}  Batches {batches.LastValue}  SetPass {setPass.LastValue}\nTris {tris.LastValue / 1000}k  Verts {verts.LastValue / 1000}k  Mem {totalMem.LastValue / 1048576}MB", style);
        }
    }
}
