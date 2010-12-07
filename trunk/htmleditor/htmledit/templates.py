html5video = """
<!-- "Video For Everybody" v0.4.2 by Kroc Camen of Camen Design <camendesign.com/code/video_for_everybody>
     =================================================================================================================== -->
<!-- first try HTML5 playback: if serving as XML, expand `controls` to `controls="controls"` and autoplay likewise       -->
<!-- warning: playback does not work on iPad/iPhone if you include the poster attribute! fixed in iOS4.0                 -->
<video controls="controls">
    <!-- MP4 must be first for iPad! -->
    <source src="__VIDEO__.MP4" /><!-- WebKit video    -->
    <source src="__VIDEO__.OGV" type="video/ogg" /><!-- Firefox / Opera -->
    <!-- fallback to Flash: -->
    <object type="application/x-shockwave-flash" data="flvplayer.swf?file=_filename_&autoStart=_autostart_">
        <!-- Firefox uses the `data` attribute above, IE/Safari uses the param below -->
        <param name="Movie" value="flvplayer.swf?file=_filename_&autoStart=_autostart_">
        <param name="Src" value="flvplayer.swf?file=_filename_&autoStart=_autostart_">
        <!-- fallback image. note the title field below, put the title of the video there -->
        <img src="__VIDEO__.JPG" width="640" height="360" alt="__TITLE__"
             title="No video playback capabilities, please download the video below" />
    </object>
</video>
<!-- you *must* offer a download link as they may be able to play the file locally. customise this bit all you want -->
<p> <strong>Download Video:</strong>
    <a href="__VIDEO__.MP4">MP4 format</a> <a href="__VIDEO__.OGV">Ogg Format</a>
</p>

"""

jwplayer = """
<script type="text/javascript" src="jwplayer.js"></script>
<div id="container">Loading the player ...</div>
<script type="text/javascript">
<![CDATA[
    var loc = new String(window.parent.document.location);
    var provider = "video";
    var useHTTPStreaming = __USE_HTTP_STREAMING__;
    if (loc.indexOf("http://") != -1 && useHTTPStreaming) {
        provider = "http";
    }
    jwplayer("container").setup({
        flashplayer: "player.swf",
        file: "__VIDEO__.MP4",
        poster: "__VIDEO__.JPG",
        height: 480,
        width: 640,
        provider: provider,
    });
]]>
</script>
"""
