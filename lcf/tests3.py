from django.test import TestCase
import time
import ast
from django.core.urlresolvers import reverse
from django.forms import modelformset_factory, formset_factory
from django.core.files.uploadedfile import SimpleUploadedFile

import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from pandas.util.testing import assert_frame_equal, assert_series_equal
import numpy.testing as npt

from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart, ColumnChart


import lcf.dataframe_helpers as dfh
from .models import Scenario, AuctionYear, Pot, Technology, Policy
from .forms import ScenarioForm, PricesForm, PolicyForm
from .helpers import process_policy_form, process_scenario_form, get_prices, create_auctionyear_and_pot_objects, update_tech_with_policies, create_technology_objects, interpolate_tech_df, parse_file, get_notes, get_default_prices

# all tests have to be run individually!
#
# python manage.py test lcf.tests3.ExcelQuirkTests.test_excel_2020_gen_error_true
# python manage.py test lcf.tests3.ExcelQuirkTests.test_excel_2020_gen_error_false
# python manage.py test lcf.tests3.ExcelQuirkTests.test_all_excel_quirks_lumped
# python manage.py test lcf.tests3.ExcelQuirkTests.test_all_excel_quirks_individual
# python manage.py test lcf.tests3.ExcelQuirkTests.test_quirks
#
# python manage.py test lcf.tests3.CumT.test_cum_future_techs
#
# python manage.py test lcf.tests3.FixedNumProjectsTests.test_create_tidal
#
# python manage.py test lcf.tests3.InputDisplayTests.test_techs_input
# python manage.py test lcf.tests3.InputDisplayTests.test_prices_input
#
# python manage.py test lcf.tests3.StoringResults.test_scenario_db_storage
# python manage.py test lcf.tests3.StoringResults.test_auction_cache
#
# python manage.py test lcf.tests3.TestCumProj.test_num_projects
# python manage.py test lcf.tests3.TestCumProj.test_run_auction
# python manage.py test lcf.tests3.TestCumProj.test_run_auction_budget
# python manage.py test lcf.tests3.TestCumProj.test_accounting_cost
# python manage.py test lcf.tests3.TestCumProj.test_budget_period_2
# python manage.py test lcf.tests3.TestCumProj.test_fit_cost_individual_quirks
# python manage.py test lcf.tests3.TestCumProj.test_fit_cost_lumped_quirks
#
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_num_projects
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_levelised_cost_distribution
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_projects_index
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_projects
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_concat_projects
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_run_auction_max_deployment_cap
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_run_auction_budget
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_budget_period_2
#
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_high
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_normal
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_low
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_lower
#
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_high
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_normal
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_low
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_lower
#
# python manage.py test lcf.tests3.TestIP.test_nw_v_gas
#
# python manage.py test lcf.tests3.ViewsTests.test_policy_new_view
# python manage.py test lcf.tests3.ViewsTests.test_scenario_new_view
#
# python manage.py test lcf.tests3.TestPolicies.test_update_tech_with_policies
# python manage.py test lcf.tests3.TestPolicies.test_process_scenario_form_with_policies
#
# python manage.py test lcf.tests3.TestHelpers.test_process_scenario_form
#
# python manage.py test lcf.tests3.Interpolate.test_interpolate_tech_df
# python manage.py test lcf.tests3.Interpolate.test_process_scenario_form_with_interpolation
#
# python manage.py test lcf.tests3.Notes.test_parse_file_with_notes
# python manage.py test lcf.tests3.Notes.test_parse_file_with_prices_and_prices_notes
# python manage.py test lcf.tests3.Notes.test_parse_file_with_and_without_prices
# python manage.py test lcf.tests3.Notes.test_parse_file_with_or_without_notes_and_get_same_tech_data
# python manage.py test lcf.tests3.Notes.test_parse_file_with_different_column_order
# python manage.py test lcf.tests3.Notes.test_process_scenario_form_with_notes_without_notes
# python manage.py test lcf.tests3.Notes.test_process_scenario_form_with_different_column_order
# python manage.py test lcf.tests3.Notes.test_retrieve_sources
# python manage.py test lcf.tests3.Notes.test_inputs_download
#
#
# python manage.py test lcf.tests3.Exceptions.test_upload_non_csv
# python manage.py test lcf.tests3.Exceptions.test_blank_scenario
# python manage.py test lcf.tests3.Exceptions.test_process_scenario_form_with_file_with_invalid_columns
# python manage.py test lcf.tests3.Exceptions.test_view_with_invalid_file
# python manage.py test lcf.tests3.Exceptions.test_view_with_invalid_scenario
# python manage.py test lcf.tests3.Exceptions.test_view_with_non_existant_scenario
#
#
# python manage.py test lcf.tests3.Intermediate.test_cum_project_summary
# python manage.py test lcf.tests3.Intermediate.test_non_cum_project_summary
# python manage.py test lcf.tests3.Intermediate.test_scenario_intermediate_results
#
# python manage.py test lcf.tests3.Clearing.test_form_option
# python manage.py test lcf.tests3.Clearing.test_exogenous
# python manage.py test lcf.tests3.Clearing.test_clearing_price_non_cum
# python manage.py test lcf.tests3.Clearing.test_clearing_price_cum
# python manage.py test lcf.tests3.Clearing.test_accounting_cost
# python manage.py test lcf.tests3.Clearing.test_intermediate_with_clearing_price_exogenous
# python manage.py test lcf.tests3.Clearing.test_intermediate_with_clearing_price_not_exogenous
#
# python manage.py test lcf.tests3.IntermediateBudget.test_intermediate_budget_results


