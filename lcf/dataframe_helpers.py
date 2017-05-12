import pandas as pd
import numpy as np
from pandas import DataFrame, Series

pot_choices = {"SN": "Separate negotiations",
        "FIT": "Feed-in-tariff",
        "E": "Emerging",
        "M": "Mature"}

technology_choices = {"OFW": "Offshore wind",
        "ONW": "Onshore wind",
        "NU": "Nuclear",
        "TL": "Tidal lagoon",
        "TS": "Tidal stream",
        "WA": "Wave",
        "PVLS": "Solar PV",
        "NW": "Negawatts"}

new_wp = [38.5, 41.8, 44.2, 49.8, 54.6, 56.2, 53.5, 57.0, 54.5, 52.2, 55.8]
excel_wp = [48.5400340402009, 54.285722954952, 58.4749297906221, 60.1487865144807, 64.9687482891174, 67.2664653151834, 68.6947628422952, 69.2053146319398, 66.3856598431318, 65.5255963446292, 65.5781764014488]
excel_gas = [85.0, 87.0, 89.0, 91.0, 93.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0]


abbrev = DataFrame([["Pot",
                #  "Technology",
                 "Technology",
                 "Year",
                 "Included?",
                 "Min LCOE",
                 "Max LCOE",
                 "Strike price",
                 "Load factor",
                 "Max new capacity",
                 "Number of new projects",
                 "Project size",
                 "LCOE CCGT plus carbon price",
                 "Wholesale electricity price",
                 "Capacity awarded each year",
                 "Generation awarded each year",
                 "Cost of generation awarded each year",
                 "Accounting cost",
                 "Cost v gas",
                 "Absolute cost",
                 "Cumulative new generation",
                 "% of original LCOE CCGT plus carbon price",
                 "% of original wholesale electricity price",
                  "% of original min LCOE",
                  "% of original max LCOE",
                  "% of original strike price",
                  "% of original load factor",
                  "% of original max new capacity",
                  "% of original number of new projects",
                  "% of original project size",
                  "change in min LCOE",
                  "change in max LCOE",
                  "change in strike price",
                  "change in load factor",
                  "change in max new capacity",
                  "change in number of new projects",
                  "change in project size",
                  "Wholesale electricity price - note",
                  "LCOE CCGT plus carbon price - note",
                   "Min LCOE - note",
                   "Max LCOE - note",
                   "Strike price - note",
                   "Load factor - note",
                   "Max new capacity - note",
                   "Number of new projects - note",
                   "Project size - note",
                 ],
                ["",
                # "",
                "","","","£/MWh", "£/MWh", "£/MWh", "%", "GW/year", "projects/year", "GWh", "£/MWh", "£/MWh", "GW", "TWh", "£bn","£bn", "£bn", "£bn", "TWh", "%", "%", "%", "%", "%", "%", "%", "%", "%",
                    "£/MWh",
                    "£/MWh",
                    "£/MWh",
                    "%",
                    "GW/year",
                    "projects/year",
                    "GWh",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",

                ],
                ["Pot",
                # "Technology",
                 "Technology",
                 "Year",
                 "Included?",
                 "Min LCOE (£/MWh)",
                 "Max LCOE (£/MWh)",
                 "Strike price (£/MWh)",
                 "Load factor (%)",
                 "Max new capacity (GW/year)",
                 "Number of new projects (projects/year)",
                 "Project size (GWh)",
                 "LCOE CCGT plus carbon price (£/MWh)",
                 "Wholesale electricity price (£/MWh)",
                 "Capacity awarded each year (GW)",
                 "Generation awarded each year (TWh)",
                 "Cost of generation awarded each year (£bn)",
                 "Accounting cost (£bn)",
                 "Cost v gas (£bn)",
                 "Absolute cost (£bn)",
                 "Cumulative new generation (TWh)",
                  "% of original LCOE CCGT plus carbon price (£/MWh)",
                  "% of original wholesale electricity price (£/MWh)",
                  "% of original min LCOE (£/MWh)",
                  "% of original max LCOE (£/MWh)",
                  "% of original strike price (£/MWh)",
                  "% of original load factor (%)",
                  "% of original max new capacity (GW/year)",
                  "% of original number of new projects (projects/year)",
                  "% of original project size (GWh)",
                  "change in min LCOE (£/MWh)",
                  "change in max LCOE (£/MWh)",
                  "change in strike price (£/MWh)",
                  "change in load factor (%)",
                  "change in max new capacity (GW/year)",
                  "change in number of new projects (projects/year)",
                  "change in project size (GWh)",
                  "Wholesale electricity price (£/MWh) - note",
                  "LCOE CCGT plus carbon price (£/MWh) - note",
                 "Min LCOE (£/MWh) - note",
                 "Max LCOE (£/MWh) - note",
                 "Strike price (£/MWh) - note",
                 "Load factor (%) - note",
                 "Max new capacity (GW/year) - note",
                 "Number of new projects (projects/year) - note",
                 "Project size (GWh) - note",

                 ]
                ],
                columns = ["pot_name",
                        #    "name",
                           "tech_name",
                           "year",
                           "included",
                           "min_levelised_cost",
                           "max_levelised_cost",
                           "strike_price",
                           "load_factor",
                           "max_deployment_cap",
                           "num_new_projects",
                           "project_gen",
                           "gas_prices",
                           "wholesale_prices",
                           "awarded_cap",
                           "awarded_gen",
                           "awarded_cost",
                           "cum_owed_v_wp",
                           "cum_owed_v_gas",
                           "cum_owed_v_absolute",
                            "cum_awarded_gen",
                            "gas_prices_change",
                            "wholesale_prices_change",
                            "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change",
                            "min_levelised_cost_change_su", "max_levelised_cost_change_su", "strike_price_change_su", "load_factor_change_su", "max_deployment_cap_change_su", "num_new_projects_change_su", "project_gen_change_su",
                            "wholesale_prices_note",
                            "gas_prices_note",
                            'min_levelised_cost_note', 'max_levelised_cost_note', 'strike_price_note', 'load_factor_note', 'max_deployment_cap_note', 'num_new_projects_note', 'project_gen_note',
                            ],
                index=["title","unit", "title+unit"])


