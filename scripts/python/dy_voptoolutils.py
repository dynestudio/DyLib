import hou
import dy_toolutils

def createMaskedMtlXSubnet(network_node, name, mask, folder_label):
    subnet_node = network_node.createNode('subnet')
    subnet_node.setName(name,True)

    parms = subnet_node.parmTemplateGroup()
    pt = hou.properties.parmTemplate('op','tabmenumask')
    pt.setDefaultValue([mask])
    if folder_label:
        subnet_folder = hou.FolderParmTemplate('folder1', folder_label,
                                               folder_type=hou.folderType.Collapsible)
        subnet_folder.addParmTemplate(pt)
        parms.append(subnet_folder)
    else:
        parms.append(pt)
    subnet_node.setParmTemplateGroup(parms)

    subnet_node.node("suboutput1").destroy()
    in_node = subnet_node.node("subinput1")
    in_node.setName("inputs")

    surface_node = subnet_node.createNode('mtlxstandard_surface','mtlxstandard_surface')
    displacement_node = subnet_node.createNode('mtlxdisplacement','mtlxdisplacement')

    surface_output = subnet_node.createNode('subnetconnector','surface_output')
    surface_output.setParms({'parmname':'surface',
                            'parmlabel':'Surface',
                            'parmtype':24,
                            'connectorkind':1,
                            'useasparmdefiner':0})
    surface_output.setColor(hou.Color((0.89,0.69,0.6)))

    displacement_output = subnet_node.createNode('subnetconnector','displacement_output')
    displacement_output.setParms({'parmname':'displacement',
                                 'parmlabel':'Displacement',
                                 'parmtype':25,
                                 'connectorkind':1,
                                 'useasparmdefiner':0})
    displacement_output.setColor(hou.Color((0.6,0.69,0.89)))

    surface_output.setInput(0,surface_node,0)
    displacement_output.setInput(0,displacement_node,0)

    surface_node.setPosition(hou.Vector2((-2.35, 0.0376)))
    surface_output.setPosition(hou.Vector2((2.5236, 0.0376)))
    in_node.setPosition(hou.Vector2((2.5236, 1.75)))
    displacement_node.setPosition(hou.Vector2((-0.288306, -9.5)))
    displacement_output.setPosition(hou.Vector2((2.5236, -2.04122)))

    subnet_node.setMaterialFlag(True)

    return subnet_node

def createOctaneSubnet(network_node, name, mask, folder_label):
    subnet_node = network_node.createNode('subnet')
    subnet_node.setName(name,True)

    parms = subnet_node.parmTemplateGroup()
    pt = hou.properties.parmTemplate('op','tabmenumask')
    pt.setDefaultValue([mask])
    if folder_label:
        subnet_folder = hou.FolderParmTemplate('folder1', folder_label,
                                               folder_type=hou.folderType.Collapsible)
        subnet_folder.addParmTemplate(pt)
        parms.append(subnet_folder)
    else:
        parms.append(pt)
    subnet_node.setParmTemplateGroup(parms)

    subnet_node.node("suboutput1").destroy()
    subnet_node.node("subinput1").destroy()

    surface_node = subnet_node.createNode('octane::NT_MAT_STANDARD_SURFACE')
    surface_builder_output = subnet_node.createNode('octane_material')

    surface_output = subnet_node.createNode('subnetconnector','surface_output')
    surface_output.setParms({'parmname':'surface',
                            'parmlabel':'Surface',
                            'parmtype':24,
                            'connectorkind':1,
                            'useasparmdefiner':0})
    surface_output.setColor(hou.Color((0.89,0.69,0.6)))

    surface_builder_output.setInput(0,surface_node,0)
    surface_output.setInput(0,surface_builder_output,0)

    surface_node.setPosition(hou.Vector2((-2.35, 0.0376)))
    surface_builder_output.setPosition(hou.Vector2((0, 0.0376)))
    surface_output.setPosition(hou.Vector2((2.5236, 0.0376)))

    subnet_node.setMaterialFlag(True)

    return subnet_node

def createBuilderSurface(network_node, name, builder_name, surface_name, out_name):
    builder = network_node.createNode(builder_name)
    builder.setName(name,True)

    surface_node = builder.createNode(surface_name)
    output_node = hou.node(builder.path() + '/' + out_name)

    surface_node.setPosition(dy_toolutils.pos_vec2(output_node.position()[0] - 3, output_node.position()[1]))

    output_node.setInput(0,surface_node,0)

    return builder

