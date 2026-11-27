// OWNER: Agent 1 (character). Copy of BWK/Soft used by the beanie knit (Mode 2) and the eyes (Mode 3).
// Stylised lit surface for soft, glossy toy-like materials:
//  _Mode 0 = foam: puffy white with soft wrap light, lavender-blue shadows and cloud bump detail
//  _Mode 1 = rainbow rail: glossy candy plastic with rainbow bands across UV.x (around the tube)
//  _Mode 2 = knit: beanie stripes along UV.y with procedural V-stitch knit bumps
//  _Mode 3 = eye: glossy brown iris (radial gradient around the UV centre) with a dark pupil
//  _Mode 4 = fabric: soft cloth (socks, towels) tinted by vertex colour stripes
Shader "BWK/Character"
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
        _PurlDepth ("Knit Purl Depth (0 = v4 look)", Range(0,1)) = 0
        _YarnRelief ("Yarn Relief Knit (0 = previous knit)", Range(0,1.5)) = 0
        _VioletLift ("Fabric: lift violet vertex colours (pom-pom yarn; 1 = off)", Range(0.5, 2.5)) = 1
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _ColorA, _ColorB, _ColorC, _ShadowColor;
            half _Mode, _Smoothness, _Metallic, _Wrap, _BumpScale, _BumpStrength, _Stripes, _StripeWidth;
            half _StitchU, _StitchV, _Glow, _RimPower, _RimStrength, _PurlDepth, _YarnRelief, _VioletLift;
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
                VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
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

            // S2 p10f (SK_Mascot_v5 knit, _YarnRelief > 0): height of a chunky 1x1 rib knit at rib / row phase ph.
            // Knit columns are round bulging ribs of stacked V stitches (two round yarn legs each, meeting in a small groove
            // at the column centre); the purl columns between them are narrow deep valleys.
            float KnitHeight(float2 ph)
            {
                float c = frac(ph.x) - 0.5;                       // -0.5..0.5 across one rib, 0 = rib crest
                float ac = abs(c);
                float rib = saturate(cos(c * 3.14159) * 1.2 - 0.04);
                float r = frac(ph.y - ac * 1.2);                  // V stitch rows: legs slant down toward the column centre
                float leg = sin(r * 3.14159);
                leg = leg * (2.0 - leg);                          // full, round yarn strand across the leg
                float pinch = smoothstep(0.0, 0.09, ac);
                return rib * (0.62 + 0.38 * leg * lerp(0.55, 1.0, pinch));
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
                }
                else if (_Mode < 2.5) // knit: vertical rib columns of stacked V stitches (classic ribbed beanie)
                {
                    float sv = i.uv.y * _Stripes;
                    half stripe = step(1.0 - _StripeWidth, frac(sv));
                    albedo = lerp(_ColorA.rgb, _ColorB.rgb, stripe);
                    if (_YarnRelief > 0.001)
                    {
                        // real yarn relief: the knit height field is sampled 3x (finite differences) and tilts the normal, so
                        // every rib and V-stitch leg shades like a round wool strand; matte wool with a soft grazing sheen
                        float2 ph = float2(i.uv.x * _StitchU, i.uv.y * _StitchV);
                        const float e = 0.04;
                        float h0 = KnitHeight(ph);
                        float gu = (KnitHeight(ph + float2(e, 0)) - h0) / e;   // dH per rib width
                        float gv = (KnitHeight(ph + float2(0, e)) - h0) / e;   // dH per stitch row
                        n = normalize(n - (i.tangentWS.xyz * gu * 0.30 + bitangent * gv * 0.22) * (_BumpStrength * _YarnRelief));
                        float ply = BWK_ValueNoise(float2(ph.x * 7.0, ph.y * 3.0 + ph.x * 2.0));   // plied fibres
                        // wool reads by its relief: rib flanks turned away from the viewer fall off (soft round tubes)
                        half facing = saturate(dot(n, v));
                        albedo *= lerp(0.5, 1.1, h0) * lerp(0.92, 1.05, ply) * lerp(0.6, 1.08, facing * facing);
                        occlusion = lerp(0.45, 1.0, h0);
                        half sheen = pow(1.0 - saturate(dot(n, v)), 3.0) * 0.45 + 0.06;
                        emission = albedo * _Glow + lerp(albedo, half3(1, 1, 1), 0.25) * (sheen * h0 * 0.35);
                        half rimK = BWK_Fresnel(n, v, _RimPower) * _RimStrength;
                        return BWK_PBR(i.positionWS, i.positionCS, n, v, albedo, metallic, smooth, occlusion, emission + albedo * rimK, 1.0, i.fog);
                    }
                    float colPhase = frac(i.uv.x * _StitchU) - 0.5;          // across one rib (-0.5..0.5)
                    float ribH = cos(colPhase * 3.14159);                    // 1 at the rib crest, 0 in the purl valley
                    float vPhase = frac(i.uv.y * _StitchV + abs(colPhase) * 0.9) - 0.5;   // stacked V stitches
                    float stitch = 1.0 - abs(vPhase) * 2.0;
                    // chunky ribs dominate (geometry + this normal); the V stitches inside each rib stay a soft yarn
                    // texture so the knit never reads as a printed chevron pattern
                    float bump = ribH * (0.85 + 0.15 * stitch);
                    half3 nb = i.tangentWS.xyz * (sin(colPhase * 3.14159) * 0.9) + bitangent * (sign(vPhase) * 0.12 * ribH);
                    n = normalize(n + nb * _BumpStrength);
                    occlusion = lerp(0.5, 1.0, ribH);
                    float yarn = BWK_ValueNoise(float2(i.uv.x * _StitchU * 4.0, i.uv.y * _StitchV * 2.0));
                    // _PurlDepth 0 = the v4 knit exactly (0.74-1.06 / 0.94-1.04); 1 = SK_Mascot_v5 materials (S2 p6: reference
                    // knit luminance spread ~3x ours, Lstd 10 vs 3 -> deeper purl valleys 0.58-1.10 / 0.92-1.05)
                    albedo *= lerp(lerp(0.74, 0.58, _PurlDepth), lerp(1.06, 1.1, _PurlDepth), bump)
                            * lerp(lerp(0.94, 0.92, _PurlDepth), lerp(1.04, 1.05, _PurlDepth), yarn);
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
                else // fabric
                {
                    albedo = _ColorA.rgb * (i.color.a > 0.001 ? i.color.rgb : half3(1, 1, 1));
                    // p10f: the v5 pom-pom yarn locks (violet vertex colours) can be lifted without touching the pink toe beans
                    albedo *= lerp(1.0, _VioletLift, saturate((i.color.b - i.color.r) * 4.0) * step(0.001, i.color.a));
                    float fib = BWK_ValueNoise(i.uv * _BumpScale * 20.0);
                    albedo *= lerp(0.9, 1.05, fib);
                    emission = albedo * _Glow;
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
