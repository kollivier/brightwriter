
# FIXME: make this work! :-)
def _(text):
    return text

std_attrs = ["class", "dir", "id", "lang", "style"]

tag_attrs = {
    "A": {
        "required": [],
        "optional": ["href", "target", "id"]
    },
    "AUDIO": {
        "required": [],
        "optional": ["width", "height", "controls", "autoplay"]
    },
    "IMG": {
        "required": ["src", "alt"],
        "optional": ["height", "width", "align"]  # FIXME: align should be part of style
    },
    "OL": {
        "required": [],
        "optional": ["type", "start"]
    },
    "SOURCE": {
        "required": ["src"],
        "optional": []
    },
    "TABLE": {
        "required": [],
        "optional": ["align", "bgcolor", "border", "cellpadding", "cellspacing", "width"]
    },
    "TR": {
        "required": [],
        "optional": ["align", "bgcolor", "valign"]
    },
    "TD": {
        "required": [],
        "optional": ["align", "bgcolor", "border", "colspan", "height", "nowrap", "rowspan", "valign", "width"]
    },
    "UL": {
        "required": [],
        "optional": ["type"]
    },
    "VIDEO": {
        "required": [],
        "optional": ["width", "height", "controls", "autoplay"]
    }
}

table_halign = {_("Default"): "", _("Left"): "left", _("Center"): "center", _("Right"): "right"}
table_valign = {_("Default"): "", _("Top"): "top", _("Middle"): "middle", _("Bottom"): "bottom"}

attr_values = {
    "A": {
        "target": {
            _("Default"): "",
            _("New Window"): "_blank",
            _("Current Window"): "_top",
            _("Current Frame"): "_self",
            _("Parent Frame"): "_parent"
        }
    },
    "IMG":  {
        "align": {
            _("Default"): "",
            _("Left"): "left",
            _("Right"): "right",
            _("Top"): "top",
            _("Middle"): "middle",
            _("Bottom"): "bottom"
        }
    },
    "OL":   {
        "type": {
            _("Default"): "",
            _("Numbered"): "1",
            _("Alphabetical (Caps)"): "A",
            _("Alphabetical"): "a",
            _("Roman Numerals (Caps)"): "I",
            _("Roman Numerals"): "i"
        }
    },
    "TABLE": {
        "align": table_halign
    },
    "TD": {
        "align": table_halign,
        "valign": table_valign
    },
    "TR": {
        "align": table_halign,
        "valign": table_valign
    },
    "UL": {
        "type": {
            _("Default"): "",
            _("Circle"): "circle",
            _("Disc"): "disc",
            _("Square"): "square",
        }
    },
}
