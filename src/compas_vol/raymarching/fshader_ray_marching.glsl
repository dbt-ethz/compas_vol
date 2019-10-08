#version 120

#define max_num 150 // CAREFUL, MEMORY LIMITED
#define v_data_max_num 50

///---------------------------------------------------------------- INPUTS
uniform vec2 u_resolution;
uniform vec3 camera_POS;
uniform float osg_FrameTime;

//v_data
uniform vec4[max_num] v_data;
// uniform int v_data_length;
uniform float[max_num] v_start_values;
uniform float[v_data_max_num] v_data_count_per_object;

uniform float y_slice;
uniform int vv;
uniform float slider_value;


///---------------------------------------------------------------- SDF FUNCTIONS (from compas-vol)
///// PRIMITIVES 
#define VolSphere_id 100
#define VolBox_id 101
#define VolTorus_id 102
#define VolCylinder_id 103

float random (vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233)))* 43758.5453123);
}

vec3 animate_point(in int current_index){
    float magnitude = random (vec2(current_index))  * 7.+ 1.;
    float frequency1 = random (vec2(current_index/3.56))  * 0.45  + 0.1;
    float offset  = random (vec2(current_index/3.56))  * 6.;
    float frequency = frequency1 * slider_value;
    // frequency *=  slider_value;
    return vec3(sin(osg_FrameTime * frequency) * magnitude, cos(offset +osg_FrameTime * frequency) * magnitude, sin(offset + osg_FrameTime * frequency) * magnitude);
}


float VolPrimitive(in vec3 p, in int id, in int current_index, in mat4 matrix, in vec4 size_xyzw){ //current_index only needed for 
    //VolSphere
    if (id == VolSphere_id){
        vec3 center = size_xyzw.xyz;
        center = center + animate_point(current_index) ;
        float radius = size_xyzw.w;
        return length(p - center) - radius;
    //VolBox
    }else if (id == VolBox_id){
        float radius= size_xyzw.w;
        vec4 pos_transformed =  transpose(matrix) * vec4(p , 1.);
        vec3 d = abs(pos_transformed.xyz) - (size_xyzw.xyz * 0.5 - radius);
        return length(max(d, 0.0)) - radius + min(max(d.x,max(d.y,d.z)), 0.0);
    //VolTorus
    }else if (id == VolTorus_id){
        float center_radius = size_xyzw.x;
        float section_radius = size_xyzw.y;
        vec4 pos_transformed = transpose(matrix)  * vec4(p , 1.);
        float dxy = length(pos_transformed.xy);
        float d2 = sqrt((dxy - center_radius)*(dxy - center_radius) + pos_transformed.z*pos_transformed.z );
        return d2 - section_radius;
    //VolCylinder
    }else if (id == VolCylinder_id){
        float h = size_xyzw.x;
        float r = size_xyzw.y;
        vec4 pos_transformed = transpose(matrix) * vec4(p , 1.);
        float d = length(pos_transformed.xy) - r;
        return max(d, abs(pos_transformed.z) - h/2.);
    } else {
        return 0.;
    }
}


float yPlane(vec3 p, float y_of_plane){
    return -(p.y - y_of_plane);
}

///// COMBINATIONS
#define Union_id 200
#define Intersection_id 201
#define Smooth_Union_id 202

float VolCombination(in float a, in float b, in float id, in float r){
    //Union
    if (id == Union_id){
        return min(a , b);
    //Intersection
    } else if (id == Intersection_id){
        return max(a , b);
    //Smooth Union
    } else if (id == Smooth_Union_id){
        float h = min(max(0.5 + 0.5 * (b - a) / r, 0), 1);
        return (b * (1 - h) + h * a) - r * h * (1 - h);
    } else {
        return 0. ;
    }
}

///// MODIFICATIONS
#define Shell_id 300

//// ---- Shell
float Shell_get_distance( in float current_dist,  in float d,in float s){ // torus centered in origin. t: vec2(rad of center of torus, rad of section of torus)
    return abs(current_dist + (s - 0.5) * d) - d/2.0;
}


/////////////////////////////////////////////////////////////
float[max_num] values; 
float dist_final;
float dist;
int current_index;
int current_id;
int parent_index; 
int parent_id;
mat4 matrix;
vec4 size_xyzw;
vec4 parent_details_xyzw = vec4(0.); // only needed for a few combinations

