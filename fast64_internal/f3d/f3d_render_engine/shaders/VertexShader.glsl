// #version 430

in vec3 position;
in vec3 normal;
in vec4 color;
in vec4 color_alpha;
in vec2 uv;

out vec4 vertex_color;
out vec3 world_normal;
out vec2 texcoord;

uniform mat4 matrix_world;
uniform mat4 mat_view_projection;

uniform f3d_state_vert {
    vec4 light_colors[8];
    vec4 light_directions[8];
    bool g_lighting;
    int padding1;
    int padding2;
    int padding3;
};

void main()
{
    gl_Position = mat_view_projection * matrix_world * vec4(position, 1);
    world_normal = normalize((matrix_world * vec4(normal, 0)).xyz);
    vertex_color = color;
    vertex_color.a = dot(vec3(0.2126729, 0.7151522, 0.0721750), color_alpha.rgb); // luminance calculation
    texcoord = uv;
}
