import compas_vol
from compas.geometry import *
from compas_vol.primitives import *
from compas_vol.combinations import *

import numpy as np
from compas.geometry import matrix_from_frame
from compas.geometry import matrix_inverse as inverse

### Constants
#primitives id
sphere_id = 100
box_id = 101
torus_id = 102
cylinder_id = 103

#combinations id
union_id = 200
intersection_id = 201
smooth_union_id = 202

#modifications id
shell_id = 300


def  get_obj_name(id):
    if id == union_id:
            return "Union"
    elif id == intersection_id:
            return "Intersection"
    elif id == smooth_union_id:
            return "Smooth Union"
    elif id == sphere_id:
            return "Sphere"
    elif id == box_id:
            return "Box"
    elif id == torus_id:
            return "Torus"   
    elif id == cylinder_id:
            return "Cylinder"     
    elif id == shell_id:
            return "Shell"           
        
identity_matrix =  [[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]

def is_vUnion(input_object):
        return isinstance(input_object, compas_vol.combinations.union.Union)
def is_vIntersection(input_object):
        return isinstance(input_object, compas_vol.combinations.intersection.Intersection)
def is_vSmooth_Union(input_object):
        return isinstance(input_object, compas_vol.combinations.smoothunion.SmoothUnion)
def is_vCOMBINATION(input_object):
        return is_vUnion(input_object) or is_vIntersection(input_object) or is_vSmooth_Union(input_object)


def is_vSphere(input_object):
        return isinstance(input_object, compas_vol.primitives.vsphere.VolSphere)
def is_vBox(input_object):
        return isinstance(input_object, compas_vol.primitives.vbox.VolBox)
def is_vTorus(input_object):
        return isinstance(input_object, compas_vol.primitives.vtorus.VolTorus)
def is_vCylinder(input_object):
        return isinstance(input_object, compas_vol.primitives.vcylinder.VolCylinder)
def is_vPRIMITIVE(input_object):
        return is_vSphere(input_object) or is_vBox(input_object) or is_vTorus(input_object) or is_vCylinder(input_object)


def is_vShell(input_object):
        return isinstance(input_object, compas_vol.modifications.shell.Shell)
def is_vMODIFICATION(input_object):
        return is_vShell(input_object)

############## primitives
class VSphere_data:
        def __init__(self, index, vSphere, parent_index, parent_id, order): ##add parent id 
                self.index = index
                self.id = sphere_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                self.order = order
                self.start_value = 0.
                self.geometry_data = [vSphere.sphere.point.x, vSphere.sphere.point.y, vSphere.sphere.point.z , vSphere.sphere.radius]

class VBox_data:
        def __init__(self, index, vBox, parent_index, parent_id, order): #add parent id 
                self.index = index
                self.id = box_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                self.matrix = inverse(matrix_from_frame(vBox.box.frame)) 
                self.order = order
                self.start_value = 0.
                self.geometry_data = [vBox.box.xsize , vBox.box.ysize , vBox.box.zsize ,  vBox.radius]
                for vec4 in self.matrix:
                        for f in vec4:
                                self.geometry_data.append(f)

class VTorus_data:
        def __init__(self, index, vTorus, parent_index, parent_id, order): #add parent id 
                self.index = index
                self.id = torus_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                frame = Frame.from_plane(vTorus.torus.plane)
                self.matrix = inverse(matrix_from_frame(frame)) 
                self.order = order
                self.start_value = 0.
                self.geometry_data = [vTorus.torus.radius_axis , vTorus.torus.radius_pipe]
                for vec4 in self.matrix:
                        for f in vec4:
                                self.geometry_data.append(f)

class VCylinder_data:
        def __init__(self, index, vCylinder, parent_index, parent_id, order): #add parent id 
                self.index = index
                self.id = cylinder_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                frame = Frame.from_plane(vCylinder.cylinder.plane)
                self.matrix = inverse(matrix_from_frame(frame)) 
                self.order = order
                self.start_value = 0.
                self.geometry_data = [vCylinder.cylinder.height , vCylinder.cylinder.radius]
                for vec4 in self.matrix:
                        for f in vec4:
                                self.geometry_data.append(f)

################### combinations
class VUnion_data:
        def __init__(self, index, vUnion, parent_index, parent_id, order): #add parent id 
                self.index = index
                self.id = union_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                self.order = order
                self.start_value = 1000.
                self.geometry_data = []

class VIntersection_data:
        def __init__(self, index, vIntersection, parent_index, parent_id, order): #add parent id 
                self.index = index
                self.id = intersection_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                self.order = order
                self.start_value = -1000.
                self.geometry_data = []

class VSmooth_Union_data:
        def __init__(self, index, vSmoothUnion, parent_index, parent_id, order): #add parent id 
                self.index = index
                self.id = smooth_union_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                self.order = order
                self.start_value = 1000.
                self.geometry_data = [vSmoothUnion.r]


################### modifications
class VShell_data:
        def __init__(self, index, vShell, parent_index, parent_id, order): #add parent id 
                self.index = index
                self.id = shell_id
                self.parent_index = parent_index
                self.parent_id = parent_id
                self.order = order
                self.start_value = 0.
                self.geometry_data = [vShell.thickness , vShell.side]


###########################################################

class Translator:
        def __init__(self, input_object_):
                self.index_count = 1
                self.input_object = input_object_
                self.objects_unwrapped_list = []

                ##data to be sent to shader
                self.indices = []
                self.ids = []
                self.parent_indices = []
                self.parent_ids = []
                self.object_geometries_data = []
                self.data_count_per_object = []
                self.shader_start_vaues = []

                self.translate_data(self.input_object, 0, union_id, 0) ## starting object, parent id = 0, 0 start_order
                self.create_final_data()
                self.create_shader_start_values()
                self.print_out_all_data(True)

                
        
        def translate_data(self, in_obj, parent_index_, parent_id_, parent_order):
                current_index = self.index_count
                parent_index = parent_index_
                parent_id = parent_id_
                self.index_count += 1

                if is_vPRIMITIVE(in_obj): 
                        if is_vSphere(in_obj):
                                new = VSphere_data(current_index, in_obj, parent_index, parent_id, parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                        elif is_vBox(in_obj):  
                                new = VBox_data(current_index, in_obj, parent_index, parent_id,  parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                        elif is_vTorus(in_obj):
                                new = VTorus_data(current_index, in_obj, parent_index, parent_id,  parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                        elif is_vCylinder(in_obj):
                                new = VCylinder_data(current_index, in_obj, parent_index, parent_id,  parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                        else: 
                                print ("Warning: Unknown primitive")
    
                elif is_vCOMBINATION(in_obj):
                        if is_vUnion(in_obj):
                                new = VUnion_data(current_index, in_obj, parent_index, parent_id,  parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                                for o in in_obj.objs:
                                        self.translate_data(o, current_index, union_id,  parent_order +1)
                        elif is_vIntersection(in_obj):
                                new = VIntersection_data(current_index, in_obj, parent_index, parent_id,  parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                                for o in in_obj.objs:
                                        self.translate_data(o, current_index, intersection_id, parent_order +1)
                        elif is_vSmooth_Union(in_obj):
                                new = VSmooth_Union_data(current_index, in_obj, parent_index, parent_id,  parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                                objects = [in_obj.a , in_obj.b]
                                for o in objects:
                                        self.translate_data(o, current_index, smooth_union_id, parent_order +1)

                elif is_vMODIFICATION(in_obj):
                        if is_vShell(in_obj):
                                new = VShell_data(current_index, in_obj, parent_index, parent_id,  parent_order + 1)
                                self.objects_unwrapped_list.append(new) 
                                self.translate_data(in_obj.o, current_index, shell_id, parent_order +1)
                        else: 
                                print ("Warning: Unknown combination mathod")
                                self.translate_data(o, current_index, smooth_union_id, parent_order +1)
                                
                else: 
                        print ("Warning: Unknown SOMETHING")


        def create_final_data(self):
                self.objects_unwrapped_list.reverse() ## reverse list of objects
                print ("List of objects reversed")

                for obj in self.objects_unwrapped_list:

                        self.indices.append(obj.index)                ###########///// append index 
                        self.ids.append(obj.id)                       ###########///// append id 
                        self.parent_indices.append(obj.parent_index)  ###########///// append parent_index   
                        self.parent_ids.append(obj.parent_id)         ###########///// append parent_id       
                        
                        current_obj_data_array = obj.geometry_data  
                        for f in current_obj_data_array:
                                f_rounded = round(f, 2)
                                self.object_geometries_data.append(f_rounded)          ###########///// append geometry data 

                        self.data_count_per_object.append(len(current_obj_data_array)) ###########///// append count 
                        


        def print_out_all_data(self, print_data_per_object):
                if print_data_per_object:
                        # print (len(self.indices), len(self.ids), len(self.parent_indices), len(self.parent_ids), len(self.data_count_per_object), len(self.object_geometries_data))
                        # print (len(self.shader_start_vaues))
                        pos = 0
                        for i in range(len(self.indices)):
                                print ("")
                                print ("index : ", self.indices[i] , ",    id : ", get_obj_name(self.ids[i]), ",    parent_index : ", self.parent_indices[i], ",    parent_id : " , get_obj_name(self.parent_ids[i]))
                                count_data = self.data_count_per_object[i]
                                print ("data_count : ", count_data)
                                print ("geometry_data : ", self.object_geometries_data[pos : pos+count_data])
                                pos += count_data

                else: 
                        print ("")
                        print ("indices : ", self.indices)
                        print ("ids : ", [get_obj_name(id) for id in self.ids])
                        print ("parent_indices : ", self.parent_indices)
                        print ("parent_ids : ", [get_obj_name(id) for id in self.parent_ids])
                        print ("")
                        print ("data_count_per_object : ", self.data_count_per_object)
                        print ("object_geometries_data : ", self.object_geometries_data)

        def create_shader_start_values(self):
                values = []
                self.shader_start_vaues.append(1000.)
                self.objects_unwrapped_list.reverse()
                for obj in self.objects_unwrapped_list:
                        self.shader_start_vaues.append(obj.start_value) ###########///// append start value  

                print ("")
                print ("shader_start_vaues : " , self.shader_start_vaues)
