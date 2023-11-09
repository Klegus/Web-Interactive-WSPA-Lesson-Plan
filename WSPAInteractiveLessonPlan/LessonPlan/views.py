from django.shortcuts import render
import pandas as pd
import datetime

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
# Create your views here.
def index(request):
    df = pd.read_excel('latest_plans/wzorowy.xlsx', sheet_name='Sheet1', skipfooter=1)
    df.fillna('', inplace=True)
    df['godziny'] = df['godziny'].apply(format_time_range)
    df.apply(lambda row: [f"{row.iloc[0]} {cell_value}" if i > 0 else cell_value for i, cell_value in enumerate(row)], axis=1)
    relevant_columns = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek']
    types_of_course = ["wykład", "ćwiczenia", "laboratorium", "lektorat", "warsztat"]
    for column_name in relevant_columns:
        for i, cell_value in enumerate(df[column_name]):
            row_numbers = df.loc[df[column_name] == cell_value].index
            
            parts = cell_value.split('-')
            if len(parts) < 2:
                continue
            course_name = parts[0].strip()
            lesson_start, lesson_end = get_datetime_range(df['godziny'][row_numbers[0]].replace("<sup>", "").replace("</sup>", ""))
            print(lesson_start, lesson_end, cell_value)
            sala = cell_value.split('\n')[-2]
            type_of_course = None
            for toc in types_of_course:
                if toc in cell_value:
                    type_of_course = toc
                    break
            dates = cell_value.split('daty:')[-1].split('\n')[0]
            dates_list = [datetime.datetime.strptime(f"{date.strip()}.{datetime.datetime.now().year}", '%d.%m.%Y') for date in dates.split(',')]
            
            # Filter out outdated dates
            current_date = datetime.datetime.now()
            upcoming_dates = [date for date in dates_list if date >= current_date]
            formatted_dates = [date.strftime('%d.%m') for date in upcoming_dates]
            if len(formatted_dates) == 0:
                df.at[i, column_name] = ""
                continue
            formatted_dates = ', '.join(formatted_dates)
            if(course_name == "Wychowanie fizyczne"):
                sala = cell_value.split("\n")[-2] + " " + cell_value.split("\n")[-1]
                df.at[i, column_name] = f'<div style="white-space: pre-wrap;">{course_name} - {type_of_course},<br/>{sala} <br>Daty: {formatted_dates}</div>'
            # Replace the cell value with the extracted information
            elif(course_name == "Komunikacja interpersonalna"):
                sala = cell_value.split("\n")[-1]
                df.at[i, column_name] = f'<div style="white-space: pre-wrap;">{course_name} - {type_of_course},<br/>{sala} <br>Daty: {formatted_dates}</div>'
            elif(course_name == "Analiza matematyczna i algebra liniowa"):
                sala = cell_value.split("\n")[-2]
                df.at[i, column_name] = f'<div style="white-space: pre-wrap;">{course_name} - {type_of_course},<br/>{sala} <br>Daty: {formatted_dates}</div>'
            else:
                df.at[i, column_name] = f'<div style="white-space: pre-wrap;">{course_name} - {type_of_course},<br/>{sala} <br>Daty: {formatted_dates}</div>'
    

    data = df.to_dict('records')
    return render(request, 'main/index.html', {'data': data})