float GetDistance(vec3 p){ //union of shapes  
    values = v_start_values;

    for (int i = 0; i < len(v_data) -1; i+= 6){ 
        //---- get data
        current_index = int( v_data[i][0]);
        current_id = int( v_data[i][1]);
        parent_index = int( v_data[i][2] );
        parent_id = int( v_data[i][3]);
        matrix = mat4(v_data[i+1], v_data[i+2], v_data[i+3], v_data[i+4]);
        size_xyzw = vec4(v_data[i+5]);

        //---- update parent_details_xyzw only when needed 
        if (parent_id == Smooth_Union_id){ // or other combination types that need it 
            int pos = int(v_data[0][0]) - parent_index;
            parent_details_xyzw = v_data[pos*6 +5];
        }

        /////------------------- Get dist of CURRENT obj
        //primitive
        if (current_id == VolSphere_id || current_id == VolBox_id || current_id == VolTorus_id || current_id == VolCylinder_id){
            dist = VolPrimitive(p, current_id, current_index, matrix, size_xyzw);
            values[current_index] = dist;
        //combination
        } else if (current_id == Union_id || current_id ==  Intersection_id ||current_id ==  Smooth_Union_id ){
            dist = values[current_index];
        //modification
        } else if(current_id == Shell_id){ // Shell
            dist = Shell_get_distance(values[current_index] , size_xyzw.x, size_xyzw.y);
            values[current_index] = dist;  
        }

        /////------------------- send information to PARENT
        // combination
        if (parent_id == Union_id || parent_id ==  Intersection_id ||parent_id ==  Smooth_Union_id ){
            values[parent_index] = VolCombination(values[parent_index], dist, parent_id, parent_details_xyzw.x);  
        // modification
        } else if (parent_id == Shell_id){
            values[parent_index] = values[current_index]; 
        }

        /////------------------- break loop once the necessary values have been calculated
        if (current_index == vv || current_index == 0 ){
            dist_final = values[vv];

            // intersect wih slicing plane !!!!!!!!!!!!!!!HERE THIS SHOULD HAPPEN ONLY IF SLICING PLANE EXISTS
            float y_slice_plane_dist = yPlane(p, y_slice);
            return max(dist_final, y_slice_plane_dist);

            return dist_final;
        }
    }  
}


int total_steps = 0;

#define MAX_STEPS 300
#define MAX_DIST 300.
#define SURF_DIST 0.01
float RayMarch(vec3 ro, vec3 rd){ // ray origin, ray direction
    float dO = 0.; // distance from origin

    for (int i = 0;  i< MAX_STEPS; i++){
        vec3 p = ro + rd * dO;
        float dS = GetDistance(p); // Get distance scene
        dO += dS;
        total_steps += 1;
        if (dO> MAX_DIST || dS < SURF_DIST) break;
    }
    return dO;
}

vec3 GetNormal(vec3 p){
    float d = GetDistance(p);
    //evaluate distance of points around p
    vec2 e = vec2(.01 , 0); // very small vector
    vec3 n = d - vec3(GetDistance(p-e.xyy), // e.xyy = vec3(.01,0,0)
                      GetDistance(p-e.yxy),
                      GetDistance(p-e.yyx));
    return normalize(n);
}

float GetLight (vec3 p){ //gets the position of intersection of ray with shape
    vec3 LightPos = vec3(0 , 5, 6);
    // LightPos.xz += vec2( sin(u_time) , cos(u_time));

    vec3 l = normalize(LightPos - p); // vector from light source to position
    vec3 n = GetNormal(p);
    float dif = clamp(dot(n, l)  , 0., 1.);

    //compute shadows
    float d = RayMarch(p+n * SURF_DIST,l);
    if(d<length(LightPos -p)){
        dif *= .3;
    }
    return dif;
}

// float GetSunLight (vec3 p, vec3 normal){ //gets the position of intersection of ray with shape
//     vec3 LightPos = vec3(5 , -5, 16);
//     vec3 l = normalize(LightPos - p); // vector from light source to position
//     return clamp(dot(normal, l)  , 0., 1.);
//     // //compute shadows
//     // float d = RayMarch(p+n * SURF_DIST,l);
//     // if(d<length(LightPos -p)){
//     //     dif *= .3;
//     // }
// }

// float GetSkyLight (vec3 p, vec3 normal){
//     vec3 sunPos = vec3(0.,10.,0.);
//     return clamp(dot(normal, sunPos), 0., 1.);
// }


//////// ------------------ Find Ray Direction
uniform mat4 trans_clip_to_model;
uniform mat4 p3d_ViewProjectionMatrixInverse;

vec3 findRayDirection(in vec2 uv, in vec3 ro){
    vec4 pixel_world_coords =  trans_clip_to_model * vec4(uv.x, uv.y, 1., 1.);
    vec3 rd = pixel_world_coords.xyz;
    return normalize(rd);
}






void main(){  
    vec2 st = gl_FragCoord.xy / u_resolution.xy;
    vec2 uv = 2*(st - vec2(0.5, 0.5));
    
    vec3 ro = camera_POS; // ray origin = camera position (world coordinates)
    vec3 rd = findRayDirection(uv, ro);

    float d = RayMarch(ro, rd);
    vec3 p  = ro + rd * d; // position of intersection of ray with solid

    float alpha = 1.0;
    if (d > 200 ){
        alpha = 0.;
    } else {
        alpha = 1.;
    }

    vec3 normal = GetNormal(p);

    vec3 color = normal;
    // color section white
    if (abs(p.y - y_slice) < 0.1) {
        color = vec3(1.);  // so that section becomes white
    }
    gl_FragColor = vec4 (color, alpha);
}





