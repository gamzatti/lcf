s = Scenario.objects.create(name="test1",
                            budget = 3.3,
                            percent_emerging = 0.6,
                            end_year = 2022)

a0 = AuctionYear.objects.create(scenario=s,
                                year=2020,
                                wholesale_price = 48.5400340402009,
                                gas_price = 85)
a1 = AuctionYear.objects.create(scenario=s,
                                year=2021,
                                wholesale_price = 54.285722954952,
                                gas_price = 87)
a2 = AuctionYear.objects.create(scenario=s,
                                year=2022,
                                wholesale_price = 58.4749297906221,
                                gas_price = 89)

p0E = Pot.objects.create(name="E", auctionyear=a0)
p1E = Pot.objects.create(name="E", auctionyear=a1)
p2E = Pot.objects.create(name="E", auctionyear=a2)

p0M = Pot.objects.create(name="M", auctionyear=a0)
p1M = Pot.objects.create(name="M", auctionyear=a1)
p2M = Pot.objects.create(name="M", auctionyear=a2)

t0Ewave = Technology.objects.create(name="WA",
                                pot=p0E,
                                min_levelised_cost = 260.75,
                                max_levelised_cost = 298,
                                strike_price = 305,
                                load_factor = .31,
                                project_gen = 27,
                                max_deployment_cap = 0.034)


t0E = Technology.objects.create(name="OFW",
                                pot=p0E,
                                min_levelised_cost = 71.3353908668731,
                                max_levelised_cost = 103.034791021672,
                                strike_price = 114.074615384615,
                                load_factor = .42,
                                project_gen = 832,
                                max_deployment_cap = 1.9)

t1E = Technology.objects.create(name="OFW",
                                pot=p1E,
                                min_levelised_cost = 71.1099729102167,
                                max_levelised_cost = 101.917093653251,
                                strike_price = 112.136153846154,
                                load_factor = .434,
                                project_gen = 832,
                                max_deployment_cap = 1.9)

t1Ewave = Technology.objects.create(name="WA",
                                pot=p1E,
                                min_levelised_cost = 245.875,
                                max_levelised_cost = 281,
                                strike_price = 305,
                                load_factor = .31,
                                project_gen = 27,
                                max_deployment_cap = 0.0032)

t2E = Technology.objects.create(name="OFW",
                                pot=p2E,
                                min_levelised_cost = 70.8845549535604,
                                max_levelised_cost = 100.79939628483,
                                strike_price = 110.197692307692,
                                load_factor = .448,
                                project_gen = 832,
                                max_deployment_cap = 1.9)

t0M = Technology.objects.create(name="ONW",
                                pot=p0M,
                                min_levelised_cost = 61,
                                max_levelised_cost = 80,
                                strike_price = 80,
                                load_factor = 0.278125,
                                project_gen = 30,
                                max_deployment_cap = 0.73)
t1M = Technology.objects.create(name="ONW",
                                pot=p1M,
                                min_levelised_cost = 61.4,
                                max_levelised_cost = 81,
                                strike_price = 80,
                                load_factor = 0.2803125,
                                project_gen = 30,
                                max_deployment_cap = 0.73)
t2M = Technology.objects.create(name="ONW",
                                pot=p2M,
                                min_levelised_cost = 61.8,
                                max_levelised_cost = 82,
                                strike_price = 80,
                                load_factor = 0.2825,
                                project_gen = 30,
                                max_deployment_cap = 0.73)
