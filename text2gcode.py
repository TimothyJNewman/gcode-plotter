#!/usr/bin/python

"""
    engrave-lines.py G-Code Engraving Generator for command-line usage
    (C) ArcEye <2012>  <arceye at mgware dot co dot uk>
    syntax  ---   see helpfile below
    
    Allows the generation of multiple lines of engraved text in one go
    Will take each string arguement, apply X and Y offset generating code until last line done
    
  
    based upon code from engrave-11.py
    Copyright (C) <2008>  <Lawrence Glaister> <ve7it at shaw dot ca>
                     based on work by John Thornton  -- GUI framwork from arcbuddy.py
                     Ben Lipkowitz  (fenn)-- cxf2cnc.py v0.5 font parsing code

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    Rev v2 21.06.2012 ArcEye
"""

from tkinter import *
from math import *
import os
import re
import sys
import string
import getopt

# defaults
GString = ""
GSafeZ = 2
GXStart = 0
GXLineOffset = 10
GXIndentList = ""
GYStart = 0
GYLineOffset = 10
GDepth = 0.1
GXScale = 1
GYScale = 1
GCSpaceP = 25
GWSpaceP = 50
GAngle = 0
GMirror = 0
GFlip = 0
GPreamble = '''
G21 (metric ftw)
G90 (absolute mode)
G92 X0.00 Y0.00 Z0.00 (you are here)
M300 S30 (pen down)
G4 P150 (wait 150ms)
M300 S50 (pen up)
G4 P150 (wait 150ms)
M18 (disengage drives)
M01 (Was registration test successful?)
M17 (engage drives if YES, and continue)
'''
GPostamble = "M2"
GFont = "romanc.cxf"
Gfontfile = []

Gstringlist = []

# =======================================================================


class Character:
    def __init__(self, key):
        self.key = key
        self.stroke_list = []

    def __repr__(self):
        return "%s" % (self.stroke_list)

    def get_xmax(self):
        try:
            return max([s.xmax for s in self.stroke_list[:]])
        except ValueError:
            return 0

    def get_ymax(self):
        try:
            return max([s.ymax for s in self.stroke_list[:]])
        except ValueError:
            return 0


# =======================================================================
class Line:

    def __init__(self, coords):
        self.xstart, self.ystart, self.xend, self.yend = coords
        self.xmax = max(self.xstart, self.xend)
        self.ymax = max(self.ystart, self.yend)

    def __repr__(self):
        return "Line([%s, %s, %s, %s])" % (self.xstart, self.ystart, self.xend, self.yend)


# =======================================================================
# This routine parses the .cxf font file and builds a font dictionary of
# line segment strokes required to cut each character.
# Arcs (only used in some fonts) are converted to a number of line
# segemnts based on the angular length of the arc. Since the idea of
# this font description is to make it support independant x and y scaling,
# we can not use native arcs in the gcode.
# =======================================================================
def parse(file):
    font = {}
    key = None
    num_cmds = 0
    line_num = 0
    for text in file:
        # format for a typical letter (lowercase r):
        # comment, with a blank line after it
        #
        # [r] 3
        # L 0,0,0,6
        # L 0,6,2,6
        # A 2,5,1,0,90
        #
        line_num += 1
        end_char = re.match('^$', text)  # blank line
        if end_char and key:  # save the character to our dictionary
            font[key] = Character(key)
            font[key].stroke_list = stroke_list
            font[key].xmax = xmax
            if (num_cmds != cmds_read):
                print("(warning: discrepancy in number of commands %s, line %s, %s != %s )" % (
                    Gfontfile, line_num, num_cmds, cmds_read))

        new_cmd = re.match('^\[(.*)\]\s(\d+)', text)
        if new_cmd:  # new character
            key = new_cmd.group(1)
            num_cmds = int(new_cmd.group(2))  # for debug
            cmds_read = 0
            stroke_list = []
            xmax, ymax = 0, 0

        line_cmd = re.match('^L (.*)', text)
        if line_cmd:
            cmds_read += 1
            coords = line_cmd.group(1)
            coords = [float(n) for n in coords.split(',')]
            stroke_list += [Line(coords)]
            xmax = max(xmax, coords[0], coords[2])

        arc_cmd = re.match('^A (.*)', text)
        if arc_cmd:
            cmds_read += 1
            coords = arc_cmd.group(1)
            coords = [float(n) for n in coords.split(',')]
            xcenter, ycenter, radius, start_angle, end_angle = coords
            # since font defn has arcs as ccw, we need some font foo
            if (end_angle < start_angle):
                start_angle -= 360.0
            # approximate arc with line seg every 20 degrees
            segs = int((end_angle - start_angle) / 20) + 1
            angleincr = (end_angle - start_angle)/segs
            xstart = cos(start_angle * pi/180) * radius + xcenter
            ystart = sin(start_angle * pi/180) * radius + ycenter
            angle = start_angle
            for i in range(segs):
                angle += angleincr
                xend = cos(angle * pi/180) * radius + xcenter
                yend = sin(angle * pi/180) * radius + ycenter
                coords = [xstart, ystart, xend, yend]
                stroke_list += [Line(coords)]
                xmax = max(xmax, coords[0], coords[2])
                ymax = max(ymax, coords[1], coords[3])
                xstart = xend
                ystart = yend
    return font


