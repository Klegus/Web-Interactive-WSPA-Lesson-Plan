from django.shortcuts import render
import pandas as pd

# Create your views here.
def index(request):
    df = pd.read_excel('latest_plans/plan-edited-4.xlsx', sheet_name='Sheet1')
    data = df.to_dict('records')
    return render(request, 'main/index.html', {'data': data})