def collect_delegates():
    network_node = dy_toolutils.current_context()

    # network editor
    network_editor = dy_toolutils.active_network_editor()
    if not network_editor:
        exit()
    initial_pos = network_editor.cursorPosition()

    # get config data
    delegates = ['Arnold', 'Karma MtlX Subnet', 'MDL OmniSurface', 'MtlX Subnet', 'Octane', 'Redshift', 'Renderman','USD Preview Surface', 'Vray']

    dlg = hou.ui.selectFromList(delegates, exclusive=False, message=None, title='Collect Delegates', column_header='Delegates', num_visible_rows=5)

    # continue if dlg has one input
    if not dlg:
        exit()

    # mats creations
    net_types = ['mat', 'matnet', 'materiallibrary', 'editmaterial']

    if network_node.type().name() in net_types:
        # collect node
        collect = None

        sel = hou.selectedNodes()
        if sel:
            if sel[0].type().name() == 'collect':
                collect = sel[0]

        if not collect:
            collect = network_node.createNode('collect')
            collect.setName('collect_', True)
            collect.setPosition(initial_pos)
            collect.setCurrent(True, clear_all_selected=True)

        # initial position
        pos_x = initial_pos[0] - 3
        pos_y = initial_pos[1]
        pos = dy_toolutils.pos_vec2(pos_x, pos_y)

        # create mat nodes
        for selected_delegate in dlg:
            delegate = delegates[selected_delegate]
            matbuilder = None ; engine_name = None

            # detect engine
            # usd preview surface
            if delegate == 'USD Preview Surface':
                matbuilder = 'usdpreviewsurface'
                engine_name = 'usd_'

            # karma mtlx subnet
            elif delegate == 'Karma MtlX Subnet':
                KARMAMTLX_TAB_MASK = "MaterialX parameter collect subnet null subnetconnector karma USD"
                engine_name = 'karma_'
                folder_label='Karma MaterialX Subnet'
                mat = createMaskedMtlXSubnet(network_node, engine_name, KARMAMTLX_TAB_MASK, folder_label)
                mat.setPosition(pos)
                mat.setCurrent(True, clear_all_selected=False)
                # update pos
                pos_y -= mat.size()[1] + 1
                pos = dy_toolutils.pos_vec2(pos_x, pos_y)
                # nodes connections
                collect.setNextInput(mat)
                continue

            # material x
            elif delegate == 'MtlX Subnet':
                MTLX_TAB_MASK = "MaterialX parameter collect subnet null subnetconnector"
                engine_name = 'mtlx_'
                folder_label='MaterialX Subnet'
                mat = createMaskedMtlXSubnet(network_node, engine_name, MTLX_TAB_MASK, folder_label)
                mat.setPosition(pos)
                mat.setCurrent(True, clear_all_selected=False)
                # update pos
                pos_y -= mat.size()[1] + 1
                pos = dy_toolutils.pos_vec2(pos_x, pos_y)
                # nodes connections
                collect.setNextInput(mat)
                continue

            # redshift
            elif delegate =='Redshift':
                matbuilder = 'rs_usd_material_builder'
                engine_name = 'rs_'

            # arnold
            elif delegate =='Arnold':
                engine_name = 'ai_'
                mat = createBuilderSurface(network_node, engine_name, 'arnold_materialbuilder', 'arnold::standard_surface', 'OUT_material')
                mat.setPosition(pos)
                mat.setCurrent(True, clear_all_selected=False)
                # update pos
                pos_y -= mat.size()[1] + 1
                pos = dy_toolutils.pos_vec2(pos_x, pos_y)
                # nodes connections
                collect.setNextInput(mat)
                continue

            # vray
            elif delegate =='Vray':
                matbuilder = 'vray_vop_material'
                engine_name = 'vray_'

            # octane
            elif delegate =='Octane':
                # matbuilder = 'octane_vopnet'
                OCT_TAB_MASK = "Octane"
                engine_name = 'oct_'
                folder_label='Octane Subnet'
                mat = createOctaneSubnet(network_node, engine_name, OCT_TAB_MASK, folder_label)
                mat.setPosition(pos)
                mat.setCurrent(True, clear_all_selected=False)
                # update pos
                pos_y -= mat.size()[1] + 1
                pos = dy_toolutils.pos_vec2(pos_x, pos_y)
                # nodes connections
                collect.setNextInput(mat)
                continue

            # mdl omnisurface
            elif delegate == 'MDL OmniSurface':
                matbuilder = 'mdlomnisurface'
                engine_name = 'mdl_'

            # renderman
            elif delegate == 'Renderman':
                engine_name = 'pxr_'
                mat = createBuilderSurface(network_node, engine_name, 'pxrmaterialbuilder', 'pxrsurface', 'output_collect')
                mat.setPosition(pos)
                mat.setCurrent(True, clear_all_selected=False)
                # update pos
                pos_y -= mat.size()[1] + 1
                pos = dy_toolutils.pos_vec2(pos_x, pos_y)
                # nodes connections
                collect.setNextInput(mat)
                continue

            # pass iteration
            else:
                continue

            # builder ops
            mat = network_node.createNode(matbuilder)
            mat.setName(engine_name, True)
            mat.setPosition(pos)
            mat.setCurrent(True, clear_all_selected=False)
            
            pos_y -= mat.size()[1] + 1
            pos = dy_toolutils.pos_vec2(pos_x, pos_y)

            # nodes connections
            collect.setNextInput(mat)