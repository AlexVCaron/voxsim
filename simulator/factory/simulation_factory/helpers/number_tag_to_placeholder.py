import re


class NumberTagToPlaceholder:
    placeholders = {
        1: "a", 2: "b", 3: "c", 4: "d", 5: "e", 6: "f", 7: "g", 8: "h", 9: "i", 0: "j"
    }

    translation = {
        "a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 0
    }

    before_tag = "nbplchdbf_"
    after_tag = "_nbplchdaf"

    @staticmethod
    def generate_placeholder(number):
        return NumberTagToPlaceholder.before_tag\
               + "".join([NumberTagToPlaceholder.placeholders[int(i)] for i in str(number)])\
               + NumberTagToPlaceholder.after_tag

    @staticmethod
    def generate_number_in_regex(placeholder):
        return "".join([
            str(NumberTagToPlaceholder.translation[i]) for i in placeholder.group(0).replace(
                NumberTagToPlaceholder.before_tag, ""
            ).replace(
                NumberTagToPlaceholder.after_tag, ""
            )
        ])

    @staticmethod
    def replace_placeholders(string):
        return re.sub(
            "((?:{0})(?:[abcdefghij]*)(?:{1}))".format(
                NumberTagToPlaceholder.before_tag,
                NumberTagToPlaceholder.after_tag
            ),
            NumberTagToPlaceholder.generate_number_in_regex,
            string
        )
