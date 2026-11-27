// Stylised lit surface for soft, glossy toy-like materials:
//  _Mode 0 = foam: puffy white with soft wrap light, lavender-blue shadows and cloud bump detail
//  _Mode 1 = rainbow rail: glossy candy plastic with rainbow bands across UV.x (around the tube)
//  _Mode 2 = knit: beanie stripes along UV.y with procedural V-stitch knit bumps
//  _Mode 3 = eye: glossy brown iris (radial gradient around the UV centre) with a dark pupil
//  _Mode 4 = fabric: soft cloth (socks, towels) tinted by vertex colour stripes
//  _Mode 5 = soap suds (foam banks): baked crevice AO in vertex colour R (lavender-blue crevices), per-puff tint in G,
//            soft wrap light, satin soap gloss, translucent bright rims, tiny bubble glints, gentle wobble
//  _Mode 6 = milk splash (3D crown splashes, droplet particles): creamy white, cool blue-grey shading and water bounce
//            from below, crisp wet highlights, bright thin edges, liquid wobble; particle vertex colour tints
//  _Mode 7 = glowing speed-boost chevron: teal edges -> mint-white arm centre (HDR for bloom), forward light pulse
//  _Mode 1 also races rainbow light streaks along the banks (UV.y = distance / 4 m) and adds a clear-coat reflection.
Shader "BWK/Soft"
{
    Properties
    {
        _Mode ("Mode", Float) = 0
        _ColorA ("Color A", Color) = (1, 1, 1, 1)
        _ColorB ("Color B", Color) = (0.78, 0.8, 1.0, 1)
        _ColorC ("Color C", Color) = (0.55, 0.3, 0.85, 1)
        _ShadowColor ("Shadow Tint", Color) = (0.62, 0.62, 0.95, 1)
        _Smoothness ("Smoothness", Range(0,1)) = 0.35
        _Metallic ("Metallic", Range(0,1)) = 0
        _Wrap ("Wrap", Range(0,1)) = 0.5
        _BumpScale ("Bump Scale", Float) = 6
        _BumpStrength ("Bump Strength", Range(0,2)) = 0.5
        _Stripes ("Stripe Count", Float) = 4
        _StripeWidth ("Stripe Width", Range(0,1)) = 0.35
        _StitchU ("Stitches Around", Float) = 64
        _StitchV ("Stitch Rows", Float) = 26
        _Glow ("Self Glow", Range(0,1)) = 0.1
        _RimPower ("Rim Power", Float) = 3
        _RimStrength ("Rim Strength", Range(0,2)) = 0.35
        _ReflectBoost ("Extra Probe Reflection", Range(0,2)) = 0
        _StreakAmount ("Rail Light Streaks", Range(0,3)) = 0
        _StreakSpeed ("Rail Streak Speed (m/s)", Float) = 6
        _Wobble ("Wobble (m, modes 5/6)", Float) = 0
        _WobbleFreq ("Wobble Frequency", Float) = 3
        _SpecStrength ("Gloss Highlight (modes 5/6)", Range(0,3)) = 1
        _GlintAmount ("Bubble Glints (mode 5)", Range(0,2)) = 0.5
        _FormShade ("S2 p9 sculpted puff shading: upper-left key + sky hemisphere + lilac contact creases (mode 5, 0 = off)", Range(0,1)) = 0
        _HotNear ("Chevron white-hot nearer than (m, mode 7)", Float) = 3.0
        _HotFar ("Chevron turquoise farther than (m, mode 7)", Float) = 3.5
        _HotBoost ("Chevron white-hot extra glow (mode 7)", Range(0,3)) = 0.6
        _MilkAlpha ("Milk opacity facing the camera (mode 6, blended materials)", Range(0,1)) = 1
        _MilkEdgeAlpha ("Milk opacity at thin / grazing edges (mode 6)", Range(0,1)) = 1
        _MilkSoft ("Round-8 rounded milk volume shading (mode 6, 0 = off)", Range(0,1)) = 0
        _MilkThin ("Thin milk edge, lit through by the water (mode 6, _MilkSoft)", Color) = (0.49, 0.75, 0.91, 1)
        _MilkGlass ("S2 p2 thin liquid sheet shading (mode 6, 0 = off)", Range(0,1)) = 0
        _ArrowEdge ("S2 p2 two-tone chevron: HDR edge band (mode 7, 0 = off)", Range(0,4)) = 0
        _ArrowFillAlpha ("S2 p2 two-tone chevron fill opacity (mode 7)", Range(0,1)) = 1
        // blend state (defaults = opaque; round 4: M_FX_Milk renders translucent with SrcAlpha / OneMinusSrcAlpha)
        [HideInInspector] _SrcBlend ("Src Blend", Float) = 1
        [HideInInspector] _DstBlend ("Dst Blend", Float) = 0
        [HideInInspector] _ZWrite ("ZWrite", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _ColorA, _ColorB, _ColorC, _ShadowColor;
            half _Mode, _Smoothness, _Metallic, _Wrap, _BumpScale, _BumpStrength, _Stripes, _StripeWidth;
            half _StitchU, _StitchV, _Glow, _RimPower, _RimStrength;
            half _ReflectBoost, _StreakAmount, _StreakSpeed, _Wobble, _WobbleFreq, _SpecStrength, _GlintAmount;
            half _HotNear, _HotFar, _HotBoost;
            half _MilkAlpha, _MilkEdgeAlpha, _SrcBlend, _DstBlend, _ZWrite;
            half4 _MilkThin;
            half _MilkSoft;
            half _MilkGlass, _ArrowEdge, _ArrowFillAlpha;
            half _FormShade;
        CBUFFER_END
        ENDHLSL
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Blend [_SrcBlend] [_DstBlend]
            ZWrite [_ZWrite]
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                half4 tangentWS : TEXCOORD2;
                float2 uv : TEXCOORD3;
                float3 positionOS : TEXCOORD4;
                half4 color : TEXCOORD5;
                half fog : TEXCOORD6;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                float3 posOS = i.positionOS.xyz;
                if (_Mode > 4.5 && _Wobble > 0.0001)
                {
                    // suds / milk: slow liquid wobble along the normal (world-space noise, so combined meshes and
                    // particles stay coherent); positionOS for the surface patterns stays undisplaced
                    float3 wp = TransformObjectToWorld(posOS);
                    float w = BWK_ValueNoise3(wp * _WobbleFreq + _Time.y * float3(0.35, 0.55, 0.25)) - 0.5;
                    posOS += i.normalOS * w * _Wobble;
                }
                VertexPositionInputs p = GetVertexPositionInputs(posOS);
                VertexNormalInputs n = GetVertexNormalInputs(i.normalOS, i.tangentOS);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = n.normalWS;
                o.tangentWS = half4(n.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.uv = i.uv;
                o.positionOS = i.positionOS.xyz;
                o.color = i.color;
                o.fog = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                half3 v = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half3 bitangent = cross(i.normalWS, i.tangentWS.xyz) * i.tangentWS.w;
                half3 albedo = _ColorA.rgb;
                half smooth = _Smoothness;
                half metallic = _Metallic;
                half occlusion = 1.0;
                half3 emission = 0;

                if (_Mode < 0.5) // foam
                {
                    float3 q = i.positionOS * _BumpScale;
                    float b0 = BWK_ValueNoise3(q);
                    float bx = BWK_ValueNoise3(q + float3(0.15, 0, 0));
                    float by = BWK_ValueNoise3(q + float3(0, 0.15, 0));
                    n = normalize(n - (i.tangentWS.xyz * (bx - b0) + bitangent * (by - b0)) * _BumpStrength * 4.0);
                    half3 light = BWK_WrapLight(i.positionWS, n, _Wrap);
                    half lum = saturate(dot(light, half3(0.3, 0.5, 0.2)));
                    half3 col = lerp(_ShadowColor.rgb, _ColorA.rgb, smoothstep(0.15, 0.9, lum)) * max(lum, 0.55);
                    col += _ColorA.rgb * BWK_Fresnel(n, v, _RimPower) * _RimStrength + _ColorA.rgb * _Glow;
                    col = MixFog(col, i.fog);
                    return half4(col, 1);
                }
                else if (_Mode < 1.5) // rainbow rail
                {
                    float t = i.uv.x;
                    half3 band = t < 0.5 ? lerp(_ColorA.rgb, _ColorB.rgb, smoothstep(0.15, 0.45, t)) : lerp(_ColorB.rgb, _ColorC.rgb, smoothstep(0.55, 0.85, t));
                    albedo = band;
                    emission = band * _Glow;
                    if (_StreakAmount > 0.001)
                    {
                        // rainbow light streaks racing along the bank toward the camera (reference: pink, orange,
                        // yellow and cyan motion lines); along = metres along the track
                        float along = i.uv.y * 4.0 + _Time.y * _StreakSpeed;
                        float r1 = 1.0 - abs(BWK_ValueNoise(float2(t * 7.0, along * 0.05)) * 2.0 - 1.0);
                        float r2 = 1.0 - abs(BWK_ValueNoise(float2(t * 13.0 + 4.0, along * 0.11 + 9.0)) * 2.0 - 1.0);
                        float gate = smoothstep(0.3, 0.75, BWK_ValueNoise(float2(t * 3.0 + 5.0, along * 0.12)));
                        half s = saturate(smoothstep(0.86, 0.985, r1) + smoothstep(0.9, 0.99, r2) * 0.6) * gate;
                        half3 sc = lerp(BWK_Rainbow(t * 0.7 + along * 0.004 + 0.85), half3(1, 1, 1), 0.45);
                        emission += sc * s * _StreakAmount;
                        albedo = lerp(albedo, half3(1, 1, 1), s * 0.25);
                    }
                    if (_ReflectBoost > 0.001)
                    {
                        // clear-coat: crisp probe reflection on top of the candy colour
                        half fr = BWK_Fresnel(n, v, 3.0);
                        emission += GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.05h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS)) * (0.06 + fr * 0.6) * _ReflectBoost;
                    }
                }
                else if (_Mode < 2.5) // knit: vertical rib columns of stacked V stitches (classic ribbed beanie)
                {
                    float sv = i.uv.y * _Stripes;
                    half stripe = step(1.0 - _StripeWidth, frac(sv));
                    albedo = lerp(_ColorA.rgb, _ColorB.rgb, stripe);
                    float colPhase = frac(i.uv.x * _StitchU) - 0.5;          // across one rib (-0.5..0.5)
                    float ribH = cos(colPhase * 3.14159);                    // 1 at the rib crest, 0 in the purl valley
                    float vPhase = frac(i.uv.y * _StitchV + abs(colPhase) * 0.9) - 0.5;   // stacked V stitches
                    float stitch = 1.0 - abs(vPhase) * 2.0;
                    float bump = ribH * (0.7 + 0.3 * stitch);
                    half3 nb = i.tangentWS.xyz * (sin(colPhase * 3.14159) * 0.9) + bitangent * (sign(vPhase) * 0.35 * ribH);
                    n = normalize(n + nb * _BumpStrength);
                    occlusion = lerp(0.42, 1.0, ribH);
                    albedo *= lerp(0.7, 1.08, bump);
                    half fuzz = BWK_Fresnel(n, v, 2.0) * 0.3;
                    emission = albedo * (_Glow + fuzz);
                }
                else if (_Mode < 3.5) // eye
                {
                    // big glossy cartoon eye: deep brown top, warm amber glow toward the bottom, radial fibres,
                    // dark limbal ring and a large soft pupil (the white catchlights are separate geometry)
                    float2 e = i.uv - 0.5;
                    float r = length(e) * 2.0;
                    half low = saturate(0.55 - e.y * 1.5);
                    half3 iris = lerp(_ColorA.rgb, _ColorB.rgb, low * smoothstep(0.2, 0.72, r));
                    float ang = atan2(e.y, e.x);
                    iris *= 0.9 + 0.1 * sin(ang * 23.0 + r * 5.0);
                    iris = lerp(iris, _ColorA.rgb * 0.4, smoothstep(0.8, 0.98, r));
                    iris = lerp(iris, _ColorC.rgb, smoothstep(0.47, 0.4, r));
                    albedo = iris;
                    smooth = 0.98;
                    emission = iris * _Glow + _ColorB.rgb * low * smoothstep(0.45, 0.75, r) * 0.25;
                }
                else if (_Mode < 4.5) // fabric
                {
                    albedo = _ColorA.rgb * (i.color.a > 0.001 ? i.color.rgb : half3(1, 1, 1));
                    float fib = BWK_ValueNoise(i.uv * _BumpScale * 20.0);
                    albedo *= lerp(0.9, 1.05, fib);
                    emission = albedo * _Glow;
                }
                else if (_Mode < 5.5) // soap suds (foam banks)
                {
                    bool hasCol = i.color.a > 0.001;
                    half ao = hasCol ? i.color.r : 1.0h;        // 1 open, 0 deep crevice between puffs
                    half puff = hasCol ? i.color.g : 0.5h;      // per-puff random
                    // fine micro-bubble bump
                    float3 q = i.positionOS * _BumpScale;
                    float b0 = BWK_ValueNoise3(q);
                    float bx = BWK_ValueNoise3(q + float3(0.15, 0, 0));
                    float by = BWK_ValueNoise3(q + float3(0, 0.15, 0));
                    n = normalize(n - (i.tangentWS.xyz * (bx - b0) + bitangent * (by - b0)) * _BumpStrength * 4.0);
#if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE)
                    Light L = GetMainLight(TransformWorldToShadowCoord(i.positionWS));
#else
                    Light L = GetMainLight();
#endif
                    half3 light = BWK_WrapLight(i.positionWS, n, _Wrap);
                    half lum = saturate(dot(light, half3(0.3, 0.5, 0.2)));
                    half occ = lerp(0.35, 1.0, ao);
                    half tone = smoothstep(0.08, 0.8, lum * occ + 0.12);
                    // S2 pass 9 (owner 06:58 + crop 17: "individual rounded foam puffs with lilac / blue shading, gaps, contact
                    // shadows"; s2p9a: the door banks lit flat white from the camera side = one white cloud): a sculpted form
                    // term independent of the scene light - every puff white toward the upper-left studio key and the sky,
                    // lilac-blue on its lower / right half and underside, deep lilac where puffs touch (baked AO)
                    if (_FormShade > 0.001)
                    {
                        half3 fnv = mul((float3x3)UNITY_MATRIX_V, n);
                        half keyF = saturate(dot(fnv, half3(-0.5, 0.62, 0.6)) * 0.62 + 0.42);
                        half hemi = saturate(n.y * 0.5 + 0.5);
                        half form = saturate(keyF * 0.75 + hemi * 0.42 - 0.06);           // p2: mids too dark (p50 #CFBDD0 vs ref #E1D1E1)
                        form = form * form * (3.0 - 2.0 * form);
                        half formT = lerp(0.18, 1.0, form) * lerp(0.4, 1.0, ao * ao);
                        tone = lerp(tone, min(tone, formT), _FormShade);
                    }
                    half3 col = lerp(_ShadowColor.rgb, _ColorA.rgb, tone);
                    col *= lerp(lerp(0.78, 0.7, _FormShade), 1.0, occ);
                    col = lerp(col, _ColorB.rgb, saturate(puff - 0.62) * 0.9);       // a few faintly tinted puffs
                    half fr = BWK_Fresnel(n, v, _RimPower);
                    col += _ColorA.rgb * fr * _RimStrength * occ;                    // translucent bright rims
                    half3 hv = normalize(L.direction + v);
                    half nh = saturate(dot(n, hv));
                    half3 nv = mul((float3x3)UNITY_MATRIX_V, n);
                    half key = saturate(dot(nv, half3(-0.35, 0.62, 0.7)));           // soft studio key from upper left
                    half spec = (pow(nh, 18.0) * 0.22 + pow(nh, 160.0) * 0.9) * L.shadowAttenuation + pow(key, 26.0) * 0.55;
                    col += spec * _SpecStrength * occ;
                    col += GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.3h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS)) * fr * _ReflectBoost * occ;
                    // tiny bubble glints: sparse bright micro-bubbles (3D cells ~3.5 cm, undisplaced object space)
                    float3 gq = i.positionOS * 28.0;
                    float3 gc = floor(gq);
                    float3 gf = frac(gq) - 0.5 - (float3(BWK_Hash31(gc + 1.7), BWK_Hash31(gc + 3.1), BWK_Hash31(gc + 5.3)) - 0.5) * 0.5;
                    half glint = smoothstep(0.17, 0.02, length(gf)) * step(0.72, BWK_Hash31(gc));
                    col += glint * _GlintAmount * (0.3 + pow(key, 4.0) + pow(nh, 8.0)) * occ;
                    col += _ColorA.rgb * _Glow;
                    col = MixFog(col, i.fog);
                    return half4(col, 1);
                }
                else if (_Mode > 6.5) // glowing speed-boost chevron (SM_Chevron strip: U across the arm, V along the V)
                {
                    // reference f_002.00-f_003.25: thick glowing turquoise arrows with crisp edges and a brighter arm
                    // centre; the one right under / behind the mascot blazes white-cyan. U / V are used symmetrically
                    // (abs around 0.5), so the look survives any UV flip.
                    half e = saturate(abs(i.uv.x - 0.5) * 2.0);          // 0 arm centre line .. 1 outer / inner edge
                    half along = saturate(abs(i.uv.y - 0.5) * 2.0);      // 0 apex .. 1 arm ends
                    // round 4 (lead: "thin outlines / hard slabs"; reference f_003.00s: one SOLID glowing arrow, mint-white
                    // top (#BEF6F5) over a turquoise body (#4EC6DD), clean edges): FILLED - a wide mint-white core (_ColorA)
                    // fading to turquoise only in the outer quarter of the arm (_ColorB), a soft deeper-turquoise border,
                    // walls turquoise (no bright outline ring)
                    // round 4 continuation (reference 4K f_03.00s measured: near arm #A6FBF3 .. #CEFAF6 = bright aqua at full
                    // value, edges #7AE3E8 turquoise, bottom arrow #DEFFF7 mint-white; NO dark walls / outlines): HDR aqua fill
                    // (_ColorA, x _Glow*4 -> ~#A6FBF3 after Neutral tonemapping), a gentle turquoise toward the edges
                    // (_ColorB), mint-white near the camera (_ColorC); walls carry the top colour so no edge line shows
                    half core = 1.0 - smoothstep(0.55, 1.0, e);
                    half3 col = lerp(_ColorB.rgb, _ColorA.rgb, 0.45 + 0.55 * core);
                    float pulse = frac(along * 0.8 + _Time.y * _StreakSpeed * 0.5);            // light racing toward the apex
                    half beam = smoothstep(0.0, 0.15, pulse) * smoothstep(0.5, 0.15, pulse);
                    col += _ColorC.rgb * beam * _StreakAmount * (0.3 + 0.7 * core);
                    if (_ArrowEdge > 0.001)
                    {
                        // S2 pass 2 (owner 20:15: ONE clean glowing cyan chevron, "bright cyan edges, two-tone, integrated
                        // into the water - not pale white-cyan blocks"): a saturated turquoise-cyan fill (_ColorA) that lets
                        // the water's ripples and light pool show through (_ArrowFillAlpha), a crisp bright aqua edge band
                        // around every arm (_ColorC x _ArrowEdge: only the edge blooms), the forward light pulse on the
                        // fill; no white-hot block near the camera.
                        half edgeBand = smoothstep(0.6, 0.88, e);
                        half3 fill = _ColorA.rgb * (0.82 + 0.35 * beam * _StreakAmount) + _ColorB.rgb * 0.18 * core;
                        half3 c2 = lerp(fill, _ColorC.rgb * _ArrowEdge, edgeBand);
                        half fr2 = BWK_Fresnel(n, v, 4.0);
                        c2 += GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.05h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS)) * (0.05 + fr2 * 0.4) * _ReflectBoost;
                        c2 *= _Glow * 4.0;
                        return half4(MixFog(c2, i.fog), lerp(_ArrowFillAlpha, 1.0, edgeBand));
                    }
                    // lights up mint-white as it passes under the mascot (the camera rides a fixed distance behind him)
                    half hot = smoothstep(_HotFar, _HotNear, distance(i.positionWS, _WorldSpaceCameraPos));
                    col = lerp(col, _ColorC.rgb, hot * (0.6 + 0.3 * core));
                    half fr = BWK_Fresnel(n, v, 4.0);
                    col += GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.05h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS)) * (0.05 + fr * 0.4) * _ReflectBoost;
                    col *= _Glow * 4.0 * (1.0 + hot * _HotBoost);
                    col = MixFog(col, i.fog);
                    return half4(col, 1);
                }
                else // milk splash (crowns, droplets)
                {
                    half3 tint = i.color.a > 0.001 ? i.color.rgb : half3(1, 1, 1);
#if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE)
                    Light L = GetMainLight(TransformWorldToShadowCoord(i.positionWS));
#else
                    Light L = GetMainLight();
#endif
                    half3 light = BWK_WrapLight(i.positionWS, n, _Wrap);
                    half lum = saturate(dot(light, half3(0.3, 0.5, 0.2)));
                    if (_MilkGlass > 0.001)
                    {
                        // S2 pass 2 (owner 20:15: "THIN, CURVED, PARTLY TRANSLUCENT liquid splash crowns with natural rounded
                        // edges and droplet beads"; judge: our crowns = opaque white plaster, white coverage 25 % vs ref 11 %):
                        // a LIQUID shading model replaces the milk volume. Like a thin water sheet the crown TRANSMITS where it
                        // faces the camera (the turquoise water behind shows through, tinted _MilkThin) and REFLECTS toward
                        // its silhouette (Fresnel: bright white rounded rims, opaque); milky ribs (object-space streak noise
                        // along the rise) keep white cores in the fingers; sharp sun / key glints + a crisp probe reflection
                        // give the wet specular; the alpha follows the same Fresnel + rib mask (see-through centres).
                        half gv = saturate(dot(n, v));
                        half gfr = pow(1.0 - gv, _RimPower);
                        float3 gq = i.positionOS * _BumpScale;
                        half g1 = BWK_ValueNoise3(gq * float3(1.0, 0.4, 1.0) + float3(0.0, _Time.y * 0.5, 0.0));
                        half g2 = BWK_ValueNoise3(gq * 2.3 + 7.1);
                        half rib = saturate((g1 * 0.65 + g2 * 0.35 - 0.5) * 3.2 + 0.45) * saturate(_BumpStrength);
                        half3 film = _MilkThin.rgb * (0.7 + 0.45 * lum);
                        half3 milkC = lerp(_ShadowColor.rgb, _ColorA.rgb, smoothstep(0.0, 0.8, lum + 0.25));
                        // (p1: too glassy vs the reference's milky strands -> _MilkSoft = milk floor in the crowns; droplets stay clear)
                        half body = saturate(rib * 0.85 + gfr * 1.1 + _MilkSoft * 0.14);   // p3: .22 -> .14 (white 16.6 % vs ref 11.2)
                        half3 gcol = lerp(film, milkC, body);
                        half3 gdown = _ColorB.rgb * saturate(-n.y * 0.8 + 0.1) * 0.35;        // turquoise bounce from the water
                        gcol += gdown * (1.0 - body);
                        half3 genv = GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.06h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS));
                        gcol += genv * (0.06 + 0.55 * gfr) * _ReflectBoost;
                        half3 ghv = normalize(L.direction + v);
                        half gnh = saturate(dot(n, ghv));
                        half3 gnv = mul((float3x3)UNITY_MATRIX_V, n);
                        half gkey = saturate(dot(gnv, half3(-0.4, 0.6, 0.69)));
                        gcol += (pow(gnh, 180.0) * 1.8 * L.shadowAttenuation + pow(gkey, 70.0) * 1.3 + pow(gkey, 10.0) * 0.1) * _SpecStrength;
                        half3 gtint = i.color.a > 0.001 ? i.color.rgb : half3(1, 1, 1);
                        gcol = gcol * gtint + _ColorA.rgb * _Glow;
                        half galpha = lerp(_MilkEdgeAlpha, _MilkAlpha, saturate(body * 1.15));
                        galpha = saturate(galpha + saturate(pow(gnh, 180.0) + pow(gkey, 70.0)) * 0.5);   // glints stay visible
                        return half4(MixFog(gcol, i.fog), galpha);
                    }
                    half3 col = lerp(_ShadowColor.rgb, _ColorA.rgb, smoothstep(0.0, 0.7, lum + 0.2));
                    half down = saturate(-dot(n, half3(0, 1, 0)) * 0.8 + 0.1);
                    col = lerp(col, _ColorB.rgb, down * 0.6);                            // cool water bounce from below
                    half fr = BWK_Fresnel(n, v, _RimPower);
                    // grazing edges of the lace strands turn translucent blue (reference: milky cores, light-blue thin parts)
                    col = lerp(col, _ShadowColor.rgb * 0.55 + _ColorB.rgb * 0.45, fr * _RimStrength);
                    half fv = saturate(dot(n, v));
                    half thick = 1.0;
                    if (_MilkSoft > 0.001)
                    {
                        // milk thickness (p2): a broad sheet facing the camera has one normal -> one flat colour. Vary the
                        // film thickness with streaky object-space value noise (stretched along the rise, drifting up), so
                        // thick milky ribs alternate with thin water-lit blue film like the reference's lacy spray
                        // (_BumpScale = ribs per metre, _BumpStrength = amount; both unused by mode 6 otherwise)
                        float3 q = i.positionOS * _BumpScale;
                        half t1 = BWK_ValueNoise3(q * float3(1.0, 0.4, 1.0) + float3(0.0, _Time.y * 0.5, 0.0));
                        half t2 = BWK_ValueNoise3(q * 2.3 + 7.1);
                        thick = saturate((t1 * 0.65 + t2 * 0.35 - 0.5) * 2.6 + 0.72);
                        thick = lerp(1.0, thick, saturate(_BumpStrength) * _MilkSoft);
                        // round 8 (lead: the crowns read as flat opaque white cut-outs in every rear view): ROUNDED milk
                        // volume - the thick cores that face the camera stay creamy white, the body rolls off toward its
                        // silhouette into a cool blue-grey that the turquoise water shines through (thin translucent
                        // edges, alpha below), and only surfaces turning up toward the tunnel light keep a soft bright wet
                        // rim. Measured f_03.00s splash pixels: luma p10/50/90 178/212/230, mean #C5D1E4 (L) / #CAE5EB (R);
                        // ours r8v1 207/216/228 #D5D8D9 = flat grey-white (self glow pushed it past 1.0 -> tonemap clip).
                        half vol = smoothstep(0.0, 0.85, fv);
                        half3 deep = lerp(_ShadowColor.rgb, _MilkThin.rgb, 0.55);
                        half3 soft = lerp(deep, col, vol * vol * (3.0 - 2.0 * vol));
                        half up = saturate(n.y * 0.6 + 0.4);
                        soft += _ColorA.rgb * pow(1.0 - fv, 3.0) * smoothstep(0.55, 0.95, up) * 0.55;
                        soft = lerp(lerp(deep, _MilkThin.rgb, 0.4), soft, thick);           // thin film -> water-lit blue
                        col = lerp(col, soft, _MilkSoft);
                    }
                    half3 hv = normalize(L.direction + v);
                    half nh = saturate(dot(n, hv));
                    half3 nv = mul((float3x3)UNITY_MATRIX_V, n);
                    half key = saturate(dot(nv, half3(-0.4, 0.6, 0.69)));
                    // round 4: soft wet sheen (broad, low) instead of plastic hot spots
                    half spec = pow(nh, 36.0) * L.shadowAttenuation * 0.45 + pow(key, 14.0) * 0.4 + pow(key, 5.0) * 0.08;
                    col += spec * _SpecStrength;
                    col += GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.25h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS)) * (0.03 + fr * 0.35) * _ReflectBoost;
                    col = col * tint + _ColorA.rgb * _Glow;
                    // translucency: opaque milky where the sheet faces the camera, see-through blue at thin / grazing parts
                    half alpha = lerp(_MilkAlpha, _MilkEdgeAlpha, saturate(fr * 1.4));
                    // round 8: soft translucent silhouette band (not a hard paper edge) where the volume shading is on
                    alpha = lerp(alpha, lerp(_MilkEdgeAlpha, _MilkAlpha, smoothstep(0.03, 0.42, fv)) * lerp(0.7, 1.0, thick), _MilkSoft);
                    col = MixFog(col, i.fog);
                    return half4(col, alpha);
                }
                half rim = BWK_Fresnel(n, v, _RimPower) * _RimStrength;
                emission += albedo * rim;
                return BWK_PBR(i.positionWS, i.positionCS, n, v, albedo, metallic, smooth, occlusion, emission, 1.0, i.fog);
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
            #include "BWKShadow.hlsl"
            ENDHLSL
        }
    }
    FallBack Off
}
