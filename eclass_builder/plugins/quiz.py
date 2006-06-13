from wxPython.wx import *
import string
import os
#import conman.conman as conman
#import conman
import locale
import re
from conman.validate import *
from conman.HTMLFunctions import *
import plugins
from conman.file_functions import *
from StringIO import StringIO
import utils 

USE_MINIDOM=0
try:
	from xml.dom.ext.reader.Sax import FromXmlFile
except:
	USE_MINIDOM=1

if USE_MINIDOM:
	from xml.dom import minidom

from threading import *
import traceback
#from xml.dom.minidom import parse

import errors
log = errors.appErrorLog

#-------------------------- PLUGIN REGISTRATION ---------------------
# This info is used so that EClass can be dynamically be added into
# EClass.Builder's plugin registry.

plugin_info = {	"Name":"quiz", 
				"FullName":"Quiz", 
				"Directory":"EClass", 
				"Extension":["quiz"], 
				"Mime Type": "",
				"Requires":"",
				"CanCreateNew":True}

#-------------------------- DATA CLASSES ----------------------------

EVT_RESULT_ID = wxNewId()

def EVT_RESULT(win, func):
	win.Connect(-1, -1, EVT_RESULT_ID, func)

# base type that makes sure all data is converted to Unicode


class QuizPage(plugins.PluginData):
	"""
	Class: quiz.QuizPage()
	Last Updated: 12/26/02
	Description: This class manages the Quiz data structure.

	Attributes:
	- window: GUI window to send status messages to
	- filename: fully qualified filename, including path, of currently open Quiz
	- directory: directory in which the currently open Quiz is located
	- name: name of the currently open Quiz
	- items: a list of quiz items

	Methods:
	- LoadPage(filename)
	- LoadDoc(document)
	- SaveAsXML(filename)
	- WriteDoc(document)
	"""

	def __init__(self, window=None):
		plugins.PluginData.__init__(self)
		self.window = window
		self.filename = ""
		self.directory = ""
		self.name = ""
		self.autograded = True
		self.profemail = ""
		self.items = []

	def LoadPage(self, filename):
		"""
		Function: LoadPage(filename)
		Last Updated: 12/26/02
		Description: Loads an Quiz file in XML format

		Arguments:
		- filename: fully qualified filename, including directory, of the XML file to load
		
		Return values:
		Returns an empty string if successful, or an error string if failed.

		"""
		self.filename = filename
		self.directory = os.path.split(filename)[0]
		if USE_MINIDOM:
			doc = minidom.parse(utils.openFile(filename))	
		else:
			doc = FromXmlFile(filename)
		self.LoadDoc(doc)
		#except:
		#	raise RuntimeError, `sys.exc_value.args`
		return ""

	def LoadDoc(self, doc):
		"""
		Function: LoadDoc(doc)
		Last Updated: 12/26/02
		Description: Loads the Quiz from an XML string.

		Arguments: 
		- doc: an XML string containing the Quiz to load

		Return values:
		None
		"""

		if doc.attributes:

			for i in range(0, len(doc.attributes)):
				attr = doc.attributes.item(i)

				if attr.name == "ident":

					self.id = attr.value

		items = doc.getElementsByTagName("item")
		#print "number of items = " + len(items)
		if len(items) > 0:
			for item in items:
				self._GetItem(item)

		print `len(self.items)`
		

	def _GetItem(self, root):
		myitem = QuizItem()

		for i in range(0, len(root.attributes)):
			attr = root.attributes.item(i)
			if attr.name == "ident":
				myitem.id = XMLAttrToText(attr.value)

		#get presentation element
		presentation = root.getElementsByTagName("presentation")
		if len(presentation) > 0:
			myitem.presentation.label = ""
			for i in range(0, len(presentation[0].attributes)):
				attr = presentation[0].attributes.item(i)
				if attr.name == "label":
					myitem.presentation.label = XMLAttrToText(attr.value)
			
			if len(presentation[0].childNodes) > 0:
				mattext = presentation[0].getElementsByTagName("mattext")
				if len(mattext) > 0:
					myitem.presentation.text = XMLCharToText(mattext[0].childNodes[0].nodeValue)
				else:
					myitem.presentation.text = ""

			response_lid = presentation[0].getElementsByTagName("response_lid")
			if len(response_lid) > 0:
				myitem.presentation.lidid = ""
				for i in range(0, len(response_lid[0].attributes)):
					attr = response_lid[0].attributes.item(i)
					if attr.name == "ident":
						myitem.presentation.lidid = XMLAttrToText(attr.value)

				choices = response_lid[0].getElementsByTagName("response_label")
				if len(choices) > 0:
					for i in range(0, len(choices)):
						newchoice = QuizItemChoice()
						if len(choices[i].attributes) > 0:
							for j in range(0, len(choices[i].attributes)):
								attr = choices[i].attributes.item(j)
								if attr.name == "ident":
									newchoice.id = XMLAttrToText(attr.value)

						text = choices[i].getElementsByTagName("mattext")
						if len(text) > 0:
							newchoice.text = XMLCharToText(text[0].childNodes[0].nodeValue)

						myitem.presentation.choices.append(newchoice)
		
		#get evaluation criteria
		conditions = root.getElementsByTagName("respcondition")
		for i in range(0, len(conditions)):
			newcondition = QuizItemCondition()
			for j in range(0, len(conditions[i].attributes)):
				attr = conditions[i].attributes.item(j)
				if attr.name == "title":
					newcondition.title = XMLAttrToText(attr.value)

			varequal = conditions[i].getElementsByTagName("varequal")
			if len(varequal) > 0:
				for k in range(0, len(varequal)):
					var = varequal[k]
					newvar = QuizItemVariable()
		
					if var.parentNode.nodeName == "not":
						newvar.condition = "not equal"

					for j in range(0, len(var.attributes)):
						attr = var.attributes.item(j)
						if attr.name == "respident":
							newvar.itemid = XMLAttrToText(attr.value)

					newvar.value = XMLCharToText(var.childNodes[0].nodeValue)
					newcondition.variables.append(newvar)
			
			setvar = conditions[i].getElementsByTagName("setvar")
			if len(setvar) > 0:
				newcondition.var = XMLCharToText(setvar[0].childNodes[0].nodeValue)

			feedback = conditions[i].getElementsByTagName("displayfeedback")
			if len(feedback) > 0:
				for j in range(0, len(feedback[0].attributes)):
					attr = feedback[0].attributes.item(j)
					if attr.name == "feedbacktype":
						newcondition.feedbacktype = XMLAttrToText(attr.value)
					elif attr.name == "linkrefid":
						newcondition.feedbackid = XMLAttrToText(attr.value)

			myitem.conditions.append(newcondition)

		#get feedback information			
		feedback = root.getElementsByTagName("itemfeedback")
		for i in range(0, len(feedback)):
			newfeedback = QuizItemFeedback()
			for j in range(0, len(feedback[i].attributes)):
				attr = feedback[i].attributes.item(j)
				if attr.name == "ident":
					newfeedback.id = XMLAttrToText(attr.value)
				elif attr.name == "view":
					newfeedback.view = XMLAttrToText(attr.value)

			feedbacktext = feedback[i].getElementsByTagName("mattext")
			if len(feedbacktext) > 0:
				newfeedback.text = XMLCharToText(feedbacktext[0].childNodes[0].nodeValue)
			
			myitem.feedback.append(newfeedback)
		self.items.append(myitem)

		

	def SaveAsXML(self, filename="", encoding="ISO-8859-1"):
		"""
		Function: SaveAsXML(filename)
		Last Updated: 9/24/02
		Description: Saves the Quiz to an XML file.

		Arguments:
		- filename: filename, including directory, of the XML file to save - if no value given, defaults to the filename used when loading the page

		Return values:
		Returns an error string if failed, or an empty string if successful.
		"""
		if filename == "":
			filename = self.filename
		else:
			self.filename = filename

		try:
			myxml = """<?xml version="1.0"?>%s""" % (self.WriteDoc())
		except:
			message = _("There was an error updating the file %(filename)s. Please check to make sure you did not enter any invalid characters (i.e. Russian, Chinese/Japanese, Arabic) and try updating again.") % {"filename":filename}
			global log
			log.write(message)
			raise IOError, message
		try:
			import types
			if type(myxml) != types.UnicodeType:
				import locale
				encoding = locale.getdefaultlocale()[1]
				myxml = unicode(myxml, encoding)
			
			myxml = myxml.encode("utf-8")
			
			myfile = utils.openFile(filename, "w")
			myfile.write(myxml)
			myfile.close()
		except:
			global log
			message = utils.getStdErrorMessage("IOError", {"type":"write", "filename": filename})
			log.write(message)
			raise IOError(message)

		return ""

	def WriteDoc(self):
		"""
		Function: WriteDoc()
		Last Updated: 12/27/02
		Description: Writes the Quiz into XML format.

		Arguments:
		None

		Return values:
		None
		"""

		myxml = """
<questestinterop>
	%s %s
</questestinterop>
""" % (self._MetadataAsXML(), self._ItemsAsXML())	
		return myxml


	def _MetadataAsXML(self):
		metastr = ""
		if not self.autograded:
			metastr = """
			<metadata>
				<eclass:profemail>%s</eclass:profemail>
			</metadata>
			
			"""
		return metastr

	def _ItemsAsXML(self):
		itemstr = ""
		counter = 1
		for item in self.items:
			if item.id == "":
				item.id = "Q" + `counter` 
			
			itemstr = itemstr + """
		<item ident="%s">
			<presentation label="%s">
				<material>
				<mattext>%s</mattext>
				</material>
				%s
			</presentation>
			<resprocessing>
				<outcomes><decvar/></outcomes>
				%s
			</resprocessing>
			%s
		</item>
		""" % (TextToXMLAttr(item.id), TextToXMLAttr(item.presentation.label), TextToXMLAttr(item.presentation.text), self._ChoicesAsXML(item), self._ConditionsAsXML(item), self._FeedbackAsXML(item))
			counter = counter + 1
		return itemstr

	def _ChoicesAsXML(self, item):
		retval = """
				<response_lid ident="%s" rcardinality="Single" rtiming="No">
					<render_choice>""" % (TextToXMLAttr(item.presentation.lidid))
		for choice in item.presentation.choices:
			retval = retval + """
						<response_label ident="%s">
							<material><mattext>%s</mattext></material>
						</response_label>
			""" % (TextToXMLAttr(choice.id), TextToXMLChar(choice.text))

		retval = retval + """
					</render_choice>
				</response_lid>
		""" 
		return retval

	def _ConditionsAsXML(self, item):
		retval = ""
		for condition in item.conditions:
			retval = retval + """
				<respcondition title="%s">
					<conditionvar>""" % (TextToXMLAttr(condition.title))
			
			for var in condition.variables:
				if var.condition == "equal":
					retval = retval + """<varequal respident="%s">%s</varequal>""" % (var.itemid, var.value)
				else:
					retval = retval + """<not><varequal respident="%s">%s</varequal></not>""" % (var.itemid, var.value)

			retval = retval + """		
					</conditionvar>
					<setvar action="Set">%s</setvar>
					<displayfeedback feedbacktype="%s" linkrefid="%s"/>
				</respcondition>
				""" % (TextToXMLChar(condition.var), TextToXMLAttr(condition.feedbacktype), TextToXMLAttr(condition.feedbackid))

		return retval

	def _FeedbackAsXML(self, item):
		retval = ""
		for feedback in item.feedback:
			retval = retval + """
				<itemfeedback ident="%s" view="%s">
					<material><mattext>%s</mattext></material>
				</itemfeedback>
			""" % (TextToXMLAttr(feedback.id), TextToXMLAttr(feedback.view), TextToXMLChar(feedback.text))

		return retval

