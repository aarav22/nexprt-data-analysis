import fractions
from unittest import getTestCaseNames
import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient
from datetime import datetime
import dateutil.parser
import matplotlib.pyplot as plt
from itertools import groupby
from pandas.io.json import json_normalize

## Setting up a time period
time_period = st.radio(
    "Select temporal aggregation period",
    ('Daily', 'Weekly'))

if time_period == 'Daily':
    time_period = 1
else:
    time_period = 7

## Another interactive feature which selects only approved docs
is_approved = st.radio(
    "Do you want only approved docs?",
    ('Yes', 'No'))

if is_approved == 'Yes':
    is_approved = True
else:
    is_approved = False
    
    
# utility function to group data into either weeks or days:
def group_util(date, min_date):
    return (date-min_date).days // time_period

### Getters

## To get timestamps for showing trends in time
def get_timestamps(items):
    timestamps = []
    for item in items:
        if item['createdAt'] is not None:
            dt = item['createdAt']
            timestamps += [dt.date()]
    return timestamps

## To get the data for modifications after approval
def get_modifications(items):
    data = []
    p = []
    for item in items:
        modified = False
        dt = datetime.now()
        try:
            if 'approvalTimestamp' in item and 'timestamp' in item\
                    and item['approvalTimestamp'] != '' and item['timestamp'] != '':
                val = item['approvalTimestamp']
                for time in item['timestamp']:
                    dt = time
                    diff = dt.replace(tzinfo=None) - val.replace(tzinfo=None)
                    hours = diff.total_seconds() / 3600
                    if hours > 0:
                        modified = True
                        break
                data += [(dt.date(), modified)]

        except Exception as e:
            print("Error: ", e)
    return data

## To get the data for approval trends
def get_approvals(items):
    data = []
    try:
        for item in items:
            val = False
            if 'createdAt' in item:
                dt = item['createdAt']
                val = True if 'approvalTimestamp' in item else False
                data += [(dt.date(), val)]
    except Exception as e:
        print("Error: ", e)
    return data

## To get the date for the use of misc field
def get_misc(items):
    data = []
    for item in items:
        val = False
        try:
            if item['createdAt'] is not None:
                dt = item['createdAt']
                if 'estBOM' in item and 'miscellaneous' in item['estBOM']\
                        and item['estBOM']['miscellaneous'] != '':
                    val = True
                else:
                    val = False
                data += [(dt.date(), val)]
        except Exception as e:
            print("Error: ", e)
    return data

## To get TAT data
def get_tat(items):
    data = []
    for item in items:
        val = False
        try:
            if item['createdAt'] is not None:
                dt = item['createdAt']
                if 'approvalTimestamp' in item:
                    val = item['approvalTimestamp']
                else:
                    val = None
                if val is not None:
                    diff = val.replace(tzinfo=None) - dt.replace(tzinfo=None)
                    hours = diff.total_seconds() / 3600
                    data += [hours]
        except Exception as e:
            print("Error: ", e)
    return data


### Showing the data

def show_timetrends(items):
    timestamps = get_timestamps(items)
    # initializing start date
    min_date = min(timestamps)

    # sorting before grouping
    timestamps.sort()

    temp = []
    for key, val in groupby(timestamps, key=lambda date: group_util(date, min_date)):
        temp.append((key, list(val)))

    # using strftime to convert to userfriendly
    # format
    res = []
    for sub in temp:
        intr = []
        for ele in sub[1]:
            intr.append(ele.strftime("%Y/%m/%d"))
        res.append((sub[0], intr))

    # printing result
    X = [x[0] for x in res]
    Y = [len(x[1]) for x in res]

    total_1 = 0
    total_2 = 0

    range_val = int(6 * 7/time_period)

    # For calculating mean:
    # for ele in range(0, range_val):
    #     total_1 = total_1 + Y[ele]
    # for ele in range(range_val, len(Y)):
    #     total_2 = total_2 + Y[ele]
    # print("Mean : " + str(total_1/range_val) +
    #     " " + str(total_2/(len(Y)-range_val)))

    chart_data = pd.DataFrame(Y, index=X, columns=['count'])
    st.subheader('Time Trends')
    st.line_chart(chart_data)

def show_approval(items):
    data = get_approvals(items)
    print(len(data))
    min_date = min(data, key=lambda x: x[0])[0]

    # sorting before grouping
    data.sort(key=lambda x: x[0])

    temp = []
    for key, val in groupby(data, key=lambda item: group_util(item[0], min_date)):
        temp.append((key, list(val)))

    # using strftime to convert to userfriendly
    # format
    res = []
    for sub in temp:
        intr = []
        for ele in sub[1]:
            intr.append((ele[0].strftime("%Y/%m/%d"), ele[1]))
        res.append((sub[0], intr))

    fraction_dict = {}
    for time_period in res:
        fraction_dict[time_period[0]] = sum(
            ele[1] for ele in time_period[1] if ele[1] == True)/len(time_period[1])
    df_1 = pd.DataFrame.from_dict(fraction_dict, orient='index')
    st.subheader('Approval trend')
    st.line_chart(df_1)


