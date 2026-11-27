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
        // lead 84b218d4 11:00 (s2p9): the 10:40 rails (top 1.10 m) rose above the camera eye line and hid the foam / tunnel; the
        // reference back-projected with the R2 camera puts the pink start at |x| ~1.45 on the floor and the rail tops ~0.55 m up.
        // -> flat 1.05, curve 0.9, top 1.75, rail 1.95 / 0.30 / 0.28 (top 0.58 m); lanes stay 0.90 (on the flat floor).
        public const float LaneWidth = 0.90f;

        /// <summary>Flat floor for |x| &lt;= FlatHalfWidth (build_track.py FLAT).</summary>
        public const float FlatHalfWidth = 1.05f;

        /// <summary>Inner wall height z = WallCurve * (|x| - FlatHalfWidth)^2 (build_track.py K).</summary>
        public const float WallCurve = 0.9f;

        /// <summary>Wall top |x|, buried inside the rail tube (build_track.py X_TOP).</summary>
        public const float WallTopX = 1.75f;

        /// <summary>Rail tube centre |x| and height, and tube radius (build_track.py RAIL_X / RAIL_Z / RAIL_R).</summary>
        public const float RailX = 1.95f, RailZ = 0.30f, RailR = 0.28f;

        /// <summary>Foam beside the rails keeps its old clearance from the tube's outer surface and its old height above the
        /// tube top (the foam offsets were tuned for the 0.16 m tube whose top was at 0.88 m).</summary>
        public const float FoamLateralBase = RailX + (RailR - 0.16f), FoamHeightLift = RailZ + RailR - 0.88f;
    }
}