class QuizItem (plugins.PluginData):
	"""
	Class: quiz.QuizItem()
	Last Updated: 12/26/02
	Description: This class contains the methods and attributes for dealing with quiz items.

	Attributes:
	- name: name of the hotword
	- presentation: contains information on how to display a quiz item
	- processing: contains information on how to grade the quiz item
	- feedback: contains feedback to be displayed based upon the answers given 

	Methods:
	- NewItem(): Creates a new Quiz Item
	- LoadItem(doc): Loads an EClass XML document.
	"""

	def __init__(self):
		plugins.PluginData.__init__(self)
		self.name = ""
		self.id = ""
		self.presentation = QuizItemPresentation()
		self.conditions = []
		self.feedback = []

class QuizItemPresentation (plugins.PluginData):
	def __init__(self):
		plugins.PluginData.__init__(self)
		self.label = ""
		self.text = ""
		self.lidid = ""
		self.choices = []

class QuizItemChoice (plugins.PluginData):
	def __init__(self):
		plugins.PluginData.__init__(self)
		self.id = ""
		self.text = ""

class QuizItemFeedback(plugins.PluginData):
	def __init__(self):
		plugins.PluginData.__init__(self)
		self.id = ""
		self.view = ""
		self.text = ""

class QuizItemCondition(plugins.PluginData):
	def __init__(self):
		plugins.PluginData.__init__(self)
		self.title = ""
		self.variables = []
		self.action = "set"
		self.var = "1"
		self.feedbacktype = "Response"
		self.feedbackid = ""

