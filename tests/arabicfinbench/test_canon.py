"""Tests for the Arabic financial canonicalisation forms."""

from __future__ import annotations

import pytest

from arabicfinbench.canon import (
    canonicalize,
    canonicalize_markup,
    fold_letter_variants,
    fold_numerals,
    normalize_era_marker_spacing,
    normalize_spacing,
    strip_diacritics,
    strip_invisibles,
)


class TestFoldNumerals:
    def test_arabic_indic_digits_become_ascii(self) -> None:
        assert fold_numerals("٨٣٩,٨٢١") == "839,821"

    def test_extended_persian_digits_become_ascii(self) -> None:
        assert fold_numerals("۸۳۹") == "839"

    def test_arabic_separators_become_ascii(self) -> None:
        # ARABIC DECIMAL SEPARATOR / THOUSANDS SEPARATOR / PERCENT SIGN.
        assert fold_numerals("١٢٣٤٫٥٦") == "1234.56"
        assert fold_numerals("١٬٢٣٤") == "1,234"
        assert fold_numerals("٥٪") == "5%"

    def test_ascii_digits_are_untouched(self) -> None:
        assert fold_numerals("839,821") == "839,821"

    def test_arabic_letters_are_untouched(self) -> None:
        assert fold_numerals("الموجودات") == "الموجودات"


class TestStripDiacritics:
    def test_harakat_are_removed(self) -> None:
        assert strip_diacritics("جُزْءاً") == "جزءا"

    def test_tatweel_is_removed(self) -> None:
        assert strip_diacritics("مـــوجودات") == "موجودات"

    def test_plain_text_is_unchanged(self) -> None:
        assert strip_diacritics("الموجودات") == "الموجودات"


class TestStripInvisibles:
    @pytest.mark.parametrize("mark", ["‎", "‏", "‪", "⁦", "﻿", "​"])
    def test_invisible_marks_are_removed(self, mark: str) -> None:
        assert strip_invisibles(f"مال{mark}") == "مال"

    def test_a_bidi_wrapped_number_matches_the_bare_one(self) -> None:
        assert strip_invisibles("‫839,821‬") == "839,821"


class TestNormalizeSpacing:
    def test_whitespace_runs_collapse(self) -> None:
        assert normalize_spacing("ذمم   مدينة\n\tتجارية") == "ذمم مدينة تجارية"

    def test_space_before_arabic_comma_is_removed(self) -> None:
        assert normalize_spacing("ذمم مدينة تجارية ، بالصافي") == "ذمم مدينة تجارية، بالصافي"

    def test_space_inside_brackets_is_tightened(self) -> None:
        assert normalize_spacing("( شركة ذات مسؤولية محدودة )") == "(شركة ذات مسؤولية محدودة)"

    def test_surrounding_whitespace_is_trimmed(self) -> None:
        assert normalize_spacing("  الموجودات  ") == "الموجودات"


class TestNormalizeEraMarkerSpacing:
    def test_gregorian_marker_closes_up(self) -> None:
        assert normalize_era_marker_spacing("2024 م") == "2024م"

    def test_hijri_marker_closes_up(self) -> None:
        # The tatweel of the usual ``هـ`` spelling is stripped before this runs.
        assert normalize_era_marker_spacing("1445 ه") == "1445ه"

    def test_a_following_word_is_left_alone(self) -> None:
        # ``مليون`` merely starts with the marker letter; closing the space here
        # would corrupt the phrase.
        assert normalize_era_marker_spacing("5 مليون") == "5 مليون"

    def test_a_marker_without_a_preceding_digit_is_left_alone(self) -> None:
        assert normalize_era_marker_spacing("ديسمبر م") == "ديسمبر م"


class TestFoldLetterVariants:
    def test_alef_forms_collapse(self) -> None:
        assert fold_letter_variants("أإآٱ") == "اااا"

    def test_alef_maqsura_becomes_ya(self) -> None:
        assert fold_letter_variants("لدى") == "لدي"

    def test_ta_marbuta_becomes_ha(self) -> None:
        assert fold_letter_variants("مدينة") == "مدينه"


