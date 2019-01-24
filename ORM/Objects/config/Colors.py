from random import randint

COLOR_CHART = {
    'Whites': ['antique_white', 'azure', 'bisque', 'blanched_almond',
               'cornsilk', 'eggshell', 'floral_white', 'gainsboro',
               'ghost_white', 'honeydew', 'ivory', 'lavender',
               'lavender_blush', 'lemon_chiffon', 'linen', 'mint_cream',
               'misty_rose', 'moccasin', 'navajo_white', 'old_lace',
               'papaya_whip', 'peach_puff', 'seashell', 'snow',
               'thistle', 'titanium_white', 'wheat', 'white',
               'white_smoke', 'zinc_white'],
    'Greys': ['cold_grey', 'dim_grey', 'grey', 'light_grey',
              'slate_grey', 'slate_grey_dark', 'slate_grey_light',
              'warm_grey'],
    'Blacks': ['black', 'ivory_black', 'lamp_black'],
    'Reds': ['alizarin_crimson', 'brick', 'cadmium_red_deep', 'coral',
             'coral_light', 'deep_pink', 'english_red', 'firebrick',
             'geranium_lake', 'hot_pink', 'indian_red', 'light_salmon',
             'madder_lake_deep', 'maroon', 'pink', 'pink_light',
             'raspberry', 'red', 'rose_madder', 'salmon', 'tomato',
             'venetian_red'],
    'Browns': ['beige', 'brown', 'brown_madder', 'brown_ochre',
               'burlywood', 'burnt_sienna', 'burnt_umber', 'chocolate',
               'deep_ochre', 'flesh', 'flesh_ochre', 'gold_ochre',
               'greenish_umber', 'khaki', 'khaki_dark', 'light_beige',
               'peru', 'rosy_brown', 'raw_sienna', 'raw_umber', 'sepia',
               'sienna', 'saddle_brown', 'sandy_brown', 'tan',
               'van_dyke_brown'],
    'Oranges': ['cadmium_orange', 'cadmium_red_light', 'carrot',
                'dark_orange', 'mars_orange', 'mars_yellow', 'orange',
                'orange_red', 'yellow_ochre'],
    'Yellows': ['aureoline_yellow', 'banana', 'cadmium_lemon',
                'cadmium_yellow', 'cadmium_yellow_light', 'gold',
                'goldenrod', 'goldenrod_dark', 'goldenrod_light',
                'goldenrod_pale', 'light_goldenrod', 'melon',
                'naples_yellow_deep', 'yellow', 'yellow_light'],
    'Greens': ['chartreuse', 'chrome_oxide_green', 'cinnabar_green',
               'cobalt_green', 'emerald_green', 'forest_green', 'green',
               'green_dark', 'green_pale', 'green_yellow', 'lawn_green',
               'lime_green', 'mint', 'olive', 'olive_drab',
               'olive_green_dark', 'permanent_green', 'sap_green',
               'sea_green', 'sea_green_dark', 'sea_green_medium',
               'sea_green_light', 'spring_green', 'spring_green_medium',
               'terre_verte', 'viridian_light', 'yellow_green'],
    'Cyans': ['aquamarine', 'aquamarine_medium', 'cyan', 'cyan_white',
              'turquoise', 'turquoise_dark', 'turquoise_medium',
              'turquoise_pale'],
    'Blues': ['alice_blue', 'blue', 'blue_light', 'blue_medium',
              'cadet', 'cobalt', 'cornflower', 'cerulean', 'dodger_blue',
              'indigo', 'manganese_blue', 'midnight_blue', 'navy',
              'peacock', 'powder_blue', 'royal_blue', 'slate_blue',
              'slate_blue_dark', 'slate_blue_light',
              'slate_blue_medium', 'sky_blue', 'sky_blue_deep',
              'sky_blue_light', 'steel_blue', 'steel_blue_light',
              'turquoise_blue', 'ultramarine'],
    'Magentas': ['blue_violet', 'cobalt_violet_deep', 'magenta',
                 'orchid', 'orchid_dark', 'orchid_medium',
                 'permanent_red_violet', 'plum', 'purple',
                 'purple_medium', 'ultramarine_violet', 'violet',
                 'violet_dark', 'violet_red', 'violet_red_medium',
                 'violet_red_pale']
}


class Colors:

    @staticmethod
    def get_color_names(category):
        return COLOR_CHART[category]

    @staticmethod
    def get_color(category, index):
        return Colors.get_color_names(category)[index]

    @staticmethod
    def get_random_color(category):
        colors = Colors.get_color_names(category)
        return colors[randint(0, len(colors) - 1)]
