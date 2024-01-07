// #version 430 /* inserted automatically by blender */

in vec4 vertex_color; // vertex color
in vec3 world_normal;
in vec2 texcoord;

layout (location = 0) out vec4 tscenelit;

// material parameters
uniform sampler2D tbasecolor;
uniform sampler2D tshadowtint;
uniform vec3 col_basecolor;
uniform vec3 col_shadowtint;
uniform int shadingmodel;

uniform f3d_state_frag {
    vec4 test;
};

uniform sampler2D tex0;
uniform sampler2D tex1;

// global parameters
uniform vec4 outline_color;

void main()
{
    tscenelit = vec4(texture(tex0, texcoord).rgb, 1) * vertex_color;
    //tscenelit = vec4(1, 0, 0, 1);
}
