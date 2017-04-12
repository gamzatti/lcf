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


abbrev = DataFrame([["Pot",
                 "Technology",
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
                 ],
                ["","","","","","£/MWh", "£/MWh", "£/MWh", "%", "GW/year", "projects/year", "GWh", "£/MWh", "£/MWh", "GW", "TWh", "£bn","£bn", "£bn", "£bn", "TWh", "%", "%", "%", "%", "%", "%", "%", "%", "%"],
                ["Pot",
                "Technology",
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
                  "% of original project size (GWh)"
                 ]
                ],
                columns = ["pot_name",
                           "name",
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
                            "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change"

                            ],
                index=["title","unit", "title+unit"])


tech_results_keys = ["year",
                        "pot_name",
                        "name",
                        "awarded_gen",
                        "awarded_cap",
                        "awarded_cost",
                        "cum_awarded_gen",
                        "cum_owed_v_gas",
                        "cum_owed_v_wp",
                        "cum_owed_v_absolute"]
tech_inputs_keys = [
                       "pot_name",
                       "name",
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

tech_inputs_index = {"titles": ["Pot", "Technology","Year"], "keys": ["pot_name", "name", "year"]}
tech_results_index = {"titles": ["Year", "Pot", "Technology"], "keys": ["year", "pot_name", "name"]}

tech_policy_index = {'titles': ['Technology', 'Year'], 'keys': ["tech_name","year"]}
tech_policy_keys = ["tech_name", "year", "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change"]
tech_policy_columns = [abbrev[column]['title'] for column in tech_policy_keys ]
prices_policy_keys = ["tech_name", "year", "price_change"]
prices_policy_index = ["tech_name","year"]
prices_policy_col_keys = ["gas_prices_change","wholesale_prices_change"]
prices_policy_columns = [abbrev[column]["title"] for column in prices_policy_col_keys]

policy_keys = ["tech_name", "year", "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change", "price_change"]
