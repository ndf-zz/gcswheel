# SPDX-License-Identifier: MIT
"""gcswheel

 Draw a gear, speed and cadence rotary slide rule for the
 following products:

   gear inches = 27 x chainring teeth / cog teeth
   speed = rollout x cadence x gear ratio

"""
from math import log, pi
import gi
import cairo

# Assume 2090mm rollout for 700x20c wheel+tyre
TYRE_C = 2.090

# output filename prefix
FILEPFX = 'gcswheel'


def calculate():
    """Calculate and return scale markings:

         gi : Gear Inches
         cr: Chainring Teeth
         cg: Cog teeth
         km: Speed
         cd: Cadence

       Rows are:
        [orig val, corrected val, logval, scaled log val, rot pos]
    """
    data = {'gi': [], 'cr': [], 'cg': [], 'km': [], 'cd': []}

    # Gear Inches (converts to gear ratio)
    i = 68
    while i <= 112:
        ng = i
        nf = i / 27.0
        nlf = log(nf)
        rad = 0.0
        data['gi'].append([ng, nf, nlf, rad, 0.0])
        i += 1

    # Chainring Teeth
    i = 42
    while i <= 52:
        nr = i
        lnr = log(i)
        data['cr'].append([nr, None, lnr, None, 0.0])
        i += 1

    # Cog Teeth
    i = 18
    while i >= 12:
        nc = i
        lnc = log(i)
        data['cg'].append([nc, None, lnc, None, 0.0])
        i -= 1

    # Speed in km/h converted to wheel speed in hertz
    # km/h * 1000/3600 -> m/s  then divide by circumference for hertz
    i = 35
    while i <= 55:
        nk = i
        kf = nk / (3.6 * TYRE_C)  # divide wheelsize out of speed in advance
        lkf = log(kf)
        data['km'].append([nk, kf, lkf, None, 0.0])
        i += 1

    # Cadence in rpm converted to hertz
    i = 80
    while i <= 150:
        nd = i
        df = nd / 60.0
        ldf = log(df)
        data['cd'].append([nd, df, ldf, None, 0.0])
        i += 1

    # Use Gear inches to determine base axis scaling
    girawmin = data['gi'][0][2]
    girawmax = data['gi'][-1][2]
    girangerad = 0.82 * pi
    girangeraw = girawmax - girawmin
    gimod = girangerad / girangeraw

    # then scale values and position at zero
    for g in data['gi']:
        rad = gimod * g[2]
        g[3] = rad
    gimin = data['gi'][0][3]
    for g in data['gi']:
        if g[0] != 60:
            g[4] = g[3] - gimin

    # CR is on same scale as GI but rotated counter-clockwise
    crmin = 0.525 * pi
    for r in data['cr']:
        rad = gimod * r[2]
        r[3] = rad
        r[4] = rad - crmin

    # COG is on inverted scale
    cogoft = 5
    data['refpt'] = data['cr'][cogoft][4]
    cgmin = gimin - data['cr'][cogoft][3]
    cgmod = -1.0 * gimod
    for c in data['cg']:
        rad = cgmod * c[2]
        c[3] = rad
        c[4] = rad - cgmin

    # Speed/cadence scales are referenced to log of gear ratio
    gearoft = 3
    data['sprefpt'] = data['cg'][gearoft][4]
    kmmin = -0.32 * pi
    for k in data['km']:
        rad = gimod * k[2]
        k[3] = rad
        k[4] = rad - kmmin

    cadmin = data['gi'][0][3] - kmmin
    for d in data['cd']:
        rad = gimod * d[2]
        d[3] = rad
        d[4] = rad + cadmin + data['sprefpt']

    return data


def place_text(c, x, y, msg):
    """Draw msg at x,y in the current transform c"""
    if msg:
        c.save()
        c.set_font_size(0.02)
        x_bearing, y_bearing, width, height = c.text_extents(msg)[:4]
        c.move_to(x, 0.3 * height)
        c.show_text(msg)
        c.restore()


def scalemark(c, a, x1, x2, lbl, right=False):
    """Draw mark on a scale"""
    c.save()
    c.rotate(a)
    c.move_to(x1, 0.0)
    c.line_to(x2, 0.0)
    c.stroke()
    if right:
        place_text(c, x2 - 0.04, -0.018, lbl)
    else:
        place_text(c, x2 + 0.01, -0.018, lbl)
    c.restore()


