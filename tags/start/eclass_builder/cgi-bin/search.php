<?php

$content = "<FORM method=POST>\n<INPUT type=text name=term";

if ($_REQUEST['term']){
    $content .= " value='" + $_REQUEST['term'];
}
$content .= ">";

if ($_REQUEST['page']){
    $content .= "<INPUT name=page type=hidden value=" . $_REQUEST['page'] . "> ";
}

$content .= "<select name=searchtype>";
$content .= "   <option name=all>All text</option>";
$content .= "   <option name=title>Titles</option>";
$content .= "   <option name=keywords>Keywords</option>";
$content .= "</select>";
$content .= "<INPUT type=submit name=\"Search\" value=\"Search\">";
$content .= "</FORM>";

if ($_REQUEST['term']){
    $content .= "<hr><h3>Search Results</h3>";
    $search = "-w ";
    $term = $_REQUEST['term'];
    
    if($_REQUEST['searchtype']){
        $searchtype = $_REQUEST['searchtype'];
        if ($searchtype == "Titles")
            $search .= $term . " -t t";
        else if ($searchtype == "Keywords")
            $search .= "Keywords=" . $term;
        else 
            $search .= $term;
    }
    else {
        $search .= $term;
    }

    if ($_REQUEST['page']){
        $page = "-b " . (1 + (20 * ((int)$_REQUEST['page'] - 1)));
    }

    $command = "swish-e -d :: -f ../index.swish-e -m 20 -p Description " . $search . " " . $page;
    #$command = "swish-e -h";
    #$retval = system("C:\\website\\students\\gtoro\\culture\\cgi-bin\\swish-e.exe --version");
    #echo $command;
    $swish = popen($command, "r" );
    $results = 0;
    while ($line = fgets($swish)){
        if (strpos($line, "err: no results") !== false){
            $content .= "Sorry, your search returned no results.";
            break;
        }
        else if (strpos($line, "# Number of hits:") !== false){
             $parts = explode(":", $line);
            $results = $parts[1];
            $content .= "<p><i>Your search returned " . $results . " results.</i></p>";
        }
        else if (strpos($line, "::") !== false)
        {
            $parts = explode("::", $line);
            $file = $parts[1];
            $title = $parts[2];
            $percent = (int)$parts[0] / 10;
            $bytes = $parts[3];
            $description = $parts[4];
            if ($file != ""){
                $link = "<p><a href=${file}>${title}</a><br><font size='-1'><i>Ranking: ${percent}% &nbsp;&nbsp;Size: ${bytes} bytes</i></font><br>${description}</p>";
                $content .= $link;
            }
        }
    }
    pclose($swish);

    if ($results > 20){
        $numpages = ceil($results / 20);
        $searchtype = str_replace(" ", "%20", $searchtype);
        
        for ($page = 1; $page <= $numpages; $page++){
            $content .= "[ <a href=search.php?searchtype=${searchtype}&amp;term=${term}&amp;page=${page}>${page}</a> ]";
        }
    }
}

$template = fopen("default.tpl", "r");
$data = fread($template, filesize("default.tpl"));
fclose($template);

$data = str_replace("--[name]--", "EClass Search Page", $data);
$data = str_replace("--[credit]--", "", $data);
$data = str_replace("--[backlink]--", "", $data);
$data = str_replace("--[nextlink]--", "", $data);
$data = str_replace("--[content]--", $content, $data);

echo $data;
?>