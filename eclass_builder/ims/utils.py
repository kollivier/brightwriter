
def getIMSResourceForIMSItem(imscp, imsitem):
    resourceid = imsitem.attrs["identifierref"]
    for resource in imscp.resources:
        if resource.attrs["identifier"] == resourceid:
            return resource
            
    return None
    