class ExcelQuirkTests(TestCase):
    fixtures = ['tests/new/data2.json']

    def test_excel_2020_gen_error_true(self):
        s = Scenario.objects.get(pk=281)
        s.excel_quirks = False
        s.excel_2020_gen_error = True
        s.save()
        #period1
        s.get_results()

        expected_cum_awarded_gen_2022 = 0
        a0 = s.auctionyear_dict[2020]
        for p in a0.pot_dict.values():
            expected_cum_awarded_gen_2022 += p.awarded_gen_result

        a1 = s.auctionyear_dict[2021]
        for p in a1.pot_dict.values():
            expected_cum_awarded_gen_2022 += p.awarded_gen_result

        a2 = s.auctionyear_dict[2022]
        for p in a2.pot_dict.values():
            expected_cum_awarded_gen_2022 += p.awarded_gen_result

        expected_cum_awarded_gen_2022 -= a0.pot_dict["FIT"].awarded_gen_result
        scenario_awarded_gen_2022 = s.pivot('cum_awarded_gen').loc[('Total', 'Total'), ('Cumulative new generation (TWh)', 2022)]
        npt.assert_almost_equal(scenario_awarded_gen_2022, expected_cum_awarded_gen_2022)

        #period2
        expected_cum_awarded_gen_2026 = s.pivot('cum_awarded_gen').loc[('Total', 'Total'), ('Cumulative new generation (TWh)', 2025)]
        a6 = s.auctionyear_dict[2026]
        for p in a6.pot_dict.values():
            expected_cum_awarded_gen_2026 += p.awarded_gen_result

        scenario_awarded_gen_2026 = s.pivot('cum_awarded_gen').loc[('Total', 'Total'), ('Cumulative new generation (TWh)', 2026)]
        npt.assert_almost_equal(scenario_awarded_gen_2026, expected_cum_awarded_gen_2026)


    def test_excel_2020_gen_error_false(self):
        s = Scenario.objects.get(pk=281)
        s.excel_quirks = False
        s.excel_2020_gen_error = False
        s.save()
        s.get_results()
        expected_cum_awarded_gen_2022 = 0

        a1 = s.auctionyear_dict[2021]
        for p in a1.pot_dict.values():
            expected_cum_awarded_gen_2022 += p.awarded_gen_result

        a2 = s.auctionyear_dict[2022]
        for p in a2.pot_dict.values():
            expected_cum_awarded_gen_2022 += p.awarded_gen_result

        scenario_awarded_gen_2022 = s.pivot('cum_awarded_gen').loc[('Total', 'Total'), ('Cumulative new generation (TWh)', 2022)]
        npt.assert_almost_equal(scenario_awarded_gen_2022, expected_cum_awarded_gen_2022)

        #period2
        expected_cum_awarded_gen_2026 = s.pivot('cum_awarded_gen').loc[('Total', 'Total'), ('Cumulative new generation (TWh)', 2025)]
        a6 = s.auctionyear_dict[2026]
        for p in a6.pot_dict.values():
            expected_cum_awarded_gen_2026 += p.awarded_gen_result
        scenario_awarded_gen_2026 = s.pivot('cum_awarded_gen').loc[('Total', 'Total'), ('Cumulative new generation (TWh)', 2026)]
        npt.assert_almost_equal(scenario_awarded_gen_2026, expected_cum_awarded_gen_2026)

    def test_all_excel_quirks_lumped(self):
        s = Scenario.objects.get(pk=281)
        s.excel_sp_error = False
        s.excel_nw_carry_error = False
        s.excel_2020_gen_error = False
        s.excel_include_previous_unsuccessful_nuclear = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_external_clearing_price = False
        s.excel_quirks = True
        s.save()
        results = s.pivot('cum_owed_v_wp')
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)

    def test_all_excel_quirks_individual(self):
        s = Scenario.objects.get(pk=281)
        s.excel_sp_error = True
        s.excel_nw_carry_error = True
        s.excel_2020_gen_error = True
        s.excel_include_previous_unsuccessful_nuclear = True
        s.excel_include_previous_unsuccessful_all = True
        s.excel_external_clearing_price = True
        s.excel_quirks = False
        s.save()
        results = s.pivot('cum_owed_v_wp')
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)

    # python manage.py test lcf.tests3.ExcelQuirkTests.test_quirks
    def test_quirks(self):
        s = Scenario.objects.get(pk=281)
        self.assertEqual(len(s.quirks()),4)
        s, results = create_scenario_from_form()
        self.assertEqual(len(s.quirks()),6)
        s, results = create_scenario_from_form(dfh.test_post_data_no_quirks)
        self.assertIsNone(s.quirks())



