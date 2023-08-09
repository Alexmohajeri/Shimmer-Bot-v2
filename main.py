# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 20:22:51 2022

@author: Alex
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import discord
import os
from discord.ext import tasks
from keep_alive import keep_alive
from datetime import datetime, date, timedelta
from tabulate import tabulate


class series:
    def __init__(self, name, url):
        self.name = name
        self.url = url


seriesList = [
    series('F1', 'https://f1calendar.com/'),
    series('F2', 'https://f2cal.com/'),
    series('F3', 'https://f3calendar.com/'),
    series('Indycar', 'https://indycarcalendar.com/')
]


def getEventDateTime(soup):
    eventDate = soup \
        .find('td', {'class': 'text-right md:text-left'}) \
        .getText()
    eventTime = soup \
        .find_all('div', {'class': 'text-right md:text-left pr-2 md:pr-0'})[-1] \
        .getText()
    return datetime.strptime(F"{eventDate}-{eventTime}", '%d %b-%H:%M')


def getEventName(soup):
    print(soup.find('tr', {'class': 'cursor-pointer'}).find('span').find('span').get_text())
    return soup.find('tr', {'class': 'cursor-pointer'}).find('span').find('span').get_text()


def getSubevents(soup):
    subevents = soup.find_all('tr')
    subevents.pop(0)
    subevents = list(
        map(
            lambda e: {
                'event':
                e.find('td', {
                    'class': 'p-4'
                }).getText(),
                'date':
                e.find('td', {
                    'class': 'text-right md:text-left'
                }).getText(),
                'UKTime':
                e.find_all('div', {
                    'class': 'text-right md:text-left pr-2 md:pr-0'
                })[-1].getText()
            }, subevents))
    return pd.DataFrame.from_dict(subevents)


def nextRaceInSeries(series):
    print("building " + series.name)
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }
    page = requests.get(series.url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser') \
        .find(id='events-table') \
        .find('tbody', {'class': 'text-white'})
    name = getEventName(soup)
    eventDateTime = getEventDateTime(soup)
    subevents = getSubevents(soup)
    raceDetails = {
        'series':
        series.name,
        'name':
        name,
        'eventDate':
        date(date.today().year, eventDateTime.month, eventDateTime.day),
        'subeventDetails':
        subevents
    }

    return raceDetails


racing = list(map(nextRaceInSeries, seriesList))


def buildMsg():
    print('buildmsg')
    print(date.today().weekday())
    print(datetime.now().hour)
    s = []
    if date.today().weekday() == 3 and datetime.now().hour == 8:
        racingThisWeek = []
        for x in racing:
            if abs(date.today() - x['eventDate']) < timedelta(days=7):
                racingThisWeek.append(x)
        if len(racingThisWeek) < 1:
            s.append("No races this week :(")
        else:
            s.append("Attention " + os.getenv('ROLEID') +
                     " - Race schedule for this weekend")
            for x in racingThisWeek:
                s.append("Series: " + x['series'])
                s.append("Round: " + x['name'])
                s.append("Timetable: ```" + tabulate(x['subeventDetails'],
                                                     showindex=False,
                                                     tablefmt="fancy_grid",
                                                     headers="keys") + '```')
            return (s)
    else:
        return ""


client = discord.Client(intents=discord.Intents.default())


@tasks.loop(hours=1)
async def run():
    msg = buildMsg()
    if msg != "":
        channel = client.get_channel(int(os.getenv('CHANNELID')))
        for i in msg:
            await channel.send(i)


@client.event
async def on_ready():
    run.start()


keep_alive()
client.run(os.getenv('TOKEN'))
