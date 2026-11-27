using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: Agent 1 - character & animation (fur, pom-pom, beanie knit, eyes, mouth, paw pads, star badge).
    // Only this domain's agent edits this file. Helpers (Mat, Lit_, Gold, Emissive, Soft, Particle, C, F, Get) live in MaterialLibrary.cs.
    public static partial class MaterialLibrary
    {
        static void CharacterMaterials()
        {
            Emissive("M_EyeHighlight", "#FFFFFF", 1.6f, pulse: 0f, core: 0f);
            Mat("M_HatKnit", "BWK/Character", m =>
            {
                // reference beanie dome: violet ribbed knit. The ribs are geometry (build_mascot_model.py CROWN_RIBS = 72,
                // UV.x = 0..1 around, UV.y = arc length in metres): _StitchU must equal CROWN_RIBS, _StitchV = rows per metre.
                // albedo chosen so the dome renders like the reference crown (~#76319f) under the tunnel's violet light
                // round 3: 44 BOLD vertical ribs around (CROWN_RIBS = CUFF_RIBS = 44), soft stitch rows, deep grooves
                F(m, "_Mode", 2); C(m, "_ColorA", "#7A467A"); C(m, "_ColorB", "#EDE6FF"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 38); F(m, "_BumpStrength", 1.0f); F(m, "_Smoothness", 0.14f); F(m, "_Glow", 0.08f);
            });
            Mat("M_HatCuff", "BWK/Character", m =>
            {
                // folded ribbed brim: CUFF_RIBS = 44 deep geometric ribs
                // warmer, lighter violet than before (rendered indigo #5414a9; reference cuff ~#74329e)
                F(m, "_Mode", 2); C(m, "_ColorA", "#945A84"); C(m, "_ColorB", "#945A84"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 40); F(m, "_BumpStrength", 1.05f); F(m, "_Smoothness", 0.12f); F(m, "_Glow", 0.12f);
            });
            Mat("M_HatStripe", "BWK/Character", m =>
            {
                // thick pale lavender-white ribbed band knitted into the crown (same 44 ribs as the dome)
                // bright pale pink-white knit band (reference ~#d7acd5, lit #f1c8ef): it sits in the hat's shade, so it self-lights
                F(m, "_Mode", 2); C(m, "_ColorA", "#F4E0F4"); C(m, "_ColorB", "#F4E0F4"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 46); F(m, "_BumpStrength", 0.95f); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.18f);
            });
            Mat("M_EyeIris", "BWK/Character", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#2E1409"); C(m, "_ColorB", "#C47C34"); C(m, "_ColorC", "#070302");
                F(m, "_Glow", 0.1f); F(m, "_RimStrength", 0.05f);
            });
            Lit_("M_Mouth", "#4B0F1E", metallic: 0f, smooth: 0.6f);
            Lit_("M_Tongue", "#FF6F93", metallic: 0f, smooth: 0.55f, emission: "#300812");
            Mat("M_PawPad", "BWK/Character", m =>
            {
                // soft candy-pink toe beans: fabric mode multiplies _ColorA by the vertex colour (pads = pink Col)
                F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFFF"); F(m, "_BumpScale", 0.6f); F(m, "_Smoothness", 0.3f); F(m, "_Glow", 0.65f);
                F(m, "_RimStrength", 0.25f);
            });
            Lit_("M_StarBadge", "#FFD43F", metallic: 0.1f, smooth: 0.6f, emission: "#7A4A00");
            var furNoise = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Tex}/T_FurNoise.png");
            Mat("M_Fur", "BWK/Fur", m =>
            {
                // warm plush pink (slightly salmon; the tunnel's violet light adds blue): light roots, soft pale tips.
                // Strand cells are square (the shader doubles UV.x); fine dense guard hairs + thick underfur = plush.
                // coral-leaning albedo: the tunnel light is violet, so this renders as the reference's warm pink (~#d06e94).
                // Short dense minky pile, soft alpha-to-coverage strands, little clumping/curl: plush, not needles.
                // round 3 (owner: "longer irregular plush clumps, avoid uniformly short fuzz"): longer pile, strong clump
                // length variation, more lean/swirl, lighter tips; the seat blends toward the cream coat (vertex alpha)
                C(m, "_RootColor", "#D06C66"); C(m, "_BaseColor", "#F28C7E"); C(m, "_TipColor", "#FFD0C2");
                C(m, "_PawRootColor", "#FFF0E2"); C(m, "_PawTipColor", "#FFF9EE"); F(m, "_PawGlow", 0.45f);   // warm white: reads WHITE under the violet light
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 200); F(m, "_FurLength", 0.052f); F(m, "_Gravity", 0.012f); F(m, "_Thinning", 0.8f); F(m, "_ClumpAmount", 0.8f); F(m, "_ClumpScale", 5f);
                F(m, "_AO", 0.2f); F(m, "_Curl", 1.5f); F(m, "_Underfur", 0.8f); F(m, "_EdgeSoft", 0.16f); F(m, "_SilhouetteFade", 0.45f);
                F(m, "_TuftScale", 20f); F(m, "_TuftAmount", 0.3f);   // ~6.5 cm irregular plush tufts converging toward their tips
                C(m, "_RimColor", "#FFD0C8"); F(m, "_Glow", 0.2f); F(m, "_RimStrength", 0.5f);
            }, (int)RenderQueue.AlphaTest);
            Mat("M_PomPom", "BWK/Fur", m =>
            {
                // dense soft yarn pom-pom: short, very dense, little thinning so the silhouette stays round and soft
                // deeper violet yarn (reference ~#8741b3, dark centre, lighter radiating tips): straight radial fibres
                // round 3: this is now only the DARK CORE of the pom-pom; the starburst is real radial yarn fibres
                // (Hair Curves + Geometry Nodes in build_mascot_model.py, material slot M_PawPad, vertex colour)
                C(m, "_RootColor", "#2E1040"); C(m, "_BaseColor", "#5C2672"); C(m, "_TipColor", "#9A5CB0");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 170); F(m, "_FurLength", 0.034f); F(m, "_Gravity", 0.0f); F(m, "_Thinning", 0.8f); F(m, "_AO", 0.5f);
                F(m, "_Curl", 0.12f); F(m, "_Underfur", 0.8f); F(m, "_ClumpAmount", 0.3f); F(m, "_EdgeSoft", 0.16f); F(m, "_SilhouetteFade", 0.3f);
                C(m, "_RimColor", "#C8A8F0"); F(m, "_Glow", 0.03f); F(m, "_RimStrength", 0.4f);
            }, (int)RenderQueue.AlphaTest);
            // static (shell-less) preview variants: no clipping, no offset
            foreach (var n in new[] { "M_Fur", "M_PomPom" })
            {
                var src = Get(n);
                if (src == null) continue;
                Mat(n + "_Static", "BWK/Fur", m => { m.CopyPropertiesFromMaterial(src); F(m, "_Thinning", 0f); F(m, "_FurLength", 0f); F(m, "_Gravity", 0f); F(m, "_StaticMode", 1f); }, (int)RenderQueue.AlphaTest);
            }
            CharacterMaterialsV5();
        }

        // ---------------------------------------------------------------- SK_Mascot_v5 (S2 pass 6, owner 2026-11-27)
        // v5's OWN materials: ModelImportRules.RemapVersionedMaterials gives SK_Mascot_v5.fbx "<name>_v5" wherever one exists
        // here (any other name keeps the shared M_* material). The v4 set above stays EXACTLY as at checkpoint-27 (owner: v4 =
        // the complete fallback incl. its materials). Measured on R2 (pass 6 run 1): v4 crown rendered Lab 39/37/-23 vs the
        // reference 33/46/-44, cuff 39/40/-25 vs 35.5/48/-45.5, stripe 61/34/-25 vs 70/27/-19, pom-pom 31/30/-27 vs 43/51/-49.
        static void CharacterMaterialsV5()
        {
            Mat("M_HatKnit_v5", "BWK/Character", m =>
            {
                // crown: more saturated blue-violet yarn, deeper purl valleys (_PurlDepth 1) and bolder ribs
                // pass 7 run 2: R2 crown rendered 40.5/36/-45 vs reference 36.7/44/-42 (too blue) -> linear x1.32/.73/.87
                F(m, "_Mode", 2); C(m, "_ColorA", "#912B9B"); C(m, "_ColorB", "#EDE6FF"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 38); F(m, "_BumpStrength", 1.6f); F(m, "_Smoothness", 0.14f); F(m, "_Glow", 0.06f);
                F(m, "_PurlDepth", 1.5f);   // prev1: crown Lstd 12.1 vs reference 16.2 (deeper purl valleys; > 1 extrapolates)
                // p10f (owner 15:55 "knitted hat materials"): YARN RELIEF knit = round V-stitch legs (height-field normals),
                // 96 ribs around like the reference (was 48 coarse pleats), matte wool + grazing sheen; R2 crown s2p10e
                // 146/84/167 vs reference 120/54/156 -> deeper, more saturated purple
                C(m, "_ColorA", "#7A2098"); F(m, "_StitchU", 88); F(m, "_StitchV", 60); F(m, "_BumpStrength", 1.0f);
                F(m, "_Smoothness", 0.05f); F(m, "_YarnRelief", 1.0f);
                F(m, "_WoolAbsorb", 0.68f); F(m, "_RimStrength", 0.6f);   // prev3 crown 131/83/158 L43.8 vs ref 120/54/156 L36.2: env grey + flat flanks
                // p10g: s2p10f crown box (600,294)-(690,312) 113/60/143 a38 b-37 vs reference 122/50/164 a50 b-48 = same L but
                // greyer -> more saturated violet yarn (linear R x1.2, B x1.35), less env grey
                C(m, "_ColorA", "#8420AF"); F(m, "_WoolAbsorb", 0.55f);
            });
            Mat("M_HatCuff_v5", "BWK/Character", m =>
            {
                // thick folded brim (v5 geometry: outer rib surface rolled out 1.2 cm): bluer violet, deep rib shading
                // pass 7 run 2: R2 cuff 36/41/-46 vs reference 39/47/-44 and FLAT (Lstd 3.4 vs 10.8) -> redder, lighter
                // (linear x1.51/1.32/1.09) and deeper rib relief
                F(m, "_Mode", 2); C(m, "_ColorA", "#9C46AE"); C(m, "_ColorB", "#9C46AE");   /* p9: was #AB52B5 (prev1 cuff L 41.9 vs reference 36.4) */ F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 40); F(m, "_BumpStrength", 2.0f); F(m, "_Smoothness", 0.12f); F(m, "_Glow", 0.06f);
                F(m, "_PurlDepth", 1.8f);   // prev1: cuff still flat (Lstd 3.6 vs reference 10.8) -> much deeper rib valleys
                // p10f: yarn relief knit (s2p10e R2 cuff Lstd 3.5 vs reference 13.0 = flat pleats)
                C(m, "_ColorA", "#B456C2"); C(m, "_ColorB", "#B456C2"); F(m, "_StitchU", 66); F(m, "_StitchV", 52);   // prev2: ref cuff ribs 1.7x wider -> 72 ribs
                F(m, "_BumpStrength", 1.2f); F(m, "_Smoothness", 0.05f); F(m, "_Glow", 0.08f); F(m, "_YarnRelief", 1.0f);
                F(m, "_WoolAbsorb", 0.72f); F(m, "_RimStrength", 0.6f);   // prev3 cuff centre L39.6 vs ref 32.2, reference flanks lighter
                // p10g: s2p10f cuff (600,356)-(690,394) 130/61/154 L38.9 vs reference 108/45/157 L33.2 -> darker, bluer violet
                // (linear x.67/.56/1.04), less env grey and self-glow
                C(m, "_ColorA", "#9640C5"); C(m, "_ColorB", "#9640C5"); F(m, "_WoolAbsorb", 0.6f); F(m, "_Glow", 0.06f);
            });
            Mat("M_HatStripe_v5", "BWK/Character", m =>
            {
                // pale-pink band (reference ~70/27/-19): warmer pale pink, a little more self-light in the hat's shade
                F(m, "_Mode", 2); C(m, "_ColorA", "#F2EAF4"); C(m, "_ColorB", "#F2EAF4"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 46); F(m, "_BumpStrength", 0.6f); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.40f);   // p9: bump 1.4 -> .6, glow .24 -> .40 (prev1 stripe L 55.5 vs reference 64)
                F(m, "_PurlDepth", 0.4f);   // p9: 1.5 read as a high-contrast picket fence at R2 (reference: soft pale knit band)
                // p10f: cream-pink knitted band with visible V stitches (yarn relief, softer than the purple ribs)
                C(m, "_ColorA", "#F6E6F0"); C(m, "_ColorB", "#F6E6F0"); F(m, "_StitchU", 66); F(m, "_StitchV", 58);
                F(m, "_BumpStrength", 0.8f); F(m, "_Smoothness", 0.06f); F(m, "_Glow", 0.46f); F(m, "_YarnRelief", 0.75f);   // prev2 stripe L60.6 vs ref 66.7
                // p10g: s2p10f stripe (600,328)-(690,342) 209/159/202 L71.5 vs reference 222/179/216 L77.8 -> lighter, less magenta
                C(m, "_ColorA", "#F8F0F2"); C(m, "_ColorB", "#F8F0F2"); F(m, "_Glow", 0.52f);
            });
            Mat("M_PawPad_v5", "BWK/Character", m =>
            {
                // fabric x vertex colour: the pink toe beans AND (new in v5) the pom-pom's ~200 radial yarn locks (dark violet
                // root -> lilac tip vertex colours). Less self-glow than v4 (.65) so the locks keep their light / shade.
                F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFFF"); F(m, "_BumpScale", 0.6f); F(m, "_Smoothness", 0.3f); F(m, "_Glow", 0.5f);
                F(m, "_RimStrength", 0.3f);
                F(m, "_VioletLift", 1.45f);   // prev3: 1.8 -> L45.8 (ref 48.8) but white lock-tip specks; 1.45   // p10f: pom-pom yarn L42 vs reference 49 (pink toe beans unaffected); prev2 1.35 -> L43
            });
            var furNoise = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Tex}/T_FurNoise.png");
            Mat("M_Fur_v5", "BWK/Fur", m =>
            {
                // body rendered 58/42/-11 vs reference 58/44/-4 -> slightly warmer albedo; bigger, stronger tufts = soft plush
                // clumps instead of streaks; white feet keep v4's paw glow (smooth white soles: rig contract sole_fur .18)
                // pass 7: the v5 FBX now carries METRIC fur UVs (body equirectangular, arms cylindrical, 1.57 m per base unit)
                // instead of the master's smart-UV islands that stretched the strand cells 2:1 = streaks / blocky patches.
                // R2 body (s2p7b) rendered 53/43/-10 vs reference 60/39/-8 -> lighter, slightly less saturated coat.
                // pass 7 run 2: R2 body 56.7/43/-11 vs reference 54.9/44/-6 (linear x1.03/.93/.84) and the 12 cm tuft cells
                // read as a QUILTED LATTICE of round bumps -> BWK_Fur _PlushMode 1 (irregular Voronoi tufts, ~6.5 cm) +
                // _StrandContrast 1 (reference body Lstd 11.3 vs ours 6.2), a little more downward droop
                // pass 9: R2 body crop (560,410)-(720,500) s2p8a 188/99/144 vs reference 203/119/158 = darker + more magenta with
                // strand streaks -> green lifted (linear x1.3), lighter roots (AO .4 -> .28), half the strand contrast, finer strands
                C(m, "_RootColor", "#FF9A78"); C(m, "_BaseColor", "#FFB48E"); C(m, "_TipColor", "#FFE6D2");   // p7 #ED826A / #FFA382 / #FFDCBB
                C(m, "_PawRootColor", "#FFF0E2"); C(m, "_PawTipColor", "#FFF9EE"); F(m, "_PawGlow", 0.45f);
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 240); F(m, "_FurLength", 0.052f); F(m, "_Gravity", 0.02f); F(m, "_Thinning", 0.8f); F(m, "_ClumpAmount", 0.6f); F(m, "_ClumpScale", 5f);   // p7 density 200
                F(m, "_AO", 0.28f); F(m, "_Curl", 1.0f); F(m, "_Underfur", 0.8f); F(m, "_EdgeSoft", 0.16f); F(m, "_SilhouetteFade", 0.45f);   // p7 AO .4
                F(m, "_TuftScale", 20f); F(m, "_TuftAmount", 0.3f); F(m, "_PlushMode", 1f); F(m, "_StrandContrast", 0.35f);   // p7 tufts 24 / .5, strand contrast 1 (prev1: still vertical streaks)
                C(m, "_RimColor", "#FFD0C8"); F(m, "_Glow", 0.22f); F(m, "_RimStrength", 0.5f);   // p7 glow .2 (prev1 body L 62.0 vs reference 60.0)
                // p10f (owner 15:55 "realistic thick pink fur"): s2p10e R2 body 206/127/173 Lstd 7.5 vs reference 203/116/154
                // Lstd 13.0 = grey-pink velvet. Now a THICK deep coat: 50 % longer pile, bigger locks that part at the tips,
                // shingled tuft depth shading (_TuftDepth), per-tuft pile length (_LenNoise: tufts break the silhouette),
                // saturated warm-rose roots -> pale pink tips, less flat self-glow, soft unlit white-pink rim (_RimSelf)
                // prev1: body 179/104/150 L54.2 (too dark), regular 'pinecone scale' pattern -> softer, irregular depth, lighter
                // prev2: body 186/112/151 L56.8 a34.6 b-8 (ref 59.8 / 39.1 / -5.2) + still scale-like in the 9x16 view ->
                // depth only in the frayed partings (fading toward the tips), smaller irregular locks, redder lighter coat
                // prev3 (central box 600-690 x 405-495): 183/98/131 L52.7 b-2.3 vs ref 198/106/148 L56.9 b-5.8 -> pinker, lighter,
                // softer lock depth (the partings read blotchy in 9x16)
                C(m, "_RootColor", "#F46A66"); C(m, "_BaseColor", "#FFA47E"); C(m, "_TipColor", "#FFE2CA");
                F(m, "_FurLength", 0.078f); F(m, "_Gravity", 0.035f); F(m, "_Thinning", 0.75f); F(m, "_Curl", 0.8f);
                F(m, "_TuftScale", 18f); F(m, "_TuftAmount", 0.55f); F(m, "_StrandContrast", 0.45f); F(m, "_AO", 0.34f);
                F(m, "_TuftDepth", 0.45f); F(m, "_LenNoise", 0.6f); F(m, "_LenNoiseScale", 0.5f); F(m, "_SilhouetteFade", 0.3f);
                C(m, "_RimColor", "#FFD6D6"); F(m, "_Glow", 0.2f); F(m, "_RimStrength", 0.55f); F(m, "_RimSelf", 0.25f);
                // p10g (lead 16:40: the p10f coat = round light CELLS + dark partings = quilted / PINECONE at R2 and gameplay
                // distance, dark red-pink): BWK_Fur _PlushMode 2 = SMALL irregular clumps (4 cm, were 8.7 cm) radiating from a
                // whorl on the back, strands combed along that flow, frayed clump borders instead of closed outlines, clumping
                // strength varying in patches. Measured s2p10f vs reference (R2 boxes): mid-back 194/103/146 vs 207/103/144
                // (warmer salmon: R up, G/B kept), lower back 180/98/144 vs 172/134/174 (cream-pink seat), right under the
                // brim 191/99/141 vs 173/73/115 (contact shade)
                F(m, "_PlushMode", 2f); F(m, "_TuftScale", 38f); F(m, "_TuftAmount", 0.5f); F(m, "_TuftLean", 0.55f);
                F(m, "_FlowRadial", 0.85f); m.SetVector("_FlowCentre", new Vector4(0.92f, 0.52f, 0f, 0f));
                F(m, "_StrandFlow", 2.5f); F(m, "_Fray", 0.45f); F(m, "_TuftDepth", 0.3f); F(m, "_StrandContrast", 0.6f);
                F(m, "_AO", 0.3f); F(m, "_Density", 260f); F(m, "_LenNoiseScale", 0.35f); F(m, "_SilhouetteFade", 0.2f);
                C(m, "_RootColor", "#F46262"); C(m, "_BaseColor", "#FF9976"); C(m, "_TipColor", "#FFD4BD");
                F(m, "_SeatLight", 0.85f); C(m, "_SeatColor", "#FFE2E6"); m.SetVector("_SeatRange", new Vector4(0.42f, 0.30f, 0f, 0f));
                F(m, "_BrimShade", 0.5f); m.SetVector("_BrimRange", new Vector4(0.614f, 0.07f, 0.0333f, 0f));
                F(m, "_RimPower", 3.0f); F(m, "_RimSelf", 0.35f);
            }, (int)RenderQueue.AlphaTest);
            Mat("M_PomPom_v5", "BWK/Fur", m =>
            {
                // v5 pom-pom = real radial yarn locks (M_PawPad_v5) around this core: a short MID-violet fuzz that fills the gaps
                // between the locks (v4's core was a near-black ball because it was the whole pom-pom)
                // pass 7 run 2: R2 pom-pom pale lilac 61/27/-31 vs reference saturated violet 47/49/-46 (linear x.86/.41/.88)
                C(m, "_RootColor", "#3E0C6E"); C(m, "_BaseColor", "#7220AE"); C(m, "_TipColor", "#A955E0");   // p9 tip was #B566E5
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 190); F(m, "_FurLength", 0.065f); F(m, "_Gravity", 0.0f); F(m, "_Thinning", 0.5f);   /* p9: core fuzz reaches past the yarn tips (core .232 + .065 > tip .272) = soft round outline; was 170 / .05 / .6 */ F(m, "_AO", 0.35f);   // cand3: longer core fuzz softens the spiky lock silhouette
                F(m, "_Curl", 0.25f); F(m, "_Underfur", 0.8f); F(m, "_ClumpAmount", 0.55f); F(m, "_EdgeSoft", 0.16f); F(m, "_SilhouetteFade", 0.3f);
                C(m, "_RimColor", "#C878F1"); F(m, "_Glow", 0.06f); F(m, "_RimStrength", 0.4f);
                // p10f: s2p10e R2 pom-pom 124/72/175 L41.5 Lstd 8 vs reference 153/87/189 L48.8 Lstd 17 = dark flat ball ->
                // longer, finer, lighter violet fibres with deeper roots and a soft lilac halo
                C(m, "_RootColor", "#5A1C96"); C(m, "_BaseColor", "#9A44D8"); C(m, "_TipColor", "#D49CFA"); F(m, "_Density", 230); F(m, "_FurLength", 0.075f); F(m, "_Thinning", 0.4f);
                F(m, "_AO", 0.5f); F(m, "_Glow", 0.1f); C(m, "_RimColor", "#DAB0FF"); F(m, "_RimStrength", 0.5f); F(m, "_RimSelf", 0.2f);
            }, (int)RenderQueue.AlphaTest);
            // static (shell-less) variants, same naming rule as v4 (name + "_Static")
            foreach (var n in new[] { "M_Fur_v5", "M_PomPom_v5" })
            {
                var src = Get(n);
                if (src == null) continue;
                Mat(n + "_Static", "BWK/Fur", m => { m.CopyPropertiesFromMaterial(src); F(m, "_Thinning", 0f); F(m, "_FurLength", 0f); F(m, "_Gravity", 0f); F(m, "_StaticMode", 1f); }, (int)RenderQueue.AlphaTest);
            }
        }
    }
}
