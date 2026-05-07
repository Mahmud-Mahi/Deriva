import re
from typing import Any
import itertools

import sympy as sp
from sympy.functions.combinatorial.numbers import stirling

from formatter import indented_math
from models import MathTask


def nP(n, r):
    n = sp.sympify(n)
    r = sp.sympify(r)
    return sp.factorial(n) / sp.factorial(n - r)


def nC(n, r):
    return sp.binomial(n, r)


def permutations(n, r=None):
    n = sp.sympify(n)
    if r is None:
        return sp.factorial(n)
    return nP(n, r)


def combinations(n, r):
    return nC(n, r)


def permutations_with_repetition(n, r):
    return sp.sympify(n) ** sp.sympify(r)


def combinations_with_repetition(n, r):
    n = sp.sympify(n)
    r = sp.sympify(r)
    return sp.binomial(n + r - 1, r)


def multiset_permutations(*counts):
    counts = [sp.sympify(count) for count in counts]
    total = sum(counts)
    denominator = sp.prod(sp.factorial(count) for count in counts)
    return sp.simplify(sp.factorial(total) / denominator)


def word_permutations(word: str):
    frequencies = [word.count(char) for char in sorted(set(word))]
    return multiset_permutations(*frequencies)


def circular_permutations(n, reflection_same=False):
    result = sp.factorial(sp.sympify(n) - 1)
    return sp.simplify(result / 2) if reflection_same else result


def arrangements_all_distinct(n):
    return sp.factorial(sp.sympify(n))


def arrangements_with_fixed_positions(n, fixed_count):
    return sp.factorial(sp.sympify(n) - sp.sympify(fixed_count))


def arrangements_items_together(n, group_size):
    n = sp.sympify(n)
    group_size = sp.sympify(group_size)
    return sp.factorial(n - group_size + 1) * sp.factorial(group_size)


def arrangements_items_not_together(n, group_size):
    return sp.simplify(sp.factorial(sp.sympify(n)) - arrangements_items_together(n, group_size))


def arrangements_no_two_together(n, restricted_count):
    n = sp.sympify(n)
    restricted_count = sp.sympify(restricted_count)
    other_count = n - restricted_count
    return sp.simplify(
        sp.factorial(other_count)
        * sp.binomial(other_count + 1, restricted_count)
        * sp.factorial(restricted_count)
    )


def derangements(n):
    return sp.subfactorial(sp.sympify(n))


def derangements_formula(n):
    n = sp.sympify(n)
    k = sp.symbols("k", integer=True, nonnegative=True)
    return sp.factorial(n) * sp.Sum((-1) ** k / sp.factorial(k), (k, 0, n))


def choose_with_required(total, choose, required=0, forbidden=0):
    total = sp.sympify(total)
    choose = sp.sympify(choose)
    required = sp.sympify(required)
    forbidden = sp.sympify(forbidden)
    return sp.binomial(total - required - forbidden, choose - required)


def choose_at_least(total, choose, minimum_from_group, group_size):
    total = sp.sympify(total)
    choose = sp.sympify(choose)
    minimum_from_group = sp.sympify(minimum_from_group)
    group_size = sp.sympify(group_size)
    i = sp.symbols("i", integer=True)
    return sp.summation(
        sp.binomial(group_size, i) * sp.binomial(total - group_size, choose - i),
        (i, minimum_from_group, sp.Min(group_size, choose)),
    )


def choose_at_most(total, choose, maximum_from_group, group_size):
    total = sp.sympify(total)
    choose = sp.sympify(choose)
    maximum_from_group = sp.sympify(maximum_from_group)
    group_size = sp.sympify(group_size)
    i = sp.symbols("i", integer=True)
    return sp.summation(
        sp.binomial(group_size, i) * sp.binomial(total - group_size, choose - i),
        (i, 0, sp.Min(maximum_from_group, group_size, choose)),
    )


