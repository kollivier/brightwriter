import bundlebuilder2, os

packageroot = "./"

myapp = bundlebuilder2.AppBuilder(verbosity=1)
myapp.mainprogram = os.path.join(packageroot, "editor.py")
myapp.semi_standalone = 1
myapp.name = "EClass.Builder"
#myapp.includePackages.append("pre")
myapp.includePackages.append("conman")
myapp.includePackages.append("encodings")

myapp.iconfile = os.path.join(os.path.join(packageroot, "icons", "eclass_builder.icns"))

#not detected by bundlebuilder2
#myapp.includePackages.append("math")

#myapp.includePackages.append("_xmlplus")
myapp.resources.append(os.path.join(packageroot, "3rdparty", "mac"))
myapp.resources.append(os.path.join(packageroot, "about"))
myapp.resources.append(os.path.join(packageroot, "autorun"))
myapp.resources.append(os.path.join(packageroot, "convert"))
myapp.resources.append(os.path.join(packageroot, "docs"))
myapp.resources.append(os.path.join(packageroot, "greenstone"))
myapp.resources.append(os.path.join(packageroot, "icons"))
myapp.resources.append(os.path.join(packageroot, "locale"))
myapp.resources.append(os.path.join(packageroot, "license"))
myapp.resources.append(os.path.join(packageroot, "plugins"))
myapp.resources.append(os.path.join(packageroot, "swishe.conf"))
myapp.resources.append(os.path.join(packageroot, "themes"))
#myapp.resources.append(os.path.join(packageroot, "OSATools"))
#myapp.resources.append(os.path.join(packageroot, "templates"))
#myapp.libs.append("/usr/local/lib/libwx_macd-2.4.0.dylib")
#myapp.libs.append("/usr/local/lib/libwx_macd-2.4.0.rsrc")

myapp.setup()
myapp.build()