class QuizItemVariable(plugins.PluginData):
	def __init__(self):
		plugins.PluginData.__init__(self)
		self.condition = "equal"
		self.itemid = ""
		self.value = ""

#------------------------------ PUBLISHER CLASSES ---------------------------------

class HTMLPublisher(plugins.BaseHTMLPublisher):

	def GetData(self):
		self.quiz = QuizPage()
		self.quiz.LoadPage(os.path.join(self.dir, self.node.content.filename))

		self.data['content'] = self._ItemsAsHTML()
		#self.data['credit'] = ""

		try:		
			#copy the correct/incorrect graphics if they don't exist
			if not os.path.exists(os.path.join(self.dir, "Graphics", "Quiz")):
				os.mkdir(os.path.join(self.dir, "Graphics", "Quiz"))
			
			CopyFiles(os.path.join(self.parent.AppDir, "plugins", "Quiz", "Files", "Graphics"), os.path.join(self.dir, "Graphics", "Quiz"), 1)

		except: 
			global log
			message = _("Could not copy Quiz files from %(directory)s to your EClass. Please check that you have enough hard disk space to write this file and that you have permission to write to the directory.") % {"directory":os.path.join(self.parent.AppDir, "plugins", "Quiz", "Files")}
			log.write(message)
			raise IOError, message
			return ""	
		return ""

	def _ItemsAsHTML(self):
		script = """
		<script language="Javascript">
		//preload images
    		correct_on = new Image();
    		correct_on.src = "../Graphics/Quiz/correct.gif";

    		incorrect_on = new Image();
    		incorrect_on.src = "../Graphics/Quiz/incorrect.gif";	


		function GradeQuiz(){
		"""

		html = "<form><table width=\"100%\">"
		counter = 1
		for item in self.quiz.items:
			correcttext = ""
			incorrecttext = ""

			for feedback in item.feedback:
				if feedback.id == "Correct":
					correcttext = feedback.text
				else:
					incorrecttext = feedback.text

			html = html + """<tr>
			<td width="50"><div id="%s_answer"><img id="%s_answerimg" src="../Graphics/Quiz/blank.gif" height="32" width="32"></div></td>
			<td width="60%%"><div id="%s_question">
			<h3><b>%s. %s</b></h3>				
			""" % (item.id, item.id, item.id, `counter`, item.presentation.text)
			choicecounter = 0
			script = script + """
				answer = document.getElementById("%s_answer");
				feedback = document.getElementById("%s_feedback");
				answerimg = document.getElementById("%s_answerimg");
			""" % (item.id, item.id, item.id)

			conditiontext = ""
			numcorrect = 0
			correctvalue = ""

			for condition in item.conditions:
				if condition.title == "Correct":
					for var in condition.variables:
						if var.condition == "equal":
							correctvalue = var.value #only matters when this is run once
							numcorrect = numcorrect + 1

					vartext = ""
					if numcorrect > 1:
						for var in condition.variables:
							if not var.condition == "equal":
								vartext = vartext + "!"

							vartext = vartext + """document.forms[0].%s_%s.checked &&""" % (item.id, var.value)
						conditiontext = conditiontext + vartext
					else:
						script = script + """
				correctitem = 0;
				radio = document.forms[0].%s;
				for(var i=0; i < radio.length; i++){
					if (radio[i].value == "%s")
					{
						correctitem = i;
					}
				}""" % (item.id, correctvalue)
						conditiontext = conditiontext + """document.forms[0].%s[correctitem].checked &&""" % (item.id)
			
			if conditiontext[-3:] == " &&":
				conditiontext = conditiontext[:-3] #get rid of the trailing && 			
	
			script = script + """
				if (%s){
					answerimg.src = correct_on.src;	
					feedback.innerHTML = "%s";
				}
				else{
					answerimg.src = incorrect_on.src;
					feedback.innerHTML = "%s";
				}
					""" % (conditiontext, correcttext, incorrecttext)
												
			
			
			for choice in item.presentation.choices:
				if numcorrect == 1:
					html = html + """
					<input type="radio" name="%s" value="%s"> %s<br>
					""" % (item.id, choice.id, choice.text)
				else:
					html = html + """
					<input type="checkbox" name="%s_%s"> %s<br>
					""" % (item.id, choice.id, choice.text)



				#if len(item.conditions[0].variables) == 1 and item.conditions[0].variables[0].value == choice.id:
				#	conditiontext = "document.forms[0].%s[%s].checked" % (item.id, `choicecounter`)

				#elif len(item.conditions[0].variables) > 1:
				#	correct = false
				#	for var in item.conditions[0].variables:	 
				#		if choice.id == var.value:
				#			correct = true

				#	if not correct:
						
				#	conditiontext = conditiontext + """!document.forms[0].%s_%s.checked &&""" % (item.id, choice.id)
					
				
				#choicecounter = choicecounter + 1

			html = html + """
				<br><br></div></td>
				<td><div id="%s_feedback"></div></td>
				</tr>
				""" % (item.id)

			
			counter = counter + 1

		script = script + "} </script>"
		html = html + "</table><input type=\"button\" onclick=\"javascript:GradeQuiz()\" name=\"Submit\" value=\"Submit\"></form>" + script
		return html	

	def GetFilename(self, filename):
		"""
		Function: GetFilename(filename)
		Last Updated: 10/8/03
		Description: Given the filename of an EClassPage, returns the filename of the converted HTML file.

		Arguments:
		- filename: the filename, without directory, of an EClassPage

		Return values:
		Returns the filename, without directory, of the HTML page generated by HTMLPublisher
		"""

		filename = os.path.splitext(filename)[0] 
		filename = os.path.basename(filename)
		filename = filename[:28]
		filename = filename + ".htm"
		filename = string.replace(filename, " ", "_")
		return filename


