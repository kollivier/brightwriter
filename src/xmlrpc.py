import xmlrpclib

def getEClassXMLRPCServer():
    return xmlrpclib.Server('http://www.eclass.net/xmlrpc-server.php')
