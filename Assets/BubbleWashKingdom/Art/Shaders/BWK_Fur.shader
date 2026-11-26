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
            half _ClumpAmount, _Wrap, _RimStrength, _AO, _Glow, _UseVertexTint, _StaticMode, _Curl, _Underfur, _EdgeSoft, _SilhouetteFade;
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
                float2 suv = float2(i.uv.x * 2.0, i.uv.y) * _Density;   // UV.x unit = 2x UV.y unit in metres -> square cells
                float2 cell = floor(suv);
                float2 jit = float2(BWK_Hash21(cell), BWK_Hash21(cell + 17.3)) - 0.5;
                float2 lean = (float2(BWK_Hash21(cell + 5.7), BWK_Hash21(cell + 9.1)) - 0.5) * 0.8 * h;
                float d = length(frac(suv) - 0.5 - jit * 0.4 - lean);
                half rnd = BWK_Hash21(cell + 3.1);
                half clump = BWK_ValueNoise(float2(i.uv.x * 2.0, i.uv.y) * _ClumpScale);
                half lenVar = lerp(1.0, 0.55 + clump * 0.9, _ClumpAmount) * (0.72 + 0.28 * rnd);
                half guard = saturate(1.0 - d * 1.75) * lenVar;
                float2 suv2 = float2(i.uv.x * 2.0, i.uv.y) * _Density * 1.85 + 3.7;
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
                    alpha = saturate(edge / _EdgeSoft + 0.5);
                    half ndv = saturate(dot(n, v));
                    alpha *= lerp(1.0, saturate(ndv * 2.5 + 0.15), _SilhouetteFade * h);
                    clip(alpha - 0.02);
                }

                // coat selector: vertex alpha 1 = pink coat, 0 = cream paw coat (blend = lighter paw tips); rgb = tint
                half3 pinkC = h < 0.5 ? lerp(_RootColor.rgb, _BaseColor.rgb, saturate(h * 2.0 + 0.55)) : lerp(_BaseColor.rgb, _TipColor.rgb, h * 2.0 - 1.0);
                half3 pawC = lerp(_PawRootColor.rgb, _PawTipColor.rgb, saturate(h * 1.4 + 0.2));
                half coat = lerp(1.0, i.color.a, _UseVertexTint);
                half3 col = lerp(pawC, pinkC, coat) * lerp(half3(1, 1, 1), i.color.rgb, _UseVertexTint);
                col *= lerp(0.86, 1.06, strand);   // low strand contrast: plush, not needles
                half3 light = BWK_WrapLight(i.positionWS, n, _Wrap);
                half ao = lerp(1.0 - _AO, 1.0, h);
                half rim = BWK_Fresnel(n, v, _RimPower) * _RimStrength * (0.4 + 0.6 * h);
                half3 c = col * light * ao + _RimColor.rgb * rim * light + col * _Glow;
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