def select_from_groups(group_sizes, picks):
    if len(group_sizes) != len(picks):
        raise ValueError("group_sizes and picks must have the same length.")
    return sp.prod(sp.binomial(group_size, pick) for group_size, pick in zip(group_sizes, picks))


def select_total_from_groups(group_sizes, total_picks):
    t = sp.Symbol("t")
    generating = sp.prod(
        sum(sp.binomial(group_size, r) * t**r for r in range(int(group_size) + 1))
        for group_size in group_sizes
    )
    return sp.expand(generating).coeff(t, int(total_picks))


def select_at_least_one_from_each(group_sizes):
    return sp.prod(2 ** sp.sympify(group_size) - 1 for group_size in group_sizes)


def distribute_identical(items, boxes, min_each=0, max_each=None):
    items = sp.sympify(items)
    boxes = sp.sympify(boxes)
    min_each = sp.sympify(min_each)
    remaining = items - boxes * min_each
    if max_each is None:
        return sp.binomial(remaining + boxes - 1, boxes - 1)

    max_each = sp.sympify(max_each)
    cap = max_each - min_each
    j = sp.symbols("j", integer=True, nonnegative=True)
    return sp.summation(
        (-1) ** j
        * sp.binomial(boxes, j)
        * sp.binomial(remaining - j * (cap + 1) + boxes - 1, boxes - 1),
        (j, 0, sp.floor(remaining / (cap + 1))),
    )


def distribute_distinct(items, boxes, allow_empty=True):
    items = sp.sympify(items)
    boxes = sp.sympify(boxes)
    if allow_empty:
        return boxes**items
    return sp.factorial(boxes) * stirling(items, boxes, kind=2)


def bijections(n):
    return sp.factorial(sp.sympify(n))


def injections(domain_size, codomain_size):
    return nP(codomain_size, domain_size)


def surjections(domain_size, codomain_size):
    return sp.factorial(sp.sympify(codomain_size)) * stirling(domain_size, codomain_size, kind=2)


def binomial_term(n, r, a=1, b=1):
    n = sp.sympify(n)
    r = sp.sympify(r)
    return sp.binomial(n, r) * sp.sympify(a) ** (n - r) * sp.sympify(b) ** r


def binomial_middle_terms(n):
    n = sp.sympify(n)
    if n % 2 == 0:
        r = n / 2
        return sp.Tuple(r + 1)
    return sp.Tuple((n + 1) / 2, (n + 3) / 2)


def inclusion_exclusion_two(a_count, b_count, both_count):
    return sp.sympify(a_count) + sp.sympify(b_count) - sp.sympify(both_count)


def inclusion_exclusion_three(a_count, b_count, c_count, ab_count, ac_count, bc_count, abc_count):
    return (
        sp.sympify(a_count)
        + sp.sympify(b_count)
        + sp.sympify(c_count)
        - sp.sympify(ab_count)
        - sp.sympify(ac_count)
        - sp.sympify(bc_count)
        + sp.sympify(abc_count)
    )


def count_numbers_from_digits(digits, length, repetition_allowed=False, first_nonzero=True, ending=None):
    digits = [int(digit) for digit in digits]
    length = int(length)
    iterator = (
        itertools.product(digits, repeat=length)
        if repetition_allowed
        else itertools.permutations(digits, length)
    )

    count = 0
    for number_digits in iterator:
        if first_nonzero and number_digits[0] == 0:
            continue
        if ending == "even" and number_digits[-1] % 2 != 0:
            continue
        if ending == "odd" and number_digits[-1] % 2 != 1:
            continue
        if ending == "zero" and number_digits[-1] != 0:
            continue
        if isinstance(ending, int) and number_digits[-1] != ending:
            continue
        count += 1
    return count


