def switch(kwargs):
    hda = kwargs['node']

    # get hda data
    parms_len = hda.evalParm('switch_parms')
    value = hda.evalParm('switch')
    switch = hda.parm('switch').menuItems()[value]

    # set data in parm nodes
    for i in range(parms_len):
        # get node data
        node = hou.node(hda.parm("node_" + str(i+1)).eval())
        parm_name = hda.parm("parm_" + str(i+1)).eval()
        parm_value = hda.parm(switch + "_" + str(i+1)).eval()

        # set node quality
        if node:
            if parm_name:
                if parm_value:
                    node.parm(parm_name).set(parm_value)