#------------------------------ EDITOR CLASSES ------------------------------------

class EditorDialog(wxDialog):
	def __init__(self, parent, item):
		self.quiz = QuizPage()
		self.item = item
		self.parent = parent

		wxDialog.__init__(self, parent, -1, _("Quiz Editor"), wxPoint(100, 100))

		self.lblList = wxStaticText(self, -1, _("Question List"))
		self.lstQuestions = wxListBox(self, -1)
		self.btnAdd = wxButton(self, -1, _("Add"))
		self.btnEdit = wxButton(self, -1, _("Edit"))
		self.btnRemove = wxButton(self, -1, _("Remove"))
		self.btnOK = wxButton(self, wxID_OK, _("OK"))
		self.btnCancel = wxButton(self, wxID_CANCEL, _("Cancel"))

		if len(self.item.content.filename) > 0:	
			filename = os.path.join(self.parent.CurrentDir, self.item.content.filename)
			try:
				if not os.path.exists(filename):
					self.quiz.SaveAsXML(filename)
	
				self.quiz.LoadPage(filename)
			except IOError, msg:
				message = utils.getStdErrorMessage("IOError", {"type":"write", "filename": filename})
				global log
				log.write(message)
				wxMessageBox(message, _("Unable to create file."), wxICON_ERROR)
				return

			for item in self.quiz.items:
				self.lstQuestions.Append(item.presentation.text, item)
		else:
			filename = self.item.content.metadata.name[:27] + ".quiz"
			counter = 1
			while os.path.exists(os.path.join(self.parent.pub.directory, "EClass", filename)):
				filename = "EClass/" + self.item.content.metadata.name[:27] + " " + `counter` + ".quiz"
				counter = counter + 1

			self.item.content.filename = filename
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.lblList, 0, wxALL, 4)
		self.mysizer.Add(self.lstQuestions, 1, wxEXPAND | wxALL, 4)

		self.editsizer = wxBoxSizer(wxHORIZONTAL)
		self.editsizer.Add(self.btnAdd, 1, wxALIGN_CENTER | wxALL, 4)
		self.editsizer.Add(self.btnEdit, 1, wxALIGN_CENTER | wxALL, 4)
		self.editsizer.Add(self.btnRemove, 1, wxALIGN_CENTER | wxALL, 4)
		self.mysizer.Add(self.editsizer, 0, wxEXPAND | wxALIGN_CENTER | wxALL, 4)

		self.btnsizer = wxStdDialogButtonSizer()
		self.btnsizer.AddButton(self.btnOK)
		self.btnsizer.AddButton(self.btnCancel)
		self.btnsizer.Realize()
		self.mysizer.Add(self.btnsizer, 0, wxEXPAND | wxALL, 4)
		
		self.SetAutoLayout(true)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		self.btnOK.SetDefault()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		EVT_BUTTON(self.btnAdd, self.btnAdd.GetId(), self.btnAddClicked)
		EVT_BUTTON(self.btnEdit, self.btnEdit.GetId(), self.btnEditClicked)
		EVT_BUTTON(self.btnRemove, self.btnRemove.GetId(), self.btnRemoveClicked)
		EVT_LEFT_DCLICK(self.lstQuestions, self.btnEditClicked)

	def btnOKClicked(self, event):
		filename = os.path.join(self.parent.CurrentDir, self.item.content.filename)
		try:
			self.quiz.SaveAsXML(filename)
			self.EndModal(wxID_OK)
		except IOError:
			message = utils.getStdErrorMessage("IOError", {"filename":filename, "type":"write"})
			global log
			log.write(message)
			wxMessageBox(message, _("Cannot Save File"), wxICON_ERROR)

	def btnAddClicked(self,event):
		editor = QuestionEditor(self)
		if editor.ShowModal() == wxID_OK:
			self.quiz.items.append(editor.question)
			self.lstQuestions.Append(editor.question.presentation.text, editor.question)

	def btnEditClicked(self, event):
		myitem = self.lstQuestions.GetClientData(self.lstQuestions.GetSelection())
		editor = QuestionEditor(self, myitem)
		editor.ShowModal()

	def btnRemoveClicked(self, event):
		myitem = self.lstQuestions.GetClientData(self.lstQuestions.GetSelection())
		self.lstQuestions.Delete(self.lstQuestions.GetSelection())
		self.quiz.items.remove(myitem)


