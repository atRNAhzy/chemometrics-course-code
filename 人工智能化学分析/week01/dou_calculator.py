def parse_formula_counts(formula: str) -> dict[str, int]:
    """Parse a molecular formula into element counts.

    Supports (), [], {} nested brackets, e.g.:
        C6H6
        CH3(CH2)4CH3
        (NH4)2SO4
        K4[Fe(CN)6]

    Notes:
        - Whitespace is ignored.
        - Standalone numbers are not allowed.
        - Element symbols are parsed as one uppercase letter followed by
          zero or more lowercase letters.
    """
    if not isinstance(formula, str) or not formula.strip():
        raise ValueError("Formula must be a non-empty string.")

    formula = "".join(formula.split())
    n = len(formula)

    open_to_close = {"(": ")", "[": "]", "{": "}"}
    close_to_open = {v: k for k, v in open_to_close.items()}

    def parse_number(i: int) -> tuple[int, int]:
        """Parse a positive integer starting at i; default to 1 if absent."""
        j = i
        while j < n and formula[j].isdigit():
            j += 1
        if j == i:
            return 1, i
        value = int(formula[i:j])
        if value <= 0:
            raise ValueError("Multipliers must be positive integers.")
        return value, j

    def merge_counts(target: dict[str, int], source: dict[str, int], factor: int = 1) -> None:
        """Add source counts into target, scaled by factor."""
        for elem, count in source.items():
            target[elem] = target.get(elem, 0) + count * factor

    def parse_group(i: int, stop: str | None = None) -> tuple[dict[str, int], int]:
        """Parse until the end or until the expected closing bracket."""
        counts: dict[str, int] = {}

        while i < n:
            ch = formula[i]

            if ch in open_to_close:
                inner_counts, i = parse_group(i + 1, open_to_close[ch])
                mult, i = parse_number(i)
                merge_counts(counts, inner_counts, mult)

            elif ch in close_to_open:
                if ch != stop:
                    raise ValueError(f"Mismatched closing bracket '{ch}' in formula.")
                return counts, i + 1

            elif ch.isupper():
                j = i + 1
                while j < n and formula[j].islower():
                    j += 1
                elem = formula[i:j]
                mult, i = parse_number(j)
                counts[elem] = counts.get(elem, 0) + mult

            elif ch.isdigit():
                raise ValueError("Standalone numbers are not allowed in formula.")

            else:
                raise ValueError(f"Unsupported character '{ch}' in formula.")

        if stop is not None:
            raise ValueError(f"Unclosed bracket '{close_to_open[stop]}' in formula.")

        return counts, i

    counts, end = parse_group(0)
    if end != n:
        raise ValueError("Failed to parse entire formula.")
    return counts


def calc_dbe_from_formula(formula: str) -> float:
    """Calculate the double bond equivalent (DBE) from a molecular formula.

    Uses the standard organic chemistry formula:
        DBE = C - (H + X)/2 + N/2 + 1

    where:
        - X = F + Cl + Br + I
        - O and S do not affect DBE in this approximation

    This is mainly appropriate for neutral, closed-shell organic molecules.
    """
    counts = parse_formula_counts(formula)

    c = counts.get("C", 0)
    h = counts.get("H", 0)
    n = counts.get("N", 0)
    x = sum(counts.get(elem, 0) for elem in ("F", "Cl", "Br", "I"))

    return c - (h + x) / 2 + n / 2 + 1


if __name__ == "__main__":
    test_formulas = [
        "C6H6",
        "C2H4",
        "C2H6",
        "(CH3)2CH2",
        "CH3(CH2)4CH3",
        "(NH4)2SO4"]

    for formula in test_formulas:
        try:
            counts = parse_formula_counts(formula)
            dbe = calc_dbe_from_formula(formula)
            print(f"{formula:<15} counts={counts}, DBE={dbe}")
        except ValueError as e:
            print(f"{formula:<15} invalid: {e}")