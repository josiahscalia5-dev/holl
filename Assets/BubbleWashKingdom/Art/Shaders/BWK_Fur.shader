// Mobile shell fur in a single draw call. The Blender mesh contains N coincident copies (shells) of the body;
// UV1.x = shell fraction (0 = skin, 1 = tip), UV1.y = fur length mask. Shells are pushed out along the normal
// here (tunable length + gravity) and alpha-clipped against a strand noise texture for a soft fluffy silhouette.
Shader "BWK/Fur"
{
    Properties
    {
        _RootColor ("Root Color", Color) = (0.86, 0.22, 0.52, 1)
        _BaseColor ("Mid Color", Color) = (1.0, 0.38, 0.66, 1)
        _TipColor ("Tip Color", Color) = (1.0, 0.66, 0.84, 1)
        _NoiseTex ("Strand Noise", 2D) = "white" {}
        _Density ("Strand Density", Float) = 38
        _FurLength ("Fur Length (m)", Float) = 0.045
        _Gravity ("Gravity Droop (m)", Float) = 0.012
        _Thinning ("Tip Thinning", Range(0, 2)) = 1.1
        _ClumpScale ("Clump Scale", Float) = 7
        _ClumpAmount ("Clump Amount", Range(0,1)) = 0.35
        _Wrap ("Wrap Lighting", Range(0,1)) = 0.6
        _RimColor ("Rim / Sheen Color", Color) = (1.0, 0.85, 0.95, 1)
        _RimPower ("Rim Power", Float) = 2.6
        _RimStrength ("Rim Strength", Range(0,2)) = 0.7
        _AO ("Root Occlusion", Range(0,1)) = 0.5
        _Glow ("Self Glow", Range(0,1)) = 0.12
        _UseVertexTint ("Use Vertex Colour Tint", Range(0,1)) = 1
        _StaticMode ("Ignore Shell UV (static meshes)", Range(0,1)) = 0
        _Curl ("Curl / Lean (x fur length)", Range(0,3)) = 1.2
        _Underfur ("Underfur Density", Range(0,1)) = 0.55
        _PawRootColor ("Paw Coat Root (vertex alpha 0)", Color) = (0.86, 0.80, 0.84, 1)
        _PawTipColor ("Paw Coat Tip (vertex alpha 0)", Color) = (1, 0.98, 0.98, 1)
        _EdgeSoft ("Strand Edge Softness", Range(0.01, 0.5)) = 0.18
        _SilhouetteFade ("Silhouette Halo Fade", Range(0, 1)) = 0.6
        _PawGlow ("Paw Coat Self Glow", Range(0, 1)) = 0
        _TuftScale ("Tuft Cells per UV unit", Float) = 24
        _TuftAmount ("Tuft Clumping (0 = off)", Range(0, 0.9)) = 0
        _PlushMode ("Tufts: 0 = v4 cells, 1 = Voronoi locks (p7), 2 = fine radial clumps (p10g)", Range(0, 2)) = 0
        _StrandContrast ("Extra Strand / Tuft Contrast (0 = v4)", Range(0, 1)) = 0
        _TuftDepth ("Tuft Depth Shading (0 = off)", Range(0, 1)) = 0
        _LenNoise ("Per-Tuft Pile Length Variation (0 = off)", Range(0, 1)) = 0
        _LenNoiseScale ("Length Variation Scale (x tuft cells)", Float) = 0.5
        _RimSelf ("Unlit Soft Rim (0 = off)", Range(0, 1)) = 0
        // S2 p10g (SK_Mascot_v5 only; defaults = off, v4 / older materials unchanged)
        _FlowRadial ("Mode 2: radial lean from the back whorl (0 = straight down)", Range(0, 1)) = 0
        _FlowCentre ("Mode 2: whorl position (base UV x, y)", Vector) = (0.92, 0.52, 0, 0)
        _TuftLean ("Mode 2: lock tip lean along the flow (clump cells)", Range(0, 1.5)) = 0
        _StrandFlow ("Mode 2: strands combed along the flow (strand cells)", Range(0, 4)) = 0
        _Fray ("Mode 2: frayed lock borders", Range(0, 1)) = 0
        _SeatLight ("Lower body toward the seat colour (0 = off)", Range(0, 1)) = 0
        _SeatColor ("Seat / lower belly colour", Color) = (1, 0.9, 0.92, 1)
        _SeatRange ("Seat gradient: body v from (x) to (y)", Vector) = (0.42, 0.3, 0, 0)
        _BrimShade ("Contact shade under the beanie brim (0 = off)", Range(0, 1)) = 0
        _BrimRange ("Brim line v (x) - cos(phi) * (z), shade band width (y)", Vector) = (0.614, 0.07, 0.0333, 0)
    }
    SubShader
    {
        Tags { "RenderType"="TransparentCutout" "RenderPipeline"="UniversalPipeline" "Queue"="AlphaTest" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        TEXTURE2D(_NoiseTex); SAMPLER(sampler_NoiseTex);
        CBUFFER_START(UnityPerMaterial)
            half4 _RootColor, _BaseColor, _TipColor, _RimColor, _PawRootColor, _PawTipColor;
            float4 _NoiseTex_ST;
            float _Density, _FurLength, _Gravity, _Thinning, _ClumpScale, _RimPower;
            half _ClumpAmount, _Wrap, _RimStrength, _AO, _Glow, _UseVertexTint, _StaticMode, _Curl, _Underfur, _EdgeSoft, _SilhouetteFade, _PawGlow;
            float _TuftScale, _TuftAmount;
            half _PlushMode, _StrandContrast;
            half _TuftDepth, _LenNoise, _RimSelf;
            float _LenNoiseScale;
            half _FlowRadial, _TuftLean, _StrandFlow, _Fray, _SeatLight, _BrimShade;
            float4 _FlowCentre, _SeatRange, _BrimRange;
            half4 _SeatColor;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Cull Back
            AlphaToMask On   // MSAA alpha-to-coverage: soft strand edges and a fuzzy silhouette without sorting
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
                float2 shell : TEXCOORD1;
                half4 color : COLOR;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                float2 uv : TEXCOORD2;
                float2 shell : TEXCOORD3;
                half4 color : TEXCOORD4;
                half fog : TEXCOORD5;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                float h = i.shell.x * (1.0 - _StaticMode);
                float mask = (i.shell.y > 0.001 && _StaticMode < 0.5) ? i.shell.y : 1.0;
                // S2 p10f (v5 only, _LenNoise > 0): every patch of locks gets its own pile length (UV-space noise, so it is
                // stable under skinning) -> long tufts break the silhouette instead of an even velvet outline
                if (_LenNoise > 0.001)
                {
                    float2 q = float2(i.uv.x * 2.0, i.uv.y) * (_TuftScale * _LenNoiseScale);
                    float nz = BWK_ValueNoise(q) * 0.7 + BWK_ValueNoise(q * 2.6 + 11.3) * 0.3;
                    mask *= lerp(1.0, 0.5 + 1.1 * nz, _LenNoise);
                    mask *= lerp(1.0, lerp(0.62, 1.0, i.color.a), _UseVertexTint);   // cream paw coat stays short (no slicing)
                }
                float3 nWS = TransformObjectToWorldNormal(i.normalOS);
                float3 posWS = TransformObjectToWorld(i.positionOS.xyz);
                posWS += nWS * (h * _FurLength * mask);
                posWS.y -= h * h * _Gravity * mask;
                // plush: tips lean in a slowly varying swirl (tangent plane) so strands cross instead of standing as spikes
                float3 pOS = i.positionOS.xyz * 9.0;
                float3 sw = float3(BWK_ValueNoise3(pOS), BWK_ValueNoise3(pOS + 7.1), BWK_ValueNoise3(pOS + 13.7)) - 0.5;
                float3 swWS = TransformObjectToWorldDir(sw, false);
                swWS -= nWS * dot(swWS, nWS);
                posWS += swWS * (h * h * _FurLength * _Curl * mask);
                o.positionWS = posWS;
                o.positionCS = TransformWorldToHClip(posWS);
                o.normalWS = nWS;
                o.uv = i.uv;
                o.shell = float2(h, mask);
                o.color = i.color;
                o.fog = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float h = i.shell.x;
                // Procedural strands, resolution independent: guard hairs lean inside their cell with height (soft crossing
                // tips), lengths vary in clumps, and a denser, shorter underfur layer fills the coat like a plush toy.
                // Tufts (round 3, "long irregular plush clumps"): the coat is split into irregular tuft cells; toward the
                // tips the strands of a tuft converge on its (jittered) centre, so the pile breaks into soft clumps with
                // partings between them. Strands are looked up at their ROOT position (expanded away from the centre).
                float2 base = float2(i.uv.x * 2.0, i.uv.y);              // UV.x unit = 2x UV.y unit in metres -> square cells
                // domain-warped tuft cells: irregular organic clumps instead of a visible square grid
                float2 tuv = base * _TuftScale;
                float2 tcell, tc, relSkin, rel;
                half tRnd, parting;
                half tuftShade = 0.5;
                float pull;
                float over = 0.0;                 // mode 2: how far the strand root lies past its clump border (frayed below)
                float2 fdir = float2(0.0, -1.0);  // mode 2: fur flow direction in base UV (v runs up the body)
                if (_PlushMode > 1.5)
                {
                    // S2 p10g (SK_Mascot_v5, _PlushMode 2): pass 10f's 9 cm Voronoi locks read as a QUILTED / PINECONE
                    // pattern of round light cells (lead 16:40). The approved coat = fine strands gathered in SMALL irregular
                    // clumps whose tips radiate from a whorl on the back: small fully jittered clumps, clumping strength
                    // varying in patches (locks here, smooth plush there), lock tips + strands combed along that radial flow,
                    // frayed lock borders (per strand, below) instead of closed dark outlines.
                    float2 dw = base - _FlowCentre.xy;
                    float dl = length(dw);
                    fdir = normalize(lerp(float2(0.0, -1.0), dw / max(dl, 1e-4), _FlowRadial * saturate(dl * 5.0)) + float2(0.0, -0.25));
                    tuv += (float2(BWK_ValueNoise(tuv * 0.5 + 3.1), BWK_ValueNoise(tuv * 0.5 + 17.9)) - 0.5) * 0.9;
                    float2 ipw = floor(tuv);
                    float g1 = 8.0, g2 = 8.0;
                    tc = ipw + 0.5; tcell = ipw;
                    [unroll] for (int wy = -1; wy <= 1; wy++)
                    {
                        [unroll] for (int wx = -1; wx <= 1; wx++)
                        {
                            float2 cw = ipw + float2(wx, wy);
                            float2 pw = cw + 0.08 + float2(BWK_Hash21(cw + 21.7), BWK_Hash21(cw + 4.3)) * 0.84;
                            float dw2 = length(tuv - pw);
                            if (dw2 < g1) { g2 = g1; g1 = dw2; tc = pw; tcell = cw; }
                            else if (dw2 < g2) { g2 = dw2; }
                        }
                    }
                    tRnd = BWK_Hash21(tcell + 11.9);
                    tuftShade = saturate((g2 - g1) * 2.2);
                    float patchK = BWK_ValueNoise(base * 6.0 + 2.3);
                    pull = _TuftAmount * h * (0.5 + 0.7 * tRnd) * lerp(0.35, 1.3, patchK);
                    tc += fdir * (h * _TuftLean);                          // the clump's tips lean along the flow
                    relSkin = tuv - tc;
                    rel = relSkin / max(1.0 - pull, 0.2);
                    over = g1 * pull / max(1.0 - pull, 0.2) - 0.5 * (g2 - g1);
                    parting = 1.0;                                         // frayed per strand below
                }
                else if (_PlushMode > 0.5)
                {
                    // S2 pass 7 (SK_Mascot_v5 only, _PlushMode 1): IRREGULAR Voronoi tufts. The v4 cells (one jittered
                    // centre per square cell) still read as a quilted lattice of round bumps on the v5 metric UVs; here
                    // every tuft centre is fully jittered and the nearest one wins (3x3 search), so tuft sizes / shapes
                    // vary like real plush and the partings follow the irregular cell borders (f2 - f1).
                    tuv += (float2(BWK_ValueNoise(tuv * 0.45 + 3.1), BWK_ValueNoise(tuv * 0.45 + 17.9)) - 0.5) * (0.7 + 0.6 * _TuftDepth);
                    // tufts ~1.8x longer along v (v5 body UV: v runs up the body) = combed plush locks, not round bobbles
                    const float2 an = float2(1.0, 0.55);
                    float2 auv = tuv * an;
                    float2 ip = floor(auv);
                    float f1 = 8.0, f2 = 8.0;
                    tc = ip + 0.5; tcell = ip;
                    [unroll] for (int vy = -1; vy <= 1; vy++)
                    {
                        [unroll] for (int vx = -1; vx <= 1; vx++)
                        {
                            float2 cc = ip + float2(vx, vy);
                            float2 pp = cc + 0.05 + float2(BWK_Hash21(cc + 21.7), BWK_Hash21(cc + 4.3)) * 0.9;
                            float dd = length(auv - pp);
                            if (dd < f1) { f2 = f1; f1 = dd; tc = pp; tcell = cc; }
                            else if (dd < f2) { f2 = dd; }
                        }
                    }
                    tRnd = BWK_Hash21(tcell + 11.9);
                    // S2 p10f (_TuftDepth): each lock is lit on its lower (tip) half and shadowed on its upper half where
                    // the lock above overlaps it, and darkens toward the partings = shingled, deep plush instead of velvet
                    tuftShade = saturate((f2 - f1) * 2.2);
                    pull = _TuftAmount * h * (0.6 + 0.8 * tRnd);
                    tc.y -= h * 0.3;                                  // the lock's tips converge BELOW its centre (droop)
                    relSkin = (auv - tc) / an;
                    rel = relSkin / max(1.0 - pull, 0.2);
                    // the strand's root (|rel| from the centre) belongs to a neighbour once it crosses the border
                    float over = f1 * pull / max(1.0 - pull, 0.2) - 0.5 * (f2 - f1);
                    parting = (_TuftAmount > 0.001 && h > 0.001) ? saturate(1.0 - over * 3.0) : 1.0;
                }
                else
                {
                    tuv += (float2(BWK_ValueNoise(tuv * 0.37 + 3.1), BWK_ValueNoise(tuv * 0.37 + 17.9)) - 0.5) * 1.3;
                    tcell = floor(tuv);
                    tc = tcell + 0.5 + (float2(BWK_Hash21(tcell + 21.7), BWK_Hash21(tcell + 4.3)) - 0.5) * 0.45;
                    tRnd = BWK_Hash21(tcell + 11.9);
                    pull = _TuftAmount * h * (0.7 + 0.6 * tRnd);
                    relSkin = tuv - tc;
                    rel = relSkin / max(1.0 - pull, 0.2);
                    float2 rootOff = abs(tc + rel - (tcell + 0.5));          // root outside its own tuft cell -> parting
                    parting = (_TuftAmount > 0.001 && h > 0.001) ? saturate(1.0 - (length(rootOff) - 0.55) * 2.5) : 1.0;
                }
                parting = lerp(1.0, parting, saturate(h * 1.6));           // partings only open toward the tips
                float2 rootUV = base + (rel - relSkin) / _TuftScale;      // = base on the skin; expands toward the tips
                rootUV -= fdir * (h * _StrandFlow) / _Density;            // p10g: strands combed along the flow (0 = off)
                float2 suv = rootUV * _Density;
                float2 cell = floor(suv);
                float2 jit = float2(BWK_Hash21(cell), BWK_Hash21(cell + 17.3)) - 0.5;
                float2 lean = (float2(BWK_Hash21(cell + 5.7), BWK_Hash21(cell + 9.1)) - 0.5) * 0.8 * h;
                float d = length(frac(suv) - 0.5 - jit * 0.4 - lean);
                half rnd = BWK_Hash21(cell + 3.1);
                if (_PlushMode > 1.5 && _TuftAmount > 0.001 && h > 0.001)   // p10g: frayed clump borders, strand by strand
                    parting = lerp(1.0, saturate(1.0 - (over - (rnd - 0.5) * _Fray) * 3.0), saturate(h * 1.6));
                half clump =BWK_ValueNoise(float2(i.uv.x * 2.0, i.uv.y) * _ClumpScale);
                half lenVar = lerp(1.0, 0.55 + clump * 0.9, _ClumpAmount) * (0.72 + 0.28 * rnd);
                lenVar *= lerp(1.0, 0.62 + 0.62 * tRnd, saturate(_TuftAmount * 1.6));   // every tuft has its own length
                half guard = saturate(1.0 - d * 1.75) * lenVar;
                float2 suv2 = rootUV * _Density * 1.85 + 3.7;
                float2 cell2 = floor(suv2);
                float2 jit2 = float2(BWK_Hash21(cell2 + 1.3), BWK_Hash21(cell2 + 7.7)) - 0.5;
                float d2 = length(frac(suv2) - 0.5 - jit2 * 0.4 - lean * 0.6);
                half under = saturate(1.0 - d2 * 1.8) * 0.5 * _Underfur * (0.8 + 0.4 * clump);
                half strand = max(guard, under);
                half3 n = normalize(i.normalWS);
                half3 v = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half alpha = 1.0;
                if (h > 0.001)
                {
                    // soft coverage instead of a hard cut (alpha-to-coverage), and the outer shells thin out where the
                    // surface turns away so the silhouette is a soft plush halo instead of a row of needles
                    half edge = strand - h * _Thinning * 0.85;
                    alpha = saturate(edge / _EdgeSoft + 0.5) * parting;
                    half ndv = saturate(dot(n, v));
                    alpha *= lerp(1.0, saturate(ndv * 2.5 + 0.15), _SilhouetteFade * h);
                    clip(alpha - 0.02);
                }

                // coat selector: vertex alpha 1 = pink coat, 0 = cream paw coat (blend = lighter paw tips); rgb = tint
                half3 pinkC = h < 0.5 ? lerp(_RootColor.rgb, _BaseColor.rgb, saturate(h * 2.0 + 0.55)) : lerp(_BaseColor.rgb, _TipColor.rgb, h * 2.0 - 1.0);
                half3 pawC = lerp(_PawRootColor.rgb, _PawTipColor.rgb, saturate(h * 1.4 + 0.2));
                half coat = lerp(1.0, i.color.a, _UseVertexTint);
                half3 col = lerp(pawC, pinkC, coat) * lerp(half3(1, 1, 1), i.color.rgb, _UseVertexTint);
                // p10g (v5 body UV: base.y = polar angle / pi from the seat pole, arms start at v 3.3): the approved coat turns a
                // soft cream-pink toward the seat, and the beanie brim (hat_alpha 69.5 deg about the 6-deg back-tilted hat axis =
                // polar angle 110.5 - 6 cos(phi)) shades the fur right under it (contact occlusion; no SSAO on mobile)
                half bodyK = coat * step(base.y, 1.2);
                half seatK = (1.0 - smoothstep(_SeatRange.y, _SeatRange.x, base.y)) * _SeatLight * bodyK;   // edges ascending (GLSL)
                col = lerp(col, _SeatColor.rgb * lerp(0.9, 1.04, h), seatK);
                float brimV = _BrimRange.x - _BrimRange.z * cos((base.x / 1.84 - 0.5) * 6.2831853);
                half brimK = smoothstep(brimV - _BrimRange.y, brimV, base.y) * _BrimShade * bodyK;
                half shade = 1.0 - brimK;
                // low strand contrast: plush, not needles (v5 _StrandContrast 1: reference R2 body Lstd 11.3 vs ours 6.2)
                col *= lerp(lerp(0.86, 0.74, _StrandContrast), lerp(1.06, 1.12, _StrandContrast), strand);
                col *= lerp(1.0, lerp(lerp(0.92, 0.86, _StrandContrast), lerp(1.04, 1.07, _StrandContrast), tRnd),
                            saturate(_TuftAmount * 1.6));   // tufts vary a little in tone
                // partings between the locks fall into shade deep in the pile; the strand pattern frays the border
                half ts = saturate(tuftShade + (strand - 0.5) * 0.6);
                col *= lerp(1.0, lerp(0.55, 1.1, ts), _TuftDepth * (1.0 - 0.6 * h));
                half3 light = BWK_WrapLight(i.positionWS, n, _Wrap);
                half ao = lerp(1.0 - _AO, 1.0, h);
                half rim = BWK_Fresnel(n, v, _RimPower) * _RimStrength * (0.4 + 0.6 * h);
                half3 c = (col * light * ao + _RimColor.rgb * rim * light) * shade
                        + col * (_Glow + _PawGlow * max(1.0 - coat, seatK * 0.6)) * lerp(1.0, shade, 0.7);
                c += _RimColor.rgb * rim * _RimSelf * shade;   // p10f: soft white-pink halo on the backlit silhouette tips
                c = MixFog(c, i.fog);
                return half4(c, alpha);
            }
            ENDHLSL
        }
        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0
            HLSLPROGRAM
            #pragma vertex ShadowVert
            #pragma fragment ShadowFrag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #define BWK_SHADOW_SKIP_SHELLS
            #include "BWKShadow.hlsl"
            ENDHLSL
        }
    }
    FallBack Off
}
