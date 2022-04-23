from re import T
import pycxsimulator
from pylab import *
from random import sample
import pandas as pd
import os

# Size of grid
height = 1
width = 1

# Number of agents
total_population = 1000

# this is the probability of being infected by the virus and agent is not vaccinated/immune
probability_infection = 0.95
# probability of agent developing immunity after contracting the virus
probability_immunity = 0.5
# probability of infection if vaccinated
probability_vacc_infection = 0.4

## probability immunity after reinfection
probability_immunity_reinfection = 0.95

### these are our probabilities of death if infected and reinfected
# probability of agent dying while infected with virus
probability_death = 0.05
# more likely to survive if reinfected
probability_reinfection_death = 0.03

## vaccination rate / can adjust slow or fast vaccination rate
vaccinate_rate =  0.9

# magnitude of movement
community_spread = 0.02

# Radius for collision detection
cd = 0.02
cdsq = cd ** 2

# starting values, which will we will track
deaths = 0
# start with 10 infections in community
infections = 10
immune = 0
vaccinated = 0
reinfections = 0
recovered = 0
# if infected change healthy pop
# don't need to take into account other states because once infected other states only come into play then
# hence infections only need to be taken into account here
healthy = total_population - infections

# lists to track and plot relevant statistics over time
healthy_lst = []
deaths_lst = []
infections_lst = []
immune_lst = []
vaccine_lst = []
reinfection_lst = []
rec_lst = []

class agent:
    pass

def initialise():
    global time, agents, deaths, infections, immune, vaccinated, reinfections, recovered, healthy

    time = 0
    agents = []
    for i in range(total_population - infections):
        ag = agent()
        ag.state = 'healthy' if random() <= probability_infection else 'immune'
        if ag.state == 'immune':
            immune += 1
            healthy -= 1
            # time agent is immune from virus after having it, can be changed setting it at low value to start
            ag.immunity_time = 10
        ag.infected_time = -1
        ag.vaccine_efficacy = -1
        ag.x = uniform(0, width)
        ag.y = uniform(0, height)
        agents.append(ag)

    # this is dealing with our initial collection of infections (total of 10)
    # this initializes the infection time they have left, location etc
    for i in range(infections):
        ag = agent()
        ag.state = 'infected'
        # infection time left -> between 1 and 7
        ag.infected_time = randint(1, 7)
        # need to initialize these parameters or else code breaks
        ag.immunity_time = 0
        ag.vaccine_efficacy = 0
        ag.x = uniform(0, width)
        ag.y = uniform(0, height)
        agents.append(ag)

    ### initialise statistics we want to track and graph over time
    healthy_lst.append([time, healthy])
    deaths_lst.append([time, deaths])
    infections_lst.append([time, infections])
    immune_lst.append([time, immune])
    vaccine_lst.append([time, vaccinated])
    reinfection_lst.append([time, reinfections])
    rec_lst.append([time, recovered])

def observe():
    global time, agents, deaths, infections, immune, vaccinated, reinfections, recovered, healthy
    subplot(2, 2, 1)
    cla()

    infected = [ag for ag in agents if ag.state == 'infected']
    if len(infected) > 0:
        x = [ag.x for ag in infected]
        y = [ag.y for ag in infected]
        plot(x, y, 'r.')

    immune_count = [ag for ag in agents if ag.state == 'immune']
    if len(immune_count) > 0:
        x = [ag.x for ag in immune_count]
        y = [ag.y for ag in immune_count]
        plot(x, y, 'g.')

    # Plotting healthy (not infected) (black)
    healthys = [ag for ag in agents if ag.state == 'healthy']
    if len(healthys) > 0:
        x = [ag.x for ag in healthys]
        y = [ag.y for ag in healthys]
        plot(x, y, 'k.')
    
    # Plotting vaccinated (magenta , none to start)
    vaccine = [ag for ag in agents if ag.state == 'vaccinated']
    if len(vaccine) > 0:
        x = [ag.x for ag in vaccine]
        y = [ag.y for ag in vaccine]
        plot(x, y, 'm.')

    reinf = [ag for ag in agents if ag.state == 'reinfected']
    if len(reinf) > 0:
        x = [ag.x for ag in reinf]
        y = [ag.y for ag in reinf]
        plot(x, y, 'c.')

    recover = [ag for ag in agents if ag.state == 'recovered']
    if len(recover) > 0:
        x = [ag.x for ag in recover]
        y = [ag.y for ag in recover]
        plot(x, y, 'b.')

    axis('image')
    axis([0, 1, 0, 1])

    ax = subplot(2, 1, 2)
    cla()
    plot(deaths_lst, color = 'crimson', label = 'deaths')
    # weird glitch was duplicating lines on plot so remove duplicates
    # these lines were in set positions at top of the plot also
    ax.lines[0].remove()
    plot(vaccine_lst, color = 'gold', label = 'vaccines')
    ax.lines[1].remove()
    plot(infections_lst, color = 'lightsalmon', label = 'infections')
    ax.lines[2].remove()
    plot(immune_lst, color = 'violet', label = 'immune')
    ax.lines[3].remove()
    plot(reinfection_lst, color = 'black', label = 'reinfection')
    ax.lines[4].remove()
    plot(rec_lst, color = 'dodgerblue', label = 'recovered')
    ax.lines[5].remove()
    plot(healthy_lst, color = 'lime', label = 'healthy')
    ax.lines[6].remove()
    legend()