tech_results_keys = ["year",
                        "pot_name",
                        "tech_name",#"name",
                        "awarded_gen",
                        "awarded_cap",
                        "awarded_cost",
                        "cum_awarded_gen",
                        "cum_owed_v_gas",
                        "cum_owed_v_wp",
                        "cum_owed_v_absolute"]
tech_inputs_keys = [
                       "pot_name",
                       "tech_name",#"name",
                       "year",
                       "included",
                       "min_levelised_cost",
                       "max_levelised_cost",
                       "strike_price",
                       "load_factor",
                       "max_deployment_cap",
                       "num_new_projects",
                       "project_gen"]
prices_keys = ["wholesale_prices", "gas_prices"]

tech_results_columns = [abbrev[column]["title"] for column in tech_results_keys]
tech_inputs_columns = [abbrev[column]["title"] for column in tech_inputs_keys]
prices_columns = [abbrev[column]["title"] for column in prices_keys]

tech_inputs_index = {"titles": ["Pot", "Technology","Year"], "keys": ["pot_name",
"tech_name",#"name",
 "year"]}
tech_results_index = {"titles": ["Year", "Pot", "Technology"], "keys": ["year", "pot_name",
"tech_name"#"name"
]}
to_interpolate =      ["min_levelised_cost",
                       "max_levelised_cost",
                       "strike_price",
                       "load_factor",
                       "max_deployment_cap",
                       "project_gen"]

tech_policy_index = {'titles': ['Technology', 'Year'], 'keys': ["tech_name","year"]}
tech_policy_keys_mu = ["tech_name", "year", "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change"]
tech_policy_keys_su = ["tech_name", "year", "min_levelised_cost_change_su", "max_levelised_cost_change_su", "strike_price_change_su", "load_factor_change_su", "max_deployment_cap_change_su", "num_new_projects_change_su", "project_gen_change_su"]

tech_policy_columns = {'MU': [abbrev[column]['title'] for column in tech_policy_keys_mu ], 'SU': [abbrev[column]['title+unit'] for column in tech_policy_keys_su ] }

test_post_data = {'name': 'test 1234',
             'percent_emerging': 0.6,
             'budget': 3.3,
             'excel_quirks': 'on',
             'end_year1': 2025,
             'wholesale_prices': "excel",
             'gas_prices': "excel",
             }
note_pair_columns = [  "min_levelised_cost",
  "max_levelised_cost",
  "strike_price",
  "load_factor",
  "max_deployment_cap",
  "num_new_projects",
  "project_gen"]
note_columns = ['min_levelised_cost_note', 'max_levelised_cost_note', 'strike_price_note', 'load_factor_note', 'max_deployment_cap_note', 'num_new_projects_note', 'project_gen_note']
note_and_tech_keys = [
                       "pot_name",
                       "tech_name",#"name",
                       "year",
                       "included",
                       "min_levelised_cost",
                       'min_levelised_cost_note',
                       "max_levelised_cost",
                       'max_levelised_cost_note',
                       "strike_price",
                       'strike_price_note',
                       "load_factor",
                       'load_factor_note',
                       "max_deployment_cap",
                       'max_deployment_cap_note',
                       "num_new_projects",
                       'num_new_projects_note',
                       "project_gen",
                       'project_gen_note']

note_cols = ['source', 'notes', 'link', 'local_link']
note_cols_inc_index = ['num', 'source', 'notes', 'link', 'local_link']
note_titles = ['Source', 'Notes', 'Link', 'Link on drive']
note_titles_inc_index = ['Ref num', 'Source', 'Notes', 'Link', 'Link on drive']

note_and_prices_keys = ['year',
                        'wholesale_prices',
                        'wholesale_prices_note',
                        'gas_prices',
                        'gas_prices_note']

prices_notes = ['wholesale_prices_note',
                'gas_prices_note'
                ]

prices_and_notes_columns = [abbrev[column]["title"] for column in note_and_prices_keys]

note_and_tech_columns = [abbrev[column]["title"] for column in note_and_tech_keys]
