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
        CBUFFER_END
        ENDHLSL
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
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
                    half3 col = lerp(_ShadowColor.rgb, _ColorA.rgb, smoothstep(0.08, 0.8, lum * occ + 0.12));
                    col *= lerp(0.78, 1.0, occ);
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
                else if (_Mode > 6.5) // glowing speed-boost chevron (SM_Chevron inner slab, planar UV)
                {
                    // reference f_003.00s: luminous teal glass arrow, mint-white light along the middle of each arm,
                    // deeper teal toward the edges, a soft light pulse racing forward, glossy top reflections.
                    float px = abs(i.uv.x - 0.5) * 1.25;
                    float py = -(i.uv.y - 0.5) * 0.72;
                    float p = dot(float2(px, py + 0.36), float2(0.7198, -0.6942));   // 0 outer edge, -0.31 inner edge
                    half g = saturate(1.0 - abs(p + 0.169) / 0.134);                 // 1 on the arm centre line
                    half core = smoothstep(0.0, 1.0, g);
                    half3 col = lerp(_ColorB.rgb, _ColorA.rgb, core * core);
                    float pulse = frac(py * 0.9 + _Time.y * _StreakSpeed * 0.5);
                    half beam = smoothstep(0.0, 0.18, pulse) * smoothstep(0.55, 0.18, pulse);
                    col += _ColorC.rgb * beam * _StreakAmount * (0.35 + 0.65 * core);
                    half fr = BWK_Fresnel(n, v, 4.0);
                    col += GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.05h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS)) * (0.1 + fr * 0.5) * _ReflectBoost;
                    col *= _Glow * 4.0;
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
                    half3 col = lerp(_ShadowColor.rgb, _ColorA.rgb, smoothstep(0.0, 0.7, lum + 0.2));
                    half down = saturate(-dot(n, half3(0, 1, 0)) * 0.8 + 0.1);
                    col = lerp(col, _ColorB.rgb, down * 0.6);                            // cool water bounce from below
                    half fr = BWK_Fresnel(n, v, _RimPower);
                    // grazing edges of the lace strands turn translucent blue-grey (reference: white cores, cool outlines)
                    col = lerp(col, _ShadowColor.rgb * 0.92 + _ColorB.rgb * 0.12, fr * _RimStrength);
                    half3 hv = normalize(L.direction + v);
                    half nh = saturate(dot(n, hv));
                    half3 nv = mul((float3x3)UNITY_MATRIX_V, n);
                    half key = saturate(dot(nv, half3(-0.4, 0.6, 0.69)));
                    half spec = pow(nh, 90.0) * L.shadowAttenuation * 1.2 + pow(key, 48.0) * 0.9 + pow(key, 8.0) * 0.12;
                    col += spec * _SpecStrength;
                    col += GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 0.12h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS)) * (0.05 + fr * 0.45) * _ReflectBoost;
                    col = col * tint + _ColorA.rgb * _Glow;
                    col = MixFog(col, i.fog);
                    return half4(col, 1);
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
