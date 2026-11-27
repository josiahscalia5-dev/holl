// Transparent glass for pipes and porthole windows: light tint, strong fresnel reflections from the reflection
// probe, crisp specular highlight from the main light. _Iridescence adds a soap-bubble thin-film shimmer.
// _Bubble = 1 (soap bubbles only; pipes / windows keep 0): reference f_003.00s bubbles - almost clear centre, thin bright
// rim, swirling thin-film colour patches (pink / cyan / yellow) and soft white "studio window" highlights that sit at a
// fixed place relative to the camera (upper left + a smaller one lower right).
Shader "BWK/Glass"
{
    Properties
    {
        _Tint ("Tint", Color) = (0.75, 0.92, 1.0, 1)
        _Alpha ("Base Opacity", Range(0,1)) = 0.12
        _FresnelPower ("Fresnel Power", Float) = 3
        _Reflectivity ("Reflectivity", Range(0,2)) = 0.9
        _Smoothness ("Smoothness", Range(0,1)) = 0.96
        _Iridescence ("Iridescence", Range(0,1)) = 0
        _IridescenceScale ("Iridescence Scale", Float) = 1.6
        _Glow ("Edge Glow", Range(0,2)) = 0.15
        _Bubble ("Soap Bubble Mode", Range(0,1)) = 0
        _FilmStrength ("Bubble Film Strength", Range(0,2)) = 1
        _WindowStrength ("Bubble Window Highlights", Range(0,3)) = 1.2
        _RimWidth ("Bubble Rim Sharpness", Float) = 5
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _Tint;
            half _Alpha, _FresnelPower, _Reflectivity, _Smoothness, _Iridescence, _IridescenceScale, _Glow;
            half _Bubble, _FilmStrength, _WindowStrength, _RimWidth;
        CBUFFER_END
        ENDHLSL
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Blend One OneMinusSrcAlpha
            ZWrite Off
            Cull Back
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; half3 normalWS : TEXCOORD1; half fog : TEXCOORD2; float3 positionOS : TEXCOORD3; UNITY_VERTEX_INPUT_INSTANCE_ID };
            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(i.normalOS);
                o.fog = ComputeFogFactor(p.positionCS.z);
                o.positionOS = i.positionOS.xyz;
                return o;
            }

            // soft rounded rectangle mask in view-normal space (studio window reflection)
            half WindowMask(half2 p, half2 c, half2 halfSize, half soft)
            {
                half2 d = abs(p - c) - halfSize;
                half dist = length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
                return smoothstep(soft, -soft * 0.5, dist);
            }

            half4 frag(Varyings i) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                half3 v = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half fres = BWK_Fresnel(n, v, _FresnelPower);
                half3 refl = GlossyEnvironmentReflection(reflect(-v, n), i.positionWS, 1.0h - _Smoothness, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS));
                Light l = GetMainLight();
                half3 h = normalize(l.direction + v);
                half spec = pow(saturate(dot(n, h)), 180.0) * 2.5;
                half3 film = BWK_Rainbow(fres * _IridescenceScale + BWK_ValueNoise3(i.positionOS * 3.0 + _Time.y * 0.15) * 0.6);
                half3 tint = lerp(_Tint.rgb, film, _Iridescence);
                half alpha = saturate(_Alpha + fres * 0.75);
                half3 c = tint * _Alpha + refl * _Reflectivity * fres * lerp(1.0, film, _Iridescence) + spec * l.color + tint * fres * _Glow;
                if (_Bubble > 0.5)
                {
                    // reference f_003.00s foreground bubbles: clear glassy beads with a soft, wide, bright WHITE rim, a
                    // faintly milky interior, a round highlight up top and a small crescent bottom-right; only a hint
                    // of thin-film colour (pink / cyan) near the rim.
                    half ndv = saturate(dot(n, v));
                    float3 fp = i.positionOS * 2.2 + float3(0.0, _Time.y * 0.12, _Time.y * 0.05);
                    float thick = BWK_ValueNoise3(fp) * 0.9 + BWK_ValueNoise3(fp * 2.7 + 4.1) * 0.35;
                    half rim = pow(1.0 - ndv, _RimWidth);
                    // round soft highlights fixed relative to the camera (view-space normal)
                    half3 nv = mul((float3x3)UNITY_MATRIX_V, n);
                    half win = smoothstep(0.2, 0.08, length((nv.xy - half2(-0.22, 0.5)) * half2(1.0, 1.35)));
                    win += smoothstep(0.07, 0.02, length(nv.xy - half2(-0.42, 0.3))) * 0.8;
                    win += smoothstep(0.16, 0.06, length((nv.xy - half2(0.45, -0.5)) * half2(1.6, 1.0))) * 0.45;
                    // S2 pass 9 p4 (crop 19 / f_03.00s upper-right bubble: SEVERAL soft studio-window highlights around the
                    // ball - top, left, lower right - not one spot): a soft left window
                    win += smoothstep(0.14, 0.05, length((nv.xy - half2(-0.64, -0.12)) * half2(1.7, 1.0))) * 0.5;
                    win *= step(0.0, nv.z);
                    // warm pink-gold glow low in the film + a faint cyan sheen in the middle (crop 19)
                    half warmSpot = smoothstep(0.26, 0.08, length((nv.xy - half2(0.08, -0.7)) * half2(0.8, 1.6))) * step(0.0, nv.z);
                    half cyanSpot = smoothstep(0.3, 0.05, length(nv.xy - half2(0.12, 0.06))) * step(0.0, nv.z);
                    half haze = (1.0 - rim) * 0.1;                                        // faint milky body
                    // S2 pass 9 (owner 06:58 "transparent iridescent bubbles"; crop 19 + f_03.00s upper-right bubble: saturated
                    // pink / cyan / yellow / violet thin-film swirls, strongest in the outer ring, a clear violet-tinted centre and
                    // a bright pink-white rim; p8a/p9a = grey glass discs with a faint rainbow fringe): real thin-film
                    // interference - the colour cycles 2-3 times with film thickness + viewing angle, its reflectance follows
                    // Fresnel (clear centre, coloured ring), patchy where the film drains
                    half edge = 1.0 - ndv;
                    float opd = thick * 1.5 + edge * 0.85 + 0.2;    // p1: 2.4 / 1.15 read as concentric contour stripes
                    half3 irid = saturate(0.5 + 0.62 * cos(6.2832 * (opd + float3(0.0, 0.36, 0.68))));
                    half filmR = 0.06 + 0.94 * edge * edge;
                    half patchy = 0.3 + 0.7 * smoothstep(0.25, 0.7, BWK_ValueNoise3(fp * 1.1 + 7.3));
                    half3 filmC = irid * filmR * patchy * 1.3 * _FilmStrength;
                    // p4 (p3: rim faint vs the reference's bright pink-white ring): a brighter PINK-WHITE rim band
                    half3 bc = lerp(half3(1.0, 0.86, 0.97), irid, 0.35) * rim * 0.95 + half3(0.85, 0.8, 1.0) * haze
                             + refl * _Reflectivity * (0.05 + rim * 0.4) + _Tint.rgb * _Glow * rim + filmC;
                    bc += half3(1, 1, 1) * (win * _WindowStrength + spec * 0.4);
                    bc += half3(1.0, 0.72, 0.62) * warmSpot * 0.32 * _FilmStrength + half3(0.35, 0.85, 1.0) * cyanSpot * 0.16 * _FilmStrength;
                    half ba = saturate(_Alpha + haze + rim * 0.85 + win * _WindowStrength * 0.8 + dot(filmC, half3(0.3, 0.4, 0.3)) * 0.7
                                       + (warmSpot * 0.2 + cyanSpot * 0.08) * _FilmStrength);
                    c = lerp(c, bc, _Bubble);
                    alpha = lerp(alpha, ba, _Bubble);
                }
                c = MixFog(c, i.fog);
                return half4(c, alpha);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
