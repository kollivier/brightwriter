from __future__ import print_function
from builtins import object
import os

class VCard(object):
    def __init__(self):
        self.name = Name()
        self.emails = []
        self.title = Title()
        self.fname = FormattedName()
        self.organization = Organization()
        self.version = "2.1"
        self.filename = ""
        self.otherprops = []

    def parseFile(self, filename):
        self.filename = filename
        infile = open(filename, "r")
        self.parseString(infile.read())
        infile.close()

    def parseString(self, vcardstring):
        lines = vcardstring.split("\r\n")
        inVCard = False

        counter = 0
        filelength = len(lines)
        while counter < filelength:
            #if we're in the VCard, check for the END marker before parsing
            line = lines[counter]

            if inVCard and line.find("END:VCARD") == 0:
                inVCard = False

            #only parse if we're in the VCard
            if inVCard:
                while counter < filelength:
                    if len(lines[counter+1]) == 0:
                        counter = counter + 1
                        continue
                    if (lines[counter+1][0] in [" ", "\t"]): #it's a continuation of a previous line
                        line = line + "\r\n" + lines[counter+1]
                        counter = counter + 1
                    else:
                        break

                if len(lines[counter+1]) == 0:
                    counter = counter + 1
                    continue

                propname = line.split(":")[0].split(";")[0]
                if propname.find(".") != -1:
                    propname = propname.split(".")[1]

                if propname.find("VERSION") == 0:
                    self.version = line.split(":")[1]
                elif propname.find("EMAIL") == 0:
                    self.emails.append(Email(line))
                elif propname.find("FN") == 0:
                    self.fname = FormattedName(line)
                elif propname.find("N") == 0:
                    self.name = Name(line)
                elif propname.find("TITLE") == 0:
                    self.title = Title(line)
                elif propname.find("ORG") == 0:
                    self.organization = Organization(line)
                else:
                    newprop = VCardProp()
                    newprop.parseString(line)
                    self.otherprops.append(newprop)

            #if we're not in the VCard, check for the opening string
            if not inVCard and line.find("BEGIN:VCARD") == 0:
                inVCard = True

            counter = counter + 1

    def saveAsFile(self):
        if self.filename == "":
            print("No filename, can't save to disk.")
            return

        try:
            myfile = open(self.filename, "w")
            myfile.write(self.asString())
            myfile.close()
        except:
            print("Unable to write file %s to disk." % (self.filename))


    def asString(self):
        content = """BEGIN:VCARD\r\n%(props)sEND:VCARD""" % {"props": self.getPropsAsString()}
        return content

    def getPropsAsString(self):
        result = "VERSION:" + self.version + "\r\n"
        result = result + self.name.asVCardString()
        if len(self.emails) > 0:
            for email in self.emails:
                result += email.asVCardString()
        if self.title.value != "":
            result += self.title.asVCardString()
        if self.organization.name != "":
            result += self.organization.asVCardString()
        if self.fname.value != "":
            result += self.fname.asVCardString()
        if len(self.otherprops) > 0:
            for prop in self.otherprops:
                result += prop.asVCardString()

        return result

class VCardProp(object):
    def __init__(self):
        self.propName = ""
        self.props = []
        #for generic properties - we can store them
        #but not edit them
        self.fields = []
        #Any VCard prop may be part of a group
        #so we need to mark that and remember it
        self.groupName = ""

    def parseString(self, text):
        text = self.parseProps(text)
        self.fields = text.split(";")

    def parseProps(self, text):
        propslist = text.split(":", 1)
        proplist = propslist[0].split(";")
        self.propName = proplist[0]
        if self.propName.find(".") != -1:
            self.groupName, self.propName = self.propName.split(".")

        if len(proplist) > 1:
            for prop in proplist[1:]:
                self.props.append(prop)

        return propslist[1]

    def asVCardString(self):
        return self.propsAsString() + ":" + self.fields.join(";") + "\r\n"

    def propsAsString(self):
        result = self.propName
        if len(self.props) > 0:
            for prop in self.props:
                result = result + ";"
                result = result + prop
        if self.groupName != "":
            result = self.groupName + "." + result
        return result

class FormattedName(VCardProp):
    def __init__(self, text=""):
        VCardProp.__init__(self)
        self.value = ""
        self.propName = "FN"

        if text != "":
            self.parseString(text)

    def parseString(self, text):
        text = self.parseProps(text)
        self.value = text

    def asVCardString(self):
        return self.propsAsString() + ":" + self.value + "\r\n"

class Name(VCardProp):
    def __init__(self, text=""):
        VCardProp.__init__(self)
        self.familyName = ""
        self.givenName = ""
        self.middleName = ""
        self.prefix = ""
        self.suffix = ""
        self.propName = "N"

        if text != "":
            self.parseString(text)

    def parseString(self, text):
        text = self.parseProps(text)
        fields = text.split(";")
        if len(fields) >= 1:
            self.familyName = fields[0]
        if len(fields) >= 2:
            self.givenName = fields[1]
        if len(fields) >= 3:
            self.middleName = fields[2]
        if len(fields) >= 4:
            self.prefix = fields[3]
        if len(fields) >= 5:
            self.suffix = fields[4]

    def asVCardString(self):
        return self.propsAsString() + ":" + \
            ";".join([self.familyName, self.givenName, self.middleName, self.prefix, self.suffix]) + "\r\n"

class Email(VCardProp):
    def __init__(self, text=""):
        VCardProp.__init__(self)
        self.value = ""
        self.propName = "EMAIL"

        if text != "":
            self.parseString(text)

    def parseString(self, text):
        text = self.parseProps(text)
        self.value = text

    def asVCardString(self):
        return self.propsAsString() + ":" + self.value + "\r\n"

class Title(VCardProp):
    def __init__(self, text=""):
        VCardProp.__init__(self)
        self.value = ""
        self.propName = "TITLE"

        if text != "":
            self.parseString(text)

    def parseString(self, text):
        text = self.parseProps(text)
        self.value = text

    def asVCardString(self):
        return self.propsAsString() + ":" + self.value + "\r\n"

class Organization(VCardProp):
    def __init__(self, text=""):
        VCardProp.__init__(self)
        self.name = ""
        self.divisions = []
        self.propName = "ORG"

        if text != "":
            self.parseString(text)

    def parseString(self, text):
        text = self.parseProps(text)
        fields = text.split(";")
        self.name = fields[0]
        if len(fields) > 1:
            for field in fields:
                self.divisions.append(field)

    def asVCardString(self):
        result = self.propsAsString() + ":" + self.name
        if len(self.divisions) > 0:
            for div in self.divisions:
                result = result + ";" + div

        return result + "\r\n"

if __name__ == "__main__":
    myvcard = VCard()
    myvcard.parseFile("test.vcf")
    output = open("test2.vcf", "w")
    output.write(myvcard.asString())
    output.close()
