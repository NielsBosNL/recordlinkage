import unittest

import pandas.util.testing as pdt
import numpy.testing as npt
import recordlinkage

import numpy as np
from numpy import nan, arange
import pandas

from test_compare import TestCompare

STRING_SIM_ALGORITHMS = [
    'jaro', 'q_gram', 'cosine', 'jaro_winkler', 'dameraulevenshtein', 'levenshtein'
]

NUMERIC_SIM_ALGORITHMS = [
    'step', 'linear', 'squared', 'exp', 'gauss'
]

# nosetests tests/test_compare_algorithms.py:TestCompareAlgorithms
class TestCompareAlgorithms(TestCompare):

    @classmethod
    def setUpClass(self):

        self.A = pandas.DataFrame([
            [u'Donell', u'Gerlach', 20, u'New York'],
            [nan, u'Smit', 17, u'Boston'],
            [u'Kalie', u'Flatley', 33, u'Boston'],
            [u'Kittie', u'Schuster', 27, nan],
            [nan, nan, nan, u'South Devyn']
        ],
            columns=['given_name', 'lastname', 'age', 'place'])

        self.A.index.name = 'index_df1'

        self.B = pandas.DataFrame([
            [u'Donel', u'Gerleach', 20, u'New York'],
            [nan, u'Smith', 17, u'Boston'],
            [u'Kaly', u'Flatley', 33, u'Boston'],
            [u'Kittie', nan, 20, nan],
            [u'Bob', u'Armstrong', 70, u'Lake Gavinmouth']
        ],
            columns=['given_name', 'lastname', 'age', 'place'])

        self.B.index.name = 'index_df2'

        self.index_AB = pandas.MultiIndex.from_arrays(
            [arange(len(self.A)), arange(len(self.B))],
            names=[self.A.index.name, self.B.index.name])