# =======================================================================
'''
def __init__(key):
    key = key
    stroke_list = []

def __repr__():
    return "%s" % (stroke_list)

def get_xmax():
    try: return max([s.xmax for s in stroke_list[:]])
    except ValueError: return 0

def get_ymax():
    try: return max([s.ymax for s in stroke_list[:]])
    except ValueError: return 0
'''


# =======================================================================

'''
def __init__( coords):
    xstart, ystart, xend, yend = coords
    xmax = max(xstart, xend)
    ymax = max(ystart, yend)

def __repr__():
    return "Line([%s, %s, %s, %s])" % (xstart, ystart, xend, yend)
'''

# =======================================================================


def sanitize(string):
    retval = ''
    good = ' ~!@#$%^&*_+=-{}[]|\:;"<>,./?'
    for char in string:
        if char.isalnum() or good.find(char) != -1:
            retval += char
        else:
            retval += (' 0x%02X ' % ord(char))
    return retval

# =======================================================================
# routine takes an x and a y in raw internal format
# x and y scales are applied and then x,y pt is rotated by angle
# Returns new x,y tuple


# routine takes an x and a y in raw internal format
# x and y scales are applied and then x,y pt is rotated by angle
# Returns new x,y tuple
def Rotn(x,y,xscale,yscale,angle,visit):
    global GXLineOffset
    global GXStart
    global GYStart
    global GYLineOffset
    newXstart = GXStart
    if GXLineOffset :
            if GXIndentList.find(str(visit)) != -1 :
                newXstart = GXStart + GXLineOffset
    newYstart = GYStart - (GYLineOffset * visit)
    Deg2Rad = 2.0 * pi / 360.0
    xx = x * xscale
    yy = y * yscale
    rad = sqrt(xx * xx + yy * yy)
    theta = atan2(yy,xx)
    newx=rad * cos(theta + angle*Deg2Rad) + newXstart
    newy=rad * sin(theta + angle*Deg2Rad) + newYstart
    return newx,newy


# =======================================================================

