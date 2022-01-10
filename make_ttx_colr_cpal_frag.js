const schemes = require("./cleancolors.json")
const fs = require('fs');

for (var scheme in schemes) {
    var xml = "<COLR>\n<version value=\"0\"/>\n"
    var palette = []
    var idx = 1
    var colors = schemes[scheme]
    for (var j in colors) {
        var key = colors[j] + ""
        if (!(key in palette)) {
            i = palette[key] = (idx++)-1
        } else {
            i = palette[key]
        }
        xml += `<ColorGlyph name="${j.toUpperCase()}"><layer colorID="${i}" name="${j.toUpperCase()}"/></ColorGlyph>\n`
        xml += `<ColorGlyph name="${j.toLowerCase()}"><layer colorID="${i}" name="${j.toLowerCase()}"/></ColorGlyph>\n`
    }
    xml += "</COLR>"
    xml += `<CPAL>\n<version value="0"/>\n<numPaletteEntries value="${Object.keys(palette).length}"/>\n<palette index="0">\n`
    for (var i in palette) {
        xml += `<color index="${palette[i]}" value="${i}"/>\n`
    }
    xml += "</palette>\n</CPAL>\n</ttFont>\n"
    // console.log(xml)
    // console.log(palette)
    fs.writeFileSync(`ttx/${scheme}.ttx`, xml)
}

