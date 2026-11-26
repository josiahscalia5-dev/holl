// Purple metallic washing-machine drum wall with a staggered grid of perforations (bevelled rims, dark
// recessed centres with a faint inner glow) and panel seams. Holes are procedural, so the wall mesh stays light.
// UV0.x wraps around the circumference (0..1), UV0.y = distance along the tunnel / _VTile.
Shader "BWK/DrumWall"
{
    Properties
    {
        _BaseColor ("Metal Color", Color) = (0.48, 0.30, 0.82, 1)
        _HighlightColor ("Highlight Color", Color) = (0.78, 0.62, 1.0, 1)
        _HoleColor ("Hole Color", Color) = (0.07, 0.03, 0.16, 1)
        _HoleGlow ("Hole Inner Glow", Color) = (0.45, 0.25, 0.9, 1)
        _Circumference ("Circumference (m)", Float) = 31.4
        _VTile ("Meters per V", Float) = 4
        _HoleSpacing ("Hole Spacing (m)", Float) = 0.42
        _HoleRadius ("Hole Radius (fraction of cell)", Range(0.05, 0.45)) = 0.26
        _Bevel ("Rim Bevel", Range(0, 1)) = 0.6
        _PanelLength ("Panel Length (m)", Float) = 3.0
        _Metallic ("Metallic", Range(0,1)) = 0.75
        _Smoothness ("Smoothness", Range(0,1)) = 0.72
        _Glow ("Self Glow", Range(0,1)) = 0.12
        _HoleBand ("Perforated band (0..1 of circumference, centred on the ceiling)", Range(0,1)) = 1
        _HoleStretch ("Slot elongation around the drum", Range(1, 2.2)) = 1
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor, _HighlightColor, _HoleColor, _HoleGlow;
            float _Circumference, _VTile, _HoleSpacing, _HoleRadius, _Bevel, _PanelLength;
            half _Metallic, _Smoothness, _Glow, _HoleBand, _HoleStretch;
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

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                half4 tangentWS : TEXCOORD2;
                float2 uv : TEXCOORD3;
                half fog : TEXCOORD4;
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
                o.fog = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 m = float2(i.uv.x * _Circumference, i.uv.y * _VTile);
                float2 cell = m / _HoleSpacing;
                float row = floor(cell.y);
                cell.x += fmod(abs(row), 2.0) * 0.5; // staggered rows
                float2 local = frac(cell) - 0.5;
                float dist = length(float2(local.x / _HoleStretch, local.y));   // slots elongated around the drum
                float r = _HoleRadius;
                float aa = fwidth(dist) * 1.5 + 1e-4;

                // Only perforate the band around the ceiling/walls (keeps the floor area under the slide plain).
                float around = abs(frac(i.uv.x) - 0.5) * 2.0;
                float band = step(around, _HoleBand + 1e-3);
                float hole = (1.0 - smoothstep(r - aa, r + aa, dist)) * band;
                float rim = smoothstep(r + 0.12, r, dist) * (1.0 - hole) * band;

                // Panel seams every _PanelLength meters.
                float seamD = abs(frac(m.y / _PanelLength) - 0.5) * 2.0;
                float seam = smoothstep(0.985, 0.995, seamD);

                // Rim bevel normal: push outward from each hole centre.
                half3 bitangent = cross(i.normalWS, i.tangentWS.xyz) * i.tangentWS.w;
                float2 dir = dist > 1e-4 ? local / dist : float2(0, 0);
                half3 n = normalize(i.normalWS + (i.tangentWS.xyz * dir.x + bitangent * dir.y) * rim * _Bevel * 0.9);

                float variation = BWK_Fbm(m * 0.35);
                half3 metal = lerp(_BaseColor.rgb, _HighlightColor.rgb, saturate(variation * 0.6 + rim * 0.5));
                metal *= (1.0 - seam * 0.45);
                half depth = saturate(1.0 - dist / max(r, 1e-3));
                half3 holeCol = lerp(_HoleColor.rgb, _HoleColor.rgb * 0.4, depth);
                half3 albedo = lerp(metal, holeCol, hole);
                half metallic = lerp(_Metallic, 0.0, hole);
                half smooth = lerp(_Smoothness, 0.2, hole);
                half3 emission = metal * _Glow * (1.0 - hole) + _HoleGlow.rgb * hole * (1.0 - depth) * 0.6;

                half3 viewDir = GetWorldSpaceNormalizeViewDir(i.positionWS);
                return BWK_PBR(i.positionWS, i.positionCS, n, viewDir, albedo, metallic, smooth, lerp(1.0, 0.4, hole), emission, 1.0, i.fog);
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