class TestCanonicalize:
    def test_the_two_transcriptions_of_a_figure_agree(self) -> None:
        assert canonicalize("٨٣٩,٨٢١") == canonicalize("839,821")

    def test_the_two_spacings_of_a_year_agree(self) -> None:
        assert canonicalize("٣١ ديسمبر ٢٠٢٣ م") == canonicalize("31 ديسمبر 2023م")

    def test_the_two_spacings_of_a_label_agree(self) -> None:
        assert canonicalize("ذمم مدينة تجارية ، بالصافي") == canonicalize("ذمم مدينة تجارية، بالصافي")

    def test_letters_are_not_folded_by_default(self) -> None:
        assert canonicalize("لدى") != canonicalize("لدي")

    def test_letters_fold_when_requested(self) -> None:
        assert canonicalize("لدى", fold_letters=True) == canonicalize("لدي", fold_letters=True)

    def test_empty_input_is_empty(self) -> None:
        assert canonicalize("") == ""

    def test_is_idempotent(self) -> None:
        once = canonicalize("٣١ ديسمبر ٢٠٢٣ م")
        assert canonicalize(once) == once


class TestCanonicalizeMarkup:
    def test_cell_text_is_canonicalized(self) -> None:
        assert canonicalize_markup("<td>٨٦٦,٠٨٣</td>") == "<td>866,083</td>"

    def test_tag_attributes_survive_untouched(self) -> None:
        # A naive whole-string pass would rewrite spacing inside the tag.
        assert canonicalize_markup('<th colspan="4">الموجودات</th>') == '<th colspan="4">الموجودات</th>'

    def test_ascii_digits_in_attributes_are_not_disturbed(self) -> None:
        assert canonicalize_markup('<td rowspan="2">٥</td>') == '<td rowspan="2">5</td>'

    def test_a_full_row_canonicalizes(self) -> None:
        row = "<tr><td>٨٣٩,٨٢١</td><td>نقد وأرصدة لدى البنوك</td></tr>"
        assert canonicalize_markup(row) == "<tr><td>839,821</td><td>نقد وأرصدة لدى البنوك</td></tr>"

    def test_empty_input_is_empty(self) -> None:
        assert canonicalize_markup("") == ""


class TestParenNegatives:
    """Accounting negatives: (1,000) and -1,000 are one value, two traditions."""

    def test_bracketed_figure_folds_to_minus(self) -> None:
        from arabicfinbench.canon import canonicalize

        assert canonicalize("(٤١٥,٦٥٩)") == "-415,659"
        assert canonicalize("(415,659)") == "-415,659"

    def test_the_two_traditions_agree_after_canon(self) -> None:
        from arabicfinbench.canon import canonicalize

        assert canonicalize("(٢١,٠٠٠,٠٠٠)") == canonicalize("-21,000,000")

    def test_parenthesised_words_are_not_negated(self) -> None:
        from arabicfinbench.canon import canonicalize

        out = canonicalize("( شركة ذات مسؤولية محدودة )")
        assert out.startswith("(") and out.endswith(")")


class TestPresentationForms:
    def test_arabic_presentation_forms_fold_to_base_letters(self) -> None:
        from arabicfinbench.canon import canonicalize

        # U+FEE3/U+FEE7 presentation forms of م/ن versus the base letters.
        assert canonicalize("ﻣﻦ") == canonicalize("من")


class TestMissingSpaceStaysAnEdit:
    def test_joined_words_are_not_repaired(self) -> None:
        # Removing a model's missing-space error would erase an edit, not a
        # convention. This is a deliberate non-rule.
        from arabicfinbench.canon import canonicalize

        assert canonicalize("رأسالمال") != canonicalize("رأس المال")


class TestTracedRules:
    def test_fired_rules_are_named(self) -> None:
        from arabicfinbench.canon import canonicalize_traced

        out, fired = canonicalize_traced("(٤١٥) ريال ، نعم")
        assert out == "-415 ريال، نعم"
        assert "text/fold_numerals" in fired
        assert "text/fold_paren_negatives" in fired
        assert "text/normalize_spacing" in fired

    def test_canonical_input_fires_nothing(self) -> None:
        from arabicfinbench.canon import canonicalize_traced

        text = "-415,659 ريال"
        out, fired = canonicalize_traced(text)
        assert out == text
        assert fired == ()

    def test_markup_trace_is_the_union_over_text_nodes(self) -> None:
        from arabicfinbench.canon import canonicalize_markup_traced

        _, fired = canonicalize_markup_traced("<td>٨٣٩</td><td>(12)</td>")
        assert "text/fold_numerals" in fired
        assert "text/fold_paren_negatives" in fired

    def test_canon_version_is_importable_and_pinned(self) -> None:
        from arabicfinbench.canon import CANON_VERSION

        major, minor, patch = CANON_VERSION.split(".")
        assert all(part.isdigit() for part in (major, minor, patch))