##########################################################
#                     EXACT ALGORITHM                    #
##########################################################

    def test_exact(self):

        self.A['test'] = ['Bob', 'Myrthe', 'Ally', 'John', 'Rose']
        self.B['test'] = ['Bob', 'Myrte', 'Ally', 'John', 'Roze']

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        result = comp.exact('test', 'test')
        expected = pandas.Series([1, 0, 1, 1, 0], index=self.index_AB)

        pdt.assert_series_equal(result, expected)

    def test_link_exact_missing(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        # Missing values as 0
        result = comp.exact('given_name', 'given_name', missing_value=0)
        expected = pandas.Series([0, 0, 0, 1, 0], index=self.index_AB)

        pdt.assert_series_equal(result, expected)

        # Missing values as nan
        result = comp.exact('given_name', 'given_name', missing_value=nan)
        expected = pandas.Series([0, nan, 0, 1, nan], index=self.index_AB)

        print(result)
        print(expected)

        pdt.assert_series_equal(result, expected)

        # Missing values as nan
        result = comp.exact('given_name', 'given_name', missing_value=9)
        expected = pandas.Series([0, 9, 0, 1, 9], index=self.index_AB)

        pdt.assert_series_equal(result, expected)

    def test_link_exact_disagree(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        # Missing values 0 and disagreement as 2
        result = comp.exact('given_name', 'given_name',
                            disagree_value=2, missing_value=0, name='y_name')
        expected = pandas.Series(
            [2, 0, 2, 1, 0], index=self.index_AB, name='y_name')

        pdt.assert_series_equal(result, expected)

    def test_dedup_exact_basic(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.A)

        # Missing values
        result = comp.exact('given_name', 'given_name')  # , name='y_name')
        # , name='y_name')
        expected = pandas.Series([1, 0, 1, 1, 0], index=self.index_AB)

        pdt.assert_series_equal(result, expected)

##########################################################
#                     DATE ALGORITHM                     #
##########################################################

    def test_dates(self):

        self.A['test_dates'] = pandas.to_datetime(
            ['2005/11/23', np.nan, '2004/11/23', '2010/01/10', '2010/10/30']
        )
        self.B['test_dates'] = pandas.to_datetime(
            ['2005/11/23', '2010/12/31', '2005/11/23', '2010/10/01', '2010/9/30']
        )

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        result = comp.date('test_dates', 'test_dates')
        expected = pandas.Series([1, 0, 0, 0.5, 0.5], index=self.index_AB)

        pdt.assert_series_equal(result, expected)

##########################################################
#                   NUMERIC ALGORITHM                    #
##########################################################

    def test_numeric(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        # Missing values 
        result = comp.numeric('age', 'age', 'step', offset=2)
        expected = pandas.Series(
            [1, 1, 1, 0, 0], index=self.index_AB)  # , name='age')

        pdt.assert_series_equal(result, expected)

    def test_numeric_batch(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        for alg in NUMERIC_SIM_ALGORITHMS:

            print (alg)

            if alg is not 'step':
                # Missing values
                result = comp.numeric('age', 'age', method=alg, offset=2, scale=2)
            else:
                result = comp.numeric('age', 'age', method=alg, offset=2)

            print (result)

            self.assertFalse(result.isnull().all())
            self.assertTrue((result[result.notnull()] >= 0).all())
            self.assertTrue((result[result.notnull()] <= 1).all())

    def test_numeric_alg_errors(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        for alg in [n for n in NUMERIC_SIM_ALGORITHMS if n is not 'step']:

            print (alg)

            with self.assertRaises(ValueError):
                comp.numeric('age', 'age', method=alg, 
                             offset=-2, scale=2)

            with self.assertRaises(ValueError):
                comp.numeric('age', 'age', method=alg, 
                             offset=2, scale=-2)

    def test_numeric_y05(self):
        """

        Test to check if d=origin+offset+scale results in a similarity of 0.5.
        This test is excecuted for all numeric methods, except 'step'.

        """

        origin = 20
        offset = 20
        scale = 20

        series_A = pandas.DataFrame({'age':np.arange(0,100)})
        series_B = pandas.DataFrame(series_A+origin+offset+scale)

        expected = np.array([0.5]*100)

        cand_pairs = pandas.MultiIndex.from_arrays([np.arange(0,100), np.arange(0,100)])

        comp = recordlinkage.Compare(cand_pairs, series_A, series_B)

        for alg in [alg for alg in NUMERIC_SIM_ALGORITHMS if alg is not 'step']:

            print (alg)

            result = comp.numeric('age', 'age', method=alg, 
                                  offset=offset, scale=scale, origin=origin, name='test')
            
            npt.assert_almost_equal(result.values, expected, decimal=4)


    def test_numeric_does_not_exist(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.A)

        with self.assertRaises(ValueError):
            comp.numeric('age', 'age', name='y_age', method='unknown_algorithm')

##########################################################
#                     GEO ALGORITHM                      #
##########################################################

    def test_geo(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        # Missing values
        result = comp.geo('age', 'age', 'age', 'age', method='linear', offset=2, scale=2)

        self.assertFalse(result.isnull().all())
        # self.assertTrue((result[result.notnull()] >= 0).all())
        # self.assertTrue((result[result.notnull()] <= 1).all())

    def test_geo_batch(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        for alg in NUMERIC_SIM_ALGORITHMS:

            print (alg)

            if alg is not 'step':
                # Missing values
                result = comp.geo('age', 'age', 'age', 'age', method=alg, offset=2, scale=2)
            else:
                result = comp.geo('age', 'age', 'age', 'age', method=alg, offset=2)

            print (result)

            self.assertFalse(result.isnull().all())
            self.assertTrue((result[result.notnull()] >= 0).all())
            self.assertTrue((result[result.notnull()] <= 1).all())


    def test_geo_does_not_exist(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.A)

        self.assertRaises(
            ValueError, comp.geo, 'age',
            'age', 'age', 'age', name='y_age', method='unknown_algorithm')

##########################################################
#                    STRING ALGORITHMS                   #
##########################################################

    def test_fuzzy_does_not_exist(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.A)

        self.assertRaises(
            ValueError, comp.string, 'given_name',
            'given_name', name='y_name', method='unknown_algorithm')

    def test_fuzzy_same_labels(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        for alg in STRING_SIM_ALGORITHMS:

            print (alg)

            # Missing values
            result = comp.string('given_name', 'given_name',
                                method=alg, missing_value=0)
            result = comp.string('given_name', 'given_name',
                                alg, missing_value=0)

            print (result)

            self.assertFalse(result.isnull().all())
            self.assertTrue((result[result.notnull()] >= 0).all())
            self.assertTrue((result[result.notnull()] <= 1).all())

    def test_fuzzy_different_labels(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        for alg in STRING_SIM_ALGORITHMS:

            print (alg)

            # Missing values
            # Change in future (should work without method)
            result = comp.string('given_name', 'given_name',
                                method=alg, missing_value=0)

            print (result)

            self.assertFalse(result.isnull().all())
            self.assertTrue((result[result.notnull()] >= 0).all())
            self.assertTrue((result[result.notnull()] <= 1).all())

            # Debug trick
            # if alg == 'q_gram':
            #     rr

    def test_fuzzy_errors(self):

        comp = recordlinkage.Compare(self.index_AB, self.A, self.B)

        for alg in STRING_SIM_ALGORITHMS:

            print (alg)

            with self.assertRaises(Exception):
                # Missing values
                result = comp.string('age', 'age', method=alg, missing_value=0)
