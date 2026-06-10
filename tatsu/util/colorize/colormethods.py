from __future__ import annotations

from typing import Self, cast


class ColorMethods:
    def fg(self, value: int) -> Self:
        return self

    def bg(self, value: int) -> Self:
        return self

    def acid_green(self) -> Self:
        return self.fg(148)

    def acid_green_bg(self) -> Self:
        return self.bg(148)

    def amethyst(self) -> Self:
        return self.fg(99)

    def amethyst_bg(self) -> Self:
        return self.bg(99)

    def aquamarine_2(self) -> Self:
        return self.fg(86)

    def aquamarine_2_bg(self) -> Self:
        return self.bg(86)

    def aquamarine_3(self) -> Self:
        return self.fg(80)

    def aquamarine_3_bg(self) -> Self:
        return self.bg(80)

    def banana(self) -> Self:
        return self.fg(228)

    def banana_bg(self) -> Self:
        return self.bg(228)

    def black(self) -> Self:
        return self.fg(16)

    def black_bg(self) -> Self:
        return self.bg(16)

    def blue(self) -> Self:
        return self.fg(21)

    def blue_bg(self) -> Self:
        return self.bg(21)

    def blue_bright(self) -> Self:
        return self.fg(20)

    def blue_bright_bg(self) -> Self:
        return self.bg(20)

    def blue_violet(self) -> Self:
        return self.fg(56)

    def blue_violet_bg(self) -> Self:
        return self.bg(56)

    def bright_black(self) -> Self:
        return self.fg(8)

    def bright_black_bg(self) -> Self:
        return self.bg(8)

    def bright_blue(self) -> Self:
        return self.fg(12)

    def bright_blue_bg(self) -> Self:
        return self.bg(12)

    def bright_cyan(self) -> Self:
        return self.fg(14)

    def bright_cyan_bg(self) -> Self:
        return self.bg(14)

    def bright_green(self) -> Self:
        return self.fg(10)

    def bright_green_bg(self) -> Self:
        return self.bg(10)

    def bright_magenta(self) -> Self:
        return self.fg(13)

    def bright_magenta_bg(self) -> Self:
        return self.bg(13)

    def bright_red(self) -> Self:
        return self.fg(154)

    def bright_red_bg(self) -> Self:
        return self.bg(154)

    def bright_white(self) -> Self:
        return self.fg(15)

    def bright_white_bg(self) -> Self:
        return self.bg(15)

    def bright_yellow(self) -> Self:
        return self.fg(11)

    def bright_yellow_bg(self) -> Self:
        return self.bg(11)

    def brown(self) -> Self:
        return self.fg(94)

    def brown_bg(self) -> Self:
        return self.bg(94)

    def cadet_blue(self) -> Self:
        return self.fg(66)

    def cadet_blue_bg(self) -> Self:
        return self.bg(66)

    def chartreuse_1(self) -> Self:
        return self.fg(118)

    def chartreuse_1_bg(self) -> Self:
        return self.bg(118)

    def chartreuse_2(self) -> Self:
        return self.fg(112)

    def chartreuse_2_bg(self) -> Self:
        return self.bg(112)

    def chartreuse_3(self) -> Self:
        return self.fg(82)

    def chartreuse_3_bg(self) -> Self:
        return self.bg(82)

    def chartreuse_4(self) -> Self:
        return self.fg(76)

    def chartreuse_4_bg(self) -> Self:
        return self.bg(76)

    def chartreuse_5(self) -> Self:
        return self.fg(70)

    def chartreuse_5_bg(self) -> Self:
        return self.bg(70)

    def chartreuse_6(self) -> Self:
        return self.fg(64)

    def chartreuse_6_bg(self) -> Self:
        return self.bg(64)

    def clay(self) -> Self:
        return self.fg(138)

    def clay_bg(self) -> Self:
        return self.bg(138)

    def coral(self) -> Self:
        return self.fg(203)

    def coral_bg(self) -> Self:
        return self.bg(203)

    def cornflower_blue(self) -> Self:
        return self.fg(68)

    def cornflower_blue_bg(self) -> Self:
        return self.bg(68)

    def cornflower_blue_bright(self) -> Self:
        return self.fg(75)

    def cornflower_blue_bright_bg(self) -> Self:
        return self.bg(75)

    def cotton_candy(self) -> Self:
        return self.fg(218)

    def cotton_candy_bg(self) -> Self:
        return self.bg(218)

    def cream(self) -> Self:
        return self.fg(229)

    def cream_bg(self) -> Self:
        return self.bg(229)

    def crimson(self) -> Self:
        return self.fg(162)

    def crimson_bg(self) -> Self:
        return self.bg(162)

    def cyan(self) -> Self:
        return self.fg(51)

    def cyan_bg(self) -> Self:
        return self.bg(51)

    def cyan_bright(self) -> Self:
        return self.fg(45)

    def cyan_bright_bg(self) -> Self:
        return self.bg(45)

    def cyan_luminous(self) -> Self:
        return self.fg(50)

    def cyan_luminous_bg(self) -> Self:
        return self.bg(50)

    def cyan_medium(self) -> Self:
        return self.fg(43)

    def cyan_medium_bg(self) -> Self:
        return self.bg(43)

    def dark_blue(self) -> Self:
        return self.fg(18)

    def dark_blue_bg(self) -> Self:
        return self.bg(18)

    def dark_cyan(self) -> Self:
        return self.fg(36)

    def dark_cyan_bg(self) -> Self:
        return self.bg(36)

    def dark_green(self) -> Self:
        return self.fg(22)

    def dark_green_bg(self) -> Self:
        return self.bg(22)

    def dark_magenta(self) -> Self:
        return self.fg(53)

    def dark_magenta_bg(self) -> Self:
        return self.bg(53)

    def dark_orange(self) -> Self:
        return self.fg(208)

    def dark_orange_bg(self) -> Self:
        return self.bg(208)

    def dark_orange_3(self) -> Self:
        return self.fg(166)

    def dark_orange_3_bg(self) -> Self:
        return self.bg(166)

    def dark_red(self) -> Self:
        return self.fg(88)

    def dark_red_bg(self) -> Self:
        return self.bg(88)

    def dark_sea_green_1(self) -> Self:
        return self.fg(108)

    def dark_sea_green_1_bg(self) -> Self:
        return self.bg(108)

    def dark_sea_green_2(self) -> Self:
        return self.fg(107)

    def dark_sea_green_2_bg(self) -> Self:
        return self.bg(107)

    def dark_sea_green_3(self) -> Self:
        return self.fg(77)

    def dark_sea_green_3_bg(self) -> Self:
        return self.bg(77)

    def dark_sea_green_4(self) -> Self:
        return self.fg(71)

    def dark_sea_green_4_bg(self) -> Self:
        return self.bg(71)

    def dark_sea_green_5(self) -> Self:
        return self.fg(65)

    def dark_sea_green_5_bg(self) -> Self:
        return self.bg(65)

    def dark_sea_green_bright(self) -> Self:
        return self.fg(114)

    def dark_sea_green_bright_bg(self) -> Self:
        return self.bg(114)

    def dark_slate_gray_bright(self) -> Self:
        return self.fg(87)

    def dark_slate_gray_bright_bg(self) -> Self:
        return self.bg(87)

    def dark_turquoise(self) -> Self:
        return self.fg(44)

    def dark_turquoise_bg(self) -> Self:
        return self.bg(44)

    def dark_violet(self) -> Self:
        return self.fg(129)

    def dark_violet_bg(self) -> Self:
        return self.bg(129)

    def deep_pink_1(self) -> Self:
        return self.fg(156)

    def deep_pink_1_bg(self) -> Self:
        return self.bg(156)

    def deep_pink_2(self) -> Self:
        return self.fg(155)

    def deep_pink_2_bg(self) -> Self:
        return self.bg(155)

    def deep_pink_3(self) -> Self:
        return self.fg(125)

    def deep_pink_3_bg(self) -> Self:
        return self.bg(125)

    def deep_pink_4(self) -> Self:
        return self.fg(89)

    def deep_pink_4_bg(self) -> Self:
        return self.bg(89)

    def deep_pink_bright(self) -> Self:
        return self.fg(197)

    def deep_pink_bright_bg(self) -> Self:
        return self.bg(197)

    def deep_sky_blue_2(self) -> Self:
        return self.fg(39)

    def deep_sky_blue_2_bg(self) -> Self:
        return self.bg(39)

    def deep_sky_blue_3(self) -> Self:
        return self.fg(38)

    def deep_sky_blue_3_bg(self) -> Self:
        return self.bg(38)

    def deep_sky_blue_4(self) -> Self:
        return self.fg(32)

    def deep_sky_blue_4_bg(self) -> Self:
        return self.bg(32)

    def deep_sky_blue_5(self) -> Self:
        return self.fg(31)

    def deep_sky_blue_5_bg(self) -> Self:
        return self.bg(31)

    def deep_sky_blue_6(self) -> Self:
        return self.fg(25)

    def deep_sky_blue_6_bg(self) -> Self:
        return self.bg(25)

    def deep_sky_blue_7(self) -> Self:
        return self.fg(24)

    def deep_sky_blue_7_bg(self) -> Self:
        return self.bg(24)

    def dodger_blue_1(self) -> Self:
        return self.fg(33)

    def dodger_blue_1_bg(self) -> Self:
        return self.bg(33)

    def dodger_blue_2(self) -> Self:
        return self.fg(27)

    def dodger_blue_2_bg(self) -> Self:
        return self.bg(27)

    def dodger_blue_3(self) -> Self:
        return self.fg(26)

    def dodger_blue_3_bg(self) -> Self:
        return self.bg(26)

    def electric_indigo(self) -> Self:
        return self.fg(57)

    def electric_indigo_bg(self) -> Self:
        return self.bg(57)

    def fuchsia(self) -> Self:
        return self.fg(199)

    def fuchsia_bg(self) -> Self:
        return self.bg(199)

    def gold(self) -> Self:
        return self.fg(220)

    def gold_bg(self) -> Self:
        return self.bg(220)

    def gold_dark(self) -> Self:
        return self.fg(136)

    def gold_dark_bg(self) -> Self:
        return self.bg(136)

    def gold_medium(self) -> Self:
        return self.fg(178)

    def gold_medium_bg(self) -> Self:
        return self.bg(178)

    def gray003(self) -> Self:
        return self.fg(232)

    def gray003_bg(self) -> Self:
        return self.bg(232)

    def gray007(self) -> Self:
        return self.fg(233)

    def gray007_bg(self) -> Self:
        return self.bg(233)

    def gray011(self) -> Self:
        return self.fg(234)

    def gray011_bg(self) -> Self:
        return self.bg(234)

    def gray015(self) -> Self:
        return self.fg(235)

    def gray015_bg(self) -> Self:
        return self.bg(235)

    def gray019(self) -> Self:
        return self.fg(236)

    def gray019_bg(self) -> Self:
        return self.bg(236)

    def gray023(self) -> Self:
        return self.fg(237)

    def gray023_bg(self) -> Self:
        return self.bg(237)

    def gray027(self) -> Self:
        return self.fg(238)

    def gray027_bg(self) -> Self:
        return self.bg(238)

    def gray031(self) -> Self:
        return self.fg(239)

    def gray031_bg(self) -> Self:
        return self.bg(239)

    def gray035(self) -> Self:
        return self.fg(240)

    def gray035_bg(self) -> Self:
        return self.bg(240)

    def gray039(self) -> Self:
        return self.fg(241)

    def gray039_bg(self) -> Self:
        return self.bg(241)

    def gray043(self) -> Self:
        return self.fg(242)

    def gray043_bg(self) -> Self:
        return self.bg(242)

    def gray047(self) -> Self:
        return self.fg(243)

    def gray047_bg(self) -> Self:
        return self.bg(243)

    def gray051(self) -> Self:
        return self.fg(244)

    def gray051_bg(self) -> Self:
        return self.bg(244)

    def gray055(self) -> Self:
        return self.fg(245)

    def gray055_bg(self) -> Self:
        return self.bg(245)

    def gray059(self) -> Self:
        return self.fg(246)

    def gray059_bg(self) -> Self:
        return self.bg(246)

    def gray063(self) -> Self:
        return self.fg(247)

    def gray063_bg(self) -> Self:
        return self.bg(247)

    def gray067(self) -> Self:
        return self.fg(248)

    def gray067_bg(self) -> Self:
        return self.bg(248)

    def gray071(self) -> Self:
        return self.fg(249)

    def gray071_bg(self) -> Self:
        return self.bg(249)

    def gray075(self) -> Self:
        return self.fg(250)

    def gray075_bg(self) -> Self:
        return self.bg(250)

    def gray079(self) -> Self:
        return self.fg(251)

    def gray079_bg(self) -> Self:
        return self.bg(251)

    def gray083(self) -> Self:
        return self.fg(252)

    def gray083_bg(self) -> Self:
        return self.bg(252)

    def gray087(self) -> Self:
        return self.fg(253)

    def gray087_bg(self) -> Self:
        return self.bg(253)

    def gray091(self) -> Self:
        return self.fg(254)

    def gray091_bg(self) -> Self:
        return self.bg(254)

    def gray095(self) -> Self:
        return self.fg(255)

    def gray095_bg(self) -> Self:
        return self.bg(255)

    def green(self) -> Self:
        return self.fg(2)

    def green_bg(self) -> Self:
        return self.bg(2)

    def green_bright(self) -> Self:
        return self.fg(40)

    def green_bright_bg(self) -> Self:
        return self.bg(40)

    def green_forest(self) -> Self:
        return self.fg(28)

    def green_forest_bg(self) -> Self:
        return self.bg(28)

    def green_yellow(self) -> Self:
        return self.fg(185)

    def green_yellow_bg(self) -> Self:
        return self.bg(185)

    def grey_37(self) -> Self:
        return self.fg(59)

    def grey_37_bg(self) -> Self:
        return self.bg(59)

    def grey_46(self) -> Self:
        return self.fg(96)

    def grey_46_bg(self) -> Self:
        return self.bg(96)

    def grey_53(self) -> Self:
        return self.fg(101)

    def grey_53_bg(self) -> Self:
        return self.bg(101)

    def grey_53_neutral(self) -> Self:
        return self.fg(102)

    def grey_53_neutral_bg(self) -> Self:
        return self.bg(102)

    def grey_69(self) -> Self:
        return self.fg(139)

    def grey_69_bg(self) -> Self:
        return self.bg(139)

    def grey_74(self) -> Self:
        return self.fg(145)

    def grey_74_bg(self) -> Self:
        return self.bg(145)

    def grey_84(self) -> Self:
        return self.fg(181)

    def grey_84_bg(self) -> Self:
        return self.bg(181)

    def grey_84_neutral(self) -> Self:
        return self.fg(182)

    def grey_84_neutral_bg(self) -> Self:
        return self.bg(182)

    def honeydew(self) -> Self:
        return self.fg(188)

    def honeydew_bg(self) -> Self:
        return self.bg(188)

    def hot_pink(self) -> Self:
        return self.fg(204)

    def hot_pink_bg(self) -> Self:
        return self.bg(204)

    def hot_pink_bright(self) -> Self:
        return self.fg(205)

    def hot_pink_bright_bg(self) -> Self:
        return self.bg(205)

    def indian_red(self) -> Self:
        return self.fg(161)

    def indian_red_bg(self) -> Self:
        return self.bg(161)

    def ivory(self) -> Self:
        return self.fg(230)

    def ivory_bg(self) -> Self:
        return self.bg(230)

    def khaki_1(self) -> Self:
        return self.fg(144)

    def khaki_1_bg(self) -> Self:
        return self.bg(144)

    def khaki_2(self) -> Self:
        return self.fg(143)

    def khaki_2_bg(self) -> Self:
        return self.bg(143)

    def khaki_3(self) -> Self:
        return self.fg(142)

    def khaki_3_bg(self) -> Self:
        return self.bg(142)

    def khaki_4(self) -> Self:
        return self.fg(100)

    def khaki_4_bg(self) -> Self:
        return self.bg(100)

    def khaki_bright(self) -> Self:
        return self.fg(179)

    def khaki_bright_bg(self) -> Self:
        return self.bg(179)

    def lavender(self) -> Self:
        return self.fg(183)

    def lavender_bg(self) -> Self:
        return self.bg(183)

    def lavender_blue(self) -> Self:
        return self.fg(147)

    def lavender_blue_bg(self) -> Self:
        return self.bg(147)

    def lavender_purple(self) -> Self:
        return self.fg(141)

    def lavender_purple_bg(self) -> Self:
        return self.bg(141)

    def light_blue_sky(self) -> Self:
        return self.fg(153)

    def light_blue_sky_bg(self) -> Self:
        return self.bg(153)

    def light_coral(self) -> Self:
        return self.fg(210)

    def light_coral_bg(self) -> Self:
        return self.bg(210)

    def light_cyan_2(self) -> Self:
        return self.fg(189)

    def light_cyan_2_bg(self) -> Self:
        return self.bg(189)

    def light_cyan_3(self) -> Self:
        return self.fg(116)

    def light_cyan_3_bg(self) -> Self:
        return self.bg(116)

    def light_green_1(self) -> Self:
        return self.fg(119)

    def light_green_1_bg(self) -> Self:
        return self.bg(119)

    def light_green_2(self) -> Self:
        return self.fg(84)

    def light_green_2_bg(self) -> Self:
        return self.bg(84)

    def light_green_3(self) -> Self:
        return self.fg(83)

    def light_green_3_bg(self) -> Self:
        return self.bg(83)

    def light_grey_blue(self) -> Self:
        return self.fg(146)

    def light_grey_blue_bg(self) -> Self:
        return self.bg(146)

    def light_khaki(self) -> Self:
        return self.fg(186)

    def light_khaki_bg(self) -> Self:
        return self.bg(186)

    def light_orchid(self) -> Self:
        return self.fg(212)

    def light_orchid_bg(self) -> Self:
        return self.bg(212)

    def light_pink(self) -> Self:
        return self.fg(169)

    def light_pink_bg(self) -> Self:
        return self.bg(169)

    def light_salmon(self) -> Self:
        return self.fg(168)

    def light_salmon_bg(self) -> Self:
        return self.bg(168)

    def light_salmon_2(self) -> Self:
        return self.fg(174)

    def light_salmon_2_bg(self) -> Self:
        return self.bg(174)

    def light_salmon_3(self) -> Self:
        return self.fg(216)

    def light_salmon_3_bg(self) -> Self:
        return self.bg(216)

    def light_sea_green(self) -> Self:
        return self.fg(37)

    def light_sea_green_bg(self) -> Self:
        return self.bg(37)

    def light_sky_blue_3(self) -> Self:
        return self.fg(110)

    def light_sky_blue_3_bg(self) -> Self:
        return self.bg(110)

    def light_sky_blue_4(self) -> Self:
        return self.fg(109)

    def light_sky_blue_4_bg(self) -> Self:
        return self.bg(109)

    def light_slate_grey(self) -> Self:
        return self.fg(103)

    def light_slate_grey_bg(self) -> Self:
        return self.bg(103)

    def light_yellow_2(self) -> Self:
        return self.fg(227)

    def light_yellow_2_bg(self) -> Self:
        return self.bg(227)

    def lime(self) -> Self:
        return self.fg(46)

    def lime_bg(self) -> Self:
        return self.bg(46)

    def lime_green(self) -> Self:
        return self.fg(34)

    def lime_green_bg(self) -> Self:
        return self.bg(34)

    def magenta(self) -> Self:
        return self.fg(201)

    def magenta_bg(self) -> Self:
        return self.bg(201)

    def magenta_bright(self) -> Self:
        return self.fg(128)

    def magenta_bright_bg(self) -> Self:
        return self.bg(128)

    def magenta_dark(self) -> Self:
        return self.fg(127)

    def magenta_dark_bg(self) -> Self:
        return self.bg(127)

    def magenta_light(self) -> Self:
        return self.fg(207)

    def magenta_light_bg(self) -> Self:
        return self.bg(207)

    def magenta_luminous(self) -> Self:
        return self.fg(157)

    def magenta_luminous_bg(self) -> Self:
        return self.bg(157)

    def magenta_medium(self) -> Self:
        return self.fg(126)

    def magenta_medium_bg(self) -> Self:
        return self.bg(126)

    def magenta_neon(self) -> Self:
        return self.fg(159)

    def magenta_neon_bg(self) -> Self:
        return self.bg(159)

    def magenta_rose(self) -> Self:
        return self.fg(198)

    def magenta_rose_bg(self) -> Self:
        return self.bg(198)

    def magenta_vibrant(self) -> Self:
        return self.fg(158)

    def magenta_vibrant_bg(self) -> Self:
        return self.bg(158)

    def maroon(self) -> Self:
        return self.fg(52)

    def maroon_bg(self) -> Self:
        return self.bg(52)

    def medium_aquamarine(self) -> Self:
        return self.fg(72)

    def medium_aquamarine_bg(self) -> Self:
        return self.bg(72)

    def medium_aquamarine_bright(self) -> Self:
        return self.fg(79)

    def medium_aquamarine_bright_bg(self) -> Self:
        return self.bg(79)

    def medium_blue(self) -> Self:
        return self.fg(19)

    def medium_blue_bg(self) -> Self:
        return self.bg(19)

    def medium_orchid(self) -> Self:
        return self.fg(165)

    def medium_orchid_bg(self) -> Self:
        return self.bg(165)

    def medium_purple_1(self) -> Self:
        return self.fg(135)

    def medium_purple_1_bg(self) -> Self:
        return self.bg(135)

    def medium_purple_2(self) -> Self:
        return self.fg(134)

    def medium_purple_2_bg(self) -> Self:
        return self.bg(134)

    def medium_purple_3(self) -> Self:
        return self.fg(133)

    def medium_purple_3_bg(self) -> Self:
        return self.bg(133)

    def medium_purple_4(self) -> Self:
        return self.fg(104)

    def medium_purple_4_bg(self) -> Self:
        return self.bg(104)

    def medium_purple_5(self) -> Self:
        return self.fg(98)

    def medium_purple_5_bg(self) -> Self:
        return self.bg(98)

    def medium_purple_6(self) -> Self:
        return self.fg(97)

    def medium_purple_6_bg(self) -> Self:
        return self.bg(97)

    def medium_purple_7(self) -> Self:
        return self.fg(60)

    def medium_purple_7_bg(self) -> Self:
        return self.bg(60)

    def medium_red(self) -> Self:
        return self.fg(124)

    def medium_red_bg(self) -> Self:
        return self.bg(124)

    def medium_spring_green(self) -> Self:
        return self.fg(49)

    def medium_spring_green_bg(self) -> Self:
        return self.bg(49)

    def medium_turquoise(self) -> Self:
        return self.fg(73)

    def medium_turquoise_bg(self) -> Self:
        return self.bg(73)

    def mint_green(self) -> Self:
        return self.fg(151)

    def mint_green_bg(self) -> Self:
        return self.bg(151)

    def misty_rose(self) -> Self:
        return self.fg(224)

    def misty_rose_bg(self) -> Self:
        return self.bg(224)

    def navajo_white(self) -> Self:
        return self.fg(221)

    def navajo_white_bg(self) -> Self:
        return self.bg(221)

    def navy(self) -> Self:
        return self.fg(17)

    def navy_bg(self) -> Self:
        return self.bg(17)

    def olive_dark(self) -> Self:
        return self.fg(58)

    def olive_dark_bg(self) -> Self:
        return self.bg(58)

    def olive_drab_3(self) -> Self:
        return self.fg(113)

    def olive_drab_3_bg(self) -> Self:
        return self.bg(113)

    def orange(self) -> Self:
        return self.fg(214)

    def orange_bg(self) -> Self:
        return self.bg(214)

    def orange_darker(self) -> Self:
        return self.fg(160)

    def orange_darker_bg(self) -> Self:
        return self.bg(160)

    def orange_red(self) -> Self:
        return self.fg(202)

    def orange_red_bg(self) -> Self:
        return self.bg(202)

    def orange_yellow(self) -> Self:
        return self.fg(172)

    def orange_yellow_bg(self) -> Self:
        return self.bg(172)

    def orchid(self) -> Self:
        return self.fg(164)

    def orchid_bg(self) -> Self:
        return self.bg(164)

    def orchid_bright(self) -> Self:
        return self.fg(206)

    def orchid_bright_bg(self) -> Self:
        return self.bg(206)

    def orchid_light(self) -> Self:
        return self.fg(170)

    def orchid_light_bg(self) -> Self:
        return self.bg(170)

    def pale_green_1(self) -> Self:
        return self.fg(115)

    def pale_green_1_bg(self) -> Self:
        return self.bg(115)

    def pale_green_2(self) -> Self:
        return self.fg(85)

    def pale_green_2_bg(self) -> Self:
        return self.bg(85)

    def pale_green_3(self) -> Self:
        return self.fg(78)

    def pale_green_3_bg(self) -> Self:
        return self.bg(78)

    def pale_green_bright(self) -> Self:
        return self.fg(120)

    def pale_green_bright_bg(self) -> Self:
        return self.bg(120)

    def pale_turquoise_2(self) -> Self:
        return self.fg(123)

    def pale_turquoise_2_bg(self) -> Self:
        return self.bg(123)

    def pale_turquoise_3(self) -> Self:
        return self.fg(122)

    def pale_turquoise_3_bg(self) -> Self:
        return self.bg(122)

    def pale_violet_red(self) -> Self:
        return self.fg(132)

    def pale_violet_red_bg(self) -> Self:
        return self.bg(132)

    def peach_puff(self) -> Self:
        return self.fg(222)

    def peach_puff_bg(self) -> Self:
        return self.bg(222)

    def peru(self) -> Self:
        return self.fg(167)

    def peru_bg(self) -> Self:
        return self.bg(167)

    def pink(self) -> Self:
        return self.fg(200)

    def pink_bg(self) -> Self:
        return self.bg(200)

    def pink_light(self) -> Self:
        return self.fg(217)

    def pink_light_bg(self) -> Self:
        return self.bg(217)

    def plum_3(self) -> Self:
        return self.fg(163)

    def plum_3_bg(self) -> Self:
        return self.bg(163)

    def plume(self) -> Self:
        return self.fg(177)

    def plume_bg(self) -> Self:
        return self.bg(177)

    def powder_blue(self) -> Self:
        return self.fg(152)

    def powder_blue_bg(self) -> Self:
        return self.bg(152)

    def purple_3(self) -> Self:
        return self.fg(55)

    def purple_3_bg(self) -> Self:
        return self.bg(55)

    def purple_4(self) -> Self:
        return self.fg(54)

    def purple_4_bg(self) -> Self:
        return self.bg(54)

    def purple_bright(self) -> Self:
        return self.fg(92)

    def purple_bright_bg(self) -> Self:
        return self.bg(92)

    def purple_medium(self) -> Self:
        return self.fg(90)

    def purple_medium_bg(self) -> Self:
        return self.bg(90)

    def purple_medium_bright(self) -> Self:
        return self.fg(91)

    def purple_medium_bright_bg(self) -> Self:
        return self.bg(91)

    def red(self) -> Self:
        return self.fg(196)

    def red_bg(self) -> Self:
        return self.bg(196)

    def rosy_brown(self) -> Self:
        return self.fg(95)

    def rosy_brown_bg(self) -> Self:
        return self.bg(95)

    def rosy_pink(self) -> Self:
        return self.fg(175)

    def rosy_pink_bg(self) -> Self:
        return self.bg(175)

    def royal_blue_1(self) -> Self:
        return self.fg(69)

    def royal_blue_1_bg(self) -> Self:
        return self.bg(69)

    def royal_blue_2(self) -> Self:
        return self.fg(63)

    def royal_blue_2_bg(self) -> Self:
        return self.bg(63)

    def salmon(self) -> Self:
        return self.fg(209)

    def salmon_bg(self) -> Self:
        return self.bg(209)

    def sand(self) -> Self:
        return self.fg(215)

    def sand_bg(self) -> Self:
        return self.bg(215)

    def sandy_brown(self) -> Self:
        return self.fg(137)

    def sandy_brown_bg(self) -> Self:
        return self.bg(137)

    def sandy_brown_bright(self) -> Self:
        return self.fg(173)

    def sandy_brown_bright_bg(self) -> Self:
        return self.bg(173)

    def sienna(self) -> Self:
        return self.fg(130)

    def sienna_bg(self) -> Self:
        return self.bg(130)

    def sky_blue_bright(self) -> Self:
        return self.fg(81)

    def sky_blue_bright_bg(self) -> Self:
        return self.bg(81)

    def sky_blue_light(self) -> Self:
        return self.fg(117)

    def sky_blue_light_bg(self) -> Self:
        return self.bg(117)

    def sky_blue_medium(self) -> Self:
        return self.fg(111)

    def sky_blue_medium_bg(self) -> Self:
        return self.bg(111)

    def slate_blue_1(self) -> Self:
        return self.fg(105)

    def slate_blue_1_bg(self) -> Self:
        return self.bg(105)

    def slate_blue_2(self) -> Self:
        return self.fg(62)

    def slate_blue_2_bg(self) -> Self:
        return self.bg(62)

    def slate_blue_3(self) -> Self:
        return self.fg(61)

    def slate_blue_3_bg(self) -> Self:
        return self.bg(61)

    def soft_green(self) -> Self:
        return self.fg(150)

    def soft_green_bg(self) -> Self:
        return self.bg(150)

    def soft_pink(self) -> Self:
        return self.fg(211)

    def soft_pink_bg(self) -> Self:
        return self.bg(211)

    def soft_yellow(self) -> Self:
        return self.fg(187)

    def soft_yellow_bg(self) -> Self:
        return self.bg(187)

    def spindrift(self) -> Self:
        return self.fg(121)

    def spindrift_bg(self) -> Self:
        return self.bg(121)

    def spring_green_1(self) -> Self:
        return self.fg(48)

    def spring_green_1_bg(self) -> Self:
        return self.bg(48)

    def spring_green_2(self) -> Self:
        return self.fg(47)

    def spring_green_2_bg(self) -> Self:
        return self.bg(47)

    def spring_green_3(self) -> Self:
        return self.fg(42)

    def spring_green_3_bg(self) -> Self:
        return self.bg(42)

    def spring_green_4(self) -> Self:
        return self.fg(41)

    def spring_green_4_bg(self) -> Self:
        return self.bg(41)

    def spring_green_5(self) -> Self:
        return self.fg(35)

    def spring_green_5_bg(self) -> Self:
        return self.bg(35)

    def spring_green_6(self) -> Self:
        return self.fg(29)

    def spring_green_6_bg(self) -> Self:
        return self.bg(29)

    def steel_blue_2(self) -> Self:
        return self.fg(74)

    def steel_blue_2_bg(self) -> Self:
        return self.bg(74)

    def steel_blue_3(self) -> Self:
        return self.fg(67)

    def steel_blue_3_bg(self) -> Self:
        return self.bg(67)

    def teal(self) -> Self:
        return self.fg(23)

    def teal_bg(self) -> Self:
        return self.bg(23)

    def terracotta(self) -> Self:
        return self.fg(131)

    def terracotta_bg(self) -> Self:
        return self.bg(131)

    def thistle_1(self) -> Self:
        return self.fg(219)

    def thistle_1_bg(self) -> Self:
        return self.bg(219)

    def thistle_2(self) -> Self:
        return self.fg(176)

    def thistle_2_bg(self) -> Self:
        return self.bg(176)

    def thistle_3(self) -> Self:
        return self.fg(140)

    def thistle_3_bg(self) -> Self:
        return self.bg(140)

    def topaz(self) -> Self:
        return self.fg(223)

    def topaz_bg(self) -> Self:
        return self.bg(223)

    def turquoise_4(self) -> Self:
        return self.fg(30)

    def turquoise_4_bg(self) -> Self:
        return self.bg(30)

    def violet_bright(self) -> Self:
        return self.fg(93)

    def violet_bright_bg(self) -> Self:
        return self.bg(93)

    def violet_light(self) -> Self:
        return self.fg(213)

    def violet_light_bg(self) -> Self:
        return self.bg(213)

    def violet_medium(self) -> Self:
        return self.fg(171)

    def violet_medium_bg(self) -> Self:
        return self.bg(171)

    def wheat(self) -> Self:
        return self.fg(180)

    def wheat_bg(self) -> Self:
        return self.bg(180)

    def white(self) -> Self:
        return self.fg(231)

    def white_bg(self) -> Self:
        return self.bg(231)

    def white_pinkish(self) -> Self:
        return self.fg(225)

    def white_pinkish_bg(self) -> Self:
        return self.bg(225)

    def yellow(self) -> Self:
        return self.fg(226)

    def yellow_bg(self) -> Self:
        return self.bg(226)

    def yellow_green(self) -> Self:
        return self.fg(106)

    def yellow_green_bg(self) -> Self:
        return self.bg(106)

    def yellow_green_bright(self) -> Self:
        return self.fg(149)

    def yellow_green_bright_bg(self) -> Self:
        return self.bg(149)

    def yellow_neon(self) -> Self:
        return self.fg(184)

    def yellow_neon_bg(self) -> Self:
        return self.bg(184)
