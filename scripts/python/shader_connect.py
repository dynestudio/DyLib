from types import LambdaType
import hou

# pendings:
# support for other render engines (arnold, octane, vray, 3delight, renderman, mantra?, karma?)

def find_output_mat(parent, vop_builder_name, material_output_name):
    out_node = None
    # find output node
    if parent.type().name() == vop_builder_name:
        childs = parent.children()

        for child in childs:
            if child.type().name() == material_output_name:
                out_node = child
                break

    return out_node

def render_material_out(mat_builder, parent):
    out_node = None
    # iterate between render engines

    # ---------------------------------------------------------------------------------------

    # redshift
    if mat_builder == "redshift_vopnet":
        out_node = find_output_mat(parent, mat_builder, "redshift_material")
    elif mat_builder == "rs_usd_material_builder":
        out_node = find_output_mat(parent, mat_builder, "redshift_usd_material")

    # arnold
    elif mat_builder == "arnold_materialbuilder":
        out_node = find_output_mat(parent, mat_builder, "arnold_material")

    # octane
    elif mat_builder == "octane_vopnet":
        out_node = find_output_mat(parent, mat_builder, "octane_material")

    # 3delight
    elif mat_builder == "3Delight::dlMaterialBuilder":
        out_node = find_output_mat(parent, mat_builder, "3Delight::dlTerminal")

    # vray
    elif mat_builder == "vray_vop_material":
        out_node = find_output_mat(parent, mat_builder, "vray_material_output")

    # renderman
    elif mat_builder == "pxrmaterialbuilder":
        out_node = find_output_mat(parent, mat_builder, "collect")

    # ---------------------------------------------------------------------------------------

    return out_node

def output_connection_type(output_connections):
    out = None
    # supported render engines
    engines = ["redshift_material",
                "redshift_usd_material",
                "arnold_material",
                "octane_material",
                "3Delight::dlTerminal",
                "vray_material_output",
                "collect"]

    for o in output_connections:
        if o.outputNode().type().name() in engines:
            out = o
        if out:
            break

    return out

def input_type(node, out_node, mat_builder):
    index = 0
    # selected node type
    n_type = node.type().name().upper()
    # inputs from output node
    out_input_types = out_node.inputNames()

    for t in out_input_types:
        input_name = t.upper()
        print (input_name)
        print (n_type)
        
        # generic inputs
        if "Displacement".upper() in n_type:
            if "Displacement".upper() in input_name:
                index = out_input_types.index(t) ; break
        elif "Volume".upper() in n_type:
            if "Volume".upper() in input_name:
                index = out_input_types.index(t) ; break

        # octane inputs
        elif "Med".upper() in n_type:
            print ("1")
            if "medium".upper() in input_name:
                print ("2")
                index = out_input_types.index(t) ; break

        # vray inputs
        elif "Displace".upper() in n_type:
            if "Surface".upper() in input_name:
                index = out_input_types.index(t) ; break
        elif "VRayNodePhxShaderFoam".upper() in n_type:
            if "Volume".upper() in input_name:
                index = out_input_types.index(t) ; break
        elif "VRayNodePhxShaderSim".upper() in n_type:
            if "Volume".upper() in input_name:
                index = out_input_types.index(t) ; break

    return index

def shader_out():
    # get selected node
    nodes = hou.selectedNodes()
    if not nodes:
        exit()

    # base parms
    node = nodes[0] ; out_node = None ; index = 0
    mat_builder = node.parent().type().name()
    
    # work only inside VOP nodes
    if node.type().category().name() == "Vop":
        # define output parms
        output_connections = node.outputConnections()

        if output_connections:
            # swap between available outputs
            out = output_connection_type(output_connections)
        
            if out:
                out_node = out.outputNode()
                out_index = out.outputIndex()

                if (out_index + 1) == len(node.outputConnectors()):
                    index = 0
                else:
                    index = out_index + 1

            else:
                out_node = render_material_out(mat_builder, node.parent())
                
        else:
            out_node = render_material_out(mat_builder, node.parent())

        # connect node to output
        if node.outputConnectors():
            if out_node:
                mat_index = input_type(node, out_node, mat_builder)
                out_node.setInput(mat_index, node, index)