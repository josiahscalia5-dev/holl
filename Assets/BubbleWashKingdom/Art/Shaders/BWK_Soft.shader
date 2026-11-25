// Stylised lit surface for soft, glossy toy-like materials:
//  _Mode 0 = foam: puffy white with soft wrap light, lavender-blue shadows and cloud bump detail
//  _Mode 1 = rainbow rail: glossy candy plastic with rainbow bands across UV.x (around the tube)
//  _Mode 2 = knit: beanie stripes along UV.y with procedural V-stitch knit bumps
//  _Mode 3 = eye: glossy brown iris (radial gradient around the UV centre) with a dark pupil
//  _Mode 4 = fabric: soft cloth (socks, towels) tinted by vertex colour stripes
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
                else if (_Mode < 2.5) // knit
                {
                    float sv = i.uv.y * _Stripes;
                    half stripe = step(1.0 - _StripeWidth, frac(sv));
                    albedo = lerp(_ColorA.rgb, _ColorB.rgb, stripe);
                    float2 st = float2(i.uv.x * _StitchU, i.uv.y * _StitchV);
                    float2 c = frac(st) - 0.5;
                    float side = c.x < 0.0 ? 1.0 : -1.0;
                    float2 e = float2(c.x + side * 0.25, (c.y + abs(c.x) * 0.6) * 1.4);
                    float d = length(e);
                    float bump = saturate(1.0 - d * 2.6);
                    half3 nb = i.tangentWS.xyz * (-side * 0.6) * bump + bitangent * (-c.y) * bump;
                    n = normalize(n + nb * _BumpStrength);
                    occlusion = lerp(0.55, 1.0, bump);
                    albedo *= lerp(0.8, 1.05, bump);
                    half fuzz = BWK_Fresnel(n, v, 2.0) * 0.25;
                    emission = albedo * (_Glow + fuzz);
                }
                else if (_Mode < 3.5) // eye
                {
                    float r = length(i.uv - 0.5) * 2.0;
                    half3 iris = lerp(_ColorB.rgb, _ColorA.rgb, smoothstep(0.0, 0.85, r));
                    iris = lerp(iris, _ColorC.rgb, smoothstep(0.32, 0.12, r)); // pupil
                    albedo = iris;
                    smooth = 0.97;
                    emission = iris * _Glow;
                }
                else // fabric
                {
                    albedo = _ColorA.rgb * (i.color.a > 0.001 ? i.color.rgb : half3(1, 1, 1));
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
