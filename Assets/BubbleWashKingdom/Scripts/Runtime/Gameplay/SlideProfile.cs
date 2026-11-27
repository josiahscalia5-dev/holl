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
        // lead 2026-11-27 10:40 corridor (owner S2 priority 1): ~0.78x narrower slide with thick rounded rails, measured on the
        // reference 3.00 s frame (its rails fill both bottom corners). Old values: lanes 1.15, flat 1.25, curve 0.9, top 2.10,
        // rail 2.22 / 0.72 / 0.16.
        public const float LaneWidth = 0.90f;

        /// <summary>Flat floor for |x| &lt;= FlatHalfWidth (build_track.py FLAT).</summary>
        public const float FlatHalfWidth = 0.95f;

        /// <summary>Inner wall height z = WallCurve * (|x| - FlatHalfWidth)^2 (build_track.py K).</summary>
        public const float WallCurve = 1.3f;

        /// <summary>Wall top |x|, buried inside the rail tube (build_track.py X_TOP).</summary>
        public const float WallTopX = 1.64f;

        /// <summary>Rail tube centre |x| and height, and tube radius (build_track.py RAIL_X / RAIL_Z / RAIL_R).</summary>
        public const float RailX = 1.86f, RailZ = 0.80f, RailR = 0.30f;

        /// <summary>Foam beside the rails keeps its old clearance from the tube's outer surface and its old height above the
        /// tube top (the foam offsets were tuned for the 0.16 m tube whose top was at 0.88 m).</summary>
        public const float FoamLateralBase = RailX + (RailR - 0.16f), FoamHeightLift = RailZ + RailR - 0.88f;
    }
}
