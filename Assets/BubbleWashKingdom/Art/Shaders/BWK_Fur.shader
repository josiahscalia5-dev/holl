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
    }
    SubShader
    {
        Tags { "RenderType"="TransparentCutout" "RenderPipeline"="UniversalPipeline" "Queue"="AlphaTest" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        TEXTURE2D(_NoiseTex); SAMPLER(sampler_NoiseTex);
        CBUFFER_START(UnityPerMaterial)
            half4 _RootColor, _BaseColor, _TipColor, _RimColor;
            float4 _NoiseTex_ST;
            float _Density, _FurLength, _Gravity, _Thinning, _ClumpScale, _RimPower;
            half _ClumpAmount, _Wrap, _RimStrength, _AO, _Glow, _UseVertexTint, _StaticMode;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Cull Back
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
                float3 nWS = TransformObjectToWorldNormal(i.normalOS);
                float3 posWS = TransformObjectToWorld(i.positionOS.xyz);
                posWS += nWS * (h * _FurLength * mask);
                posWS.y -= h * h * _Gravity * mask;
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
                float2 uv = i.uv * _Density;
                half strand = SAMPLE_TEXTURE2D(_NoiseTex, sampler_NoiseTex, uv).r;
                half clump = BWK_ValueNoise(i.uv * _ClumpScale);
                strand = saturate(strand * lerp(1.0, clump * 1.6, _ClumpAmount));
                if (h > 0.001) clip(strand - pow(h, 0.8) * _Thinning);

                half3 tint = lerp(half3(1, 1, 1), i.color.rgb, _UseVertexTint * step(0.001, i.color.a));
                half3 col = h < 0.5 ? lerp(_RootColor.rgb, _BaseColor.rgb, saturate(h * 2.0 + 0.55)) : lerp(_BaseColor.rgb, _TipColor.rgb, h * 2.0 - 1.0);
                col *= tint * lerp(0.85, 1.12, strand);

                half3 n = normalize(i.normalWS);
                half3 v = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half3 light = BWK_WrapLight(i.positionWS, n, _Wrap);
                half ao = lerp(1.0 - _AO, 1.0, h);
                half rim = BWK_Fresnel(n, v, _RimPower) * _RimStrength * (0.4 + 0.6 * h);
                half3 c = col * light * ao + _RimColor.rgb * rim * light + col * _Glow;
                c = MixFog(c, i.fog);
                return half4(c, 1);
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
