import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import reduce
import lcf.dataframe_helpers as dfh


for s in Scenario.objects.all():
    s.clear()

from lcf.models import Scenario, AuctionYear, Pot, Technology, Policy
s1 = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=688)
s2 = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=700)
s3 = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=703)
s4 = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=704)


s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=707)


def load_factor(cap_gw,gen_twh):
    return gen_twh / (cap_gw * 8.760)


def cap(gen_twh,load_factor):
    return gen_twh / (load_factor * 8.760)


def gen(cap_gw,load_factor):
    return cap_gw * load_factor * 8.760







        """for i in combined_tech_projects.index:
            if i in previous_year_projects.index:
                combined_tech_projects.funded[i] = "previously funded"
            else:
                funded_gen = sum(combined_tech_projects.gen[combined_tech_projects.funded=="this year"])
                attempted_gen = funded_gen + combined_tech_projects.gen[i]
                attempted_clearing_price = combined_tech_projects.levelised_cost[i] if self.auctionyear.scenario.set_strike_price == True else combined_tech_projects.strike_price[i]
                attempted_cost = attempted_gen/1000 * (attempted_clearing_price - self.auctionyear.wholesale_price)
                if attempted_cost < self.budget() - all_tech_cost:
                    combined_tech_projects.funded[i] = "this year"
                    tech_gen[combined_tech_projects.technology[i]] = attempted_gen
                    combined_tech_projects.clearing_price = attempted_clearing_price
                    tech_cost[combined_tech_projects.technology[i]] = attempted_cost
                else:
                    break
            all_tech_cost += tech_cost[combined_tech_projects.technology[i]]
            all_tech_gen += tech_gen[combined_tech_projects.technology[i]]"""


def scenario_new2(request,pk):
    TechnologyFormSet = modelformset_factory(Technology, extra=0, fields="__all__")
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    #queryset = Technology.objects.filter(pot__auctionyear__scenario__name="default")
    queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
    if request.method == "POST":

        formset = TechnologyFormSet(request.POST, queryset=queryset)
        scenario_form = ScenarioForm(request.POST)
        if formset.is_valid() and scenario_form.is_valid():
            scenario_new = scenario_form.save()
            for y in range(2020,2031):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new)
                for p in ['E','M','SN','NW']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)
            for form in formset:
                pot = q.filter(auctionyear__year=form.cleaned_data['pot'].auctionyear.year).get(name=form.cleaned_data['pot'].name)
                Technology.objects.create(pot = pot,
                                        name = form.cleaned_data['name'],
                                        min_levelised_cost = form.cleaned_data['min_levelised_cost'],
                                        max_levelised_cost = form.cleaned_data['max_levelised_cost'],
                                        strike_price = form.cleaned_data['strike_price'],
                                        load_factor = form.cleaned_data['load_factor'],
                                        project_gen = form.cleaned_data['project_gen'],
                                        max_deployment_cap = form.cleaned_data['max_deployment_cap'])

            return redirect('scenario_detail', pk=scenario_new.pk)
    else:
        scenario_form = ScenarioForm()
        #formset = TechnologyFormSet(queryset=queryset)
        formset = "foo"

    return render(request, 'lcf/scenario_new2.html', {'scenario_original': scenario_original, 'formset': formset, 'scenarios': scenarios, 'scenario_form': scenario_form })



