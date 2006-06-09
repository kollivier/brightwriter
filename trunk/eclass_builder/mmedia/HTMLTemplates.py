#these are templates to be used by both the EClass Page editor and the HTML editor to insert media 
#files into web pages

rmAudioTemp = """<CENTER>
<OBJECT classid=clsid:CFCDAA03-8BE4-11CF-B84B-0020AFBBCCFA width="320" height="32">
	<Param name="AUTOSTART" value="_autostart_"/>
	<Param name="SRC" value="_filename_"/>
	<Param name="LOOP" value="0"/>
	<Param name="CONTROLS" value="ControlPanel">
	<Param name="BACKGROUNDCOLOR" value="#000000"/>
	<embed src="_filename_" width="320" height="32" autostart="_autostart_" controls="ControlPanel" />
</OBJECT>
</CENTER>
		"""

rmVideoTemp = """
<CENTER>
<OBJECT classid=clsid:CFCDAA03-8BE4-11CF-B84B-0020AFBBCCFA width="320" height="240">
	<Param name="AUTOSTART" value="_autostart_"/>
	<Param name="SRC" value="_filename_"/>
	<Param name="LOOP" value="0"/>
	<Param name="CONSOLE" value="Clip1">
	<Param name="CONTROLS" value="ImageWindow"/>
	<Param name="BACKGROUNDCOLOR" value="#000000"/>
	<embed src="_filename_" type="_mimetype_" controls="ImageWindow" width="320" height="240" autostart="_autostart_" console="Clip1"/><br>
</OBJECT>
<br>
<OBJECT classid=clsid:CFCDAA03-8BE4-11CF-B84B-0020AFBBCCFA width="320" height="32">
	<Param name="AUTOSTART" value="_autostart_"/>
	<Param name="SRC" value="_filename_"/>
	<Param name="LOOP" value="0"/>
	<Param name="CONSOLE" value="Clip1">
	<Param name="CONTROLS" value="ControlPanel">
	<Param name="BACKGROUNDCOLOR" value="#000000"/>
	<embed src="_filename_" width="320" height="32" autostart="_autostart_" controls="ControlPanel" console="Clip1"/>
</OBJECT>
</CENTER>
		"""

wmTemp = """
<CENTER>
<OBJECT classid=clsid:22D6F312-B0F6-11D0-94AB-0080C74C7E95>
	<Param name="AutoSize" value="1"/>
	<Param name="AutoStart" value="_autostart_"/>
	<Param name="AutoRewind" value="1"/>
	<Param name="Filename" value="_filename_"/>
	<Param name="PreviewMode" value="1"/>
	<embed src="_filename_" type="_mimetype_" autostart="_autostart_"/><br>
</OBJECT>
</CENTER>
		"""

qtTemp = """
<OBJECT CLASSID="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B" CODEBASE="http://www.apple.com/qtactivex/qtplugin.cab" WIDTH="320" HEIGHT="256">
	<PARAM name="SRC" VALUE="_filename_">
	<PARAM name="AUTOPLAY" VALUE="_autostart_">
	<PARAM name="CONTROLLER" VALUE="true">
	<EMBED SRC="_filename_" AUTOPLAY="_autostart_" WIDTH="320" HEIGHT="256" CONTROLLER="true" PLUGINSPAGE="http://www.apple.com/quicktime/download/">
	</EMBED>
</OBJECT>
		"""

flashTemp = """
		<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=5,0,0,0">
			<param name="FlashVars" value="0">
			<param name="Movie" value="_filename_">
			<param name="Src" value="_filename_">
			<param name="WMode" value="Window">
			<param name="Play" value="_autostart_">
			<param name="Loop" value="-1">

			<param name="Quality" value="AutoHigh">
			<param name="SAlign" value>
			<param name="Menu" value="-1">
			<param name="Base" value>
			<param name="Scale" value="ExactFit">
			<param name="DeviceFont" value="0">
			<param name="EmbedMovie" value="0">
			<param name="BGColor" value>
			<param name="SWRemote" value>
			<embed src="_filename_" quality="autolow" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" scale="exactfit"> 
		</object> 
		"""
flvTemp = """
		<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=5,0,0,0">
			<param name="FlashVars" value="0">
			<param name="Movie" value="mp3player.swf?file=__filename__">
			<param name="Src" value="mp3player.swf?file=__filename__">
			<param name="menu" value="False">
			<param name="WMode" value="Window">
			<param name="Play" value="True">
			<param name="Loop" value="-1">

			<param name="Quality" value="AutoHigh">
			<param name="SAlign" value>
			<param name="Menu" value="-1">
			<param name="Base" value>
			<param name="Scale" value="ExactFit">
			<param name="DeviceFont" value="0">
			<param name="EmbedMovie" value="0">
			<param name="BGColor" value>
			<param name="SWRemote" value>
			<embed src="mp3player.swf" flashvars="&file=__filename__" menu="false" quality="autolow" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" scale="exactfit"> 
		</object> 
		"""

mp4Temp = """
        <applet name="mediaframe" code="mediaframe.mpeg4.MPEG4.class" archive="mediaframe-mpeg4.jar,mediaframe-aac.jar" width="384" height="224" mayscript="true">
			<param name="id"				value="ID: __filename__">
			<param name="default_media"		value="__filename__">
			<param name="pre_buffer"  		value="28%%">
			<param name="playback"			value="autostart">
			<param name="loop"				value="false">
			<param name="control_location"	value="control_set">
			<param name="smooth_video"		value="true">
			<param name="video_license"		value="false">
			<!-- <param name="save_script"		value="save_scripts/movie_save.php"> -->
			<param name="allow_save"		value="false">
		</applet>
"""

mp3Temp = """
<center>
<object width="320" height="32">
	<param name="SRC" value="_filename_">
	<param name="AUTOPLAY" value="_autostart_">
	<param src="_filename_" autoplay="_autostart_" width="320" height="32">
	</embed>
</object>
</center>
		"""