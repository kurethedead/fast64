VERTEX_SHADER = open("shaders/VertexShader.glsl").read()
PIXEL_SHADER = open("shaders/FallbackPixelShader.glsl").read()

VERTEX_2D = """
    in vec2 pos;
    out vec2 uv;

    void main()
    {
        uv = pos;
        gl_Position = vec4(pos * 2 - 1, 0, 1);
    }
"""

PIXEL_2D = """
    uniform sampler2D image;
    uniform sampler2D depth;
    in vec2 uv;
    out vec4 color;

    void main()
    {
        color = finalize_color(texture(image, uv));
        gl_FragDepth = texture(depth, uv).x;
    }
"""

PIXEL_RGBL = """
    uniform sampler2D image;
    in vec2 uv;
    out vec4 color;

    void main()
    {
        color = texture(image, uv);
        color.a = dot(color.rgb, vec3(0.3, 0.59, 0.11));
    }
"""

PIXEL_FXAA = """
    uniform sampler2D image;
    uniform sampler2D depth;
    in vec2 uv;
    out vec4 color;

    uniform vec2 invScreenSize;

    FXAA_HEADER

    void main()
    {
    #if USE_FXAA
        color = FxaaPixelShader(
            uv,
            vec4(0.0),
            image,
            image,
            image,
            invScreenSize,
            vec4(0.0),
            vec4(0.0),
            vec4(0.0),
            0.5,
            0.125,
            0.0312,
            0.0,
            0.0,
            0.0,
            vec4(0.0));
    #else
        color = texture(image, uv);
    #endif
        color.a = 1;
        gl_FragDepth = texture(depth, uv).x;
    }
"""

PIXEL_DEFERRED_WORLDPOS = """
    uniform sampler2D image; // unused
    uniform sampler2D depth;
    in vec2 uv;
    out vec4 color;
    //uniform mat4 mat_view;
    //uniform mat4 mat_projection;
    uniform mat4 mat_view_projection;

    vec3 ScreenToWorldPos()
    {
        vec4 pos;
        pos.w = 1;
        pos.xy = uv * 2 - 1;
        pos.z = texture(depth, uv).r * 2 - 1;
        pos = inverse(mat_view_projection) * pos;
        pos /= pos.w;
        return pos.xyz;
    }

    void main()
    {
        vec3 pos = ScreenToWorldPos();
        color = vec4(fract(pos), 1);
        gl_FragDepth = texture(depth, uv).x;
    }
"""

PIXEL_SHADINGMODEL = """
    uniform usampler2D image;
    in vec2 uv;
    out vec4 color;

    void main()
    {
        uint shadingmodel = texture(image, uv).r;
        switch (shadingmodel)
        {
            case SHADINGMODEL_UNLIT:
                color = vec4(0, 0, 0, 1);
                break;
            case SHADINGMODEL_LAMBERT:
                color = vec4(1, 0, 0, 1);
                break;
            case SHADINGMODEL_TOON:
                color = vec4(0, 1, 0, 1);
                break;
            default:
                color = vec4(1, 1, 1, 1);
                break;
        }
    }
"""

# PIXEL_AVG = """
#     uniform sampler2D image;
#     uniform sampler2D depth;
#     uniform ivec2 view_size;
#     uniform ivec2 buffer_size;

#     in vec2 uv;

#     out vec4 color;

#     void main()
#     {
#         vec4 tex = texture(image, uv);
#         if (length(view_size) < length(buffer_size))
#         {
#             int count = 0;
#             vec4 acc = vec4(0);
#             ivec2 scale = view_size / buffer_size;
#             ivec2 ipos = ivec2(round(uv * buffer_size));
#             ivec2 end = ipos + scale;
#             for (; ipos.x <= end.x; ++ipos.x)
#             {
#                 for (; ipos.y <= end.y; ++ipos.y)
#                 {
#                     vec4 texel = texelFetch(image, ipos, 0);
#                     acc += texel;
#                     ++count;
#                 }
#             }
#             acc /= count;
#             tex = acc;
#         }
#         color = tex;
#     }
# """

PIXEL_SCENE_LIGHTING = """
    uniform sampler2D tbasecolor;
    uniform usampler2D tshadingmodel;
    in vec2 uv;

    out vec4 color;

    uniform vec4 scene_color;

    void main()
    {
        vec4 tex = texture(tbasecolor, uv);
        uint shadingmodel = texture(tshadingmodel, uv).r;
        if (shadingmodel != SHADINGMODEL_UNLIT)
        {
            color.rgb = (tex.rgb * scene_color.rgb);
        }
        else
        {
        #if BACKGROUND_COLOR
            color.rgb = mix(tex.rgb, scene_color.rgb, 1 - tex.a);
        #else
            color.rgb = mix(tex.rgb, vec3(.05), 1 - tex.a);
        #endif
        }
        color.a = 1;
    }
"""