class CumT(TestCase):
    fixtures = ['tests/new/data2.json']

    def test_cum_future_techs(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.get_results()
        techs = s.flat_tech_dict
        t = techs["OFW2028"]
        self.assertQuerysetEqual(t.cum_future_techs(), ["<Technology: (<AuctionYear: 2028>, 'E', 'OFW')>",
                                                          "<Technology: (<AuctionYear: 2029>, 'E', 'OFW')>",
                                                          "<Technology: (<AuctionYear: 2030>, 'E', 'OFW')>"])

        t = techs["OFW2022"]

        self.assertQuerysetEqual(t.cum_future_techs(), ["<Technology: (<AuctionYear: 2022>, 'E', 'OFW')>",
                                                          "<Technology: (<AuctionYear: 2023>, 'E', 'OFW')>",
                                                          "<Technology: (<AuctionYear: 2024>, 'E', 'OFW')>",
                                                          "<Technology: (<AuctionYear: 2025>, 'E', 'OFW')>"])


class FixedNumProjectsTests(TestCase):
    fixtures = ['tests/new/data2.json']

    def test_create_tidal(self):
        s = Scenario.objects.get(pk=281)
        s.excel_quirks = True
        s.save()
        p = Pot.objects.get(auctionyear__scenario = s, name = "E", auctionyear__year=2022)

        #if num projects not specified, must be calculated
        t = Technology.objects.create(pot=p, name= "TL", max_deployment_cap = 1.14155251141553, load_factor = 0.22, project_gen=2200)
        self.assertEqual(round(t.this_year_gen()), 2200)
        self.assertEqual(t.previous_year().num_projects(),1)
        self.assertEqual(t.num_projects(),2)

        #using different LF/cap:
        t = Technology.objects.create(pot=p, name= "TL", max_deployment_cap = 1.00456621004566, load_factor = 0.25, project_gen=2200)
        self.assertEqual(round(t.this_year_gen()), 2200)
        self.assertEqual(t.previous_year().num_projects(),1)
        self.assertEqual(t.num_projects(),2)

        #if num_new_projects is specified, this number should be used instead and max_deployment_cap should be backfilled
        t = Technology.objects.create(pot=p, name= "TL", num_new_projects = 1, load_factor = 0.22, project_gen=2200)
        self.assertEqual(round(t._max_deployment_cap,5),round(1.14155251141553,5))
        self.assertEqual(round(t.this_year_gen()),2200)
        self.assertEqual(t.previous_year().num_projects(),1)
        self.assertEqual(t.num_projects(),2)

        #if both are specified, use num projects
        t = Technology.objects.create(pot=p, name= "TL", num_new_projects = 1, max_deployment_cap = 9999999999, load_factor = 0.22, project_gen=2200)
        self.assertEqual(round(t._max_deployment_cap,5),round(1.14155251141553,5))
        self.assertEqual(round(t.this_year_gen()),2200)
        self.assertEqual(t.previous_year().num_projects(),1)
        self.assertEqual(t.num_projects(),2)

        #if not tidal:
        t = Technology.objects.create(pot=p, name= "OFW", num_new_projects = 5, load_factor = 0.448, project_gen=832)
        self.assertEqual(round(t.this_year_gen()),4160) #= 5 * 832
        self.assertEqual(round(t._max_deployment_cap,2),round(t.project_gen / t.load_factor / 8760 * 5,2))
        self.assertEqual(t.previous_year()._max_deployment_cap,1.9)
        self.assertEqual(t.previous_year().load_factor,0.434)
        self.assertEqual(round(t.previous_year().new_generation_available(),2),round(14213.975999999999,2))
        self.assertEqual(t.previous_year().num_new_projects,None)
        self.assertEqual(t.previous_year().project_gen,832)
        self.assertEqual(t.previous_year().num_projects(),17) # sketchy because I was getting 25 doing the same thing in the shell
        self.assertEqual(t.num_projects(),22)



class InputDisplayTests(TestCase):
    fixtures = ['tests/new/data2.json']

    def test_techs_input(self):
        s = Scenario.objects.get(pk=245)
        inp = s.techs_input().set_index(dfh.tech_inputs_index['titles'])
        val = inp.loc[('E','OFW',2025),'Min LCOE']
        self.assertEqual(val, 70.21)
        val = inp.loc[('SN','NU',2024),'Max new capacity']
        self.assertEqual(val, 2.9)

    def test_prices_input(self):
        s = Scenario.objects.get(pk=245)
        df = s.prices_input()
        df.index = dfh.prices_columns
        val = df.loc['Wholesale electricity price', 2022]
        self.assertEqual(val, 58.47)

class StoringResults(TestCase):
    fixtures = ['tests/new/data2.json']

    def test_scenario_db_storage(self):
        s = Scenario.objects.all().get(pk=281)
        s.get_results()
        t = Scenario.objects.all().get(pk=281)
        t.get_results()
        assert_frame_equal(s.get_results(),t.get_results())

    def test_auction_cache(self):
        s = Scenario.objects.get(pk=281)
        auctionyears = AuctionYear.objects.filter(scenario=s,year__range=[2020,2030]).order_by('-year')
        pots = Pot.objects.filter(auctionyear__in = auctionyears)
        p1 = pots.get(auctionyear__year=2021,name="E")
        df = p1.run_relevant_auction()
        p1.run_relevant_auction.cache_clear()
        p1_again = pots.get(auctionyear__year=2021,name="E")
        df_again = p1_again.run_relevant_auction()
        df.dtypes
        df_again.dtypes
        assert_frame_equal(df, df_again)


class TestCumProj(TestCase):
    fixtures = ['tests/3/data2.json'] # old TS gen, but with new 'false cum proj'


    def test_num_projects(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        self.assertEqual([ofw.num_projects() for ofw in ofw_list], [8, 17, 26, 35, 44, 54, 64, 74, 84, 93, 103])

    def test_run_auction(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        p = s.auctionyear_dict[2022].pot_dict['E']
        p.cum_run_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
        # print(p.projects())
        s.get_results()
        # print(s.pivot('awarded_cap',2))

    def test_run_auction_budget(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.excel_external_clearing_price = True
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2031)]
        # p = s.auctionyear_dict[2027].pot_dict['E']
        for p in e_list:
            p.cum_run_auction()
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
            self.assertTrue(p.awarded_cost_result < p.budget())


    def test_budget_period_2(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        a1 = s.auctionyear_dict[2021]
        a6 = s.auctionyear_dict[2026]
        self.assertEqual(a1.budget_all(), a1.starting_budget())
        self.assertEqual(a6.budget_all(), a6.starting_budget())


    def test_accounting_cost(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.excel_external_clearing_price = True
        s.save()
        results = s.pivot('cum_owed_v_wp',1)
        # print(results)
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)


    def test_fit_cost_individual_quirks(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.excel_external_clearing_price = True
        s.excel_quirks = False
        s.save()
        s.get_results()
        p = s.auctionyear_dict[2021].pot_dict['FIT']
        self.assertEqual(p.awarded_cost_result, 89)

    def test_fit_cost_lumped_quirks(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = False
        s.excel_sp_error = False
        s.excel_2020_gen_error = False
        s.excel_quirks = True
        s.save()
        s.get_results()
        p = s.auctionyear_dict[2021].pot_dict['FIT']
        self.assertEqual(p.awarded_cost_result, 89)


class TestNonCumProj(TestCase):
    fixtures = ['tests/3/data2.json'] # old TS gen, but with new 'false cum proj'

    def test_non_cum_num_projects(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        #results = s.pivot('cum_owed_v_wp',1)
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        self.assertEqual([ofw.non_cum_num_projects() for ofw in ofw_list], [8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9])

    def test_non_cum_levelised_cost_distribution(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        #results = s.pivot('cum_owed_v_wp',1)
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        self.assertEqual([round(i) for i in ofw_list[1].non_cum_levelised_cost_distribution().values.tolist() ], [75, 78, 81, 85, 88, 92, 95, 98])

    def test_non_cum_projects_index(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        #results = s.pivot('cum_owed_v_wp',1)
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        ofw = ofw_list[1]
        self.assertEqual(ofw.non_cum_projects_index(), ['2021_OFW1', '2021_OFW2', '2021_OFW3', '2021_OFW4', '2021_OFW5', '2021_OFW6', '2021_OFW7', '2021_OFW8'])

    def test_non_cum_projects(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        ofw = ofw_list[1]
        self.assertEqual(ofw.non_cum_projects().levelised_cost[3], ofw.non_cum_levelised_cost_distribution()[3])

    def test_non_cum_concat_projects(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        p = s.auctionyear_dict[2026].pot_dict['E']
        tech_index = [item for t in p.technology_dict.values() for item in t.non_cum_projects_index() ]
        tech_costs = [item for t in p.technology_dict.values() for item in t.non_cum_levelised_cost_distribution().tolist() ]
        self.assertEqual(sorted(p.non_cum_concat_projects().index.tolist()), sorted(tech_index))
        self.assertEqual(sorted(p.non_cum_concat_projects().levelised_cost.tolist()), sorted(tech_costs))

    def test_non_cum_run_auction_max_deployment_cap(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        results = s.get_results()
        ofw_max_deployment_caps = Series([ a.pot_dict['E'].technology_dict['OFW'].max_deployment_cap for a in s.auctionyear_dict.values() if a.year > 2020 ], index=range(2021,2031))
        ofw_caps = s.pivot('awarded_cap').loc[('Emerging', 'Offshore wind')]
        ofw_caps.index = range(2021,2031)
        self.assertTrue((ofw_max_deployment_caps > ofw_caps).all())

    def test_non_cum_run_auction_budget(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2026)]
        # p = s.auctionyear_dict[2027].pot_dict['E']
        for p in e_list:
            p.non_cum_run_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
            self.assertTrue(p.awarded_cost_result < p.budget())

    def test_non_cum_budget_period_2(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        a1 = s.auctionyear_dict[2021]
        a6 = s.auctionyear_dict[2026]
        self.assertEqual(a1.budget_all(), a1.starting_budget())
        self.assertEqual(a6.budget_all(), a6.starting_budget())




class TestCumProjSimple(TestCase):
    fixtures = ['tests/3/simple.json']

    def test_unspent(self,budget,expected_cost_2025):
        s = Scenario.objects.all().get(pk=586)
        s.excel_external_clearing_price = True
        s.excel_include_previous_unsuccessful_all = True
        s.budget = budget
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2026)]
        for p in e_list:
            p.cum_run_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all(), 'starting auctionyear budget', p.auctionyear.starting_budget())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
        results = s.pivot('cum_owed_v_wp',1)
        # print('scenario budget', s.budget)
        # print('accounting cost 2025', results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)])
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],2),expected_cost_2025)


    def test_unspent_high(self):
        self.test_unspent(5, 1.42)
        # constrained by (inaccurate) deployment

    def test_unspent_normal(self):
        self.test_unspent(2.9, 1.42)
        # constrained by (inaccurate) deployment

    def test_unspent_low(self):
        self.test_unspent(1.8, 1.42)
        # constrained by (inaccurate) deployment

    def test_unspent_lower(self):
        self.test_unspent(1.3, 1.05)
        # constrained by budget


class TestNonCumProjSimple(TestCase):
    fixtures = ['tests/3/simple.json']

    def test_non_cum_unspent(self,budget, expected_cost_2025):
        s = Scenario.objects.all().get(pk=586)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.excel_external_clearing_price = True
        s.budget = budget
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2026)]
        for p in e_list:
            p.run_relevant_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all(), 'starting auctionyear budget', p.auctionyear.starting_budget())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
        results = s.pivot('cum_owed_v_wp',1)
        # print('scenario budget', s.budget)
        # print('accounting cost 2025', results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)])
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],2),expected_cost_2025)


    def test_non_cum_unspent_high(self):
        self.test_non_cum_unspent(5,1.33)
        # constrained by deployment

    def test_non_cum_unspent_normal(self):
        self.test_non_cum_unspent(2.9,1.33)
        # constrained by deployment

    def test_non_cum_unspent_low(self):
        self.test_non_cum_unspent(1.8,1.30)
        # constrained by deployment 2022-2025, constrained by budget in 2021

    def test_non_cum_unspent_lower(self):
        self.test_non_cum_unspent(1.3, 1.05)
        # constrained by budget

