

def getIMSResourceForIMSItem(imscp, imsitem):
    if "identifierref" in imsitem.attrs:
        resourceid = imsitem.attrs["identifierref"]
        for resource in imscp.resources:
            if resource.attrs["identifier"] == resourceid:
                return resource

    return None
