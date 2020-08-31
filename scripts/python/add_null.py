selection = hou.selectedNodes()

if len(selection) != 0:
    selected = selection[0]
    parent = selected.parent().path() + '/'
    selNodeName = selected.name()
    selNodePos = selected.position()  
    
    node = hou.node('/%s' %parent).createNode('null')
    
### Setting node position ###
    node.setPosition(hou.Vector2(selNodePos[0], selNodePos[1]-1))
    node.setInput(0, selected)
    selected.setSelected(False)
    node.setSelected(True)
    
### Setting render and display flags for respective contexts ###
    try:
        node.setDisplayFlag(True)
        node.setRenderFlag(True)
    except:
        node.setDisplayFlag(True)