def coverbox(c, a, x1, x2):
    """Draw a highlight box for the top layer"""
    c.save()
    c.rotate(a)
    c.rectangle(x1, -0.018, x2 - x1, 0.036)
    c.stroke()
    c.restore()


def drawpage(c, layers, data):
    """Draw the selected layers into the provided context"""
    c.select_font_face("Nimbus Sans", cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(0, 0, 0)

    c.set_line_width(0.001)

    # middle cut
    if 2 in layers:
        c.new_sub_path()
        c.arc(0.0, 0.0, 0.393, 0.0, 2.0 * pi)

    # bottom/top cut
    if 1 in layers or 3 in layers:
        c.new_sub_path()
        c.arc(0.0, 0.0, 0.49, 0.0, 2.0 * pi)

    # centrepoint always drawn
    c.new_sub_path()
    c.arc(0.0, 0.0, 0.01, 0.0, 2.0 * pi)
    c.move_to(-0.015, 0.0)
    c.line_to(0.015, 0.0)
    c.move_to(0.0, -0.015)
    c.line_to(0.0, 0.015)
    c.stroke()

    c.set_line_width(0.002)

    if 3 in layers:
        # main marker
        c.new_sub_path()
        c.arc(0.0, 0.0, 0.4, data['gi'][0][4], data['gi'][-1][4])
        c.stroke()
        #GI scale marks
        for g in data['gi']:
            if g[0] % 2 == 0:
                scalemark(c, g[4], 0.4, 0.42, '{0}"'.format(g[0]))
            else:
                scalemark(c, g[4], 0.4, 0.41, '')

    # Chainring marks
    if 3 in layers:
        c.new_sub_path()
        c.arc(0.0, 0.0, 0.4, data['cr'][0][4], data['cr'][-1][4])
        c.stroke()
        for r in data['cr']:
            scalemark(c, r[4], 0.4, 0.42, '{0}t'.format(r[0]))

    # Cog Marks
    if 2 in layers:
        c.new_sub_path()
        c.arc(0.0, 0.0, 0.386, data['cg'][0][4], data['cg'][-1][4])
        c.stroke()
        scalemark(c, data['refpt'], 0.386, 0.36, 'CR', True)
        for g in data['cg']:
            scalemark(c, g[4], 0.386, 0.36, '{0}t'.format(g[0]), True)

    c.set_source_rgb(0.0, 0.0, 1.0)
    # Speed, Cadence, Gear on top layer
    if 1 in layers:
        scalemark(c, data['sprefpt'], 0.31, 0.28, 'GR', True)
        coverbox(c, data['sprefpt'], 0.31, 0.48)
        c.new_sub_path()
        c.arc(0.0, 0.0, 0.386, data['cd'][0][4], data['cd'][-1][4])
        for d in data['cd']:
            if d[0] % 5 == 0:
                scalemark(c, d[4], 0.386, 0.36, '{0}'.format(d[0]), True)
            else:
                scalemark(c, d[4], 0.386, 0.373, '')

    ## KM/H on base layer
    if 3 in layers:
        c.new_sub_path()
        c.arc(0.0, 0.0, 0.4, data['km'][0][4], data['km'][-1][4])
        for k in data['km']:
            if k[0] % 5 == 0:
                scalemark(c, k[4], 0.4, 0.42, '{0}'.format(k[0]))
            else:
                scalemark(c, k[4], 0.4, 0.41, '')


def output_layers(file, layers, data):
    v = mm2pt(100)
    p = mm2pt(80)
    d = 0.5 * (v - p)
    s = cairo.PDFSurface(file, v, v)
    cx = cairo.Context(s)
    # transform context to unit size
    cx.translate(d, d)
    cx.scale(p, p)
    cx.translate(0.5, 0.5)
    drawpage(cx, layers, data)
    s.flush()
    s.finish()


def mm2pt(mm=1):
    """25.4mm -> 72pt (1 inch)"""
    return float(mm) * 72.0 / 25.4


if __name__ == '__main__':
    data = calculate()
    with open(FILEPFX + '_combined.pdf', 'wb') as f:
        output_layers(f, (1, 2, 3), data)
    with open(FILEPFX + '_base.pdf', 'wb') as f:
        output_layers(f, (3, ), data)
    with open(FILEPFX + '_middle.pdf', 'wb') as f:
        output_layers(f, (2, ), data)
    with open(FILEPFX + '_top.pdf', 'wb') as f:
        output_layers(f, (1, ), data)
