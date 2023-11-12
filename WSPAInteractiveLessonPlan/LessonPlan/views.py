from django.shortcuts import render, redirect
import pandas as pd
import datetime
from pymongo import MongoClient, DESCENDING

def format_time_range(time_range):
    start_time_str, end_time_str = time_range.split('-')
    start_time = datetime.datetime.strptime(start_time_str.strip(), '%H%M').time()
    end_time = datetime.datetime.strptime(end_time_str.strip(), '%H%M').time()
    formatted_time_range = f"{start_time.strftime('%H<sup>%M</sup>')}-{end_time.strftime('%H<sup>%M</sup>')}"
    return formatted_time_range
def get_datetime_range(time_range):
    start_time_str, end_time_str = time_range.split('-')
    start_time = datetime.datetime.strptime(start_time_str.strip(), '%H%M').time()
    end_time = datetime.datetime.strptime(end_time_str.strip(), '%H%M').time()
    return [start_time, end_time]
def get_latest_document_for_group(group: int):
    """
    Get the latest document for a specified group from a MongoDB collection
    """
    
    # Create a MongoDB client, change "your_connection_string" to your actual connection string
    client = MongoClient("mongodb://mongo:ca15bbfhDH4Gf-5D6bE1DdFC54-CFACG@viaduct.proxy.rlwy.net:32898")
    
    # Specify the database and collection
    db = client["LessonPlan"]
    collection = db["plans"]

    # Construct the group key
    group_key = f"group{group}"

    # Get the latest document for the specified group
    latest_document = collection.find_one({group_key: {"$exists": True}}, sort=[('_id', DESCENDING)])

    # Close the client
    client.close()

    return latest_document
# Create your views here.
def index(request):
    group = request.COOKIES.get('group', 1)

    # Ensure the group number is an integer
    group = int(group)
    data = get_latest_document_for_group(group)
    return render(request, 'main/index.html', {'data': data[f"group{group}"], 'current_group': group})

def change_group(request):
    group = request.POST.get('group', 1)
    response = redirect('index')
    response.set_cookie('group', group)
    return response