def code(arg, visit, last):

    global GSafeZ
    global GXStart
    global GXLineOffset
    global GXIndentList
    global GYStart
    global GYLineOffset
    global GDepth
    global GXScale
    global GYScale
    global GCSpaceP
    global GWSpaceP
    global GAngle
    global GMirror
    global GFlip
    global GPreamble
    global GPostamble
    global Gstringlist
    global Gfontfile

    GString = arg

    str1 = ""
    # erase old gcode as needed
    gcode = []

    file = open(Gfontfile, encoding="ISO-8859-1")

    oldx = oldy = -99990.0
    print("visit:"+str(visit))
    if visit != 0:
        # all we need is new X and Y for subsequent lines
        gcode.append(
            "(===================================================================)")
        gcode.append('( Engraving: "%s" )' % (GString))
        gcode.append('( Line %d )' % (visit))

        str1 = '#1002 = %.4f  ( X Start )' % (GXStart)
        if GXLineOffset:
            if GXIndentList.find(str(visit)) != -1:
                str1 = '#1002 = %.4f  ( X Start )' % (GXStart + GXLineOffset)

        gcode.append(str1)
        gcode.append('#1003 = %.4f  ( Y Start )' %
                     (GYStart - (GYLineOffset * visit)))
        print("Y start: "+str(GYStart - (GYLineOffset * visit)))
        gcode.append(
            "(===================================================================)")

    else:
        gcode.append('( Code generated by engrave-lines.py )')
        gcode.append('( by ArcEye 2012, based on work by <Lawrence Glaister>)')
        gcode.append('( Fontfile: %s )' % (Gfontfile))
        # write out subroutine for rotation logic just once at head
        gcode.append(
            "(===================================================================)")
        gcode.append("(Subroutine to handle x,y rotation about 0,0)")
        gcode.append("(input x,y get scaled, rotated then offset )")
        gcode.append(
            "( [#1 = 0 or 1 for a G0 or G1 type of move], [#2=x], [#3=y])")
        gcode.append("o9000 sub")
        gcode.append("  #28 = [#2 * #1004]  ( scaled x )")
        gcode.append("  #29 = [#3 * #1005]  ( scaled y )")
        gcode.append(
            "  #30 = [SQRT[#28 * #28 + #29 * #29 ]]   ( dist from 0 to x,y )")
        gcode.append(
            "  #31 = [ATAN[#29]/[#28]]                ( direction to  x,y )")
        gcode.append("  #32 = [#30 * cos[#31 + #1006]]     ( rotated x )")
        gcode.append("  #33 = [#30 * sin[#31 + #1006]]     ( rotated y )")
        gcode.append("  o9010 if [#1 LT 0.5]")
        gcode.append("    G00 X[#32+#1002] Y[#33+#1003]")
        gcode.append("  o9010 else")
        gcode.append("    G01 X[#32+#1002] Y[#33+#1003]")
        gcode.append("  o9010 endif")
        gcode.append("o9000 endsub")
        gcode.append(
            "(===================================================================)")

        gcode.append("#1000 = %.4f" % (GSafeZ))
        gcode.append('#1001 = %.4f  ( Engraving Depth Z )' % (GDepth))

        gcode.append('#1004 = %.4f  ( X Scale )' % (GXScale))
        gcode.append('#1005 = %.4f  ( Y Scale )' % (GYScale))
        gcode.append('#1006 = %.4f  ( Angle )' % (GAngle))
        gcode.append(GPreamble)
        gcode.append(
            "(===================================================================)")
        gcode.append('( Engraving: "%s" )' % (GString))
        gcode.append('( Line %d )' % (visit))
        str1 = '#1002 = %.4f  ( X Start )' % (GXStart)
        if GXLineOffset:
            if GXIndentList.find(str(visit)) != -1:
                str1 = '#1002 = %.4f  ( X Start )' % (GXStart + GXLineOffset)
        gcode.append(str1)
        gcode.append('#1003 = %.4f  ( Y Start )' % (GYStart))
        gcode.append(
            "(===================================================================)\n")

    gcode.append('G0 Z#1000')

    font = parse(file)          # build stroke lists from font file
    file.close()

    font_line_height = max(font[key].get_ymax() for key in font)
    font_word_space = max(font[key].get_xmax()
                          for key in font) * (GWSpaceP/100.0)
    font_char_space = font_word_space * (GCSpaceP / 100.0)

    xoffset = 0                 # distance along raw string in font units

    # calc a plot scale so we can show about first 15 chars of string
    # in the preview window
    PlotScale = 15 * font['A'].get_xmax() * GXScale / 150

    for char in GString:
        if char == ' ':
            xoffset += font_word_space
            continue
        try:
            gcode.append("(character '%s')" % sanitize(char))

            first_stroke = True
            for stroke in font[char].stroke_list:
                #               gcode.append("(%f,%f to %f,%f)" %(stroke.xstart,stroke.ystart,stroke.xend,stroke.yend ))
                dx = oldx - stroke.xstart
                dy = oldy - stroke.ystart
                dist = sqrt(dx*dx + dy*dy)

                x1 = stroke.xstart + xoffset
                y1 = stroke.ystart
                if GMirror == 1:
                    x1 = -x1
                if GFlip == 1:
                    y1 = -y1

                # check and see if we need to move to a new discontinuous start point
                if (dist > 0.001) or first_stroke:
                    first_stroke = False
                    # lift engraver, rapid to start of stroke, drop tool
                    # perform transformations
                    x1,y1 = Rotn(x1, y1, 1, 1, 0, visit)
                    gcode.append("G0 Z#1000")
                    gcode.append('G0 Z2 X%.4f Y%.4f' % (x1, y1))
                    gcode.append("G1 Z#1001")

                x2 = stroke.xend + xoffset
                y2 = stroke.yend
                if GMirror == 1:
                    x2 = -x2
                if GFlip == 1:
                    y2 = -y2
                x2,y2 = Rotn(x2, y2, 1, 1, 0, visit)
                gcode.append('G1 Z0.1 X%.4f Y%.4f' % (x2, y2))
                oldx, oldy = stroke.xend, stroke.yend

            # move over for next character
            char_width = font[char].get_xmax()
            xoffset += font_char_space + char_width

        except KeyError:
            gcode.append(
                "(warning: character '0x%02X' not found in font defn)" % ord(char))

        gcode.append("")       # blank line after every char block

    gcode.append('G0 Z#1000')     # final engraver up

    # finish up with icing
    if last:
        gcode.append(GPostamble)

    for line in gcode:
        sys.stdout.write(line+'\n')

