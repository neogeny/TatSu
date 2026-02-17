# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# from: https://www.unicode.org/charts/nameslist/n_2500.html
from __future__ import annotations

""" Box Drawing
    © 2003–2025 Unicode, Inc. 
    Unicode and the Unicode Logo are registered trademarks of Unicode, Inc., 
    in the U.S. and other countries. For terms of use and license, 
    see https://www.unicode.org/terms_of_use.html.
"""

# NOTE:
#   All of these characters are intended for compatibility
#   with character cell graphic sets in use prior to 1990.

# fmt: off
BOX_DRAWING = [
    # Light and heavy solid lines
    ('\u2500', '─', "BOX DRAWINGS LIGHT HORIZONTAL"),
    #           =    Videotex Mosaic DG 15
    #           →    1FBAF 🮯 box drawings light horizontal with vertical stroke
    ('\u2501', '━', "BOX DRAWINGS HEAVY HORIZONTAL"),
    ('\u2502', '│', "BOX DRAWINGS LIGHT VERTICAL"),
    #           =    Videotex Mosaic DG 14
    ('\u2503', '┃', "BOX DRAWINGS HEAVY VERTICAL"),

    # Light and heavy dashed lines
    ('\u2504', '┄', "BOX DRAWINGS LIGHT TRIPLE DASH HORIZONTAL"),
    ('\u2505', '┅', "BOX DRAWINGS HEAVY TRIPLE DASH HORIZONTAL"),
    ('\u2506', '┆', "BOX DRAWINGS LIGHT TRIPLE DASH VERTICAL"),
    ('\u2507', '┇', "BOX DRAWINGS HEAVY TRIPLE DASH VERTICAL"),
    ('\u2508', '┈', "BOX DRAWINGS LIGHT QUADRUPLE DASH HORIZONTAL"),
    ('\u2509', '┉', "BOX DRAWINGS HEAVY QUADRUPLE DASH HORIZONTAL"),
    ('\u250A', '┊', "BOX DRAWINGS LIGHT QUADRUPLE DASH VERTICAL"),
    ('\u250B', '┋', "BOX DRAWINGS HEAVY QUADRUPLE DASH VERTICAL"),

    # Light and heavy line box components
    ('\u250C', '┌', "BOX DRAWINGS LIGHT DOWN AND RIGHT"),
    #           =    Videotex Mosaic DG 16
    ('\u250D', '┍', "BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY"),
    ('\u250E', '┎', "BOX DRAWINGS DOWN HEAVY AND RIGHT LIGHT"),
    ('\u250F', '┏', "BOX DRAWINGS HEAVY DOWN AND RIGHT"),
    ('\u2510', '┐', "BOX DRAWINGS LIGHT DOWN AND LEFT"),
    #           =    Videotex Mosaic DG 17
    ('\u2511', '┑', "BOX DRAWINGS DOWN LIGHT AND LEFT HEAVY"),
    ('\u2512', '┒', "BOX DRAWINGS DOWN HEAVY AND LEFT LIGHT"),
    ('\u2513', '┓', "BOX DRAWINGS HEAVY DOWN AND LEFT"),
    ('\u2514', '└', "BOX DRAWINGS LIGHT UP AND RIGHT"),
    #           =    Videotex Mosaic DG 18
    ('\u2515', '┕', "BOX DRAWINGS UP LIGHT AND RIGHT HEAVY"),
    ('\u2516', '┖', "BOX DRAWINGS UP HEAVY AND RIGHT LIGHT"),
    ('\u2517', '┗', "BOX DRAWINGS HEAVY UP AND RIGHT"),
    ('\u2518', '┘', "BOX DRAWINGS LIGHT UP AND LEFT"),
    #           =    Videotex Mosaic DG 19
    ('\u2519', '┙', "BOX DRAWINGS UP LIGHT AND LEFT HEAVY"),
    ('\u251A', '┚', "BOX DRAWINGS UP HEAVY AND LEFT LIGHT"),
    ('\u251B', '┛', "BOX DRAWINGS HEAVY UP AND LEFT"),
    ('\u251C', '├', "BOX DRAWINGS LIGHT VERTICAL AND RIGHT"),
    #           =    Videotex Mosaic DG 20
    ('\u251D', '┝', "BOX DRAWINGS VERTICAL LIGHT AND RIGHT HEAVY"),
    #           =    Videotex Mosaic DG 03
    ('\u251E', '┞', "BOX DRAWINGS UP HEAVY AND RIGHT DOWN LIGHT"),
    ('\u251F', '┟', "BOX DRAWINGS DOWN HEAVY AND RIGHT UP LIGHT"),
    ('\u2520', '┠', "BOX DRAWINGS VERTICAL HEAVY AND RIGHT LIGHT"),
    ('\u2521', '┡', "BOX DRAWINGS DOWN LIGHT AND RIGHT UP HEAVY"),
    ('\u2522', '┢', "BOX DRAWINGS UP LIGHT AND RIGHT DOWN HEAVY"),
    ('\u2523', '┣', "BOX DRAWINGS HEAVY VERTICAL AND RIGHT"),
    ('\u2524', '┤', "BOX DRAWINGS LIGHT VERTICAL AND LEFT"),
    #           =    Videotex Mosaic DG 21
    ('\u2525', '┥', "BOX DRAWINGS VERTICAL LIGHT AND LEFT HEAVY"),
    #           =    Videotex Mosaic DG 04
    ('\u2526', '┦', "BOX DRAWINGS UP HEAVY AND LEFT DOWN LIGHT"),
    ('\u2527', '┧', "BOX DRAWINGS DOWN HEAVY AND LEFT UP LIGHT"),
    ('\u2528', '┨', "BOX DRAWINGS VERTICAL HEAVY AND LEFT LIGHT"),
    ('\u2529', '┩', "BOX DRAWINGS DOWN LIGHT AND LEFT UP HEAVY"),
    ('\u252A', '┪', "BOX DRAWINGS UP LIGHT AND LEFT DOWN HEAVY"),
    ('\u252B', '┫', "BOX DRAWINGS HEAVY VERTICAL AND LEFT"),
    ('\u252C', '┬', "BOX DRAWINGS LIGHT DOWN AND HORIZONTAL"),
    #           =    Videotex Mosaic DG 22
    ('\u252D', '┭', "BOX DRAWINGS LEFT HEAVY AND RIGHT DOWN LIGHT"),
    ('\u252E', '┮', "BOX DRAWINGS RIGHT HEAVY AND LEFT DOWN LIGHT"),
    ('\u252F', '┯', "BOX DRAWINGS DOWN LIGHT AND HORIZONTAL HEAVY"),
    #           =    Videotex Mosaic DG 02
    ('\u2530', '┰', "BOX DRAWINGS DOWN HEAVY AND HORIZONTAL LIGHT"),
    ('\u2531', '┱', "BOX DRAWINGS RIGHT LIGHT AND LEFT DOWN HEAVY"),
    ('\u2532', '┲', "BOX DRAWINGS LEFT LIGHT AND RIGHT DOWN HEAVY"),
    ('\u2533', '┳', "BOX DRAWINGS HEAVY DOWN AND HORIZONTAL"),
    ('\u2534', '┴', "BOX DRAWINGS LIGHT UP AND HORIZONTAL"),
    #           =    Videotex Mosaic DG 23
    ('\u2535', '┵', "BOX DRAWINGS LEFT HEAVY AND RIGHT UP LIGHT"),
    ('\u2536', '┶', "BOX DRAWINGS RIGHT HEAVY AND LEFT UP LIGHT"),
    ('\u2537', '┷', "BOX DRAWINGS UP LIGHT AND HORIZONTAL HEAVY"),
    #           =    Videotex Mosaic DG 01
    ('\u2538', '┸', "BOX DRAWINGS UP HEAVY AND HORIZONTAL LIGHT"),
    ('\u2539', '┹', "BOX DRAWINGS RIGHT LIGHT AND LEFT UP HEAVY"),
    ('\u253A', '┺', "BOX DRAWINGS LEFT LIGHT AND RIGHT UP HEAVY"),
    ('\u253B', '┻', "BOX DRAWINGS HEAVY UP AND HORIZONTAL"),
    ('\u253C', '┼', "BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL"),
    #           =    Videotex Mosaic DG 24
    ('\u253D', '┽', "BOX DRAWINGS LEFT HEAVY AND RIGHT VERTICAL LIGHT"),
    ('\u253E', '┾', "BOX DRAWINGS RIGHT HEAVY AND LEFT VERTICAL LIGHT"),
    ('\u253F', '┿', "BOX DRAWINGS VERTICAL LIGHT AND HORIZONTAL HEAVY"),
    #           =    Videotex Mosaic DG 13
    ('\u2540', '╀', "BOX DRAWINGS UP HEAVY AND DOWN HORIZONTAL LIGHT"),
    ('\u2541', '╁', "BOX DRAWINGS DOWN HEAVY AND UP HORIZONTAL LIGHT"),
    ('\u2542', '╂', "BOX DRAWINGS VERTICAL HEAVY AND HORIZONTAL LIGHT"),
    ('\u2543', '╃', "BOX DRAWINGS LEFT UP HEAVY AND RIGHT DOWN LIGHT"),
    ('\u2544', '╄', "BOX DRAWINGS RIGHT UP HEAVY AND LEFT DOWN LIGHT"),
    ('\u2545', '╅', "BOX DRAWINGS LEFT DOWN HEAVY AND RIGHT UP LIGHT"),
    ('\u2546', '╆', "BOX DRAWINGS RIGHT DOWN HEAVY AND LEFT UP LIGHT"),
    ('\u2547', '╇', "BOX DRAWINGS DOWN LIGHT AND UP HORIZONTAL HEAVY"),
    ('\u2548', '╈', "BOX DRAWINGS UP LIGHT AND DOWN HORIZONTAL HEAVY"),
    ('\u2549', '╉', "BOX DRAWINGS RIGHT LIGHT AND LEFT VERTICAL HEAVY"),
    ('\u254A', '╊', "BOX DRAWINGS LEFT LIGHT AND RIGHT VERTICAL HEAVY"),
    ('\u254B', '╋', "BOX DRAWINGS HEAVY VERTICAL AND HORIZONTAL"),

    # Light and heavy dashed lines
    ('\u254C', '╌', "BOX DRAWINGS LIGHT DOUBLE DASH HORIZONTAL"),
    ('\u254D', '╍', "BOX DRAWINGS HEAVY DOUBLE DASH HORIZONTAL"),
    ('\u254E', '╎', "BOX DRAWINGS LIGHT DOUBLE DASH VERTICAL"),
    ('\u254F', '╏', "BOX DRAWINGS HEAVY DOUBLE DASH VERTICAL"),

    # Double lines
    ('\u2550', '═', "BOX DRAWINGS DOUBLE HORIZONTAL"),
    ('\u2551', '║', "BOX DRAWINGS DOUBLE VERTICAL"),

    # Light and double line box components
    ('\u2552', '╒', "BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE"),
    ('\u2553', '╓', "BOX DRAWINGS DOWN DOUBLE AND RIGHT SINGLE"),
    ('\u2554', '╔', "BOX DRAWINGS DOUBLE DOWN AND RIGHT"),
    ('\u2555', '╕', "BOX DRAWINGS DOWN SINGLE AND LEFT DOUBLE"),
    ('\u2556', '╖', "BOX DRAWINGS DOWN DOUBLE AND LEFT SINGLE"),
    ('\u2557', '╗', "BOX DRAWINGS DOUBLE DOWN AND LEFT"),
    ('\u2558', '╘', "BOX DRAWINGS UP SINGLE AND RIGHT DOUBLE"),
    ('\u2559', '╙', "BOX DRAWINGS UP DOUBLE AND RIGHT SINGLE"),
    ('\u255A', '╚', "BOX DRAWINGS DOUBLE UP AND RIGHT"),
    ('\u255B', '╛', "BOX DRAWINGS UP SINGLE AND LEFT DOUBLE"),
    ('\u255C', '╜', "BOX DRAWINGS UP DOUBLE AND LEFT SINGLE"),
    ('\u255D', '╝', "BOX DRAWINGS DOUBLE UP AND LEFT"),
    ('\u255E', '╞', "BOX DRAWINGS VERTICAL SINGLE AND RIGHT DOUBLE"),
    ('\u255F', '╟', "BOX DRAWINGS VERTICAL DOUBLE AND RIGHT SINGLE"),
    ('\u2560', '╠', "BOX DRAWINGS DOUBLE VERTICAL AND RIGHT"),
    ('\u2561', '╡', "BOX DRAWINGS VERTICAL SINGLE AND LEFT DOUBLE"),
    ('\u2562', '╢', "BOX DRAWINGS VERTICAL DOUBLE AND LEFT SINGLE"),
    ('\u2563', '╣', "BOX DRAWINGS DOUBLE VERTICAL AND LEFT"),
    ('\u2564', '╤', "BOX DRAWINGS DOWN SINGLE AND HORIZONTAL DOUBLE"),
    ('\u2565', '╥', "BOX DRAWINGS DOWN DOUBLE AND HORIZONTAL SINGLE"),
    ('\u2566', '╦', "BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL"),
    ('\u2567', '╧', "BOX DRAWINGS UP SINGLE AND HORIZONTAL DOUBLE"),
    ('\u2568', '╨', "BOX DRAWINGS UP DOUBLE AND HORIZONTAL SINGLE"),
    ('\u2569', '╩', "BOX DRAWINGS DOUBLE UP AND HORIZONTAL"),
    ('\u256A', '╪', "BOX DRAWINGS VERTICAL SINGLE AND HORIZONTAL DOUBLE"),
    ('\u256B', '╫', "BOX DRAWINGS VERTICAL DOUBLE AND HORIZONTAL SINGLE"),
    ('\u256C', '╬', "BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL"),

    # Character cell arcs
    ('\u256D', '╭', "BOX DRAWINGS LIGHT ARC DOWN AND RIGHT"),
    ('\u256E', '╮', "BOX DRAWINGS LIGHT ARC DOWN AND LEFT"),
    ('\u256F', '╯', "BOX DRAWINGS LIGHT ARC UP AND LEFT"),
    ('\u2570', '╰', "BOX DRAWINGS LIGHT ARC UP AND RIGHT"),

    # Character cell diagonals
    # For a more extensive set of legacy terminal graphic character cell diagonals,
    # see also 1FBA0-1FBAE in the Symbols for Legacy Computing block.
    ('\u2571', '╱', "BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT"),
    #           •    not intended for mathematical symbol \diagup
    #           →    002F / solidus
    #           →    2044 ⁄ fraction slash
    #           →    2215 ∕ division slash
    ('\u2572', '╲', "BOX DRAWINGS LIGHT DIAGONAL UPPER LEFT TO LOWER RIGHT"),
    #           •    not intended for mathematical symbol \diagdown
    #           →    005C \ reverse solidus
    #           →    2216 ∖ set minus
    #           →    29F5 ⧵ reverse solidus operator
    ('\u2573', '╳', "BOX DRAWINGS LIGHT DIAGONAL CROSS"),
    #           →    2613 ☓ saltire
    #           →    2715 ✕ multiplication x

    # Light and heavy half lines
    ('\u2574', '╴', "BOX DRAWINGS LIGHT LEFT"),
    ('\u2575', '╵', "BOX DRAWINGS LIGHT UP"),
    ('\u2576', '╶', "BOX DRAWINGS LIGHT RIGHT"),
    ('\u2577', '╷', "BOX DRAWINGS LIGHT DOWN"),
    ('\u2578', '╸', "BOX DRAWINGS HEAVY LEFT"),
    ('\u2579', '╹', "BOX DRAWINGS HEAVY UP"),
    ('\u257A', '╺', "BOX DRAWINGS HEAVY RIGHT"),
    ('\u257B', '╻', "BOX DRAWINGS HEAVY DOWN"),

    # Mixed light and heavy lines
    ('\u257C', '╼', "BOX DRAWINGS LIGHT LEFT AND HEAVY RIGHT"),
    ('\u257D', '╽', "BOX DRAWINGS LIGHT UP AND HEAVY DOWN"),
    ('\u257E', '╾', "BOX DRAWINGS HEAVY LEFT AND LIGHT RIGHT"),
    ('\u257F', '╿', "BOX DRAWINGS HEAVY UP AND LIGHT DOWN"),

    ('\U0001F51A', '🔚', "END WITH LEFTWARDS ARROW ABOVE"),
]
