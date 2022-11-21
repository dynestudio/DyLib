if int(hou.getenv("DYLIB_DEFAULT_SCENE_MERGE")) == 1:
    hou.hipFile.merge(hou.getenv("DYLIB_DEFAULT_SCENE_PATH"))