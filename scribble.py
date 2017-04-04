import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from lcf.models import Scenario, AuctionYear, Pot, Technology

from django.test.utils import setup_test_environment
setup_test_environment()
from django.test import Client
client = Client()


import timeit

s = Scenario.objects.get(pk=119)
a = s.auctionyear_set.get(year=2021)
p = a.pot_set.get(name="E")
t = p.technology_set.get(name="OFW")

a0 = s.auctionyear_set.get(year=2020)
p0 = a0.pot_set.get(name="E")
t0 = p0.technology_set.get(name="OFW")


a2 = s.auctionyear_set.get(year=2022)
p2 = a2.pot_set.get(name="E")
t2 = p2.technology_set.get(name="OFW")


def mini_auction(p):
    gen = 0
    cost = 0
    projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded'])
    if p.auctionyear.year == 2020:
        previous_year_projects = DataFrame()
    else:
        previous_year = p.auctionyear.scenario.auctionyear_set.get(year = p.auctionyear.year - 1).pot_set.get(name=p.name)
        previous_year_projects = previous_year.projects()[(previous_year.projects().funded == "this year") | (previous_year.projects().funded == "previously")]
    return previous_year_projects



t.project_gen = t.project_gen_incorrect / 1000
t.cum_project_gen = t.cum_project_gen_incorrect / 1000
t.project_cap = cap(t.project_gen,t.load_factor)
t.years_supported = 2031 - t.pot.auctionyear.year
t.max_deployment_gen = gen(t.max_deployment_cap,t.load_factor)
t.num_projects = round(t.max_deployment_gen / t.cum_project_gen) # change to truncate?

def load_factor(cap_gw,gen_twh):
    return gen_twh / (cap_gw * 8.760)


def cap(gen_twh,load_factor):
    return gen_twh / (load_factor * 8.760)


def gen(cap_gw,load_factor):
    return cap_gw * load_factor * 8.760


t.min_levelised_cost = 71
t.max_levelised_cost = 81
t.strike_price = 76
t.load_factor = .45
t.project_gen_incorrect = 700
t.max_deployment_cap = 1.2
t.cum_project_gen_incorrect = 700
t.cum_project_gen_incorrect = 1400
t.cum_project_gen_incorrect = 2100


t2.previous_year = None if t2.pot.auctionyear.year == 2020 else t2.pot.auctionyear.scenario.auctionyear_set.get(year=t2.pot.auctionyear.year-1).pot_set.get(name=t2.pot.name).technology_set.get(name=t2.name)








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