class TestIP(TestCase):
    fixtures = ['tests/3/data2.json']

    def test_nw_v_gas(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_quirks = True
        s.save()
        p = s.auctionyear_dict[2021].pot_dict['FIT']

        p.run_relevant_auction()
        t = p.technology_dict['NW']
        self.assertEqual(t.cum_owed_v_gas, (t.awarded_gen * t.strike_price) - (t.awarded_gen * p.auctionyear.gas_price))
        self.assertEqual(t.cum_owed_v_gas, (t.awarded_gen * (t.strike_price - p.auctionyear.gas_price)))
        pivot = s.pivot('cum_owed_v_gas',1)
        # print(pivot)

class ViewsTests(TestCase):

    fixtures = ['tests/new/data2.json']

    def test_policy_new_view(self):
        initial_policy_count = Policy.objects.count()
        resp = self.client.get(reverse('policy_new'))
        self.assertEqual(resp.status_code, 200)
        post_data = {'name': 'test name',
                     'description': 'test description',
                     'method': 'SU',
                     'file': open('lcf/template.csv'),
                     }
        post_resp = self.client.post(reverse('policy_new'),post_data)

        self.assertEqual(post_resp.status_code,302)
        new_policy_count = Policy.objects.count()
        self.assertEqual(new_policy_count,initial_policy_count+1)

    # python manage.py test lcf.tests3.ViewsTests.test_scenario_new_view
    def test_scenario_new_view(self):
        initial_scenario_count = Scenario.objects.count()
        initial_technology_count = Technology.objects.count()
        # print(initial_technology_count)
        resp = self.client.get(reverse('scenario_new'))
        post_data = dfh.test_post_data_quirks
        post_data['file'] = open('lcf/template.csv')

        post_resp = self.client.post(reverse('scenario_new'),post_data)

        self.assertEqual(post_resp.status_code,302)
        new_scenario_count = Scenario.objects.count()
        self.assertEqual(new_scenario_count,initial_scenario_count+1)
        s = Scenario.objects.order_by('-date')[0]
        results = s.pivot('cum_owed_v_wp',1)
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 3.123)
        self.assertEqual(Technology.objects.count(), initial_technology_count + 88)

class TestPolicies(TestCase):
    fixtures = ['prod/data.json']

    def update_tech_with_policies(self,method,n, expected_min_levelised_cost):
        filename = {'MU': "lcf/policy_template_mu.csv", 'SU': "lcf/policy_template_su.csv"}
        effects = DataFrame(pd.read_csv(filename[method])).to_json()
        pl = Policy.objects.create(name="test", effects=effects, method=method)
        policies = [pl] if n == 1 else [pl, pl]
        tech_df = DataFrame(pd.read_csv("lcf/template.csv"))
        res = update_tech_with_policies(tech_df,policies)
        # npt.assert_almost_equal(res.loc[('OFW', 2020), 'min_levelised_cost'], expected_min_levelised_cost, decimal=4)
        npt.assert_almost_equal(res[(res.tech_name == 'OFW') & (res.year == 2020)].min_levelised_cost[0], expected_min_levelised_cost, decimal=4)
        # npt.assert_almost_equal(res.loc[('OFW', 2020), 'max_deployment_cap'], 1.9, decimal=4)
        npt.assert_almost_equal(res[(res.tech_name == 'OFW') & (res.year == 2020)].max_deployment_cap[0], 1.9, decimal=4)

    def process_scenario_form_with_policies(self,method,n,expected_accounting_cost):
        filename = {'MU': "lcf/policy_template_mu.csv", 'SU': "lcf/policy_template_su.csv"}
        effects = DataFrame(pd.read_csv(filename[method])).to_json()
        if n == 1:
            pl = Policy.objects.create(name="test", effects=effects, method=method)
            policies = [pl.pk]
        elif n == 2:
            pl1 = Policy.objects.create(name="test", effects=effects, method=method)
            pl2 = Policy.objects.create(name="test", effects=effects, method=method)
            policies = [pl1.pk, pl2.pk]
        post_data = dfh.test_post_data_quirks
        post_data['policies'] = policies
        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        if scenario_form.is_valid():
            process_scenario_form(scenario_form,new_wp=False)
            recent_s = Scenario.objects.order_by('-date')[0]
            results = recent_s.pivot('cum_owed_v_wp')
            self.assertEqual(recent_s.name, "test 1234")
            self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), expected_accounting_cost)
        else:
            print(scenario_form.errors)

    def test_update_tech_with_policies(self):
        self.update_tech_with_policies('MU',1, 64.20185)
        self.update_tech_with_policies('SU',1, 66.33539)
        self.update_tech_with_policies('MU',2, 57.78166)
        self.update_tech_with_policies('SU',2, 61.33539)

    def test_process_scenario_form_with_policies(self):
        self.process_scenario_form_with_policies('MU',1, 2.482)
        self.process_scenario_form_with_policies('SU',1, 2.597)
        self.process_scenario_form_with_policies('MU',2, 2.124)
        self.process_scenario_form_with_policies('SU',2, 2.367)


    def test_update_tech_with_policies_with_different_methods(self):
        effects1 = DataFrame(pd.read_csv("lcf/policy_template_mu.csv")).to_json()
        effects2 = DataFrame(pd.read_csv("lcf/policy_template_su.csv")).to_json()
        pl1 = Policy.objects.create(name="test", effects=effects1, method='MU')
        pl2 = Policy.objects.create(name="test", effects=effects2, method='SU')
        policies = [pl1, pl2]
        tech_df = DataFrame(pd.read_csv("lcf/template.csv"))
        self.assertRaises(PolicyMethodErrorTypeError, update_tech_with_policies, tech_df, policies)


    def test_process_scenario_form_with_policies_with_different_methods(self):
        effects1 = DataFrame(pd.read_csv("lcf/policy_template_mu.csv")).to_json()
        effects2 = DataFrame(pd.read_csv("lcf/policy_template_su.csv")).to_json()
        pl1 = Policy.objects.create(name="test", effects=effects1, method='MU')
        pl2 = Policy.objects.create(name="test", effects=effects2, method='SU')
        policies = [pl1.pk, pl2.pk]
        post_data = dfh.test_post_data_quirks
        post_data['policies'] = policies
        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        if scenario_form.is_valid():
            self.assertEqual(process_scenario_form(scenario_form,new_wp=False),'error')


class TestHelpers(TestCase):
    fixtures = ['prod/data.json']

    def test_process_scenario_form(self):
        recent_s = Scenario.objects.order_by('-date')[0]
        print(recent_s.name)

        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        if scenario_form.is_valid():
            process_scenario_form(scenario_form,new_wp=False)
            recent_s = Scenario.objects.order_by('-date')[0]
            results = recent_s.pivot('cum_owed_v_wp')
            self.assertEqual(recent_s.name, "test 1234")
            self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)
        else:
            print(scenario_form.errors)

