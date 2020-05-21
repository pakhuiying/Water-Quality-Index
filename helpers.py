import os
import requests
import urllib.parse
import pandas as pd
import csv
import math

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def calculate_wqi_obs(obs,weights): #function that performs on an observation i.e. single dictionary
    breaks = pd.read_csv("breaks.csv")
    breaks = breaks.set_index("Parameters") #set column as row names
    breaks_transposed = breaks.transpose()
    labels_norm = list(reversed(range(0,101,10))) #need to use 101 instead of 100 because stop: is non-inclusive
    labels_inv = list(range(0,101,10))

    obs = {k: v if v is not None else -99 for k, v in obs.items()} #replace None with -99

    for k, column in zip(obs.keys(), breaks_transposed): #iterating key & column simultaneously, make sure number of keys are same
        value = pd.Series(obs[k]) #change scalar value into a 1D object using pd.Series as pd.cut doesnt accept scalar
        si_breaks = breaks_transposed[column].values
        if k=="do":
            SI = pd.cut(value,si_breaks,labels=labels_inv) #use reverse labels for DO cus SI=100 for high, not low DO
        else:
            SI = pd.cut(value,si_breaks,labels=labels_norm) #assign SI (categories) based on value of obs
        obs[k] = SI #replace values with SI
        #print("parameter: ", k,"SI: ",SI)

    si_list = [] #init empty list
    weights_list = [] #make a copy of weights list that adjusts for weightage for NaN SI values
    for wt, si in zip(weights,obs.keys()):
        si = obs[si].astype(str) #change category type to str type, then use int to cast it to integer
        si = float(si.values)
        wts = weights[wt]
        if math.isnan(si) is True:
            si = -99
            wts = 0
        si_list.append(si*wts)
        weights_list.append(wts)
    wqi = round(sum(si_list)/sum(weights_list),2) #round to 2 dec
    return wqi

def assign_class(obs,weights):
    classes = pd.read_csv("wql_std.csv")
    classes = classes.set_index("Classes") #set column as row names

    for k,column in zip(obs.keys(),classes):
        if obs[k] is None:
            classes[k] = None

    classes_transposed = classes.transpose()

    classes_break = [] #create breaks for classes aka wql std
    for column in classes_transposed:
        wql_dict = classes_transposed[column].to_dict()
        classes_break.append(calculate_wqi_obs(wql_dict,weights))
    classes_break.reverse() #use print(classes_break) to check the list has been reversed
    classes_break.insert(0,0)
    classes_break.insert(5,100) #insert 0, 100 to list so nbreaks=6
    print(classes_break)
    class_labels = [] #create class labels
    for i in reversed(range(1,6)):
        class_labels.append("Class "+ str(i))

    wqi = calculate_wqi_obs(obs,weights) #get wqi and assign a class
    class_wqi = pd.cut(pd.Series(wqi),classes_break,labels=class_labels)
    class_wqi = class_wqi.astype(str)
    class_wqi = str(class_wqi.values) #class string
    return (wqi,class_wqi)

def replace_str(string): #string is a list
    str_dict = {'arsenic':'As','cd':'Cd','cod':'COD','cr':'Cr','do':'DO','ecoli':'E.coli','fluoride':'Fluoride','nh3':'NH3-N','no2':'NO2-N','no3':'NO3-N','pb':'Pb','po4':'PO4','turbidity':'Turbidity'}
    new_string = [str_dict.get(n,n) for n in string]
    return new_string