def list_numbers_from_digits(digits, length, repetition_allowed=False, first_nonzero=True, ending=None):
    digits = [int(digit) for digit in digits]
    length = int(length)
    iterator = (
        itertools.product(digits, repeat=length)
        if repetition_allowed
        else itertools.permutations(digits, length)
    )

    numbers = []
    for number_digits in iterator:
        if first_nonzero and number_digits[0] == 0:
            continue
        if ending == "even" and number_digits[-1] % 2 != 0:
            continue
        if ending == "odd" and number_digits[-1] % 2 != 1:
            continue
        if ending == "zero" and number_digits[-1] != 0:
            continue
        if isinstance(ending, int) and number_digits[-1] != ending:
            continue
        numbers.append(int("".join(str(digit) for digit in number_digits)))
    return sp.Tuple(*numbers)


def handshakes(n):
    return sp.binomial(sp.sympify(n), 2)


def polygon_diagonals(n):
    n = sp.sympify(n)
    return sp.binomial(n, 2) - n


SYMPY_LOCALS = {
    "factorial": sp.factorial,
    "binomial": sp.binomial,
    "nC": nC,
    "nP": nP,
    "permutations": permutations,
    "combinations": combinations,
    "permutations_with_repetition": permutations_with_repetition,
    "combinations_with_repetition": combinations_with_repetition,
    "multiset_permutations": multiset_permutations,
    "word_permutations": word_permutations,
    "circular_permutations": circular_permutations,
    "arrangements_all_distinct": arrangements_all_distinct,
    "arrangements_with_fixed_positions": arrangements_with_fixed_positions,
    "arrangements_items_together": arrangements_items_together,
    "arrangements_items_not_together": arrangements_items_not_together,
    "arrangements_no_two_together": arrangements_no_two_together,
    "derangements": derangements,
    "derangements_formula": derangements_formula,
    "choose_with_required": choose_with_required,
    "choose_at_least": choose_at_least,
    "choose_at_most": choose_at_most,
    "select_from_groups": select_from_groups,
    "select_total_from_groups": select_total_from_groups,
    "select_at_least_one_from_each": select_at_least_one_from_each,
    "distribute_identical": distribute_identical,
    "distribute_distinct": distribute_distinct,
    "bijections": bijections,
    "injections": injections,
    "surjections": surjections,
    "binomial_term": binomial_term,
    "binomial_middle_terms": binomial_middle_terms,
    "inclusion_exclusion_two": inclusion_exclusion_two,
    "inclusion_exclusion_three": inclusion_exclusion_three,
    "count_numbers_from_digits": count_numbers_from_digits,
    "list_numbers_from_digits": list_numbers_from_digits,
    "handshakes": handshakes,
    "polygon_diagonals": polygon_diagonals,
}

RULES = [
    "For PERMUTATIONS: use nP(n,r), permutations(n,r), or arrangements_all_distinct(n).",
    "For COMBINATIONS: use nC(n,r) or combinations(n,r).",
    "For REPETITION allowed: use permutations_with_repetition(n,r) or combinations_with_repetition(n,r).",
    "For IDENTICAL/repeated items: use multiset_permutations(k1,k2,...) or word_permutations('WORD').",
    "For CIRCULAR arrangements: use circular_permutations(n); if clockwise and anticlockwise are same use circular_permutations(n, True).",
    "For restricted arrangements: use arrangements_items_together(n,k), arrangements_items_not_together(n,k), arrangements_no_two_together(n,k), arrangements_with_fixed_positions(n,k), or derangements(n).",
    "For committee/selection restrictions: use choose_with_required(total,choose,required,forbidden), choose_at_least(total,choose,min,group_size), or choose_at_most(total,choose,max,group_size).",
    "For group-wise selections: use select_from_groups([sizes],[picks]), select_total_from_groups([sizes],total), or select_at_least_one_from_each([sizes]).",
    "For distributions/stars and bars: use distribute_identical(items,boxes,min_each,max_each) or distribute_distinct(items,boxes,allow_empty).",
    "For functions/mappings: use injections(domain,codomain), surjections(domain,codomain), or bijections(n).",
    "For binomial theorem counting terms: use binomial_term(n,r,a,b) or binomial_middle_terms(n).",
    "For inclusion-exclusion: use inclusion_exclusion_two(a,b,both) or inclusion_exclusion_three(a,b,c,ab,ac,bc,abc).",
    "For digit number formation: use count_numbers_from_digits([digits], length, repetition_allowed, first_nonzero, ending). ending can be 'even', 'odd', 'zero', an integer digit, or None.",
    "For handshakes or polygon diagonals: use handshakes(n) or polygon_diagonals(n).",
]