class Interpolate(TestCase):
    fixtures = ['prod/data.json']

    # python manage.py test lcf.tests3.Interpolate.test_interpolate_tech_df
    def test_interpolate_tech_df(self):
        post_data = dfh.test_post_data_quirks
        file_data_without = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        file_data_with = {'file': SimpleUploadedFile('template_interpolate.csv', open('lcf/template_interpolate.csv', 'rb').read())}
        scenario_form_without = ScenarioForm(post_data, file_data_without)
        scenario_form_with = ScenarioForm(post_data, file_data_with)
        s_without = scenario_form_without.save()
        s_with = scenario_form_with.save()
        # prices_df = get_prices(s_without, scenario_form_without)
        prices_df = get_default_prices(new_wp=False)[0]
        create_auctionyear_and_pot_objects(prices_df,s_without)
        create_auctionyear_and_pot_objects(prices_df,s_with)
        tech_df_without = pd.read_csv(scenario_form_without.cleaned_data['file'])
        tech_df_with = pd.read_csv(scenario_form_with.cleaned_data['file'])
        tech_df_with = interpolate_tech_df(tech_df_with)
        ofw_with = tech_df_with[(tech_df_with.tech_name == 'OFW') & (tech_df_with.year == 2024)].min_levelised_cost.values[0]
        ofw_without = tech_df_without[(tech_df_without.tech_name == 'OFW') & (tech_df_without.year == 2024)].min_levelised_cost.values[0]
        npt.assert_almost_equal(ofw_with, ofw_without, decimal=4)
        tech_df_without_interpolated_anyway = interpolate_tech_df(tech_df_without)
        ofw_without_interpolated_anyway = tech_df_without_interpolated_anyway[(tech_df_without_interpolated_anyway.tech_name == 'OFW') & (tech_df_without_interpolated_anyway.year == 2024)].min_levelised_cost.values[0]
        npt.assert_almost_equal(ofw_without, ofw_without_interpolated_anyway, decimal=4)

    # python manage.py test lcf.tests3.Interpolate.test_process_scenario_form_with_interpolation
    def test_process_scenario_form_with_interpolation(self):
        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template_interpolate.csv', open('lcf/template_interpolate.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        if scenario_form.is_valid():
            process_scenario_form(scenario_form,new_wp=False)
            recent_s = Scenario.objects.order_by('-date')[0]
            results = recent_s.pivot('cum_owed_v_wp')
            self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)


