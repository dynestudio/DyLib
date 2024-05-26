import hou
import dy_snippets
import sys

#job_path = sys.argv[1]
hip = "HIPPATH"

# Load the .hip file
hou.hipFile.load(hip)

FUNCTION

# Save the .hip file (if needed)
hou.hipFile.save()

# Clear the Houdini session
hou.hipFile.clear()