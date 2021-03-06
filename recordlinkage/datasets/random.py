import pandas as pd
import numpy as np


def binary_comparisons(n, n_match, m=[0.9] * 8, u=[0.1] * 8,
                       random_state=None):
    """Generate random binary comparison vectors

    This function is used to generate random comparison vectors. The outcome
    of each comparison is restricted to 0 and 1.

    Parameters
    ----------
    n : int
        The number of comparison vectors.
    n_match : int
        The number of matches.
    m : list, default [0.9] * 8, optional
        The probability of an agreeing comparison given the pairs is a match.
    u : list, default [0.9] * 8, optional
        The probability of an agreeing comparison given the records in the
        pair do not belong to the same entity.
    random_state : int or numpy.random.RandomState, optional
        Seed for the random number generator (if int), or numpy RandomState
        object.

    Returns
    -------
    dict
        The dicitionary with your classifier parameters.


    """

    if len(m) != len(u):
        raise ValueError("the length of 'm' is not equal the length of 'u'")

    if n_match >= n or n_match < 0:
        raise ValueError("the number of matches is bounded by [0, n]")

    # set the random seed
    np.random.seed(random_state)

    matches = []
    nonmatches = []

    for i, _ in enumerate(m):

        p_mi = [1 - m[i], m[i]]
        p_ui = [1 - u[i], u[i]]

        comp_mi = np.random.choice([0, 1], (n_match, 1), p=p_mi)
        comp_ui = np.random.choice([0, 1], (n - n_match, 1), p=p_ui)

        nonmatches.append(comp_ui)
        matches.append(comp_mi)

    match_block = np.concatenate(matches, axis=1)
    nonmatch_block = np.concatenate(nonmatches, axis=1)

    data_np = np.concatenate((match_block, nonmatch_block), axis=0)
    index_np = np.random.randint(1001, 1001 + n * 2, (n, 2))

    data_col_names = ['c_%s' % (i + 1) for i in range(len(m))]
    data_mi = pd.MultiIndex.from_arrays([index_np[:, 0], index_np[:, 1]])
    data_df = pd.DataFrame(data_np, index=data_mi, columns=data_col_names)

    return data_df.sample(frac=1, random_state=random_state)