class Notes(TestCase):
    fixtures = ['prod/data.json']


    # python manage.py test lcf.tests3.Notes.test_parse_file_with_notes
    def test_parse_file_with_notes(self):
        file = open('lcf/template_with_sources.csv')
        tech_df, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes = parse_file(file)
        self.assertEqual(len(tech_df), 88)
        self.assertEqual(len(tech_df.columns), 11)
        self.assertEqual(len(notes), 17)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)
        self.assertEqual(len(original_tech_df_with_note_columns.columns), 18)


    # python manage.py test lcf.tests3.Notes.test_parse_file_with_prices_and_prices_notes
    def test_parse_file_with_prices_and_prices_notes(self):
        file = open('lcf/template_with_sources_and_prices.csv')
        tech_df, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes = parse_file(file)
        self.assertEqual(len(notes), 19)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)
        self.assertEqual(len(original_tech_df_with_note_columns.columns), 18)
        self.assertFalse((original_tech_df_with_note_columns.min_levelised_cost_note == 'nan').all())

    # python manage.py test lcf.tests3.Notes.test_parse_file_with_and_without_prices
    def test_parse_file_with_and_without_prices(self):
        file = open('lcf/template_with_prices.csv')
        tech_df_with_prices, original_tech_df_with_note_columns, prices_df_from_upload, original_prices_df_with_note_columns_from_upload, notes = parse_file(file)
        self.assertEqual(len(notes), 0)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)
        self.assertEqual(len(original_tech_df_with_note_columns.columns), 18)
        # print(prices_df)
        file = open('lcf/template.csv')
        tech_df_without_prices, original_tech_df_with_note_columns, prices_df_from_default, original_prices_df_with_note_columns_from_default, notes = parse_file(file)
        self.assertEqual(len(notes), 0)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)
        self.assertEqual(len(original_tech_df_with_note_columns.columns), 18)

        assert_frame_equal(tech_df_with_prices,tech_df_without_prices)
        assert_frame_equal(prices_df_from_upload, prices_df_from_default)
        assert_frame_equal(original_prices_df_with_note_columns_from_upload, original_prices_df_with_note_columns_from_default)

        # different prices in upload should override default
        file = open('lcf/template_with_new_prices.csv')
        tech_df_with_prices, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes = parse_file(file)
        self.assertNotEqual(prices_df.wholesale_prices[2021],prices_df_from_default.wholesale_prices[2021])

    # python manage.py test lcf.tests3.Notes.test_parse_file_with_or_without_notes_and_get_same_tech_data
    def test_parse_file_with_or_without_notes_and_get_same_tech_data(self):
        """Test that a file with sources at the bottom returns same tech df as one without"""
        file = open('lcf/template_with_sources.csv')
        tech_df_with_notes, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes = parse_file(file)
        self.assertEqual(len(notes), 17)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)
        self.assertEqual(len(original_tech_df_with_note_columns.columns), 18)
        self.assertFalse((original_tech_df_with_note_columns.min_levelised_cost_note == 'nan').all())

        file = open('lcf/template.csv')
        tech_df_without_notes, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes = parse_file(file)
        self.assertEqual(len(notes), 0)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)
        self.assertEqual(len(original_tech_df_with_note_columns.columns), 18)
        original_tech_df_with_note_columns.min_levelised_cost_note = original_tech_df_with_note_columns.min_levelised_cost_note.astype(str)
        self.assertTrue((original_tech_df_with_note_columns.min_levelised_cost_note == 'nan').all())

        assert_frame_equal(tech_df_with_notes,tech_df_without_notes)

    # python manage.py test lcf.tests3.Notes.test_parse_file_with_different_column_order
    def test_parse_file_with_different_column_order(self):
        file = open('lcf/template_with_sources2.csv')
        tech_df, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes = parse_file(file)
        self.assertEqual(len(notes), 17)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)


    # python manage.py test lcf.tests3.Notes.test_process_scenario_form_with_notes_without_notes
    def test_process_scenario_form_with_notes_without_notes(self):
        post_data = dfh.test_post_data_quirks

        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        if scenario_form.is_valid():
            process_scenario_form(scenario_form,new_wp=False)
            recent_s = Scenario.objects.order_by('-date')[0]
            results = recent_s.pivot('cum_owed_v_wp')
            self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)
            # print(recent_s.csv_inc_notes)

        file_data = {'file': SimpleUploadedFile('template_with_sources.csv', open('lcf/template_with_sources.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        if scenario_form.is_valid():
            process_scenario_form(scenario_form,new_wp=False)
            recent_s = Scenario.objects.order_by('-date')[0]
            results = recent_s.pivot('cum_owed_v_wp')
            self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)
            # print(recent_s.csv_inc_notes)

    # python manage.py test lcf.tests3.Notes.test_process_scenario_form_with_different_column_order
    def test_process_scenario_form_with_different_column_order(self):
        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template_with_sources2.csv', open('lcf/template_with_sources2.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        if scenario_form.is_valid():
            process_scenario_form(scenario_form,new_wp=False)
            recent_s = Scenario.objects.order_by('-date')[0]
            results = recent_s.pivot('cum_owed_v_wp')
            self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)

    # python manage.py test lcf.tests3.Notes.test_retrieve_sources
    def test_retrieve_sources(self):
        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template_with_sources.csv', open('lcf/template_with_sources.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        process_scenario_form(scenario_form,new_wp=False)
        s = Scenario.objects.order_by('-date')[0]
        notes = s.get_notes()
        self.assertEqual(notes.link[0], 'http://www.theccc.org.uk/wp-content/uploads/2014/07/CCC-Progress-Report-2014_web_2.pdf')
        sources = s.get_original_data_inc_sources()
        sources = sources.set_index(dfh.tech_inputs_index['keys'])
        self.assertEqual(sources.loc[('E','OFW', 2020), 'min_levelised_cost_note'], 2)
        self.assertFalse(sources[dfh.note_columns].isnull().all().all())

        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        process_scenario_form(scenario_form,new_wp=False)
        s = Scenario.objects.order_by('-date')[0]
        notes = s.get_notes()
        self.assertEqual(len(notes), 0)
        self.assertEqual(len(notes.columns), 5)
        sources = s.get_original_data_inc_sources()
        self.assertEqual(len(sources.columns), 18)
        self.assertTrue(sources[dfh.note_columns].isnull().all().all())

        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template_with_sources_and_prices.csv', open('lcf/template_with_sources_and_prices.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        process_scenario_form(scenario_form,new_wp=False)
        s = Scenario.objects.order_by('-date')[0]
        notes = s.get_notes()
        self.assertEqual(notes.link[0], 'http://www.theccc.org.uk/wp-content/uploads/2014/07/CCC-Progress-Report-2014_web_2.pdf')
        sources = s.get_original_data_inc_sources()
        sources = sources.set_index(dfh.tech_inputs_index['keys'])
        self.assertEqual(sources.loc[('E','OFW', 2020), 'min_levelised_cost_note'], 2)
        self.assertFalse(sources[dfh.note_columns].isnull().all().all())

    # # python manage.py test lcf.tests3.Notes.test_sources_html
    # def test_sources_html(self):
    #     post_data = dfh.test_post_data_quirks
    #     file_data = {'file': SimpleUploadedFile('template_with_sources_and_prices.csv', open('lcf/template_with_sources_and_prices.csv', 'rb').read())}
    #     scenario_form = ScenarioForm(post_data, file_data)
    #     process_scenario_form(scenario_form)
    #     s = Scenario.objects.order_by('-date')[0]
    #     s.original_data_inc_prices_html()

    # # python manage.py test lcf.tests3.Notes.test_get_prices
    # def test_get_prices(self):
    #     post_data = dfh.test_post_data_quirks
    #     file_data = {'file': SimpleUploadedFile('template_with_sources_and_prices.csv', open('lcf/template_with_sources_and_prices.csv', 'rb').read())}
    #     scenario_form = ScenarioForm(post_data, file_data)
    #     process_scenario_form(scenario_form,new_wp=False)
    #     s = Scenario.objects.order_by('-date')[0]
    #     prices = s.get_original_prices_inc_sources()
    #     prices_html = s.original_prices_inc_sources_html()
    #     # print(prices_html)


    # python manage.py test lcf.tests3.Notes.test_inputs_download
    def test_inputs_download(self):
        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template_with_sources_and_prices.csv', open('lcf/template_with_sources_and_prices.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        process_scenario_form(scenario_form,new_wp=False)
        s = Scenario.objects.order_by('-date')[0]
        tech, prices, notes = s.inputs_download()
        self.assertEqual(len(prices),5)
        self.assertEqual(prices[0][1], 2020)
        self.assertEqual(len(tech[0]),18)
        self.assertEqual(tech[1][2], 2020)
        # print(prices)
        # print(tech)
        # print(notes)

        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        process_scenario_form(scenario_form,new_wp=False)
        s = Scenario.objects.order_by('-date')[0]
        tech, prices, notes = s.inputs_download()
        self.assertEqual(len(prices),5)
        self.assertEqual(prices[0][1], 2020)
        self.assertEqual(len(tech[0]),18)
        self.assertEqual(tech[1][2], 2020)


        s = Scenario.objects.get(pk=453)
        tech, prices, notes = s.inputs_download()
        self.assertEqual(len(prices),3)
        self.assertEqual(prices[0][1], 2020)
        self.assertEqual(len(tech[0]),11)
        self.assertEqual(tech[1][2], 2020)

class Exceptions(TestCase):
    fixtures = ['prod/data.json']

    # python manage.py test lcf.tests3.Exceptions.test_upload_non_csv
    def test_upload_non_csv(self):
        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('admin.py', open('lcf/admin.py', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        self.assertFalse(scenario_form.is_valid())

    # python manage.py test lcf.tests3.Exceptions.test_blank_scenario
    def test_blank_scenario(self):
        post_data = {'name': '',
                     'percent_emerging': 0.6,
                     'budget': 3.3,
                     'excel_quirks': 'on',
                     'end_year1': 2025,
                     'wholesale_prices': "excel",
                     'gas_prices': "excel",
                     }
        scenario_form = ScenarioForm(post_data)
        self.assertFalse(scenario_form.is_valid())
        self.assertEqual(scenario_form.errors, {
            'name': ['This field is required.'],
            'file': ['This field is required.'],
        })

    # python manage.py test lcf.tests3.Exceptions.test_process_scenario_form_with_file_with_invalid_columns
    def test_process_scenario_form_with_file_with_invalid_columns(self):
        scenario_count = Scenario.objects.count()
        post_data = dfh.test_post_data_quirks
        file_data = {'file': SimpleUploadedFile('template_error.csv', open('lcf/template_error.csv', 'rb').read())}
        # print(pd.read_csv(file_data['file']))
        scenario_form = ScenarioForm(post_data, file_data)
        self.assertTrue(scenario_form.is_valid())
        self.assertRaises(KeyError, process_scenario_form, scenario_form)
        new_scenario_count = Scenario.objects.count()
        self.assertEqual(scenario_count, new_scenario_count)

        scenario_count = Scenario.objects.count()
        file_data = {'file': SimpleUploadedFile('template_with_sources_error.csv', open('lcf/template_with_sources_error.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        self.assertTrue(scenario_form.is_valid())

        self.assertRaises(KeyError, process_scenario_form, scenario_form)
        new_scenario_count = Scenario.objects.count()
        self.assertEqual(scenario_count, new_scenario_count)

        scenario_count = Scenario.objects.count()
        file_data = {'file': SimpleUploadedFile('template_with_sources_error2.csv', open('lcf/template_with_sources_error2.csv', 'rb').read())}
        scenario_form = ScenarioForm(post_data, file_data)
        self.assertTrue(scenario_form.is_valid())
        self.assertRaises(KeyError, process_scenario_form, scenario_form)
        new_scenario_count = Scenario.objects.count()
        self.assertEqual(scenario_count, new_scenario_count)

    # python manage.py test lcf.tests3.Exceptions.test_view_with_invalid_file
    def test_view_with_invalid_file(self):
        post_data = dfh.test_post_data_quirks
        post_data['file'] = open('lcf/template_with_sources_error.csv')
        post_resp = self.client.post(reverse('scenario_new'), post_data)
        self.assertEqual(post_resp.status_code,200)
        self.assertEqual(post_resp.context['file_error'].args[0], "load_factor6 shouldn't be in column headers")
        # self.assertEqual(post_resp.context['file_error'].args[0], "['load_factor'] not in index")

        post_data = dfh.test_post_data_quirks
        post_data['file'] = open('lcf/template_with_sources_error2.csv')
        post_resp = self.client.post(reverse('scenario_new'), post_data)
        self.assertEqual(post_resp.status_code,200)
        self.assertEqual(post_resp.context['file_error'].args[0], "load_factor_note6 shouldn't be in column headers")

        post_data = dfh.test_post_data_quirks
        post_data['file'] = open('lcf/template_with_sources_error3.csv')
        post_resp = self.client.post(reverse('scenario_new'), post_data)
        self.assertEqual(post_resp.status_code,200)
        self.assertEqual(post_resp.context['file_error'].args[0], "year2 shouldn't be in column headers")

    # python manage.py test lcf.tests3.Exceptions.test_view_with_invalid_scenario
    def test_view_with_invalid_scenario(self):
        s = Scenario.objects.create(name="foo")
        resp = self.client.get(reverse('scenario_detail', kwargs={'pk':s.pk}))
        self.assertEqual(resp.status_code,200)

    # python manage.py test lcf.tests3.Exceptions.test_view_with_non_existant_scenario
    def test_view_with_non_existant_scenario(self):
        resp = self.client.get(reverse('scenario_detail', kwargs={'pk':999}))
        self.assertEqual(resp.status_code,200)

class Display(TestCase):
    fixtures = ['prod/data.json']

    # python manage.py test lcf.tests3.Display.test_summary_chart
    def test_summary_chart(self):
        column = 'cum_owed_v_wp'
        s = Scenario.objects.get(pk=453)
        chart_data, options, options_small = s.df_to_chart_data(column,summary=True)['chart_data'], s.df_to_chart_data(column,summary=True)['options'], s.df_to_chart_data(column,summary=True)['options_small']
        # print(chart_data)

class Intermediate(TestCase):
    fixtures = ['prod/data.json']

    # python manage.py test lcf.tests3.Intermediate.test_cum_project_summary
    def test_cum_project_summary(self):
        s = Scenario.objects.get(pk=453)
        s.results = None
        s.save()
        s.get_results()
        p = s.auctionyear_dict[2021].pot_dict['E']
        t = s.flat_tech_dict['OFW2021']
        # print(p.project_summary('available', t))
        npt.assert_almost_equal(t.project_summary('available', 'num'), 13)
        npt.assert_almost_equal(t.project_summary('eligible', 'num'), 13)
        npt.assert_almost_equal(t.project_summary('successful', 'num'), 7)
        npt.assert_almost_equal(t.project_summary('available', 'gen'), 13*.832)
        npt.assert_almost_equal(t.project_summary('eligible', 'gen'), 13*.832)
        npt.assert_almost_equal(t.project_summary('successful', 'gen'), 7*.832)
        npt.assert_almost_equal(t.project_summary('available', 'cost'), 13*832*(t.strike_price-t.pot.auctionyear.wholesale_price)/1000)
        npt.assert_almost_equal(t.project_summary('eligible', 'cost'), 13*832*(t.strike_price-t.pot.auctionyear.wholesale_price)/1000)
        npt.assert_almost_equal(t.project_summary('successful', 'cost'), 7*832*(t.strike_price-t.pot.auctionyear.wholesale_price)/1000)

    # python manage.py test lcf.tests3.Intermediate.test_non_cum_project_summary

    def test_non_cum_project_summary(self):
        post_data = dfh.test_post_data_no_quirks
        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
        # just because this test was written before I had made the below option to switch off exogenous clearing price, so the answers it expects are with it on
        post_data['excel_external_clearing_price'] = 'on'
        scenario_form = ScenarioForm(post_data, file_data)
        process_scenario_form(scenario_form,new_wp=False)
        s = Scenario.objects.order_by('-date')[0]
        p = s.auctionyear_dict[2021].pot_dict['E']
        t = s.flat_tech_dict['OFW2021']
        results = s.pivot('cum_owed_v_wp')
        npt.assert_almost_equal(t.project_summary('available', 'num'), 8)
        npt.assert_almost_equal(t.project_summary('eligible', 'num'), 8)
        npt.assert_almost_equal(t.project_summary('successful', 'num'), 7)
        npt.assert_almost_equal(t.project_summary('available', 'gen'), 8*.832)
        npt.assert_almost_equal(t.project_summary('eligible', 'gen'), 8*.832)
        npt.assert_almost_equal(t.project_summary('successful', 'gen'), 7*.832)
        npt.assert_almost_equal(t.project_summary('available', 'cost'), 8*832*(t.strike_price-t.pot.auctionyear.wholesale_price)/1000)
        npt.assert_almost_equal(t.project_summary('eligible', 'cost'), 8*832*(t.strike_price-t.pot.auctionyear.wholesale_price)/1000)
        npt.assert_almost_equal(t.project_summary('successful', 'cost'), 7*832*(t.strike_price-t.pot.auctionyear.wholesale_price)/1000)

    # python manage.py test lcf.tests3.Intermediate.test_scenario_intermediate_results
    def test_scenario_intermediate_results(self):
        s = Scenario.objects.get(pk=453)
        s.results = None
        s.intermediate_results = None
        s.save()
        s.get_results()
        s.get_intermediate_results()



def create_scenario_from_form(post_data=dfh.test_post_data_quirks, file_data=None):
    if file_data is None:
        file_data = {'file': SimpleUploadedFile('template.csv', open('lcf/template.csv', 'rb').read())}
    scenario_form = ScenarioForm(post_data, file_data)
    if scenario_form.is_valid():
        process_scenario_form(scenario_form,new_wp=False)
        recent_s = Scenario.objects.order_by('-date')[0]
        results = recent_s.pivot('cum_owed_v_wp')
        return recent_s, results
        # self.assertEqual(recent_s.name, "test 1234")
        # self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)


class Clearing(TestCase):
    fixtures = ['prod/data.json']

    # python manage.py test lcf.tests3.Clearing.test_form_option
    def test_form_option(self):
        post_data = {'name': 'test 1234',
                     'percent_emerging': 0.6,
                     'budget': 3.3,
                     'end_year1': 2025,
                     'wholesale_prices': "excel",
                     'gas_prices': "excel",
                     'excel_sp_error': 'on',
                     'excel_2020_gen_error': 'on',
                     'excel_nw_carry_error': 'on',
                     'excel_include_previous_unsuccessful_nuclear': 'on',
                     'excel_include_previous_unsuccessful_all': 'on',
                     'excel_external_clearing_price': 'on',
                     }
        s, results = create_scenario_from_form(post_data)
        p = s.auctionyear_dict[2021].pot_dict['E']

        s_quirks, results_quirks = create_scenario_from_form(dfh.test_post_data_quirks)
        p_quirks = s_quirks.auctionyear_dict[2021].pot_dict['E']
        assert_frame_equal(results, results_quirks)

    # python manage.py test lcf.tests3.Clearing.test_exogenous
    def test_exogenous(self):
        """check the right part of the auction code is being run"""
        post_data = {'name': 'test 1234',
                     'percent_emerging': 0.6,
                     'budget': 3.3,
                     'end_year1': 2025,
                     'wholesale_prices': "excel",
                     'gas_prices': "excel",
                     'excel_include_previous_unsuccessful_nuclear': 'on',
                     'excel_external_clearing_price': 'on',
                     }
        s, results = create_scenario_from_form(post_data)
        p = s.auctionyear_dict[2021].pot_dict['E']
        self.assertFalse('attempted_clearing_price' in p.non_cum_run_auction().columns)


        post_data = dfh.test_post_data_just_prev_nuc
        s, results = create_scenario_from_form(post_data)
        p = s.auctionyear_dict[2021].pot_dict['E']
        self.assertTrue('attempted_clearing_price' in p.non_cum_run_auction().columns)

    # python manage.py test lcf.tests3.Clearing.test_clearing_price_non_cum
    def test_clearing_price_non_cum(self):
        post_data = dfh.test_post_data_just_prev_nuc
        s, results = create_scenario_from_form(post_data)
        # for i in range(2021,2031):
        for i in range(2021,2023):
            a = s.auctionyear_dict[i]
            for j in ['E', 'M', 'SN', 'FIT']:
            # for j in ['E']:
                p = a.pot_dict[j]
                projects = p.run_relevant_auction()
                # print(projects)
                if len(projects.index) > 0:
                    self.assertEqual(projects.levelised_cost[projects.funded_this_year == True].max(),projects.clearing_price.max())
                    if j != 'FIT':
                        self.assertTrue((projects.difference != projects.strike_price-a.wholesale_price).any())
                    npt.assert_almost_equal(p.awarded_cost(), projects.attempted_cum_cost[projects.funded_this_year == True].max())
                    if j not in ['SN','FIT']:
                        self.assertTrue(p.awarded_cost() < p.budget())


    # python manage.py test lcf.tests3.Clearing.test_clearing_price_cum
    def test_clearing_price_cum(self):
        post_data = dfh.test_post_data_just_prev_all
        s, results = create_scenario_from_form(post_data)
        for i in range(2021,2031):
        # for i in range(2021,2022):
            a = s.auctionyear_dict[i]
            for j in ['E', 'M', 'SN', 'FIT']:
            # for j in ['E']:
                p = a.pot_dict[j]
                projects = p.cum_run_auction()
                # print(projects)
                if len(projects.index) > 0:
                    if pd.notnull(projects.clearing_price.max()):
                        self.assertEqual(projects.levelised_cost[projects.funded_this_year == True].max(),projects.clearing_price.max())
                        if j != 'FIT':
                            self.assertTrue((projects.difference != projects.strike_price-a.wholesale_price).any())
                        npt.assert_almost_equal(p.awarded_cost(), projects.attempted_cum_cost[projects.funded_this_year == True].max())
                        if j not in ['SN','FIT']:
                            self.assertTrue(p.awarded_cost() < p.budget())

    # python manage.py test lcf.tests3.Clearing.test_accounting_cost
    def test_accounting_cost(self):
        post_data = dfh.test_post_data_just_prev_nuc
        s, results = create_scenario_from_form(post_data)
        a = s.auctionyear_dict[2021]
        p = a.pot_dict['M']
        t = p.technology_dict['PVLS']
        print(t.clearing_price)
        # print(p.run_relevant_auction())
#

        self.assertTrue(results.notnull().values.all())



    # python manage.py test lcf.tests3.Clearing.test_intermediate_with_clearing_price_exogenous
    def test_intermediate_with_clearing_price_exogenous(self):
        post_data = dfh.test_post_data_just_prev_nuc
        post_data['excel_external_clearing_price'] = 'on'
        s, results = create_scenario_from_form(post_data)
        intermediate_results = s.get_intermediate_results()
        available_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'available'), 'Equivalent cost (£m)']
        available_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'available'), 'Equivalent generation (GWh)']

        eligible_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'eligible'), 'Equivalent cost (£m)']
        eligible_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'eligible'), 'Equivalent generation (GWh)']

        successful_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Equivalent cost (£m)']
        successful_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Equivalent generation (GWh)']

        difference = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Clearing price (£/MWh)'] - s.auctionyear_dict[2020].wholesale_price

        npt.assert_almost_equal(available_cost, available_gen * difference)
        npt.assert_almost_equal(eligible_cost, eligible_gen * difference)
        npt.assert_almost_equal(successful_cost, successful_gen * difference)

        intermediate_results = s.get_intermediate_results()
        available_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'available'), 'Equivalent cost (£m)']
        available_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'available'), 'Equivalent generation (GWh)']

        eligible_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'eligible'), 'Equivalent cost (£m)']
        eligible_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'eligible'), 'Equivalent generation (GWh)']

        successful_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Equivalent cost (£m)']
        successful_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Equivalent generation (GWh)']

        difference = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Clearing price (£/MWh)'] - s.auctionyear_dict[2020].wholesale_price
        # print(intermediate_results)
        npt.assert_almost_equal(available_cost, available_gen * difference)
        npt.assert_almost_equal(eligible_cost, eligible_gen * difference)
        npt.assert_almost_equal(successful_cost, successful_gen * difference)

        pk = Scenario.objects.all().order_by("-date")[0].pk
        scenario = Scenario.objects.prefetch_related('auctionyear_set__pot_set__technology_set', 'policies').get(pk=pk) #new

        scenario.get_results()
        scenario.get_intermediate_results()
        # just checking it doesn't raise an error




    # python manage.py test lcf.tests3.Clearing.test_intermediate_with_clearing_price_not_exogenous
    def test_intermediate_with_clearing_price_not_exogenous(self):
        post_data = dfh.test_post_data_just_prev_nuc
        s, results = create_scenario_from_form(post_data)
        intermediate_results = s.get_intermediate_results()
        intermediate_budget_results = s.get_intermediate_budget_results()
        available_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'available'), 'Equivalent cost (£m)']
        available_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'available'), 'Equivalent generation (GWh)']

        eligible_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'eligible'), 'Equivalent cost (£m)']
        eligible_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'eligible'), 'Equivalent generation (GWh)']

        successful_cost = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Equivalent cost (£m)']
        successful_gen = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Equivalent generation (GWh)']

        difference = intermediate_results.loc[(2020,'E', 235.37, 'OFW', 'successful'), 'Clearing price (£/MWh)'] - s.auctionyear_dict[2020].wholesale_price

        npt.assert_almost_equal(available_cost, available_gen * difference)
        npt.assert_almost_equal(eligible_cost, eligible_gen * difference)
        npt.assert_almost_equal(successful_cost, successful_gen * difference)

        resp = self.client.get(reverse('scenario_detail', kwargs={'pk':s.pk}))
        self.assertEqual(resp.status_code,200)

