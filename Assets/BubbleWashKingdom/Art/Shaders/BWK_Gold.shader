// Stylised polished jewellery gold (rings, coins, pipes, porthole frames); with a violet palette it also drives the gems.
// Animated-film look that never goes dark:
//  * a procedural "studio" environment looked up with the VIEW-SPACE REFLECTION vector (sphere-map style), so even the
//    flat front face of a ring gets a deep-amber -> bright-yellow gradient across the screen instead of one flat colour;
//  * the real reflection probe (violet tunnel, warm bulbs) blended in, partly gold-tinted, for soft coloured reflections;
//  * crisp key-light highlight + sharp warm glints from nearby point lights (ring bulbs) + a hot fresnel rim;
//  * optional object-space sparkle (gems, coins) that twinkles as the item spins.
// Mobile friendly: no textures, one forward pass + shadow caster + depth.
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
        _SpecPower ("Specular Power", Range(4, 512)) = 64
        _SpecStrength ("Specular Strength", Range(0, 6)) = 1.4
        _Brightness ("Brightness", Range(0, 3)) = 1.0
        _LightInfluence ("Light Influence", Range(0, 1)) = 0.35
        _Emission ("Self Glow", Range(0, 2)) = 0.12
        _FogAmount ("Fog Amount", Range(0, 1)) = 0.7
        _Contrast ("Body Contrast", Range(0.5, 3)) = 1
        _ViewGradient ("View-dependent gradient (flat faces)", Range(0, 1)) = 0
        _EnvReflect ("Probe Reflection", Range(0, 2)) = 0
        _EnvTint ("Probe Reflection Gold Tint", Range(0, 1)) = 0.6
        _EnvRoughness ("Probe Reflection Roughness", Range(0, 1)) = 0.3
        _GlintStrength ("Point Light Glints", Range(0, 8)) = 1
        _Sparkle ("Sparkle", Range(0, 6)) = 0
        _SparkleScale ("Sparkle Cells per Unit", Float) = 18
        _StreakStrength ("Studio Streak Strength", Range(0, 3)) = 0
        _StreakHeight ("Studio Streak Height (view-space y)", Range(-1, 1)) = 0.6
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _HighColor, _MidColor, _LowColor, _RimColor, _BandColor;
            half _HighlightSize, _BandSharpness, _SpecPower, _SpecStrength, _Brightness, _LightInfluence, _Emission, _FogAmount;
            half _Contrast, _ViewGradient, _EnvReflect, _EnvTint, _EnvRoughness, _GlintStrength, _Sparkle, _SparkleScale;
            half _StreakStrength, _StreakHeight;
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
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings
            {
                float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; half3 normalWS : TEXCOORD1; half fog : TEXCOORD2;
                float3 positionOS : TEXCOORD3; half3 normalOS : TEXCOORD4; UNITY_VERTEX_INPUT_INSTANCE_ID
            };
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
                o.normalOS = i.normalOS;
                return o;
            }

            // procedural studio environment for a view-space direction (x right, y up, z toward the camera)
            half3 GoldStudio(half3 d, half fres)
            {
                half t = d.y * 0.5 + 0.5;
                half body = smoothstep(0.08, 0.62, t);
                body = saturate((body - 0.5) * _Contrast + 0.5);
                half3 env = lerp(_LowColor.rgb, _MidColor.rgb, body);
                env = lerp(env, _HighColor.rgb, smoothstep(0.78, 1.0, t) * 0.55);
                half2 hl = d.xy - half2(-0.38, 0.52);
                env += _HighColor.rgb * exp(-dot(hl, hl) * _HighlightSize) * 1.25;
                half2 hl2 = d.xy - half2(0.45, 0.3);
                env += _HighColor.rgb * exp(-dot(hl2, hl2) * _HighlightSize * 1.6) * 0.55;
                env += _BandColor.rgb * exp(-abs(d.y + 0.08) * _BandSharpness) * 0.45;
                // long soft-box streaks (polished-jewellery look): a bright strip above and a thinner one below the horizon,
                // stretched across the whole width, so curved ring tubes get a crisp white-gold specular line along them
                env += _HighColor.rgb * (exp(-abs(d.y - _StreakHeight) * 22.0) + 0.45 * exp(-abs(d.y + _StreakHeight * 0.55) * 30.0)) * _StreakStrength;
                return lerp(env, _RimColor.rgb * 1.15, fres * 0.55);
            }

            half4 frag(Varyings i) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                half3 v = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half fres = BWK_Fresnel(n, v, 3.0);
                // view-space normal (classic matcap) and the sphere-map direction of the view-space reflection vector:
                // identical on curved parts, but the reflection version varies across flat faces with perspective.
                half3 nv = normalize(mul((float3x3)UNITY_MATRIX_V, (float3)n));
                half3 rWS = reflect(-v, n);
                half3 rv = normalize(mul((float3x3)UNITY_MATRIX_V, (float3)rWS));
                half3 sm = normalize(rv + half3(0, 0, 1));
                half3 d = normalize(lerp(nv, sm, _ViewGradient));
                half3 env = GoldStudio(d, fres);

                // real reflection probe: the violet tunnel and warm bulbs, partly tinted by the gold body colour
                float2 suv = GetNormalizedScreenSpaceUV(i.positionCS);
                half3 probe = GlossyEnvironmentReflection(rWS, i.positionWS, _EnvRoughness, 1.0h, suv);
                half3 probeTinted = lerp(probe, probe * _MidColor.rgb * 1.5, _EnvTint);
                env = env * (1.0 - 0.3 * saturate(_EnvReflect)) + probeTinted * _EnvReflect * (0.6 + 0.4 * fres);

            #if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE)
                float4 sc = TransformWorldToShadowCoord(i.positionWS);
            #else
                float4 sc = float4(0, 0, 0, 0);
            #endif
                Light ml = GetMainLight(sc);
                half shadow = lerp(0.6, 1.0, ml.shadowAttenuation);
                half ndl = saturate(dot(n, ml.direction) * 0.5 + 0.5);
                half3 h = normalize(ml.direction + v);
                half nh = saturate(dot(n, h));
                half spec = pow(nh, _SpecPower) * _SpecStrength + pow(nh, _SpecPower * 0.15) * _SpecStrength * 0.12;
                half3 col = env * lerp(1.0, (0.55 + 0.6 * ndl) * shadow, _LightInfluence) * _Brightness;
                col += ml.color * spec * shadow * _HighColor.rgb;
            #if defined(_ADDITIONAL_LIGHTS)
                uint count = GetAdditionalLightsCount();
                for (uint li = 0u; li < count; ++li)
                {
                    Light l = GetAdditionalLight(li, i.positionWS);
                    half3 hh = normalize(l.direction + v);
                    half nhh = saturate(dot(n, hh));
                    half glint = pow(nhh, _SpecPower * 0.8) * _SpecStrength * _GlintStrength + pow(nhh, 12.0) * 0.15;
                    col += l.color * l.distanceAttenuation * (glint * _HighColor.rgb + saturate(dot(n, l.direction)) * _MidColor.rgb * 0.25);
                }
            #endif
                // object-space sparkle: random facet directions per cell that flash when they line up with the viewer
                if (_Sparkle > 0.001)
                {
                    float3 cell = floor(i.positionOS * _SparkleScale);
                    float3 rnd = float3(BWK_Hash31(cell), BWK_Hash31(cell + 11.3), BWK_Hash31(cell + 23.7)) * 2.0 - 1.0;
                    half3 sdir = normalize(TransformObjectToWorldDir(normalize(rnd + i.normalOS * 1.2), false));
                    half flash = pow(saturate(dot(sdir, normalize(v + ml.direction * 0.35))), 90.0);
                    col += _HighColor.rgb * flash * _Sparkle;
                }
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