################################################################################################################


def help_message():
    print('''engrave-lines.py G-Code Engraving Generator for command-line usage
            (C) ArcEye <2012> 
            based upon code from engrave-11.py
            Copyright (C) <2008>  <Lawrence Glaister> <ve7it at shaw dot ca>''')

    print('''engrave-lines.py -X -x -i -Y -y -S -s -Z -D -C -W -M -F -P -p -0 -1 -2 -3 ..............
       Options: 
       -h   Display this help message
       -X   Start X value                       Defaults to 0
       -x   X offset between lines              Defaults to 0
       -i   X indent line list                  String of lines to indent in single quotes
       -Y   Start Y value                       Defaults to 0
       -y   Y offset between lines              Defaults to 0
       -S   X Scale                             Defaults to 1
       -s   Y Scale                             Defaults to 1       
       -Z   Safe Z for moves                    Defaults to 2mm
       -D   Z depth for engraving               Defaults to 0.1mm
       -C   Charactor Space %                   Defaults to 25%
       -W   Word Space %                        Defaults to 100%
       -M   Mirror                              Defaults to 0 (No)
       -F   Flip                                Defaults to 0 (No)
       -P   Preamble g code                     Defaults to "G17 G21 G40 G90 G64 P0.003 F50"
       -p   Postamble g code                    Defaults to "M2"
       -0   Line0 string follow this
       -1   Line1 string follow this
       -2   Line2 string follow this        
       -3   Line3 string follow this
       -4   Line4 string follow this
       -5   Line5 string follow this
       -6   Line6 string follow this
       -7   Line7 string follow this                                
       -8   Line8 string follow this
       -9   Line9 string follow this
      Example
      engrave-lines.py -X7.5 -x5 -i'123' -Y12.75 -y5.25 -S0.4 -s0.5 -Z2 -D0.1 -0'Line0' -1'Line1' -2'Line2' -3'Line3' > test.ngc
    ''')
    sys.exit(0)

# ===============================================================================================================


def TextToGcode(
    stringlist=[],
    SafeZ=GSafeZ,
    XStart=GXStart,
    XLineOffset=GXLineOffset,
    XIndentList=GXIndentList,
    YStart=GYStart,
    YLineOffset=GYLineOffset,
    Depth=GDepth,
    XScale=GXScale,
    YScale=GYScale,
    CSpaceP=GCSpaceP,
    WSpaceP=GWSpaceP,
    Angle=GAngle,
    Mirror=GMirror,
    Flip=GFlip,
    Preamble=GPreamble,
    Postamble=GPostamble,
    Font=GFont
):

    debug = 0
    # need to declare the globals because we want to write to them
    # otherwise python will create a local of the same name and
    # not change the global - stupid python
    global GSafeZ
    global GXStart
    global GXLineOffset
    global GXIndentList
    global GYStart
    global GYLineOffset
    global GDepth
    global GXScale
    global GYScale
    global GCSpaceP
    global GWSpaceP
    global GAngle
    global GMirror
    global GFlip
    global GPreamble
    global GPostamble
    global Gstringlist
    global Gfontfile

    if len(stringlist) > 0:
        Gstringlist = [elem for elem in stringlist if isinstance(elem, str)]
        assert len(Gstringlist) > 0 and len(Gstringlist) < 11

    if XStart:
        GXStart = float(XStart)

    if XLineOffset:
        GXLineOffset = float(XLineOffset)

    if XIndentList:
        GXIndentList = XIndentList

    if YStart:
        GYStart = float(YStart)

    if YLineOffset:
        GYLineOffset = float(YLineOffset)

    if XScale:
        GXScale = float(XScale)

    if YScale:
        GYScale = float(YScale)

    if SafeZ:
        GSafeZ = float(SafeZ)

    if Depth:
        GDepth = float(Depth)

    if CSpaceP:
        GCSpaceP = float(CSpaceP)

    if WSpaceP:
        GWSpaceP = float(WSpaceP)

    if Angle:
        GAngle = float(Angle)

    if Mirror:
        GMirror = float(Mirror)

    if Flip:
        GFlip = float(Flip)

    if Preamble:
        GPreamble = Preamble

    if Postamble:
        GPostamble = Postamble

    if Font:
        Gfontfile = "./cxf-fonts/%s" % (Font)

    for index, item in enumerate(stringlist):
        code(item, index, index == (len(stringlist) - 1))


# ===============================================================================================

if __name__ == "__main__":
    TextToGcode(["hello"])

# ===============================================================================================END