EXAMPLES = [
    'User problem: Ways to choose 3 from 10\nJSON: {"operation":"evaluate","expression":"nC(10, 3)"}',
    'User problem: Ways to arrange the letters in BANANA\nJSON: {"operation":"evaluate","expression":"word_permutations(\'BANANA\')"}',
    'User problem: Arrange 8 people around a round table\nJSON: {"operation":"evaluate","expression":"circular_permutations(8)"}',
    'User problem: Arrange 7 books if 3 particular books are together\nJSON: {"operation":"evaluate","expression":"arrangements_items_together(7, 3)"}',
    'User problem: Arrange 7 people if 3 particular people are never together\nJSON: {"operation":"evaluate","expression":"arrangements_items_not_together(7, 3)"}',
    'User problem: Arrange 8 people if no two of 3 girls sit together\nJSON: {"operation":"evaluate","expression":"arrangements_no_two_together(8, 3)"}',
    'User problem: Derangements of 5 letters\nJSON: {"operation":"evaluate","expression":"derangements(5)"}',
    'User problem: Select a committee of 5 from 8 men and 6 women with at least 2 women\nJSON: {"operation":"evaluate","expression":"choose_at_least(14, 5, 2, 6)"}',
    'User problem: Distribute 10 identical balls among 4 boxes with at least one in each\nJSON: {"operation":"evaluate","expression":"distribute_identical(10, 4, 1)"}',
    'User problem: Number of onto functions from 5 elements to 3 elements\nJSON: {"operation":"evaluate","expression":"surjections(5, 3)"}',
    'User problem: How many 3 digit even numbers can be formed from 0,1,2,3,4 without repetition\nJSON: {"operation":"evaluate","expression":"count_numbers_from_digits([0, 1, 2, 3, 4], 3, False, True, \'even\')"}',
    'User problem: Number of diagonals in a 10 sided polygon\nJSON: {"operation":"evaluate","expression":"polygon_diagonals(10)"}',
]

COMBINATION_MARKERS = (
    "nC(",
    "nP(",
    "binomial(",
    "factorial(",
    "permutations(",
    "combinations(",
    "permutations_with_repetition(",
    "combinations_with_repetition(",
    "multiset_permutations(",
    "word_permutations(",
    "circular_permutations(",
    "arrangements_",
    "derangements(",
    "choose_",
    "select_",
    "distribute_",
    "bijections(",
    "injections(",
    "surjections(",
    "binomial_term(",
    "binomial_middle_terms(",
    "inclusion_exclusion_",
    "count_numbers_from_digits(",
    "list_numbers_from_digits(",
    "handshakes(",
    "polygon_diagonals(",
)


def is_combination_task(task: MathTask, expr_str: str | None = None) -> bool:
    text = expr_str if expr_str is not None else (task.expression or task.equation or "")
    return any(marker in text for marker in COMBINATION_MARKERS)


