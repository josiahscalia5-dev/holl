namespace BubbleWash
{
    /// <summary>
    /// The water slide's cross-section contract, in ONE place (lead 72ca2928, 2026-11-27). Shared by the runner (lanes and
    /// the wall height it slides up in curves), the gameplay item lanes, the foam beside the rails, the capture lanes and the
    /// procedural fallback module. The Blender track module mirrors it: Tools/Blender/scripts/build_track.py FLAT, K, X_TOP,
    /// RAIL_R / RAIL_X / RAIL_Z. To change the corridor (owner S2 brief: narrower slide, broad rounded pink rails sweeping
    /// up from the bottom corners), change both files together, rebuild SM_Slide_Module, then the lead's full build + Play Mode
    /// (lane changes over all 3 lanes, jumps, landings, no mascot / rail clipping).
    /// </summary>
    public static class SlideProfile
    {
        /// <summary>Lane centres at -LaneWidth, 0 and +LaneWidth (metres from the slide centre).</summary>
        public const float LaneWidth = 1.15f;

        /// <summary>Flat floor for |x| &lt;= FlatHalfWidth (build_track.py FLAT).</summary>
        public const float FlatHalfWidth = 1.25f;

        /// <summary>Inner wall height z = WallCurve * (|x| - FlatHalfWidth)^2 (build_track.py K).</summary>
        public const float WallCurve = 0.9f;

        /// <summary>Wall top |x|, buried inside the rail tube (build_track.py X_TOP).</summary>
        public const float WallTopX = 2.10f;

        /// <summary>Rail tube centre |x| and height, and tube radius (build_track.py RAIL_X / RAIL_Z / RAIL_R).</summary>
        public const float RailX = 2.22f, RailZ = 0.72f, RailR = 0.16f;
    }
}