def update_one_agent():
    global time, agents, deaths, infections, immune, vaccinated, reinfections, recovered, healthy

    if len(agents) == 0:
        return

    ag = choice(agents)

    ag.x += uniform(-community_spread, community_spread)
    ag.y += uniform(-community_spread, community_spread)
    ag.x = 1 if ag.x > 1 else 0 if ag.x < 0 else ag.x
    ag.y = 1 if ag.y > 1 else 0 if ag.y < 0 else ag.y

    # Detecting collisions
    neighbours = [nb for nb in agents if (ag.x - nb.x) ** 2 + (ag.y - nb.y) ** 2 < cdsq]

    # If current agent is infected, all neighbours become infected unless immune or vaccinated
    if ag.state == 'infected':
        for nb in neighbours:
            if nb.state == 'healthy':
                nb.state = 'infected'
                nb.infected_time = 0
                nb.immunity_time = 0
                nb.vaccine_efficacy = 0
                infections += 1
                healthy -= 1
            elif nb.state == 'recovered':
                nb.state = 'reinfected'
                nb.infected_time = 0
                nb.immunity_time = 0
                nb.vaccine_efficacy = 0
                reinfections += 1
            else:
                continue

    elif ag.state == 'reinfected':
        for nb in neighbours:
            if nb.state == 'healthy':
                nb.state = 'infected'
                nb.infected_time = 0
                nb.immunity_time = 0
                nb.vaccine_efficacy = 0
                infections += 1
                healthy -= 1
            elif nb.state == 'recovered':
                nb.state = 'reinfected'
                nb.infected_time = 0
                nb.immunity_time = 0
                nb.vaccine_efficacy = 0
                reinfections += 1
            else:
                continue

    # If current agent is healthy, it will become infected if any neighbours are infected
    elif ag.state == 'healthy':
        infected_neighbours = [ag for ag in neighbours if ag.state == 'infected']
        reinfected_neighbours = [ag for ag in neighbours if ag.state == 'reinfected']
        if len(infected_neighbours) > 0 or len(reinfected_neighbours) > 0:
            ag.state = 'infected'
            ag.infected_time = 0
            ag.immunity_time = 0
            ag.vaccine_efficacy = 0
            infections += 1
            healthy -= 1

    # handle reinfected case    
    elif ag.state == 'recovered':
        infected_neighbours = [ag for ag in neighbours if ag.state == 'infected']
        reinfected_neighbours = [ag for ag in neighbours if ag.state == 'reinfected']
        if len(infected_neighbours) > 0 or len(reinfected_neighbours) > 0:
            ag.state = 'reinfected'
            ag.infected_time = 0
            ag.immunity_time = 0
            ag.vaccine_efficacy = 0
            reinfections += 1
            recovered -= 1
        
    elif ag.state == 'vaccinated':
        # small chance of infection if vaccinated
        infected_neighbours = [ag for ag in neighbours if ag.state == 'infected']
        reinfected_neighbours = [ag for ag in neighbours if ag.state == 'reinfected']
        if len(infected_neighbours) > 0 or len(reinfected_neighbours) > 0:
            if random() <= probability_vacc_infection:
                ag.state = 'infected'
                ag.infected_time = 0
                ag.immunity_time = -1
                ag.vaccine_efficacy = -1
                infections += 1
                vaccinated -= 1
            else:
                pass
        else:
            pass

    # If current agent is immune ignore
    else:
        pass

