// Stylised polished gold (rings, coins, pipes, porthole frames). Animated-film look that never goes dark:
// a procedural view-space "matcap" environment (warm sky highlight, yellow body, deep amber under-side and a
// bright horizon band) + real light specular from the key and nearby point lights (warm bulbs) + a hot rim.
// Mobile friendly: no textures, no reflection probe dependency, one pass + shadow caster.
Shader "BWK/Gold"
{
    Properties
    {
        _HighColor ("Highlight", Color) = (1.0, 0.96, 0.78, 1)
        _MidColor ("Body", Color) = (0.98, 0.72, 0.22, 1)
        _LowColor ("Underside", Color) = (0.55, 0.27, 0.06, 1)
        _RimColor ("Rim / bulb glints", Color) = (1.0, 0.82, 0.45, 1)
        _BandColor ("Horizon band", Color) = (1.0, 0.92, 0.6, 1)
        _HighlightSize ("Highlight Size", Range(1, 40)) = 9
        _BandSharpness ("Band Sharpness", Range(1, 60)) = 18
        _SpecPower ("Specular Power", Range(4, 256)) = 64
        _SpecStrength ("Specular Strength", Range(0, 4)) = 1.4
        _Brightness ("Brightness", Range(0, 3)) = 1.0
        _LightInfluence ("Light Influence", Range(0, 1)) = 0.35
        _Emission ("Self Glow", Range(0, 2)) = 0.12
        _FogAmount ("Fog Amount", Range(0, 1)) = 0.7
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _HighColor, _MidColor, _LowColor, _RimColor, _BandColor;
            half _HighlightSize, _BandSharpness, _SpecPower, _SpecStrength, _Brightness, _LightInfluence, _Emission, _FogAmount;
        CBUFFER_END
        ENDHLSL
        Pass
        {
            Name "Forward"
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; half3 normalWS : TEXCOORD1; half fog : TEXCOORD2; UNITY_VERTEX_INPUT_INSTANCE_ID };
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
                return o;
            }
            half4 frag(Varyings i) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                half3 v = GetWorldSpaceNormalizeViewDir(i.positionWS);
                // view-space normal -> procedural matcap
                half3 nv = normalize(mul((float3x3)UNITY_MATRIX_V, (float3)n));
                half t = nv.y * 0.5 + 0.5;
                half3 env = lerp(_LowColor.rgb, _MidColor.rgb, smoothstep(0.08, 0.62, t));
                env = lerp(env, _HighColor.rgb, smoothstep(0.78, 1.0, t) * 0.55);
                half2 hl = nv.xy - half2(-0.38, 0.52);
                env += _HighColor.rgb * exp(-dot(hl, hl) * _HighlightSize) * 1.25;
                half2 hl2 = nv.xy - half2(0.45, 0.3);
                env += _HighColor.rgb * exp(-dot(hl2, hl2) * _HighlightSize * 1.6) * 0.55;
                env += _BandColor.rgb * exp(-abs(nv.y + 0.08) * _BandSharpness) * 0.45;
                half fres = BWK_Fresnel(n, v, 3.0);
                env = lerp(env, _RimColor.rgb * 1.15, fres * 0.55);

            #if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE)
                float4 sc = TransformWorldToShadowCoord(i.positionWS);
            #else
                float4 sc = float4(0, 0, 0, 0);
            #endif
                Light ml = GetMainLight(sc);
                half shadow = lerp(0.6, 1.0, ml.shadowAttenuation);
                half ndl = saturate(dot(n, ml.direction) * 0.5 + 0.5);
                half3 h = normalize(ml.direction + v);
                half spec = pow(saturate(dot(n, h)), _SpecPower) * _SpecStrength;
                half3 col = env * lerp(1.0, (0.55 + 0.6 * ndl) * shadow, _LightInfluence) * _Brightness;
                col += ml.color * spec * shadow * _HighColor.rgb;
            #if defined(_ADDITIONAL_LIGHTS)
                uint count = GetAdditionalLightsCount();
                for (uint li = 0u; li < count; ++li)
                {
                    Light l = GetAdditionalLight(li, i.positionWS);
                    half3 hh = normalize(l.direction + v);
                    half s = pow(saturate(dot(n, hh)), _SpecPower * 0.5) * _SpecStrength;
                    col += l.color * l.distanceAttenuation * (s * _HighColor.rgb + saturate(dot(n, l.direction)) * _MidColor.rgb * 0.25);
                }
            #endif
                col += _MidColor.rgb * _Emission;
                half3 fogged = MixFog(col, i.fog);
                col = lerp(col, fogged, _FogAmount);
                return half4(col, 1);
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
        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On ColorMask R
            HLSLPROGRAM
            #pragma vertex DepthVert
            #pragma fragment DepthFrag
            #pragma multi_compile_instancing
            struct DA { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            float4 DepthVert(DA i) : SV_POSITION { UNITY_SETUP_INSTANCE_ID(i); return TransformObjectToHClip(i.positionOS.xyz); }
            half DepthFrag() : SV_Target { return 0; }
            ENDHLSL
        }
    }
    FallBack Off
}