class QuestionEditor(wxDialog):
	def __init__(self, parent, question=None):
		wxDialog.__init__(self, parent, -1, _("Question Editor"), wxPoint(100, 100))

		self.lblQuestion = wxStaticText(self, -1, _("Question:"))
		self.txtQuestion = wxTextCtrl(self, -1, "", wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE)
		#self.lblAnswers = wxStaticText(self, -1, _("Answers:"))
		self.lblCorrect = wxStaticText(self, -1, _("Correct?"))
		#self.lblID = wxStaticText(self, -1, "Answer ID")
		self.lblText = wxStaticText(self, -1, _("Answer Text"))

		self.chkCorrect1 = wxCheckBox(self, -1, "")
		self.txtID1 = wxTextCtrl(self, -1, "", wxDefaultPosition, wxSize(40, -1))
		self.txtAnswer1 = wxTextCtrl(self, -1, "",  wxDefaultPosition, wxSize(240, -1)) 
		
		self.chkCorrect2 = wxCheckBox(self, -1, "")
		self.txtID2 = wxTextCtrl(self, -1, "", wxDefaultPosition, wxSize(40, -1))
		self.txtAnswer2 = wxTextCtrl(self, -1, "",  wxDefaultPosition, wxSize(240, -1)) 

		self.chkCorrect3 = wxCheckBox(self, -1, "")
		self.txtID3 = wxTextCtrl(self, -1, "", wxDefaultPosition, wxSize(40, -1))
		self.txtAnswer3 = wxTextCtrl(self, -1, "",  wxDefaultPosition, wxSize(240, -1)) 

		self.chkCorrect4 = wxCheckBox(self, -1, "")
		self.txtID4 = wxTextCtrl(self, -1, "", wxDefaultPosition, wxSize(40, -1))
		self.txtAnswer4 = wxTextCtrl(self, -1, "",  wxDefaultPosition, wxSize(240, -1)) 

		self.chkCorrect5 = wxCheckBox(self, -1, "")
		self.txtID5 = wxTextCtrl(self, -1, "", wxDefaultPosition, wxSize(40, -1))
		self.txtAnswer5 = wxTextCtrl(self, -1, "",  wxDefaultPosition, wxSize(240, -1)) 

		self.txtID1.Show(false)
		self.txtID2.Show(false)
		self.txtID3.Show(false)
		self.txtID4.Show(false)
		self.txtID5.Show(false)

		self.btnFeedback = wxButton(self, -1, _("Feedback"))
		self.btnOK = wxButton(self, wxID_OK, _("OK"))
		self.btnCancel = wxButton(self, wxID_CANCEL, _("Cancel"))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.lblQuestion, 0, wxALL, 4)
		self.mysizer.Add(self.txtQuestion, 1, wxEXPAND | wxALL, 4)
		#self.mysizer.Add(self.lblAnswers, 0, wxALIGN_CENTER | wxALL, 4)
		
		self.answersizer = wxFlexGridSizer(0, 2, 4, 4)
		self.answersizer.Add(self.lblCorrect, 0, wxALL | wxALIGN_CENTER, 4)
		#self.answersizer.Add(self.lblID, 0, wxALL | wxALIGN_CENTER, 4)
		self.answersizer.Add(self.lblText, 0, wxALL | wxALIGN_CENTER, 4)

		self.answersizer.Add(self.chkCorrect1, 0, wxALL | wxALIGN_CENTER, 4)
		#self.answersizer.Add(self.txtID1, 0, wxALL, 4)
		self.answersizer.Add(self.txtAnswer1, 0, wxALL, 4)

		self.answersizer.Add(self.chkCorrect2, 0, wxALL | wxALIGN_CENTER, 4)
		#self.answersizer.Add(self.txtID2, 0, wxALL, 4)
		self.answersizer.Add(self.txtAnswer2, 0, wxALL, 4)

		self.answersizer.Add(self.chkCorrect3, 0, wxALL | wxALIGN_CENTER, 4)
		#self.answersizer.Add(self.txtID3, 0, wxALL, 4)
		self.answersizer.Add(self.txtAnswer3, 0, wxALL, 4)

		self.answersizer.Add(self.chkCorrect4, 0, wxALL | wxALIGN_CENTER, 4)
		#self.answersizer.Add(self.txtID4, 0, wxALL, 4)
		self.answersizer.Add(self.txtAnswer4, 0, wxALL, 4)

		self.answersizer.Add(self.chkCorrect5, 0, wxALL | wxALIGN_CENTER, 4)
		#self.answersizer.Add(self.txtID5, 0, wxALL, 4)
		self.answersizer.Add(self.txtAnswer5, 0, wxALL, 4)

		self.mysizer.Add(self.answersizer, 0, wxEXPAND)
	
		self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonsizer.Add(self.btnFeedback, 0, wxALL, 4)
		self.buttonsizer.Add((100, 1), 1, wxEXPAND | wxALL, 4)
		stdbuttonsizer = wxStdDialogButtonSizer()
		stdbuttonsizer.AddButton(self.btnOK)
		stdbuttonsizer.AddButton(self.btnCancel)
		stdbuttonsizer.Realize()
		self.buttonsizer.Add(stdbuttonsizer)
		self.mysizer.Add(self.buttonsizer, 0, wxEXPAND, 4)

		self.btnOK.SetDefault()
		self.txtQuestion.SetFocus()
		self.SetAutoLayout(true)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		if not question == None:
			self.question = question
			self.txtQuestion.SetValue(question.presentation.text)
			counter = 0
			for choice in question.presentation.choices:
				eval("self.txtID" + `(counter + 1)` + ".SetValue(u\"" + choice.id + "\")")
				if counter < 6:
					eval("self.txtAnswer" + `(counter + 1)` + ".SetValue(u\"" + choice.text + "\")")
					for cond in question.conditions:
						if cond.title == "Correct":
							for var in cond.variables:
								if var.value == choice.id and var.condition == "equal":
									eval("self.chkCorrect" + `(counter + 1)` + ".SetValue(true)")
				counter = counter + 1
		else:
			self.question = QuizItem()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.SavePage)
		EVT_BUTTON(self.btnFeedback, self.btnFeedback.GetId(), self.EditFeedback)

	def EditFeedback(self, event):
		mydialog = QuestionFeedbackDialog(self, self.question.feedback)
		if mydialog.ShowModal() == wxID_OK:
			self.question.feedback = mydialog.feedback

	def SavePage(self, event):
		self.question.presentation.text = self.txtQuestion.GetValue()
		self.question.presentation.choices = []
		self.question.conditions = []
		correctcondition = QuizItemCondition()
		correctcondition.title = "Correct"
		correctcondition.itemid = self.question.presentation.lidid

		#incorrectcondition = QuizItemCondition()
		#incorrectcondition.title = "Correct"
		#incorrectcondition.itemid = self.question.presentation.lidid
		correctAnswer = False
		numAnswers = 0
		for counter in range(1, 6):
			exec("chkCorrect = self.chkCorrect" + `counter`)
			exec("txtAnswer = self.txtAnswer" + `counter`)
			
			if chkCorrect.GetValue() == True:
				correctAnswer = True

			if not txtAnswer.GetValue() == "":
				numAnswers = numAnswers + 1

		if self.question.presentation.text == "":
			wxMessageBox(_("Please enter a question."))
			return False

		if not correctAnswer:
			wxMessageBox(_("Please specify one or more correct answer(s)."))
			return False 

		if numAnswers <= 1:
			wxMessageBox(_("Questions must have at least 2 answers."))
			return False

		for counter in range(1, 6):
			exec("txtAnswer = self.txtAnswer" + `counter`)
			exec("txtID = self.txtID" + `counter`)
			exec("chkCorrect = self.chkCorrect" + `counter`)

			if not len(txtAnswer.GetValue()) == 0:
				newchoice = QuizItemChoice()

				if not len(txtID.GetValue()) == 0:
					newchoice.id = txtID.GetValue()
				else: 
					newchoice.id = "A" + `counter`

				newchoice.text = txtAnswer.GetValue()					

				if chkCorrect.GetValue() == true:
					var = QuizItemVariable()
					var.value = newchoice.id
					correctcondition.variables.append(var)
				else:
					var = QuizItemVariable()
					var.condition = "not equal"
					var.value = newchoice.id
					correctcondition.variables.append(var)

				self.question.presentation.choices.append(newchoice)

		self.question.conditions.append(correctcondition)

		self.EndModal(wxID_OK)