def update():
    global time, agents, infections, deaths, immune, vaccinated, healthy, recovered, reinfections

    # increase infection time over time
    infected = [ag for ag in agents if ag.state == 'infected']
    for ag in infected:
        ag.infected_time += 1

    # decrease immunity over time
    immun = [ag for ag in agents if ag.state == 'immune']
    for ag in immun:
        ag.immunity_time -= 1

    # decrease vaccine efficacy over time
    vacc = [ag for ag in agents if ag.state == 'vaccinated']
    for ag in vacc:
        ag.vaccine_efficacy -= 1
    
    # increase time reinfected after each step
    reinfs = [ag for ag in agents if ag.state == 'reinfected']
    for ag in reinfs:
        ag.infected_time += 1

    ## randomly vaccinate portion of population that has not contracted the virus
    healthys = [ag for ag in agents if ag.state == 'healthy']
    # take random sample of healthy agents
    if len(healthys) > 10:
        r = len(healthys) % 10
        sample1 = sample(healthys, r)
    else:
        sample1 = healthys
    for ag in sample1:
        if random() < vaccinate_rate:
            ag.state = 'vaccinated'
            # set timeframe on vaccine effectiveness
            ag.vaccine_efficacy = 250
            vaccinated += 1
            healthy -= 1
        else:
            continue

    # Change agents who have been infected for 14 days to either immune/recovered
    infection_over = [ag for ag in agents if ag.infected_time == 14 and ag.state == 'infected']
    # Subtract number of recovered from current infections
    infections -= len(infection_over)
    for ag in infection_over:
        # Random chance of death after infection
        if random() <= probability_death:
            agents.remove(ag)
            # Add to deaths total
            deaths += 1
        ag.infected_time = -1

        # Change to immune if greater than or equal random prob
        if random() <= probability_immunity:
            ag.state = 'immune'
            # set time of immunity
            ag.immunity_time = 30
            ag.infected_time = -1
            # Add to immune total
            immune += 1
        # if not immune label as recovered so can track reinfection if it occurs
        else:
            ag.state = 'recovered'
            ag.infected_time = -1
            recovered += 1

    # Change agents who have been reinfected for 14 days to immune if they survive
    reinfection_over = [ag for ag in agents if ag.infected_time == 14 and ag.state == 'reinfected']
    # Subtract number of recovered from current reinfections
    reinfections -= len(reinfection_over)
    for ag in reinfection_over:
        # Random chance of death after reinfection (higher rate this time)
        if random() <= probability_reinfection_death:
            agents.remove(ag)
            # Add to deaths total
            deaths += 1
        ag.infection_time = -1
        
        if random() <= probability_immunity_reinfection:
            ag.state = 'immune'
        # high number as we want no real chance of reinfection after being reinfected once
            ag.immunity_time = 365
            immune += 1
        else:
            ag.state = 'recovered'

    # take random sample of recovered agents and vaccinate
    recoveries = [ag for ag in agents if ag.state == 'recovered']
    if len(recoveries) > 10:
        r1 = len(recoveries) % 10
        sample2 = sample(recoveries, r1)
    else:
        sample2 = recoveries
    for ag in sample2:
        if random() < vaccinate_rate:
            ag.state = 'vaccinated'
            # set timeframe on vaccine effectiveness, longer here to previous infection
            ag.vaccine_efficacy = 360
            vaccinated += 1
            recovered -= 1
        else:
            continue
    
    # Change agents who's immunity has waned to at risk again (healthy)
    for ag in immun:
        # if agents immunity from virus is gone change state
        if ag.immunity_time == 0:
            ag.state = 'recovered'
            # remove agent from count of immune
            immune -= 1
            recovered += 1
        else:
            continue
    
    for ag in vacc:
        # if agents vaccine efficacy timeline has passed change state
        # change to healthy as they needed to be healthy to get vaccine at start
        if ag.vaccine_efficacy == 0:
            ag.state = 'healthy'
            healthy += 1
        else:
            continue

    sample_move = total_population * 0.5
    sample_move = round(sample_move)
    for i in range(sample_move):   
        update_one_agent()

    # Collecting statistics over time for subplot of statistics over time
    healthy_lst.append([time, healthy])
    deaths_lst.append([time, deaths])
    infections_lst.append([time, infections])
    immune_lst.append([time, immune])
    vaccine_lst.append([time, vaccinated])
    reinfection_lst.append([time, reinfections])
    rec_lst.append([time, recovered])

pycxsimulator.GUI().start(func=[initialise, observe, update])

#### we have tuples in our lists here need to get into csv format to analyse better
#### Creates a DataFrame object from a structured ndarray, sequence of tuples (pd.DataFrame.from_records)

pd.DataFrame.from_records(deaths_lst, columns=['time', 'deaths']).to_csv(os.path.join('./data-analysis/ineffective-vaccine/', 'deaths.csv'), index=False)
pd.DataFrame.from_records(infections_lst, columns=['time', 'infections']).to_csv(os.path.join('./data-analysis/ineffective-vaccine/', 'infections.csv'), index=False)
pd.DataFrame.from_records(vaccine_lst, columns=['time', 'vaccinated']).to_csv(os.path.join('./data-analysis/ineffective-vaccine/', 'vaccine.csv'), index=False)
pd.DataFrame.from_records(reinfection_lst, columns=['time', 'reinfections']).to_csv(os.path.join('./data-analysis/ineffective-vaccine/', 'reinfections.csv'), index=False)