def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    if task.operation == "evaluate" and is_combination_task(task):
        if isinstance(expr, (dict, sp.Tuple, list)):
            return expr
        return sp.simplify(expr)
    return None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if task.operation != "evaluate" or not is_combination_task(task, expr_str):
        return None

    match = re.search(r"n([PC])\s*\(\s*([^,]+),\s*([^)]+)\)", expr_str)
    if match:
        ctype, n, r = match.groups()
        is_perm = ctype == "P"
        return "\n".join([
            f"1. Identify this as {'a permutation' if is_perm else 'a combination'} problem.",
            f"2. Use {'nPr = n! / (n-r)!' if is_perm else 'nCr = n! / (r!(n-r)!)'} with n={n}, r={r}.",
            "3. The result is:",
            indented_math(result),
        ])

    step_map = [
        ("permutations_with_repetition(", "1. Repetition is allowed, so each position has n choices."),
        ("combinations_with_repetition(", "1. Use stars and bars for selecting with repetition."),
        ("multiset_permutations(", "1. Divide total permutations by factorials of repeated item counts."),
        ("word_permutations(", "1. Count repeated letters, then use the multiset permutation formula."),
        ("circular_permutations(", "1. Fix one object to remove rotational symmetry."),
        ("arrangements_items_together(", "1. Treat the specified items as one block, then arrange inside the block."),
        ("arrangements_items_not_together(", "1. Subtract arrangements where the specified items are together from all arrangements."),
        ("arrangements_no_two_together(", "1. Arrange the other items first, then place restricted items in gaps."),
        ("arrangements_with_fixed_positions(", "1. Keep fixed objects in place and arrange the remaining objects."),
        ("arrangements_all_distinct(", "1. Arrange all distinct objects using n!."),
        ("derangements(", "1. Use derangement counting where no object remains in its original position."),
        ("choose_with_required(", "1. Include required items, exclude forbidden items, then choose the remaining items."),
        ("choose_at_least(", "1. Sum cases where the selected group contributes at least the required number."),
        ("choose_at_most(", "1. Sum cases where the selected group contributes at most the allowed number."),
        ("select_from_groups(", "1. Choose the required number from each group and multiply."),
        ("select_total_from_groups(", "1. Use a generating function and take the coefficient of the required power."),
        ("select_at_least_one_from_each(", "1. For each group, choose any non-empty subset, then multiply."),
        ("distribute_identical(", "1. Use stars and bars, adjusted for minimum or maximum limits."),
        ("distribute_distinct(", "1. Treat each distinct object as choosing one box; use onto-function counting if boxes cannot be empty."),
        ("bijections(", "1. A bijection is a one-to-one correspondence, counted by n!."),
        ("injections(", "1. Assign domain elements to distinct codomain elements using permutations."),
        ("surjections(", "1. Count onto functions using k! times Stirling numbers of the second kind."),
        ("binomial_term(", "1. Use the general binomial term C(n,r)a^(n-r)b^r."),
        ("binomial_middle_terms(", "1. Determine the middle term index or indices from the parity of n."),
        ("inclusion_exclusion_two(", "1. Use |A∪B| = |A| + |B| - |A∩B|."),
        ("inclusion_exclusion_three(", "1. Use inclusion-exclusion for three sets."),
        ("count_numbers_from_digits(", "1. Count valid digit arrangements after applying leading digit and ending restrictions."),
        ("list_numbers_from_digits(", "1. Generate valid digit arrangements after applying leading digit and ending restrictions."),
        ("handshakes(", "1. Each handshake is a choice of 2 people."),
        ("polygon_diagonals(", "1. Choose any two vertices, then subtract the sides."),
        ("factorial(", "1. This is an arrangement of all distinct objects, counted by factorial."),
        ("binomial(", "1. This is a selection problem, counted by a binomial coefficient."),
        ("permutations(", "1. This is a permutation problem where order matters."),
        ("combinations(", "1. This is a combination problem where order does not matter."),
    ]

    for marker, first_step in step_map:
        if marker in expr_str:
            return "\n".join([
                first_step,
                "2. Substitute the given values into the formula.",
                "3. The result is:",
                indented_math(result),
            ])

    return "\n".join([
        "1. Identify whether order matters and whether repetition or restrictions apply.",
        "2. Apply the matching counting formula.",
        "3. The result is:",
        indented_math(result),
    ])
