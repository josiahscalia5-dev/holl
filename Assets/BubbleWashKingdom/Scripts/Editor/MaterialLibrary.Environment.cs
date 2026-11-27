using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: Agent 3 - 3D environment & machinery (drum walls, glass pipes, pipe water, chambers, rollers, machinery, laundry, portal rays).
    // Only this domain's agent edits this file. Helpers (Mat, Lit_, Gold, Emissive, Soft, Particle, C, F, Get) live in MaterialLibrary.cs.
    public static partial class MaterialLibrary
    {
        static void EnvironmentMaterials()
        {
            Mat("M_DrumWall", "BWK/DrumWall", m =>
            {
                // Round 3 (reference f_003.00s measured on the ceiling + owner sheet 04): muted silver-lavender metal (the
                // violet comes from the light, not a saturated albedo), steel-blue / periwinkle ceiling bays, deep indigo
                // toward the middle of each bay, pink light spilling from the rims, bevelled panel seams, and ROWS OF
                // SMALL ROUNDED OVAL HOLES (~0.36 x 0.25 m, 0.62 m apart around, rows ~1 m apart) with real depth.
                // Sections: gold ring - bay - one lavender rim at _RimPhase (0.40) - bay - gold ring; _BandOffset /
                // _BandLength / _RimPhase are rewritten by SceneBuilder.BuildRings (gold every 12.75 m from 71.5 m).
                // Round 4 (reference 4K f_03.00s): ceiling panels (within 45 deg of the top) carry short rounded dashes in
                // broken rows; the side walls carry big rounded ovals stacked in columns (3 per 3.3 m panel, rows 1.6 m
                // apart); the zone edge is a panel seam with plain metal beside it. Less saturated, pinker mauve side walls
                // (ref #7652a8 vs ours #5d36b5), weaker blue depth tint, purple-grey holes, pale steel-blue bay sheen.
                // r7 shared look: deeper, richer metallic blue-purple (ref wall V 0.63-0.71 vs ours 0.77-0.84; lit upper wall mauve
                // ~#a87ea0, deep violet in shadow) and bigger dark oval perforations
                // r8 (lighting, owner sheet 02 item 2 "deeper blue-violet metal, dark perforations"): measured on the same
                // crops (reference vs r7w stills, blue-purple wall pixels) S2-S7 reference S .37-.48 / V .49-.66 vs ours
                // S .55-.68 / V .66-.76, dark perforation pixels (V < .22) 1.6-5.7 % vs 0.0 %. -> greyer, deeper blue-violet
                // base (the violet comes from the light), less ceiling blue, less self glow / pink spill, near-black hole
                // interiors with a stronger dark halo, a little more metallic sheen from the (now box-projected) probes.
                C(m, "_BaseColor", "#846E9E"); C(m, "_HighlightColor", "#AA98C6"); C(m, "_HoleColor", "#06030E");
                C(m, "_HoleGlow", "#24163E"); F(m, "_Circumference", 26.39f); F(m, "_VTile", 4f);
                C(m, "_CeilingColor", "#4A5886"); F(m, "_CeilingTint", 0.7f); F(m, "_CeilingWidth", 0.55f);
                F(m, "_Pattern", 1f); F(m, "_BandLength", 12.75f); F(m, "_BandOffset", 71.5f); F(m, "_RimPhase", 0.40f);
                F(m, "_PlainBack", 0.85f); F(m, "_PlainFront", 0.75f); F(m, "_Rows", 5f); F(m, "_RowPitch", 0.85f);
                F(m, "_SlotPitch", 0.58f); F(m, "_SlotLength", 0.40f); F(m, "_SlotWidth", 0.22f); F(m, "_SlotVariation", 0.2f);
                F(m, "_SideZone", 0.25f); F(m, "_SideSlotPitch", 1.1f); F(m, "_SideSlotLength", 0.64f); F(m, "_SideSlotWidth", 0.48f);
                F(m, "_SideRowPitch", 1.6f); F(m, "_SeamMargin", 0.06f); F(m, "_SlotDropout", 0.18f);
                F(m, "_LipWidth", 0.035f); F(m, "_Bevel", 0.8f); F(m, "_GlowChance", 0.03f); F(m, "_HoleDepth", 0.10f);
                F(m, "_InnerWall", 0.2f);
                m.SetColor("_GlowColorA", new Color(1.7f, 0.85f, 1.6f)); m.SetColor("_GlowColorB", new Color(0.75f, 1.35f, 1.9f));
                C(m, "_SeamColor", "#20144A"); C(m, "_SheenColor", "#F0B0F0"); F(m, "_SheenStrength", 0.06f);
                F(m, "_Sparkle", 0.25f); F(m, "_CeilingLight", 0.02f); F(m, "_Glow", 0.035f);
                F(m, "_Metallic", 0.58f); F(m, "_Smoothness", 0.58f); F(m, "_HoleBand", 1f);
                F(m, "_EdgeAO", 0.4f); F(m, "_EdgeAOWidth", 0.5f); F(m, "_HoleAO", 0.62f); F(m, "_HoleAOWidth", 0.08f);
                C(m, "_ShadowColor", "#3A3A7E"); F(m, "_ShadowTint", 0.4f);
                C(m, "_DepthTintColor", "#4E5A8C"); F(m, "_DepthTint", 0.45f); F(m, "_DepthTintStart", 14f); F(m, "_DepthTintEnd", 26f);
                C(m, "_PinkSpill", "#FF6ED2"); F(m, "_PinkSpillStrength", 0.36f); F(m, "_PinkSpillWidth", 0.75f);
                F(m, "_SeamHighlight", 0.5f); F(m, "_FlangeWidth", 0.2f); C(m, "_FlangeColor", "#8C74C8");
                C(m, "_BaySheenColor", "#86A8E6"); F(m, "_BaySheen", 0.12f); F(m, "_BaySheenWidth", 0.25f); F(m, "_BaySheenPos", 0.6f);
                // r8 v2 (lighting, owner library 07 "muted grey-lavender / blue-violet brushed metal, black recessed holes"):
                // the v1 albedo change was invisible in gameplay because the violet LIGHT makes the saturation (hero wall
                // S .65 vs ref .48). Grade the lit metal in the shader: 35 % toward a value-preserving grey-lavender (linear
                // tint .88/.50/1 solved so a typical wall pixel #54399f lands on the reference's H 263 / S .48 / V .64) and
                // darken the lit recesses to 30 % (navy holes -> near black before the fog)
                // masters wave (metal, 18:12): a bluer _LitTint was tried twice (r8m p1 H 271, p2 H 255 + desat .6): hero
                // walls_upper_right only #98769e -> #907197 (ref #8067ac, the mauve comes from the LIGHTS), palette distance
                // 23.4 -> 23.9 (worse) -> reverted to the checkpoint-20 values; the wall needs a light / probe method next wave
                F(m, "_LitDesat", 0.5f); m.SetColor("_LitTint", new Color(0.945f, 0.727f, 1.0f)); F(m, "_HoleDarken", 0.3f);   // p2 .35 -> p3 .5
                // S2 pass 1 (lead gap #2, 4K f_03.00s right wall): the side walls carry DENSE columns of SMALL vertical ovals
                // (720p ~8 x 17 px, ~21 px apart around, columns ~30 px apart) - ours were 45 x 75 px ovals 150 px apart
                // (1.1 m pitch). ~2.7x denser around and along, ~1/9 the hole area; thinner dark halos and lips so the
                // small holes read as crisp recesses with lit rims on a lighter metal (not big dark blotches)
                F(m, "_SideSlotPitch", 0.41f); F(m, "_SideSlotLength", 0.24f); F(m, "_SideSlotWidth", 0.14f); F(m, "_SideRowPitch", 0.6f);
                F(m, "_SlotPitch", 0.41f); F(m, "_SlotLength", 0.30f); F(m, "_SlotWidth", 0.14f); F(m, "_RowPitch", 0.62f);
                F(m, "_HoleAO", 0.35f); F(m, "_HoleAOWidth", 0.03f); F(m, "_LipWidth", 0.018f);
                // v2: lighter, greyer lilac metal (wall-hue pixels upper right ref #7758aa V .67 vs ours #68488e V .56; top band
                // ref V .67 vs ours .56-.65): albedo only (no exposure / light change), hue kept blue-violet
                C(m, "_BaseColor", "#9886B6"); C(m, "_HighlightColor", "#B8AAD6");
                m.SetColor("_LitTint", new Color(0.91f, 0.745f, 1.0f));   // v3: a little bluer (upper-right wall hue 271 vs reference 263)
                // S2 pass 3 (owner directive 1 + judge gap #1: the pass-1 dense small slots read as a SPEAKER GRILLE). Measured
                // on 4K f_03.00s inside the hatch through the R2 door camera (wall 8-11 m away): sparse COLUMNS of big dark
                // ovals, 720p ~15-17 x 22-30 px (long ones ~13 x 50), ~36 px apart in a column, columns ~49 px apart
                // -> world ~0.33 m along x 0.30-0.46 m around, 0.48-0.6 m around pitch, columns ~1.1 m apart along the drum.
                // Same metres everywhere, so the far sections show them smaller (perspective). Long / short ovals alternate
                // inside a column (per-slot length hash), soft dark recess halos, thin lit countersink lip, deeper parallax.
                F(m, "_SideSlotPitch", 0.60f); F(m, "_SideSlotLength", 0.46f); F(m, "_SideSlotWidth", 0.34f); F(m, "_SideRowPitch", 1.1f);
                F(m, "_SlotPitch", 0.58f); F(m, "_SlotLength", 0.40f); F(m, "_SlotWidth", 0.26f); F(m, "_RowPitch", 0.95f);
                F(m, "_SlotVariation", 0.38f); F(m, "_SlotVarPerSlot", 1f); F(m, "_SlotDropout", 0.12f);
                F(m, "_HoleAO", 0.55f); F(m, "_HoleAOWidth", 0.07f); F(m, "_LipWidth", 0.03f); F(m, "_HoleDepth", 0.16f); F(m, "_InnerWall", 0.16f);
                // owner directive 1 "realistic blue-violet + lavender metallic sheen, soft specular bands, curved panel seams":
                // curved pressed panels (normal +-14 deg across each panel) and a little more polish so the key light and
                // the box-projected probes draw soft lavender bands per panel (judge gap #2: wall reads flat purple)
                F(m, "_PanelCurve", 0.25f); F(m, "_Smoothness", 0.66f); F(m, "_Metallic", 0.64f);
                // Screen ALL pass 5 (lighting owns the drum wall now; judge gap #5): measured wall crops under the approved grade,
                // Lab ref vs ours: R3 (34.6, 25.6, -34.2) vs (53.5, 19.9, -15.0), R4 (44.6, 15.8, -15.1) vs (64.4, 17.8, -2.9),
                // R5 (38.9, 15.7, -26.6) vs (64.3, 14.7, 1.4) = ours ~20 L lighter and far less blue. Beyond the S2 door drum
                // (graded from 68 m, full at 92 m) the lit metal goes darker slate blue-violet, the recesses blacker, the pink
                // spill weaker, plus a thin cool light line along every flange edge (reference: glowing panel edges).
                F(m, "_DeepAmount", 1f); F(m, "_DeepStart", 68f); F(m, "_DeepEnd", 92f);
                m.SetColor("_DeepTint", new Color(0.66f, 0.67f, 0.82f)); F(m, "_DeepHole", 0.45f); F(m, "_DeepEmit", 0.6f);   // sRGB -> linear x(.39, .41, .64): luminance x.42, bluer
                m.SetColor("_DeepEdgeGlow", new Color(0.30f, 0.40f, 0.70f));   // v4: v3 (.45, .6, 1) drew bright blue ring lines (finale portal, 07)
                // Screen S2 pass 7 (owner 06:58 s6 + judge gap #10 "paler lilac with small dots, speaker grille"): the S2 door
                // drum (40 m) fading out by 112 m (S3+ unchanged). R2 wall patches, Lab ours vs reference f_03.00s: (44.0, 20.6,
                // -25.2) vs (49.0, 37.0, -42.4), (47.4, 26.4, -26.9) vs (47.7, 21.4, -39.0), ceiling (45.5, 22.1, -29.5) vs
                // (43.1, 19.2, -43.8); L p10-p90 spread 13 vs 24-28 -> keep the light's blue-violet (desat .5 -> .12), polished
                // metal (smoothness .66 -> .82: probe reflections of the rings / rims), near-black recesses, and bigger, sparser
                // oval columns in the door drum with finer slots deeper inside (reference: 2-3 columns of big dark ovals
                // right inside the hatch, thin slot rings in the far sections)
                F(m, "_DoorAmount", 1f); F(m, "_DoorFadeStart", 78f); F(m, "_DoorFadeEnd", 112f);
                // v2: v1 (tint .86/.88/1, holes .42) had the reference hue but ~10 L too dark and flat (patches L 38 / 37.5 vs
                // 49 / 47.7, p10-p90 11-15 vs 24-28): brighter lit metal (x1.5 linear ~ +8-10 L), holes kept near black
                // v3: v2 (x1.3 / 1.42) matched the contrast (p10-p90 26.7 / 25.4 vs ref 24-28) but lifted the ceiling to L 57.9
                // (ref 43.1) and its bloom washed the yellow stars cream-pink -> half way back, and the contrast from deeper
                // pressed panels instead (_DoorPanelCurve .25 -> .45: broader probe / key sheen band per panel)
                F(m, "_DoorDesat", 0.12f); m.SetColor("_DoorTint", new Color(1.08f, 1.08f, 1.18f)); F(m, "_DoorHole", 0.32f);
                F(m, "_DoorPanelCurve", 0.45f);
                F(m, "_DoorSmooth", 0.82f);
                F(m, "_DoorSlotNear", 1.15f); F(m, "_DoorSlotFar", 0.72f); F(m, "_DoorSlotStart", 54f); F(m, "_DoorSlotEnd", 70f);
                F(m, "_DoorRowSpread", 1.45f);
                // Screen S2 pass 9 (judge gap #2, R2 vs reference 01_Approved_S2: walls flat saturated blue-violet, local
                // contrast 0.8-1.8 vs 4.6-5.2; reference = polished metal with bright streaks running AROUND the drum, warm
                // gold pickup beside the rings, near-black ovals, luminous far end): the door drum mirrors the far end through
                // shallow lathe ribs (0.7 m, +-0.22 rad) -> circumferential sheen streaks strongest toward the vanishing point,
                // warm gold beside every rim, a soft far-end glow; rounder drum (panel facets .45 -> .22), greyer lit metal
                // (desat .12 -> .22), darker recesses (.32 -> .24)
                m.SetColor("_DoorSheenColor", new Color(0.36f, 0.30f, 0.56f)); F(m, "_DoorSheenPower", 28f);   // v4: v3 (.42/.36/.62, p22) read milky in the portrait gameplay frame -> tighter crests   // v2: v1 (.24/.20/.36, p7) lit the whole drum evenly (every wall is seen within ~25 deg of the axis) -> tight crests
                F(m, "_DoorRibPitch", 0.85f); F(m, "_DoorRibTilt", 0.30f);
                m.SetColor("_DoorWarmColor", new Color(0.22f, 0.12f, 0.03f)); F(m, "_DoorWarmWidth", 0.45f);
                m.SetColor("_FarGlowColor", new Color(0.13f, 0.12f, 0.24f));   // v3: v2 (.10/.08/.16 from 80 m) far end 158/126/178 vs ref 152/110/190 (bluer, brighter core)
                F(m, "_FarGlowNear", 35f); F(m, "_FarGlowFar", 70f); F(m, "_FarGlowEnd", 150f);
                F(m, "_DoorPanelCurve", 0.22f); F(m, "_DoorDesat", 0.16f); F(m, "_DoorHole", 0.24f);   // v4: desat .22 -> .16 (keep the violet)
                // Screen S2 pass 10 (judge gap #3 "flat grey-violet matte plastic; the approved drum glows violet / magenta / blue
                // with specular chrome highlights", wallR2 rgb 113/76/159 L p90 113 vs ref 134/98/180 p90 153): the door drum
                // MIRRORS the tunnel (reflected ray intersected with the drum cylinder): warm gold rings, pink-magenta LED rims,
                // turquoise water on the upper drum, the luminous far end, deep blue metal between; the old far-end-only sheen
                // drops to ~45 %, the lit metal a little bluer / darker so the reflections carry the value contrast
                m.SetColor("_MirrorGold", new Color(1.0f, 0.62f, 0.30f)); m.SetColor("_MirrorRim", new Color(1.0f, 0.42f, 0.88f));
                m.SetColor("_MirrorWall", new Color(0.10f, 0.10f, 0.30f)); m.SetColor("_MirrorFloor", new Color(0.25f, 0.62f, 0.85f));
                m.SetColor("_MirrorCore", new Color(0.30f, 0.27f, 0.62f)); F(m, "_MirrorF0", 0.55f);   // v2: v1 .42/.38/.80 milky far end
                // far end: ours 172/135/173 (bg) vs ref 154/111/192 - bluer / darker deep drum, the flat far glow halves
                m.SetColor("_FarGlowColor", new Color(0.05f, 0.05f, 0.12f));   // v2: v1 .07/.065/.15
                F(m, "_MirrorRingA", 50.5f); F(m, "_MirrorRingB", 61.7f); F(m, "_MirrorRingWidth", 0.45f);
                F(m, "_MirrorCoreStart", 25f); F(m, "_MirrorCoreEnd", 80f);
                m.SetColor("_DoorSheenColor", new Color(0.16f, 0.13f, 0.26f));
                // v2: v1 (.92/.90/1.10) + rib-normal mirror = speckled streaks, wallR2 p50 96 vs ref 106 -> lighter near
                // lavender metal, the deep drum (camera 14-30 m+) deep blue (ref: indigo between the rings, pale only near)
                m.SetColor("_DoorTint", new Color(1.02f, 1.0f, 1.16f));
                m.SetColor("_MirrorWall", new Color(0.14f, 0.12f, 0.34f));
                m.SetColor("_DoorDeepTint", new Color(0.62f, 0.66f, 0.92f)); F(m, "_DoorDeepNear", 14f); F(m, "_DoorDeepFar", 30f);
                // crop 07: near ovals bigger and ~2:1 (ours 1.35:1)
                F(m, "_DoorSlotNear", 1.25f); F(m, "_DoorSlotAspect", 1.3f);
                // Screen S2 pass 10 v3 (lead 13:50 #1 defect: PALE lavender arc in the upper third of the portrait frame, s2p10
                // ceiling (170,90)-(640,250) L 148 / chroma 50 vs s2p9r 102 / 78, R2 ceiling L 169 vs reference 98 / chroma
                // 96; owner 13:25 (4) washed-out deep tunnel L 167 vs 121). Cause: v1/v2 mirror term - the ceiling mirrors the
                // FLOOR (cyan water .25/.62/.85) + a pale far core, added to violet = pale grey-lavender. METHOD CHANGE: the
                // lit door metal is gradient-mapped onto a neon-metal ramp (deep indigo -> saturated blue-violet -> lavender-
                // pink gloss below the bloom threshold; deeper drum darker), and the mirror keeps only the warm gold / pink
                // LED-rim reflections over deep blue (no cyan floor, no pale core)
                F(m, "_DoorRampAmount", 1f);
                m.SetColor("_DoorRampDark", new Color(0.13f, 0.10f, 0.36f));    // display ~ deep indigo between the rims
                m.SetColor("_DoorRampMid", new Color(0.46f, 0.34f, 0.80f));     // display ~ ref ceiling 110/86/178, wall 132/96/178
                m.SetColor("_DoorRampHigh", new Color(0.88f, 0.70f, 1.0f));     // glossy lavender-pink band (lum < .9 bloom threshold)
                F(m, "_DoorRampScale", 3.5f); F(m, "_DoorRampFar", 0.72f); F(m, "_DoorRampNear", 12f); F(m, "_DoorRampFarDist", 40f);
                m.SetColor("_MirrorFloor", new Color(0.05f, 0.05f, 0.20f));     // v2 .25/.62/.85 cyan = the pale ceiling
                m.SetColor("_MirrorWall", new Color(0.04f, 0.035f, 0.15f));
                m.SetColor("_MirrorCore", new Color(0.16f, 0.09f, 0.42f));      // v2 .30/.27/.62
                F(m, "_MirrorF0", 0.45f);
                // owner 13:25 (5) insufficient perforations: MANY rows of small dark pill slots per band (smaller deeper), big
                // ovals only on the near walls -> far slot scale .72 -> .5 (from the first gold ring), near rows no longer
                // spread (1.45 -> 1.0), fewer dropped dashes, blacker recesses
                F(m, "_DoorSlotFar", 0.5f); F(m, "_DoorSlotStart", 48f); F(m, "_DoorSlotEnd", 60f); F(m, "_DoorRowSpread", 1.0f);
                F(m, "_SlotDropout", 0.05f); F(m, "_DoorHole", 0.14f);
            });
            // polished lavender drum lips between the gold rings (SM_DrumRim, m1: fat rolled lip): the stylised BWK/Gold
            // environment shading with a lavender palette - violet body, magenta-pink fresnel edge, soft pink-lavender
            // studio streaks (reference: broad glossy lavender bands with pink-white glints; r3: less white, pinker highs)
            // r4: deeper violet body, pinker highlights (reference top rim band mean #7951b2 / bright #d892df vs ours
            // #aa77d9 / #e2bdec: ours read pale lavender)
            Mat("M_DrumRim", "BWK/Gold", m =>
            {
                C(m, "_HighColor", "#FFB8F0"); C(m, "_MidColor", "#7E52C8"); C(m, "_LowColor", "#34186E");
                C(m, "_RimColor", "#FF6AD6"); C(m, "_BandColor", "#E0A0F0");
                F(m, "_Brightness", 0.78f); F(m, "_Emission", 0.10f); F(m, "_Contrast", 1.5f); F(m, "_ViewGradient", 1f);
                F(m, "_EnvReflect", 0.38f); F(m, "_EnvTint", 0.5f); F(m, "_EnvRoughness", 0.25f);
                F(m, "_SpecPower", 90f); F(m, "_SpecStrength", 1.3f); F(m, "_GlintStrength", 1.0f);
                F(m, "_Sparkle", 0.4f); F(m, "_SparkleScale", 16f); F(m, "_FogAmount", 0.75f);
                F(m, "_HighlightSize", 7f); F(m, "_BandSharpness", 14f); F(m, "_LightInfluence", 0.35f);
                F(m, "_StreakStrength", 0.55f); F(m, "_StreakHeight", 0.6f);
            });
            // soft pink LED lamps along the drum lips (reference: soft pink glows on the violet rims; r4: 24 bigger lamps,
            // pinker, less white core)
            Mat("M_RimLight", "BWK/Emissive", m =>
            {
                C(m, "_Color", "#FF4FC4"); F(m, "_Intensity", 2.6f); F(m, "_CoreWhite", 0.12f); F(m, "_CorePower", 3f);
                F(m, "_HaloBoost", 0.5f); F(m, "_EdgeSaturate", 0.3f); F(m, "_Chase", 0f); F(m, "_PulseAmount", 0.2f);
                F(m, "_PulseSpeed", 0.8f); F(m, "_FogAmount", 0.25f);
            });
            // inside the side chamber windows: bright silver-lavender washing drum with small round perforations
            Mat("M_ChamberDrum", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#B6A6EA"); C(m, "_HighlightColor", "#E8DFFF"); C(m, "_HoleColor", "#2A1A55");
                C(m, "_HoleGlow", "#B48CFF"); F(m, "_Pattern", 0f); F(m, "_Circumference", 26.4f); F(m, "_VTile", 4f);
                F(m, "_HoleSpacing", 0.22f); F(m, "_HoleRadius", 0.22f); F(m, "_HoleStretch", 1f); F(m, "_PanelLength", 1000f);
                F(m, "_Glow", 0.28f); F(m, "_Metallic", 0.55f); F(m, "_Smoothness", 0.8f); F(m, "_HoleBand", 1f);
                F(m, "_SheenStrength", 0.25f); F(m, "_Sparkle", 0.4f);
            });
            // r8 (lighting): the S1 hall walls measured hue 248 / S .68 vs reference f_00.50s 275 / S .47 (the reference hall
            // is pink-lilac, ours saturated blue): lilac-pink metal, pinker self glow, darker holes
            Mat("M_DrumWallHall", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#B08CC8"); C(m, "_HighlightColor", "#D8BCE6"); C(m, "_HoleColor", "#1E0C34");
                C(m, "_HoleGlow", "#8A4AB8"); F(m, "_Circumference", 84.4f); F(m, "_HoleSpacing", 0.9f);
                F(m, "_HoleRadius", 0.24f); F(m, "_Glow", 0.2f);
            });
            Mat("M_DrumWallFlat", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#B08CC8"); C(m, "_HighlightColor", "#D8BCE6"); C(m, "_HoleColor", "#1E0C34");
                C(m, "_HoleGlow", "#8A4AB8"); F(m, "_Circumference", 4f); F(m, "_VTile", 4f); F(m, "_HoleSpacing", 0.8f);
                F(m, "_HoleRadius", 0.25f); F(m, "_Glow", 0.18f); F(m, "_PanelLength", 1000f);
                // S2 pass 3: this bulkhead (TunnelMouthWall 62 m / HallBackWall) is only seen THROUGH the annular gap between
                // the door ring (inner r ~4.98) and the mouth drum (r 4.2): its bright grid of small holes read as a speaker
                // grille right inside the hatch. Reference f_03.00s shows a DARK recessed violet band there -> plain dark
                // violet metal, no holes (_HoleBand 0), almost no self glow
                C(m, "_BaseColor", "#3E2E72"); C(m, "_HighlightColor", "#5C4A98"); F(m, "_HoleBand", 0f); F(m, "_Glow", 0.03f);
                F(m, "_Metallic", 0.6f); F(m, "_Smoothness", 0.55f);
            });
            Emissive("M_Screen", "#5E8FC7", 1.6f, pulse: 0.05f);
            Emissive("M_ButtonCyan", "#3FF0FF", 2.2f);
            Emissive("M_ButtonYellow", "#F4D82B", 2.2f);
            Emissive("M_ButtonPink", "#FF5FD0", 2.2f);
            // round 8 masters (water agent): the M_Glass master, the M_PipeWater liquid master + its Cyan / Pink variants and
            // M_Bubble come from MaterialLibrary.WaterFX.cs (glass / liquid shading of library 03 / 13 / 14 = water domain)
            GlassLiquidMasters();
            Mat("M_ChamberSwirl", "BWK/FlowGlow", m => { F(m, "_Mode", 1); C(m, "_ColorA", "#9FE8FF"); F(m, "_Intensity", 1.15f); F(m, "_Speed", 1f); });
            Mat("M_PortalRays", "BWK/FlowGlow", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#FFF6D8"); C(m, "_ColorB", "#FFB43A"); F(m, "_Intensity", 2.4f); F(m, "_Speed", 1f);
                F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One); F(m, "_ZWrite", 0); F(m, "_RayCount", 18);
            }, (int)RenderQueue.Transparent + 10);
            Soft("M_BrushPink", "#E463B1", "#FFB6E1");
            Soft("M_BrushBlue", "#6FD3FF", "#B4ECFF");
            Soft("M_BrushWhite", "#FFF6FF", "#FFFFFF");
            Lit_("M_MachinePink", "#E84AA3", metallic: 0.05f, smooth: 0.78f, emission: "#2A0A1E");
            Lit_("M_MachineLavender", "#D79AD8", metallic: 0.05f, smooth: 0.75f, emission: "#1E1430");
            Lit_("M_PlasticWhite", "#F6F1FF", metallic: 0f, smooth: 0.8f, emission: "#1A181F");
            Lit_("M_MetalPurple", "#6C3FC4", metallic: 0.85f, smooth: 0.75f);
            Mat("M_Fabric", "BWK/Soft", m => { F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFFF"); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.12f); F(m, "_BumpScale", 2f); });
        }
    }
}