##version that ought to work!!
def scenario_new(request,pk):
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
    first_auctionyear = scenario_original.auctionyear_set.all()[0]
    techs = Technology.objects.filter(pot__auctionyear=first_auctionyear)
    num_techs = techs.count()
    TechnologyStringFormSet = formset_factory(TechnologyStringForm, extra=0, max_num=num_techs)
    if request.method == "POST":
        scenario_form = ScenarioForm(request.POST)
        prices_form = PricesForm(request.POST)
        string_formset = TechnologyStringFormSet(request.POST)
        if string_formset.is_valid() and scenario_form.is_valid() and prices_form.is_valid():
            scenario_new = scenario_form.save()
            gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['gas_prices'])))]
            wholesale_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['wholesale_prices'])))]

            for i, y in enumerate(range(2020,2023)):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])
                for p in ['E','M','SN','NW']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)
            """for form in formset:
                pot = q.filter(auctionyear__year=form.cleaned_data['pot'].auctionyear.year).get(name=form.cleaned_data['pot'].name)
                Technology.objects.create(pot = pot,
                                        name = form.cleaned_data['name'],
                                        min_levelised_cost = form.cleaned_data['min_levelised_cost'],
                                        max_levelised_cost = form.cleaned_data['max_levelised_cost'],
                                        strike_price = form.cleaned_data['strike_price'],
                                        load_factor = form.cleaned_data['load_factor'],
                                        project_gen = form.cleaned_data['project_gen'],
                                        max_deployment_cap = form.cleaned_data['max_deployment_cap'])"""


            return redirect('scenario_detail', pk=scenario_new.pk)
    scenario_form = ScenarioForm(instance=scenario_original)
    initial_prices = {'gas_prices': str([a.gas_price for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([a.wholesale_price for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
    prices_form = PricesForm(initial=initial_prices)

    t_names = [t.name for t in techs]
    t_max_levelised_costs = ["5 6 7 8", "6 7 8 9", "10 11 12 13"]
    t_min_levelised_costs = []

    for t in t_names:
        objects = Technology.objects.filter(name=t, pot__auctionyear__scenario=scenario_original)
        min_levelised_costs = str([objects.get(pot__auctionyear=a).min_levelised_cost for a in scenario_original.auctionyear_set.all()]).strip('[]')
        t_min_levelised_costs.append(min_levelised_costs)

    ofw_objects = Technology.objects.filter(name="OFW", pot__auctionyear__scenario=scenario_original)
    ofw_min_levelised_costs = str([ofw_objects.get(pot__auctionyear=a).min_levelised_cost for a in scenario_original.auctionyear_set.all()]).strip('[]')


    t_min_levelised_costs = ["1 2 3 4", ofw_min_levelised_costs, "3 4 5 6", "4 5 6 7"]


    #initial_min_levelised_costs = [ str([t.min_levelised_cost for t in a for a in scenario_original.auctionyear_set.all()]).strip('[]') ]
    initial_technologies = []
    for i in range(len(techs)):
        line = {'name': t_names[i], 'min_levelised_costs': t_min_levelised_costs[i], 'max_levelised_costs': t_max_levelised_costs[i]}
        initial_technologies.append(line)
    string_formset = TechnologyStringFormSet(initial=initial_technologies)
    return render(request, 'lcf/scenario_new.html', {'scenario': scenario_original, 'scenarios': scenarios, 'scenario_form': scenario_form, 'prices_form': prices_form, 'string_formset': string_formset})




test:
    def test_valid_stringformset(self):
        data = {
                'form-0-pot': "E",
                'form-0-min_levelised_cost': "50 51 52",
                'form-0-max_levelised_cost': "60 61 62",
                'form-0-strike_price': "43 45 34",
                'form-0-load_factor': "33 34 34",
                'form-0-project_gen': "44 34 34",
                'form-0-name': "OFW",
                'form-0-max_deployment_cap': "3 23 23"
                }
        TechnologyStringFormSet = formset_factory(TechnologyStringForm, extra=0, max_num=1)
        string_formset = TechnologyStringFormSet(data, initial=data)
        print(string_formset.errors)
        #self.assertTrue(string_formset.is_valid())




Scenario debugging methods:
    def projects_df(self):
        projects = pd.concat([t.projects() for a in self.auctionyear_set.all() for p in a.active_pots().all() for t in p.tech_set().all() ])
        return projects

    def techs_df(self):
        techs = pd.concat([t.fields_df() for a in self.auctionyear_set.all() for p in a.active_pots().all() for t in p.technology_set.all() ])
        techs = techs.set_index('id')
        return techs

Auctionyear old method:
    @lru_cache(maxsize=None)
    def owed_v2(self, comparison, previous_year):
        if comparison == "gas":
            compare = self.gas_price
        elif comparison == "wp":
            compare = self.wholesale_price
        elif comparison == "absolute":
            compare = 0
        owed = {}
        for pot in previous_year.active_pots().all():
            owed[pot.name] = 0
            if pot.auction_has_run == False:
                pot.run_auction()
            for t in pot.tech_set().all():
                gen = t.awarded_gen
                strike_price = t.strike_price
                if self.scenario.excel_wp_error == True:
                    #next 5 lines account for Angela's error
                    if (pot.name == "E") or (pot.name == "SN"):
                        try:
                            strike_price = self.active_pots().get(name=pot.name).tech_set().get(name=t.name).strike_price
                        except:
                            break
                difference = strike_price - compare
                if pot.name == "FIT":
                    difference = strike_price
                tech_owed = gen * difference
                owed[pot.name] += tech_owed
        owed = sum(owed.values())
        return owed

    def nw_owed_old(self,previous_year):
        if self.active_pots().filter(name="FIT").exists():
            pot = self.active_pots().get(name="FIT")
            previous_pot = previous_year.active_pots().get(name="FIT")
            return pot.nw_owed(previous_pot)
        else:
            return 0


    def cum_owed_v2(self, comparison):
        if self.year == 2020:
            return self.owed_v(comparison,self)
        else:
            return sum([self.owed_v(comparison,year) for year in self.cum_years()])

    def nw_cum_owed_old(self):
        if self.year == 2020:
            return self.nw_owed(self)
        else:
            return sum([self.nw_owed(year) for year in self.cum_years()])

    def cum_awarded_gen_old(self):
        extra2020 = 0
        if self.scenario.excel_2020_gen_error:
            pots2020 = self.scenario.auctionyear_set.get(year=2020).active_pots().exclude(name="FIT")
            extra2020 = sum([pot.awarded_gen() for pot in pots2020])
        print('cum awarded gen: auctionyear method',sum([year.awarded_gen() for year in self.cum_years()]) + extra2020)
        return sum([year.awarded_gen() for year in self.cum_years()]) + extra2020


    #template methods:
    def cum_owed_v_wp(self):
        return self.cum_owed_v("wp")

    def cum_owed_v_gas(self):
        return self.cum_owed_v("gas")


#Pot methods:
    def funded_projects(self):
        return self.projects()[self.projects().funded == "this year"]


        for tl in t_set:
            if tl.max_deployment_cap == 1:
                print('changing tidal')
                tl.max_deployment_cap = 1.0045662100457
                tl.save()


# trying to make a groupby version:
    def all_in_one(self):
        index = [item for sublist in [t.projects_index() for t in t.pot.tech_set()] for item in sublist]
        projects = DataFrame(index = index)
        projects['pot'] = self.name
        projects['listed_year'] = self.auctionyear.year
        projects.groupby()
        for t in self.tech_set().all():
            projects['levelised_cost'] = t.levelised_cost_distribution()
            projects['gen'] = t.project_gen
            projects['technology'] = t.name
            projects['strike_price'] = t.strike_price
            projects['affordable'] = projects.levelised_cost <= projects.strike_price
        print('{} {} time taken to concat: {}'.format(self.name,self.auctionyear.year,(t3-t2)*1000))
        return projects

#slow pot methods:

    # slow
    # def nw_owed(self,previous_pot):
    #     print('calling nw_owed')
    #
    #     if previous_pot.auction_has_run == False:
    #         previous_pot.run_auction()
    #     previous_t = Technology.objects.get(name="NW", pot=previous_pot)
    #     gen = previous_t.awarded_gen
    #     difference = previous_t.strike_price
    #     owed = gen * difference
    #     return owed

    # slow too?
    # def cum_nw_owed(self):
    #     print('calling cum_nw_owed')
    #     return sum([self.nw_owed(pot) for pot in self.cum_pots()])


# experimental pot methods
    @lru_cache(maxsize=128)
    def will_pay_v(self, comparison, future_pot):
        if self.name == "FIT":
            comparison = "absolute"
        di = {"gas": future_pot.auctionyear.gas_price, "wp": future_pot.auctionyear.wholesale_price, "absolute": 0}
        compare = di[comparison]
        will_pay = 0
        will_pay_tech = {}
        if self.auction_has_run == False:
            self.run_auction()
        for t in Technology.objects.filter(pot=self):
            gen = t.awarded_gen
            strike_price = t.strike_price
            if self.auctionyear.scenario.excel_sp_error == True or self.auctionyear.scenario.excel_quirks == True:
                if (self.name == "E") or (self.name == "SN"):
                    try:
                        strike_price = Technology.objects.get(name=t.name,pot=future_pot).strike_price
                    except:
                        break
            difference = strike_price - compare
            will_pay_tech[t.name] = gen * difference
            will_pay += will_pay_tech[t.name]
        return {'total': will_pay, 'by_tech': will_pay_tech }

    @lru_cache(maxsize=128)
    def cum_will_pay_v(self, comparison):
        if self.name == "FIT":
            comparison = "absolute"
        will_pay = 0
        will_pay_by_year = { p.auctionyear.year : 0 for p in self.cum_future_pots()}
        if self.auction_has_run == False:
            self.run_auction()

        for future_pot in self.cum_future_pots():
            di = {"gas": future_pot.auctionyear.gas_price, "wp": future_pot.auctionyear.wholesale_price, "absolute": 0}
            compare = di[comparison]

            for t in Technology.objects.filter(pot=self):
                gen = t.awarded_gen
                strike_price = t.strike_price
                if self.auctionyear.scenario.excel_sp_error == True or self.auctionyear.scenario.excel_quirks == True:
                    if (self.name == "E") or (self.name == "SN"):
                        try:
                            strike_price = Technology.objects.get(name=t.name,pot=future_pot).strike_price
                        except:
                            break
                difference = strike_price - compare
                will_pay_by_year[future_pot.auctionyear.year] += gen * difference
                #will_pay += will_pay_by_year[future_pot.auctionyear.year]
        return will_pay_by_year


#to move:
# successful_projects = projects[(projects.funded_this_year == True)]
# grouped = successful_projects.groupby('technology')
# t = Technology.objects.all().order_by('max_levelised_cost')[0]
# print('before',t.awarded_gen)
# grouped.agg({'attempted_project_gen': lambda x: setattr(t,'awarded_gen',np.sum(x)/1000),
#                     'cost': np.sum})
# print('after',t.awarded_gen)
#

<a class="new" href="{% url 'scenario_new' pk=s.pk %}"><span title="new scenario" class="glyphicon glyphicon-plus"></span> Save as</a>

<!--<li><a class="new" href="{% url 'scenario_new' pk=scenario.pk %}"><span title="new scenario" class="glyphicon glyphicon-plus"></span> New scenario based on current</a></li>-->

# def scenario_new(request,pk):
#     scenarios = Scenario.objects.all()
#     scenario_original = get_object_or_404(Scenario, pk=pk)
#     queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
#     techs = Technology.objects.filter(pot__auctionyear=scenario_original.auctionyear_set.all()[0])
#     num_techs = techs.count()
#     TechnologyStringFormSet = formset_factory(TechnologyStringForm, extra=0, max_num=10)
#     recent_pk = Scenario.objects.all().order_by("-date")[0].pk
#
#     if request.method == "POST":
#         scenario_form = ScenarioForm(request.POST)
#         prices_form = PricesForm(request.POST)
#         string_formset = TechnologyStringFormSet(request.POST)
#
#         if string_formset.is_valid() and scenario_form.is_valid() and prices_form.is_valid():
#             scenario_new = scenario_form.save()
#             wholesale_prices = [float(w) for w in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['wholesale_prices'])))]
#             gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['gas_prices'])))]
#             for i, y in enumerate(range(2020,scenario_new.end_year2+1)):
#                 a = AuctionYear.objects.create(year=y, scenario=scenario_new, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])
#                 for p in [p.name for p in scenario_original.auctionyear_set.all()[0].pot_set.all()]:
#                 #for p in ['E', 'M', 'SN', 'FIT']:
#                     Pot.objects.create(auctionyear=a,name=p)
#             q = Pot.objects.filter(auctionyear__scenario=scenario_new)
#
#             for form in string_formset:
#                 fields = [f.name for f in Technology._meta.get_fields() if f.name not in ["pot", "id", "name", "included", "awarded_gen", "awarded_cost"]]
#                 field_data = { field : [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data[field])))] for field in fields  }
#                 for i, a in enumerate(AuctionYear.objects.filter(scenario=scenario_new)):
#                     kwargs = { field : field_data[field][i] if field_data[field] != [] else None for field in field_data }
#                     kwargs['name'] = form.cleaned_data['name']
#                     kwargs['included'] = form.cleaned_data['included']
#                     kwargs['pot'] = q.filter(auctionyear=a).get(name=form.cleaned_data['pot'])
#                     Technology.objects.create_technology(**kwargs)
#             return redirect('scenario_detail', pk=scenario_new.pk)
#         else:
#             print(string_formset.errors)
#             print(scenario_form.errors)
#             print(prices_form.errors)
#     print('rendering scenario form')
#     scenario_form = ScenarioForm(instance=scenario_original)
#     print('finding initial prices')
#     initial_prices = {'gas_prices': str([a.gas_price for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([a.wholesale_price for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
#     print('rendering pries form')
#     prices_form = PricesForm(initial=initial_prices)
#     print('finding technology data')
#     names = scenario_original.technology_form_helper()[0]
#     print('rendering technology form')
#     technology_form_helper = scenario_original.technology_form_helper()[1]
#     string_formset = TechnologyStringFormSet(initial=technology_form_helper)
#     print('assembling context')
#     context = {'scenario': scenario_original,
#                'scenarios': scenarios,
#                'scenario_form': scenario_form,
#                'prices_form': prices_form,
#                'string_formset': string_formset,
#                'names': names,
#                'recent_pk': recent_pk}
#     return render(request, 'lcf/scenario_new.html', context)

#From Scenario
# #if I separate inputs by technology for display on detail page. needs to be grouped by technology rather than just be individual dfs for all years.
#     def tech_df_list(self):
#         dfs = [t.fields_df_html() for a in self.auctionyear_set.all() for p in a.active_pots().all() for t in p.technology_set.all() ]
#         return dfs

    # def clear_all(self):
    #     for a in AuctionYear.objects.filter(scenario = self):
    #         a.budget_result = None
    #         for p in Pot.objects.filter(auctionyear = a):
    #             p.auction_has_run = False
    #             p.budget_result = None
    #             p.awarded_cost_result = None
    #             p.awarded_gen_result = None
    #             p.auction_results = None
    #             p.cum_owed_v_wp = None
    #             p.cum_owed_v_gas = None
    #             p.cum_owed_v_absolute = None
    #             p.cum_awarded_gen_result = None
    #             p.previously_funded_projects_results = None
    #             for t in Technology.objects.filter(pot=p):
    #                 t.awarded_gen = None
    #                 t.awarded_cost = 0
    #                 t.cum_owed_v_wp = 0
    #                 t.cum_owed_v_gas = 0
    #                 t.cum_owed_v_absolute = 0
    #                 t.cum_awarded_gen = 0
    #                 t.save()
    #             p.save()
    #         a.save()


    # @lru_cache(maxsize=128)
    # def cumulative_costs(self, period_num):
    #     index = ['Accounting cost', 'Cost v gas', 'Innovation premium', 'Absolute cost']
    #     auctionyears = self.period(period_num)
    #     columns = [str(a.year) for a in auctionyears]
    #     accounting_costs = [round(a.cum_owed_v("wp")/1000,3) for a in auctionyears]
    #     cost_v_gas = [round(a.cum_owed_v("gas")/1000,3) for a in auctionyears]
    #     innovation_premium = [round(a.innovation_premium()/1000,3) for a in auctionyears]
    #     absolute_cost = [round(a.cum_owed_v("absolute")/1000,3) for a in auctionyears]
    #     df = DataFrame([accounting_costs, cost_v_gas, innovation_premium, absolute_cost], index=index, columns=columns)
    #     options = {'title': None, 'vAxis': {'title': '£bn'}}
    #     return {'df': df, 'options': options}
    #
    # @lru_cache(maxsize=128)
    # def cum_awarded_gen_by_pot(self,period_num):
    #     auctionyears = self.period(period_num)
    #     index = [pot.name for pot in auctionyears[0].active_pots()]
    #     data = { str(a.year) : [round(p.cum_awarded_gen(),2) for p in a.active_pots()] for a in auctionyears }
    #     df = DataFrame(data=data, index=index)
    #     options = {'vAxis': {'title': 'TWh'}, 'title': None}
    #     return {'df': df, 'options': options}
    #
    #
    # @lru_cache(maxsize=128)
    # def awarded_cost_by_tech(self,period_num):
    #     auctionyears = self.period(period_num)
    #     index = [t.name for pot in auctionyears[0].active_pots() for t in pot.tech_set().order_by("name")]
    #     data = { str(a.year) : [round(t.awarded_cost,2) for p in a.active_pots() for t in p.tech_set().order_by("name")] for a in auctionyears }
    #     df = DataFrame(data=data, index=index)
    #     options = {'vAxis': {'title': '£m'}, 'title': None}
    #     return {'df': df, 'options': options}
    #


    # otherwise, manually assemble the dataframe

Graph methods:
    # could happen at the very end, after the objects are in the db?
    # def tech_pivot_table_using_db(self,period_num,column):
    #     auctionyears = self.period(period_num).values()
    #     qs = Technology.objects.filter(pot__auctionyear__in = auctionyears)
    #     df = read_frame(qs, fieldnames=['pot__auctionyear__year','pot__name','name',column])
    #     df.columns = ['year','pot','name',Technology._meta.get_field(column).verbose_name]
    #     dfsum = df.groupby(['year','pot'],as_index=False).sum()
    #     dfsum['name']='_Subtotal'
    #     dfsum_outer = df.groupby(['year'],as_index=False).sum()
    #     dfsum_outer['name']='Total'
    #     dfsum_outer['pot']='Total'
    #     result = dfsum.append(df)
    #     result = dfsum_outer.append(result)
    #     result = result.set_index(['year','pot','name']).sort_index()
    #     result = result.unstack(0)
    #     if column == "cum_owed_v_wp" or column == "cum_owed_v_gas" or column == "cum_owed_v_absolute":
    #         result = result/1000
    #     return result

    # @lru_cache(maxsize=128)
    # def gen_by_tech(self,period_num):
    #     auctionyears = self.period(period_num)
    #     index = [t.name for pot in auctionyears[0].active_pots() for t in pot.tech_set().order_by("name")]
    #     data = { str(a.year) : [round(t.awarded_gen,2) for p in a.active_pots() for t in p.tech_set().order_by("name")] for a in auctionyears }
    #     df = DataFrame(data=data, index=index)
    #     options = {'vAxis': {'title': 'TWh'}, 'title': None}
    #     return {'df': df, 'options': options}
    #
    #
    # @lru_cache(maxsize=128)
    # def cap_by_tech(self,period_num):
    #     auctionyears = self.period(period_num)
    #     index = [t.name for pot in auctionyears[0].active_pots() for t in pot.tech_set().order_by("name")]
    #     data = { str(a.year) : [round(t.awarded_gen/8.760/t.load_factor,2) for p in a.active_pots() for t in p.tech_set().order_by("name")] for a in auctionyears }
    #     df = DataFrame(data=data, index=index)
    #     options = {'vAxis': {'title': 'GW'}, 'title': None}
    #     return {'df': df, 'options': options}

    #helper methods
    #
    # def df_to_chart_data(self,df):
    #     chart_data = df['df'].copy()
    #     chart_data['index_column'] = chart_data.index
    #     chart_data.loc['years_row'] = chart_data.columns
    #     chart_data = chart_data.reindex(index = ['years_row']+list(chart_data.index)[:-1], columns = ['index_column'] +list(chart_data.columns)[:-1])
    #     chart_data = chart_data.T.values.tolist()
    #     return {'data': chart_data, 'df': df['df'], 'options': df['options']}
    #
    # def get_or_make_chart_data(self, method, period_num):
    #     attr_name = ("").join(["_",method,str(period_num)])
    #     if self.__getattribute__(attr_name) == None:
    #         methods = globals()['Scenario']
    #         meth = getattr(methods,method)
    #         df = meth(self, period_num)
    #         chart_data = self.df_to_chart_data(df)
    #         self.__setattr__(attr_name, chart_data)
    #         return self.__getattribute__(attr_name)
    #     elif self.__getattribute__(attr_name) != None:
    #         return self.__getattribute__(attr_name)

    # @lru_cache(maxsize=128)
    # def technology_form_helper(self):
    #     techs = [t for p in self.auctionyear_set.all()[0].pot_set.all() for t in p.technology_set.all() ]
    #     t_form_data = { t.name : {} for t in techs}
    #     for t in techs:
    #         #creating subset is the slow bit. speed up by directly accessing database?
    #         subset = self.techs_df()[self.techs_df().name == t.name]
    #         for field, value in techs[0].get_field_values().items():
    #             if field == "id":
    #                 pass
    #             elif field == "name":
    #                 t_form_data[t.name][field] = t.name
    #             elif field == "included":
    #                 t_form_data[t.name][field] = t.included
    #             elif field == "pot":
    #                 t_form_data[t.name][field] = t.pot.name
    #             else:
    #                 if value == None:
    #                     t_form_data[t.name][field] = ""
    #                 else:
    #                     li = list(subset[field])
    #                     #li = ['{:.2f}'.format(x) for x in li]
    #                     t_form_data[t.name][field] = str(li).strip('[]').replace("'",'')
    #
    #     initial_technologies = list(t_form_data.values())
    #     t_names = [t.name for t in techs]
    #     return t_names, initial_technologies

    #calling fields.df() is querying the database
    # @lru_cache(maxsize=128)


from auctionyear:


    #@lru_cache(maxsize=128)
    # def cum_years(self):
    #     if self.year == 2020:
    #         return [self]
    #     else:
    #         start_year = self.scenario.start_year1 if self.year <= self.scenario.end_year1 else self.scenario.start_year2
    #         return self.scenario.auctionyear_set.filter(year__range=(start_year,self.year)).order_by('year')
    #
    #
    #
    #
    # #@lru_cache(maxsize=128)
    # def awarded_gen(self):
    #     return sum(pot.awarded_gen() for pot in self.active_pots().all())
    #
    #
    # @lru_cache(maxsize=128)
    # def owed_v(self, comparison, previous_year):
    #     return sum([pot.owed_v(comparison, previous_year.active_pots().get(name=pot.name)) for pot in self.active_pots() ])
    #
    # #@lru_cache(maxsize=128)
    # def nw_owed(self,previous_year):
    #     if self.active_pots().filter(name="FIT").exists():
    #         # pot = self.active_pots().get(name="FIT")
    #         # previous_fpot = previous_year.active_pots().get(name="FIT")
    #         # return pot.owed_v("absolute", previous_fpot)
    #         pot = Pot.objects.get(auctionyear=self,name="FIT")
    #         previous_pot = Pot.objects.get(auctionyear = previous_year, name="FIT")
    #         return pot.owed_v("absolute",previous_pot)
    #     else:
    #         return 0
    #
    #
    # #accumulating methods
    # #@lru_cache(maxsize=128)
    # def cum_awarded_gen(self):
    #     return sum([pot.cum_awarded_gen() for pot in self.active_pots()])
    #
    # @lru_cache(maxsize=128)
    # def cum_owed_v(self, comparison):
    #     if self.year == 2020:
    #         return self.owed_v(comparison, self)
    #     else:
    #         return sum([pot.cum_owed_v(comparison) for pot in self.active_pots()])
    #
    # #@lru_cache(maxsize=128)
    # def innovation_premium(self):
    #     return self.cum_owed_v("gas") - self.cum_nw_owed()
    #
    # def cum_nw_owed(self):
    #     if self.year == 2020:
    #         return self.nw_owed(self)
    #     else:
    #         return self.active_pots().get(name="FIT").cum_owed_v("absolute")

from Pot:


    #
    # def cum_pots(self):
    #     if self.auctionyear.year == 2020:
    #         return [self]
    #     else:
    #         start_year = self.auctionyear.scenario.start_year1 if self.auctionyear.year <= self.auctionyear.scenario.end_year1 else self.auctionyear.scenario.start_year2
    #         cum_pots = Pot.objects.filter(auctionyear__scenario=self.auctionyear.scenario, name=self.name, auctionyear__year__range=(start_year, self.auctionyear.year)).order_by("auctionyear__year")
    #         return cum_pots
    #
    # def cum_future_pots(self):
    #     if self.auctionyear.year == 2020:
    #         return [self]
    #     else:
    #         end_year = self.auctionyear.scenario.end_year1 if self.auctionyear.year <= self.auctionyear.scenario.end_year1 else self.auctionyear.scenario.end_year2
    #         cum_future_pots = Pot.objects.filter(auctionyear__scenario=self.auctionyear.scenario, name=self.name, auctionyear__year__range=(self.auctionyear.year, end_year)).order_by("auctionyear__year")
    #         return cum_future_pots


    #
    # #@lru_cache(maxsize=128)
    # def awarded_gen(self):
    #     if self.awarded_gen_result:
    #         res = self.awarded_gen_result
    #         return res
    #     else:
    #         if self.auction_has_run == False:
    #             self.run_auction()
    #         res = self.awarded_gen_result
    #         return res
    #
    #
    # @lru_cache(maxsize=128)
    # def owed_v(self, comparison, previous_pot):
    #     #print("calling for", self.name, self.auctionyear.year, previous_pot, comparison)
    #     di = {"gas": self.auctionyear.gas_price, "wp": self.auctionyear.wholesale_price, "absolute": 0}
    #     compare = di[comparison]
    #     if self.name == "FIT":
    #         compare = 0
    #     owed = 0
    #     if previous_pot.auction_has_run == False:
    #         previous_pot.run_auction()
    #     for t in previous_pot.tech_set().all():
    #         gen = t.awarded_gen
    #         strike_price = t.strike_price
    #         if self.auctionyear.scenario.excel_sp_error == True or self.auctionyear.scenario.excel_quirks == True:
    #             #next 5 lines account for Angela's error
    #             if (self.name == "E") or (self.name == "SN"):
    #                 try:
    #                     strike_price = Technology.objects.get(name=t.name,pot=self).strike_price
    #                     #strike_price = self.auctionyear.active_pots().get(name=self.name).tech_set().get(name=t.name).strike_price
    #                 except:
    #                     break
    #         difference = strike_price - compare
    #         tech_owed = gen * difference
    #
    #         owed += tech_owed
    #     return owed
    #
    # #accumulating methods
    # @lru_cache(maxsize=128)
    # def cum_owed_v(self,comparison):
    #     attr_name = "_".join(["cum_owed_v",comparison])
    #     if getattr(self,attr_name,None) == None:
    #         print('setting attr')
    #         #print("calculating",self.name)
    #         res = sum([self.owed_v(comparison, pot) for pot in self.cum_pots()])
    #         setattr(self,attr_name,res)
    #         self.save()
    #     else:
    #         print('retrieving from database')
    #         print(getattr(self,attr_name))
    #     return getattr(self,attr_name)
    #
    #
    #
    # def cum_awarded_gen(self):
    #     if self.cum_awarded_gen_result == None:
    #         extra2020 = 0
    #         excel = self.auctionyear.scenario.excel_2020_gen_error or self.auctionyear.scenario.excel_quirks == True
    #         if excel == True and self.name != "FIT" and self.period_num() == 1:
    #             pot2020 = self.auctionyear.scenario.auctionyear_set.get(year=2020).active_pots().get(name=self.name)
    #             #pot2020 = Pot.objects.get(auctionyear__scenario=self.auctionyear.scenario,auctionyear__year=2020,name=self.name) #which is faster?
    #             extra2020 = pot2020.awarded_gen()
    #         res = sum([pot.awarded_gen() for pot in self.cum_pots()]) + extra2020
    #         self.cum_awarded_gen_result = res
    #         self.save()
    #     return self.cum_awarded_gen_result
    #def will_pay_df(self):
    #    projects = self.run_auction()
    #
    # #summary methods

from Technology
# class TechnologyManager(models.Manager):
#     def create_technology(self, **kwargs):
#         t = self.create(**kwargs)
#         if t.num_new_projects != None:
#             t.fill_in_max_deployment_cap()
#         elif t.max_deployment_cap == None:
#             print("You must specify either num_new_projects or max_deployment_cap")
#         return t
#
From template:

<h2 class="sub-header">Summary</h2>
<!-- <div class="graph"> -->
    <!-- {{ cumulative_costs_chart1.as_html }} -->
    <!-- {{ cumulative_costs_df1 | safe }} -->
    {{ tech_cum_owed_v_wp_pivot | safe }}
    {{ tech_cum_owed_v_gas_pivot | safe }}
    {{ tech_cum_owed_v_absolute_pivot | safe }}
    <!-- {{ cumulative_costs_chart2.as_html }} -->
    <!-- {{ cumulative_costs_df2 | safe }} -->
    {{ tech_cum_owed_v_wp_pivot2 | safe }}
    {{ tech_cum_owed_v_gas_pivot2 | safe }}
    {{ tech_cum_owed_v_absolute_pivot2 | safe }}
<!-- </div> -->

<!-- <h2 class="sub-header">Breakdown by technology</h2>
<div> -->
<!--    {{ pot_cum_owed_v_wp_pivot | safe }}-->
<!-- </div> -->


<h2 class="sub-header">Cumulative new generation</h2>
<!-- <div class="graph">
    {{ cum_awarded_gen_by_pot_chart1.as_html }} -->
    <!-- {{ pot_cum_awarded_gen_pivot| safe }} -->
    {{ tech_cum_awarded_gen_pivot | safe }}

<!--    {{ cum_awarded_gen_by_pot_df1 | safe }}-->
    <!-- {{ cum_awarded_gen_by_pot_chart2.as_html }}
    {{ cum_awarded_gen_by_pot_df2 | safe }} -->
    {{ tech_cum_awarded_gen_pivot2 | safe }}

<!-- </div> -->

<!--<h2 class="sub-header">Cost each year of new generation awarded</h2>
<div class="graph">
    {{ awarded_cost_by_tech_chart1.as_html }}
    {{ awarded_cost_by_tech_df1 | safe }}
    {{ awarded_cost_by_tech_chart2.as_html }}
    {{ awarded_cost_by_tech_df2 | safe }}
</div>-->

<h2 class="sub-header">Generation by technology</h2>
<!-- <div class="graph">
    {{ gen_by_tech_chart1.as_html }} -->
    {{ tech_gen_pivot | safe }}
    {{ tech_gen_pivot2 | safe }}

<!--    {{ gen_by_tech_df1 | safe }} -->
    <!-- {{ gen_by_tech_chart2.as_html }}
    {{ gen_by_tech_df2 | safe }}
</div> -->

<!-- <h2 class="sub-header">Capacity by technology</h2>
<div class="graph">
    {{ cap_by_tech_chart1.as_html }}
    {{ cap_by_tech_df1 | safe }}
    {{ cap_by_tech_chart2.as_html }}
    {{ cap_by_tech_df2 | safe }}
</div> -->

<div class="hide-button btn btn-primary">Show/hide inputs</div>
<div class="to-hide">
  {{ scenario.techs_input_html | safe }}
  {{ scenario.prices_input_html | safe }}
  <!-- {% for tech_df in scenario.tech_df_list %}
    {{ tech_df1 | safe }}
  {% endfor %}-->
</div>
# class TechnologyStringForm(forms.Form):
#     POT_CHOICES = (
#             ('E', 'Emerging'),
#             ('M', 'Mature'),
#             ('FIT', 'Feed-in-tariff'),
#             ('SN', 'Separate negotiations'),
#     )
#     name = forms.CharField(max_length=400)
#     included = forms.BooleanField(required=False)
#     pot = forms.ChoiceField(widget=forms.Select,
#         choices=POT_CHOICES)
#     min_levelised_cost = forms.CharField(max_length=400)
#     max_levelised_cost = forms.CharField(max_length=400)
#     max_deployment_cap = forms.CharField(max_length=400,required=False)
#     num_new_projects = forms.CharField(max_length=400,required=False)
#     load_factor = forms.CharField(max_length=400)
#     strike_price = forms.CharField(max_length=400)
#     project_gen = forms.CharField(max_length=400)
#     """def __init__(self, *args, **kwargs):
#         super(TechnologyStringForm, self).__init__(*args, **kwargs)
#         self.fields['name'].disabled = True
#         self.fields['pot'].disabled = True"""

#http://stackoverflow.com/questions/37688054/saving-a-pandas-dataframe-to-a-django-model
# def handle_uploaded_file(file):
#     t0 =time.time()
#     data = pd.read_csv(file)
#     df = DataFrame(data)
#     s = Scenario.objects.create(name="test")
#     for year in range(2020,2031):
#         a,created = AuctionYear.objects.get_or_create(year = year, scenario = s)
#         for pot_name in ["E", "M", "SN", "FIT"]
#             p,created = Pot.objects.get_or_create(name=pot_name, auctionyear = a)
#
#     user = settings.DATABASES['default']['USER']
#     password = settings.DATABASES['default']['PASSWORD']
#     database_name = settings.DATABASES['default']['NAME']
#
#     database_url = 'postgresql://{user}:{password}@localhost:5432/{database_name}'.format(
#         user=user,
#         password=password,
#         database_name=database_name,
#     )
#
#     engine = create_engine(database_url, echo=False)
#     df.to_sql(Technology, con=engine)
#     t1 = time.time()
#     total = t1-t0
#     print("SQL",total)


# def handle_uploaded_file2(file):
#     t0 = time.time()
#     csv_file = file
#     decoded_file = csv_file.read().decode('utf-8')
#     io_string = io.StringIO(decoded_file)
#     s = Scenario.objects.create(name="test")
#     for row in csv.DictReader(io_string, quotechar='|'):
#         kwargs = {}
#         pot_name = row['pot']
#         year = int(row['year'])
#         a,created = AuctionYear.objects.get_or_create(year = year, scenario = s)
#         p,created = Pot.objects.get_or_create(name=pot_name, auctionyear = a)
#         kwargs['pot'] = p
#         kwargs['name'] = row['name']
#         kwargs['min_levelised_cost'] = float(row['min LCOE'])
#         kwargs['max_levelised_cost'] = float(row['max LCOE'])
#         kwargs['strike_price'] = float(row['strike price'])
#         kwargs['load_factor'] = float(row['load factor'])
#         kwargs['max_deployment_cap'] = float(row['max GW pa'])
#         kwargs['num_new_projects'] = int(row['number of new projects']) if row['number of new projects'] != "" else None
#         kwargs['project_gen'] = float(row['project size GWh'])
#         t = Technology.objects.create_technology(**kwargs)
#         t.save()
#     t1 = time.time()
#     total = t1-t0
#     print("csv.DictReader",total) #6.880906581878662
#
# def handle_uploaded_file3(file):
#     t0 =time.time()
#     data = pd.read_csv(file)
#     df = DataFrame(data)
#     s = Scenario.objects.create(name="test")
#     for index, row in df.iterrows():
#         kwargs = {}
#         pot_name = row['pot']
#         year = int(row['year'])
#         a,created = AuctionYear.objects.get_or_create(year = year, scenario = s)
#         p,created = Pot.objects.get_or_create(name=pot_name, auctionyear = a)
#         kwargs['pot'] = p
#         kwargs['name'] = row['name']
#         kwargs['min_levelised_cost'] = float(row['min LCOE'])
#         kwargs['max_levelised_cost'] = float(row['max LCOE'])
#         kwargs['strike_price'] = float(row['strike price'])
#         kwargs['load_factor'] = float(row['load factor'])
#         kwargs['max_deployment_cap'] = float(row['max GW pa'])
#         kwargs['num_new_projects'] = int(row['number of new projects']) if pd.notnull(row['number of new projects']) else None
#         kwargs['project_gen'] = float(row['project size GWh'])
#         t = Technology.objects.create_technology(**kwargs)
#         t.save()
#     t1 = time.time()
#     total = t1-t0
#     print("pandas",total) #6.874750375747681
#
# def handle_uploaded_file2(file,s):
#     t0 = time.time()
#     data = pd.read_csv(file)
#     df = DataFrame(data)
#     print("creating technology objects")
#
#     for row_id, row in enumerate(df.values):
#         kwargs = {}
#         pot_name = row[0]
#         year = int(row[2])
#         a = AuctionYear.objects.get(year = year, scenario = s)
#         #print(a)
#         p = Pot.objects.get(name=pot_name, auctionyear = a)
#         #p = s.auctionyear_dict[year].pot_dict[pot_name]
#         #print(p)
#         kwargs['pot'] = p
#         kwargs['name'] = row[1]
#         kwargs['min_levelised_cost'] = float(row[4])
#         kwargs['max_levelised_cost'] = float(row[5])
#         kwargs['strike_price'] = float(row[6])
#         kwargs['load_factor'] = float(row[7])
#         kwargs['max_deployment_cap'] = float(row[8])
#         kwargs['num_new_projects'] = int(row[9]) if pd.notnull(row[9]) else None
#         kwargs['project_gen'] = float(row[10])
#         t = Technology.objects.create(**kwargs)
#         #t.save()
#         print(t.id)
#     t1 = time.time()
#     total = t1-t0
#     print("numpy",total) #6.731263160705566
#
#    #qs_techs = Technology.objects.filter(pot__auctionyear__in = auctionyears)
    #df_techs = read_frame(qs_techs, fieldnames=['pot__auctionyear__year','pot__name','name','awarded_gen', 'awarded_cost', 'cum_awarded_gen', 'cum_owed_v_gas', 'cum_owed_v_wp', 'cum_owed_v_absolute'])

    # df_pots = read_frame(qs_pots, fieldnames=['auctionyear__year','name','cum_awarded_gen_result', 'cum_owed_v_wp', 'cum_owed_v_gas'])
    # qs_pots = Pot.objects.filter(auctionyear__in = auctionyears)
    # pot_data = df_pots.values.tolist()
    # pot_col_names = list(df_pots.columns)


    # writer.writerow(["Summary tables"])

    # df_list = [
    #            ('Cumulative costs (£bn) (2021-2025)', scenario.cumulative_costs(1)['df']),
    #            ('Cumulative costs (£bn) (2026-2030)', scenario.cumulative_costs(2)['df']),
    #            ('Cumulative generation (TWh) (2021-2025)', scenario.cum_awarded_gen_by_pot(1)['df']),
    #            ('Cumulative generation (TWh) (2026-2030)', scenario.cum_awarded_gen_by_pot(2)['df']),
    #            ('Cost of new generation awarded (£m) (2021-2025)', scenario.awarded_cost_by_tech(1)['df']),
    #            ('Cost of new generation awarded (£m) (2026-2030)', scenario.awarded_cost_by_tech(2)['df']),
    #            ('Generation (TWh) (2021-2025)', scenario.gen_by_tech(1)['df']),
    #            ('Generation (TWh) (2026-2030)', scenario.gen_by_tech(2)['df']),
    #            ('Capacity (GW) (2021-2025)', scenario.cap_by_tech(1)['df']),
    #            ('Capacity (GW) (2026-2030)', scenario.cap_by_tech(2)['df']),
    #            ]

    # for df_pair in df_list:
    #     title = [df_pair[0]]
    #     writer.writerow(title)
    #     headers = ['']
    #     headers.extend(df_pair[1].columns)
    #     writer.writerow(headers)
    #     for i in range(len(df_pair[1].index)):
    #         row = [df_pair[1].index[i]]
    #         row.extend(df_pair[1].iloc[i])
    #         writer.writerow(row)
        # writer.writerow([])


    # for meth in meth_list:
    #     chart[meth] = {}
    #     df[meth] = {}
    #     for period_num in [1,2]:
    #         results = scenario.get_or_make_chart_data(meth,period_num)
    #         data = results['data']
    #         data_source = SimpleDataSource(data=data)
    #         options = results['options']
    #         if meth == "cumulative_costs" or meth == "cum_awarded_gen_by_pot":
    #             chart[meth][period_num] = LineChart(data_source, options=options, height=400, width="100%")
    #         else:
    #             chart[meth][period_num] = ColumnChart(data_source, options=options, height=400, width="100%")
    #         df[meth][period_num] = results['df'].to_html(classes="table table-striped table-condensed") # slowest line; consider saving in db
    #         context["".join([meth,"_chart",str(period_num)])] = chart[meth][period_num]
    #         context["".join([meth,"_df",str(period_num)])] = df[meth][period_num]
    # t2 = time.time() * 1000
    # print(t2-t1,t1-t0)
    #print(connection.queries)
    #for query in connection.queries:
    #    print('\n',query)

    # def df_for_display(self):
    #     effects = self.df()
    #     effects = effects.dropna(axis=1,how="all")
    #     effects = effects.set_index(tech_policy_index)
    #     effects = effects.style.format("{:.0%}").render()
    #     effects = effects.replace('<table id=', '<table class="table table-striped table-condensed" id=')
    #     return effects


    # def df_techs_for_display(self):
        # effects = self.df('techs')
        # effects.columns = dfh.tech_policy_columns
        # effects = effects.dropna(axis=1,how="all")
        # effects = effects.set_index(dfh.tech_policy_index['titles'])
        # effects = effects.dropna(axis=0,how="all")
        # effects = effects.style.format("{:.0%}").render()
        # effects = effects.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        # return effects

    # def df_prices_for_display(self):
        # effects = self.df('prices')
        # effects = effects.dropna(axis=1,how="all")
        # effects = effects.set_index(dfh.prices_policy_index)
        # effects = effects.dropna(axis=0,how="all")
        # effects = effects.unstack(0)
        # effects.columns = dfh.prices_policy_columns
        # effects = effects.style.format("{:.0%}").render()
        # effects = effects.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        # return effects
form playing:
<h1 class="page-header">New scenario from CSV</h1>
<!-- <form method="POST" class="post-form" enctype="multipart/form-data">{% csrf_token %} -->
    <!-- {{ scenario_form }} -->

<form method="POST" class="form-horizontal" enctype="multipart/form-data">{% csrf_token %}
    <div class="form-group">
        <label for="{{ scenario_form.name.id_for_label }}" class="col-sm-2 control-label">Scenario name:</label>
        <div class="col-sm-10">{{ scenario_form.name }}</div>
    </div>

    <div class="form-group">
        <label for="{{ scenario_form.description.id_for_label }}" class="col-sm-2 control-label">Description:</label>
        <div class="col-sm-10">{{ scenario_form.description }}</div>
    </div>
</form>
<form method="POST" class="inline-form" enctype="multipart/form-data">{% csrf_token %}
      <div class="form-group">
          <label for="{{ scenario_form.budget.id_for_label }}" class="col-sm-2 control-label">Budget period 1:</label>
          <div class="col-sm-10">{{ scenario_form.budget }}</div>
      </div>
      <div class="form-group">
          <label for="{{ scenario_form.budget2.id_for_label }}" class="col-sm-2 control-label">Budget period 2:</label>
          <div class="col-sm-10">{{ scenario_form.budget2 }}</div>
      </div>
    </div>
    <!-- 'name', 'description', 'budget', 'budget2', 'percent_emerging','excel_quirks', 'end_year1', 'subsidy_free_p2', 'policies') -->
<form method="POST" class="form-horizontal" enctype="multipart/form-data">{% csrf_token %}

    <h3>Technology prices</h3>
    {{ upload_form }}
    <button type="submit" class="save btn btn-primary">Submit</button>
</form>
https://getbootstrap.com/css/#forms
https://docs.djangoproject.com/en/1.10/topics/forms/#form-rendering-options


### Some methods that match notes to note dictionary that might not be necessary:
def get_notes(df):
    # or start_of_notes = df.index[df.pot_name.isnull()][-1]+1
    start_of_notes = df.index[df.pot_name.isin(["Notes", "notes"])][0]+1
    notes = df.copy()[start_of_notes:-1]
    notes.columns = pd.Index(notes.iloc[0].values,name = None)
    for col in ['source', 'notes', 'link', 'secondary_link']:
        notes[col] = notes[col].astype(str)
    notes = notes.iloc[1:]
    notes = notes.dropna(how="all",axis=1)
    notes.index = np.arange(0,len(notes))
    return notes

def match_notes_to_note_columns(tech_df_with_note_columns, notes):
    f = lambda x: str(x.to_dict())
    note_dict = notes.apply(f, axis=1).values
    notes = notes.set_index('num')
    note_stump = notes.index.values
    for i, val in enumerate(note_stump):
        try:
            note_stump[i] = str(float(note_stump[i]))
        except ValueError:
            note_stump[i] = note_stump[i]
    tech_df_with_note_columns[dfh.note_columns] = tech_df_with_note_columns[dfh.note_columns].replace(note_stump,note_dict)
    return tech_df_with_note_columns

def parse_file(file):
    df = pd.read_csv(file)
    try:

        end_of_techs = df.index[df.pot_name.isnull()][0]
        tech_df_with_note_columns = df.copy()[0:end_of_techs]
        tech_df_with_note_columns.year, tech_df_with_note_columns.included = tech_df_with_note_columns.year.astype(int), tech_df_with_note_columns.included.astype(bool)
        for col in dfh.note_columns:
            tech_df_with_note_columns[col] = tech_df_with_note_columns[col].astype(str)
        # print(tech_df_with_note_columns.dtypes)
        notes = get_notes(df)
        matched_notes_df = match_notes_to_note_columns(tech_df_with_note_columns, notes)
        tech_df_with_note_columns.min_levelised_cost = tech_df_with_note_columns.min_levelised_cost.astype(float)
        tech_df = tech_df_with_note_columns[dfh.tech_inputs_keys]
        print('notes')
    except IndexError:
        tech_df = df
        matched_notes_df = None
        notes = None
        print('no notes')
    finally:

        tech_df = interpolate_tech_df(tech_df)
        # print(tech_df)
    return tech_df, matched_notes_df, notes

# @lru_cache(maxsize=1024)
def process_scenario_form(scenario_form):
    s = scenario_form.save()
    prices_df = get_prices(s, scenario_form)
    create_auctionyear_and_pot_objects(prices_df,s)
    policies = s.policies.all()
    file = scenario_form.cleaned_data['file']
    tech_df, matched_notes_df, notes = parse_file(file)
    s.csv_inc_notes = matched_notes_df.to_json()
    s.notes = notes.to_json()
    s.save()
    try:
        updated_tech_df = update_tech_with_policies(tech_df,policies)
        create_technology_objects(updated_tech_df,s)
        return 'success'
    except TypeError:
        print("policies must have same method")
        s.delete()
        return 'error'

##unnecessary tests:
    # python manage.py test lcf.tests3.Notes.test_match_notes_to_columns
    def test_match_notes_to_columns(self):
        file = open('lcf/template_with_sources.csv')
        df = pd.read_csv(file)
        end_of_techs = df.index[df.pot_name.isnull()][0]
        original_tech_df_with_note_columns = df.copy()[0:end_of_techs]
        original_tech_df_with_note_columns.year, original_tech_df_with_note_columns.included = original_tech_df_with_note_columns.year.astype(int), original_tech_df_with_note_columns.included.astype(bool)
        for col in dfh.note_columns:
            original_tech_df_with_note_columns[col] = original_tech_df_with_note_columns[col].astype(str)
        notes = get_notes(df)
        matched_notes_df = match_notes_to_note_columns(original_tech_df_with_note_columns, notes)
        di = ast.literal_eval(matched_notes_df.min_levelised_cost_note[0])
        self.assertEqual(di['link'], 'https://www.gov.uk/government/collections/energy-generation-cost-projections')

    def test_parse_file_with_notes(self):
        file = open('lcf/template_with_sources.csv')
        tech_df, original_tech_df_with_note_columns, notes = parse_file(file)
        self.assertEqual(len(tech_df), 88)
        self.assertEqual(len(tech_df.columns), 11)
        self.assertEqual(len(notes), 16)
        self.assertEqual(len(notes.columns), 5)
        self.assertEqual(len(original_tech_df_with_note_columns), 88)
        self.assertEqual(len(original_tech_df_with_note_columns.columns), 18)
        # di = ast.literal_eval(matched_notes_df.min_levelised_cost_note[0])
        # self.assertEqual(di['link'], 'https://www.gov.uk/government/collections/energy-generation-cost-projections')


###Before I destroy my helpers:

def get_prices(s, scenario_form):
    new_wp = dfh.new_wp
    excel_wp = dfh.excel_wp
    wp_dict = {"new": new_wp, "excel": excel_wp, "other": None}
    wholesale_prices = wp_dict[scenario_form.cleaned_data['wholesale_prices']]
    if wholesale_prices == None:
        wholesale_prices = [float(w) for w in list(filter(None, re.split("[, \-!?:\t]+",scenario_form.cleaned_data['wholesale_prices_other'])))]
    excel_gas = [85.0, 87.0, 89.0, 91.0, 93.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0]
    gas_dict = {"excel": excel_gas, "other": None}
    gas_prices = gas_dict[scenario_form.cleaned_data['gas_prices']]
    if gas_prices == None:
        gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",scenario_form.cleaned_data['gas_prices_other'])))]
    prices_df = DataFrame({'gas_prices': gas_prices, 'wholesale_prices': wholesale_prices},index=range(2020,2031))
    return prices_df


def create_auctionyear_and_pot_objects(prices_df,s):
    gas_prices = prices_df.gas_prices
    wholesale_prices = prices_df.wholesale_prices
    for i, y in enumerate(range(2020,s.end_year2+1)):
        a = AuctionYear.objects.create(year=y, scenario=s, gas_price=gas_prices[y], wholesale_price=wholesale_prices[y])
        for p in ['E', 'M', 'SN', 'FIT']:
            Pot.objects.create(auctionyear=a,name=p)


def interpolate_tech_df(tech_df):
    tech_df = tech_df.set_index(dfh.tech_policy_index['keys'])
    techs = list(tech_df.index.levels[0])
    new_index = [(t, y) for t in techs for y in range(2020,2031) ]
    tech_df = tech_df.reindex(index=new_index)
    try:
        tech_df[dfh.to_interpolate] = tech_df[dfh.to_interpolate].interpolate()
    except KeyError:
        raise
    else:
        tech_df[['pot_name', 'included']] = tech_df[['pot_name', 'included']].fillna(method="ffill")
        tech_df = tech_df.reset_index()
        return tech_df

def update_tech_with_policies(tech_df,policies):
    if len(policies) == 0:
        return tech_df
    else:
        tech_df.set_index(dfh.tech_policy_index['keys'], inplace=True)
        tech_df = tech_df[tech_df.included == True]
        included = tech_df.included
        tech_df = tech_df.drop('included',axis=1)
        pots = tech_df.pot_name
        tech_df = tech_df.drop('pot_name',axis=1)
        dfs = []
        for policy in policies:
            if policy.method != policies[0].method:
                raise PolicyMethodError("Unable to combine multiplication and subtraction policies in same scenario")
        for policy in policies:
            policy_df = policy.df().copy()
            policy_df = policy_df.set_index(dfh.tech_policy_index['keys'])
            policy_techs = list(policy_df.index.levels[0])
            index = [(t, y) for t in policy_techs for y in range(2020,2031) ]
            interpolated = policy_df.reindex(index=index).interpolate()
            fillna = 1 if policies[0].method == 'MU' else 0
            interpolated = interpolated.reindex(index=tech_df.index).fillna(fillna)
            interpolated.columns = tech_df.columns
            dfs.append(interpolated)
        if policies[0].method == 'MU':
            updated_tech_df = tech_df * reduce((lambda x, y : x * y), dfs)
        elif policies[0].method == 'SU':
            updated_tech_df = tech_df - reduce((lambda x, y : x + y), dfs)
        updated_tech_df['pot_name'] = pots
        updated_tech_df['included'] = included
        updated_tech_df = updated_tech_df.reset_index()
        return updated_tech_df

def create_technology_objects(df,s):
    print("creating technology objects")
    # df = df.reset_index()
    for index, row in df.iterrows():
        a = AuctionYear.objects.get(year = row.year, scenario = s)
        p = Pot.objects.get(name=row.pot_name, auctionyear = a)
        t = Technology.objects.create(
            name = row.tech_name,
            pot = p,
            included = row.included,
            min_levelised_cost = row.min_levelised_cost,
            max_levelised_cost = row.max_levelised_cost,
            strike_price = row.strike_price,
            load_factor = row.load_factor,
            max_deployment_cap = row.max_deployment_cap if pd.notnull(row.max_deployment_cap) else None,
            num_new_projects = row.num_new_projects if pd.notnull(row.num_new_projects) else None,
            project_gen = row.project_gen
        )


def get_notes(df):
    # or start_of_notes = df.index[df.pot_name.isnull()][-1]+1
    # start_of_notes = df.index[df.pot_name.isin(["Notes", "notes"])][0]+1
    start_of_notes = df.index[df.isin(["Notes", "notes"]).any(axis=1)][0]+1

    notes = df.copy()[start_of_notes:]
    notes.columns = pd.Index(notes.iloc[0].values,name = None)
    for col in dfh.note_cols:
        notes[col] = notes[col].astype(str)
    notes = notes.iloc[1:]
    notes = notes.dropna(how="all",axis=1)
    notes.index = np.arange(0,len(notes))
    return notes

def parse_file(file):
    df = pd.read_csv(file)
    if 'name' in df.columns:
        df.rename(columns={'name':'tech_name'}, inplace=True)
    try:
        # end_of_techs = df.index[df.pot_name.isnull()][0]
        end_of_techs = df.index[df.isnull().all(axis=1)][0]

    except IndexError: #ie only techs are in doc
        tech_df = df
        original_tech_df_with_note_columns = tech_df.reindex(columns = dfh.note_and_tech_keys)

        notes = DataFrame(columns = dfh.note_cols_inc_index)
        tech_df = interpolate_tech_df(tech_df)
        return tech_df, original_tech_df_with_note_columns, notes
    else:
        original_tech_df_with_note_columns = df.copy()[0:end_of_techs]
        original_tech_df_with_note_columns.year, original_tech_df_with_note_columns.included = original_tech_df_with_note_columns.year.astype(int), original_tech_df_with_note_columns.included.astype(bool)
        for col in dfh.note_columns:
            original_tech_df_with_note_columns[col] = original_tech_df_with_note_columns[col].astype(str)
        else:
            notes = get_notes(df)
            original_tech_df_with_note_columns.min_levelised_cost = original_tech_df_with_note_columns.min_levelised_cost.astype(float)
            tech_df = original_tech_df_with_note_columns[dfh.tech_inputs_keys]
            tech_df = interpolate_tech_df(tech_df)
            return tech_df, original_tech_df_with_note_columns, notes



# @lru_cache(maxsize=1024)
def process_scenario_form(scenario_form):
    s = scenario_form.save()
    prices_df = get_prices(s, scenario_form)
    create_auctionyear_and_pot_objects(prices_df,s)
    policies = s.policies.all()
    file = scenario_form.cleaned_data['file']
    try:
        tech_df, original_tech_df_with_note_columns, notes = parse_file(file)
    except (KeyError, AttributeError):
        s.delete()
        raise
    else:
        s.csv_inc_notes = original_tech_df_with_note_columns.to_json()
        s.notes = notes.to_json()
        s.save()
        try:
            updated_tech_df = update_tech_with_policies(tech_df,policies)
            create_technology_objects(updated_tech_df,s)
        except PolicyMethodError:
            s.delete()
            raise

# scenario detail view scribble:
        # context['techs_input_html'] = scenario.techs_input_html()
        # context['prices_input_html'] = scenario.prices_input_html()
        # context['tech_cap_pivot1'] = scenario.pivot_to_html(scenario.pivot('awarded_cap',1))
        # context['tech_cap_pivot2'] = scenario.pivot_to_html(scenario.pivot('awarded_cap',2))
        # context['tech_gen_pivot1'] = scenario.pivot_to_html(scenario.pivot('awarded_gen',1))
        # context['tech_gen_pivot2'] = scenario.pivot_to_html(scenario.pivot('awarded_gen',2))
        # context['tech_cum_owed_v_wp_pivot1'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_wp',1))
        # context['tech_cum_owed_v_wp_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_wp',2))
        # context['tech_cum_owed_v_gas_pivot1'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_gas',1))
        # context['tech_cum_owed_v_gas_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_gas',2))
        # context['tech_cum_owed_v_absolute_pivot1'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_absolute',1))
        # context['tech_cum_owed_v_absolute_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_absolute',2))
        # context['tech_cum_awarded_gen_pivot1'] = scenario.pivot_to_html(scenario.pivot('cum_awarded_gen',1))
        # context['tech_cum_awarded_gen_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_awarded_gen',2))

    # writer.writerow(["............Inputs to model, after policies have been applied..........."])
    # inputs = [
    #            ('Prices (£/MWh)', scenario.prices_input()),
    #            ('Technology data', scenario.techs_input()),
    #            ]
    # for df_pair in inputs:
    #     title = [df_pair[0]]
    #     writer.writerow(title)
    #     if df_pair[0] == 'Prices (£/MWh)':
    #         headers = ['']
    #     else:
    #         headers = []
    #     headers.extend(df_pair[1].columns)
    #     writer.writerow(headers)
    #     for i in range(len(df_pair[1].index)):
    #         row = [df_pair[1].index[i]]
    #         row.extend(df_pair[1].iloc[i])
    #         if df_pair[0] == 'Technology data':
    #             row = row[1:]
    #         writer.writerow(row)
    #     writer.writerow([])
    #


<div class="row placeholders">
  <div class="col-xs-6 col-sm-3 placeholder">
    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAHd3dwAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw==" width="200" height="200" class="img-responsive" alt="Generic placeholder thumbnail">
    <h4>Label</h4>
    <span class="text-muted">Something else</span>
  </div>
  <div class="col-xs-6 col-sm-3 placeholder">
    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAHd3dwAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw==" width="200" height="200" class="img-responsive" alt="Generic placeholder thumbnail">
    <h4>Label</h4>
    <span class="text-muted">Something else</span>
  </div>
  <div class="col-xs-6 col-sm-3 placeholder">
    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAHd3dwAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw==" width="200" height="200" class="img-responsive" alt="Generic placeholder thumbnail">
    <h4>Label</h4>
    <span class="text-muted">Something else</span>
  </div>
  <div class="col-xs-6 col-sm-3 placeholder">
    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAHd3dwAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw==" width="200" height="200" class="img-responsive" alt="Generic placeholder thumbnail">
    <h4>Label</h4>
    <span class="text-muted">Something else</span>
  </div>
</div>