class IntermediateBudget(TestCase):

# python manage.py test lcf.tests3.IntermediateBudget.test_intermediate_budget_results

    def test_intermediate_budget_results(self):
        post_data = dfh.test_post_data_quirks
        s, results = create_scenario_from_form(post_data)
        s.get_intermediate_budget_results()
        npt.assert_almost_equal(s.get_intermediate_budget_results().loc[2030,'total unspent'],628.775821, decimal=4)

class GraphsTest(TestCase):

# python manage.py test lcf.tests3.GraphsTest.test_graph_starts_at_2021
    def test_graph_starts_at_2021(self):
        post_data = dfh.test_post_data_quirks
        s, results = create_scenario_from_form(post_data)
        chart_data = s.df_to_chart_data('cum_owed_v_wp')['chart_data']
        self.assertEqual(chart_data[1][0],'2021')

# python manage.py test lcf.tests3.GraphsTest.test_graph_cost_in_bn

    def test_graph_cost_in_bn(self):
        post_data = dfh.test_post_data_quirks
        s, results = create_scenario_from_form(post_data)
        chart_data = s.df_to_chart_data('cum_owed_v_wp')['chart_data']
        chart_data = DataFrame([ row[1:] for row in chart_data[1:] ])
        self.assertTrue((chart_data < 2).all().all())