class QuestionFeedbackDialog(wxDialog):
	def __init__(self, parent, feedback):
		self.feedback = feedback
		wxDialog.__init__(self, parent, -1, _("Question Editor"), wxPoint(100, 100))
		self.lblCorrect = wxStaticText(self, -1, _("Correct Answer Feedback"))
		self.txtCorrect = wxTextCtrl(self, -1, "", wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE)
		self.lblIncorrect = wxStaticText(self, -1, _("Incorrect Answer Feedback"))
		self.txtIncorrect = wxTextCtrl(self, -1, "", wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE)

		self.btnOK = wxButton(self, wxID_OK, _("OK"))
		self.btnCancel = wxButton(self, wxID_CANCEL, _("Cancel"))
		
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.lblCorrect, 0, wxALL, 4)
		self.mysizer.Add(self.txtCorrect, 1, wxEXPAND | wxALL, 4)
		self.mysizer.Add(self.lblIncorrect, 0, wxALL, 4)
		self.mysizer.Add(self.txtIncorrect, 1, wxEXPAND | wxALL, 4)
		
		self.buttonsizer = wxStdDialogButtonSizer()
		self.buttonsizer.AddButton(self.btnOK)
		self.buttonsizer.AddButton(self.btnCancel)
		self.buttonsizer.Realize()
		self.mysizer.Add(self.buttonsizer, 0, wxEXPAND)

		self.btnOK.SetDefault()
		for itemfeedback in feedback:
			if itemfeedback.id == "Correct":
				self.txtCorrect.SetValue(itemfeedback.text)
			elif itemfeedback.id == "Incorrect":
				self.txtIncorrect.SetValue(itemfeedback.text)

		self.SetAutoLayout(true)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.SaveFeedback)


	def SaveFeedback(self, event):
		self.feedback = []
		if len(self.txtCorrect.GetValue()) > 0:
			newfeedback = QuizItemFeedback()
			newfeedback.id = "Correct"
			newfeedback.view = "Candidate"
			newfeedback.text = self.txtCorrect.GetValue()
			self.feedback.append(newfeedback)

		if len(self.txtIncorrect.GetValue()) > 0:
			newfeedback = QuizItemFeedback()
			newfeedback.id = "Incorrect"
			newfeedback.view = "Candidate"
			newfeedback.text = self.txtIncorrect.GetValue()
			self.feedback.append(newfeedback)
		
		self.EndModal(wxID_OK)

def Test():
	quiz = QuizPage()
	scriptpath = os.path.abspath(sys.path[0])
	quiz.LoadPage(os.path.join(scriptpath, "plugins", "quiztest", "qtitest.xml"))
	quiz.SaveAsXML(os.path.join(scriptpath, "plugins", "quiztest", "quitestresult.xml"))

if __name__ == "__main__":
	Test()