def show_tat(items):
    data = get_tat(items)
    data = [item for item in data if item >= 0]
    df_1 = pd.DataFrame(data, columns=['TAT'])
    st.subheader('TAT trend')
    st.line_chart(df_1)


def show_misc(items):
    data = get_misc(items)
    min_date = min(data, key=lambda x: x[0])[0]

    # sorting before grouping
    data.sort(key=lambda x: x[0])

    temp = []
    for key, val in groupby(data, key=lambda item: group_util(item[0], min_date)):
        temp.append((key, list(val)))

    # using strftime to convert to userfriendly
    # format
    res = []
    for sub in temp:
        intr = []
        for ele in sub[1]:
            intr.append((ele[0].strftime("%Y/%m/%d"), ele[1]))
        res.append((sub[0], intr))

    fraction_dict = {}
    for time_period in res:
        fraction_dict[time_period[0]] = sum(
            ele[1] for ele in time_period[1] if ele[1] == True)/len(time_period[1])
    # st.write(fraction_dict)
    st.subheader('Misc trend')
    df_1 = pd.DataFrame.from_dict(fraction_dict, orient='index')
    st.line_chart(df_1)


def show_modifications(items):
    data = get_modifications(items)
    min_date = min(data, key=lambda x: x[0])[0]

    # sorting before grouping
    data.sort(key=lambda x: x[0])

    temp = []
    for key, val in groupby(data, key=lambda item: group_util(item[0], min_date)):
        temp.append((key, list(val)))

    # using strftime to convert to userfriendly
    # format
    res = []
    for sub in temp:
        intr = []
        for ele in sub[1]:
            intr.append((ele[0].strftime("%Y/%m/%d"), ele[1]))
        res.append((sub[0], intr))

    fraction_dict = {}
    for time_period in res:
        fraction_dict[time_period[0]] = sum(
            ele[1] for ele in time_period[1] if ele[1] == True)/len(time_period[1])
    # st.write(fraction_dict)
    st.subheader('Modification trend')
    df_1 = pd.DataFrame.from_dict(fraction_dict, orient='index')
    st.line_chart(df_1)



## Entry point for the file:
if __name__ == '__main__':
    st.title('Pricing Trends')
    
    ## Establishing connection to the database:
    mongoClient = MongoClient(
        "mongodb+srv://candidate:candidate2022@cluster0.p8u2o.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = mongoClient['master-catalogue']['test-temp']
    
    ## Extracting data from the database with no ObjectIds:
    items = db.find({}, {'_id': False})
    l = list(items)

    ## Cleaning and making the db consistent
    for index in range(0, len(l)):
        if l[index]['timestamp'] is not None\
                and l[index]['timestamp'] != ''\
                and len(l[index]['timestamp']) > 0:
            # fixing timestamps:
            for i in range(0, len(l[index]['timestamp'])):
                if isinstance(l[index]['timestamp'][i], str):
                    l[index]['timestamp'][i] = dateutil.parser.parse(
                        l[index]['timestamp'][i]).replace(tzinfo=None)

            # fixing createdAt:
            l[index]['createdAt'] = l[index]['timestamp'][0].replace(tzinfo=None)

            # fixing approvalTime:
            if 'approvalTimestamp' in l[index]:
                if isinstance(l[index]['approvalTimestamp'][0], str):
                    l[index]['approvalTimestamp'] = dateutil.parser.parse(
                        l[index]['approvalTimestamp'][0])
                else:
                    l[index]['approvalTimestamp'] = l[index]['approvalTimestamp'][0]
                    

    ## Getting a data of a particular range given by the slider:
    min_date = min(l, key=lambda x: x['createdAt'])['createdAt']
    max_date = max(l, key=lambda x: x['createdAt'])['createdAt']
    
    ## Code for the slider
    values = st.slider(
        "When do you start?",
        min_date,
        max_date,
        (min_date,  max_date),
        format="MM/DD/YY - hh:mm")
    
    st.write('Values:', values)
    
    # exclude items that do not fit in the time range values[0] and values[1]:
    l = [item for item in l if item['createdAt'].replace(tzinfo=None) >= values[0].replace(
        tzinfo=None) and item['createdAt'].replace(tzinfo=None) <= values[1].replace(tzinfo=None)]
    
    if is_approved:
        # remove all items that do not have approvalTimestamp:
        l = [item for item in l if 'approvalTimestamp' in item and item['approvalTimestamp'] is not None]
    # show time trends:
    show_timetrends(l)

    ## show approval:
    show_approval(l)

    ## show tat:
    show_tat(l)

    ## show misc:
    show_misc(l)

    ## show modifications:
    show_modifications(l)
