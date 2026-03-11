import tkinter as tk
from tkinter import messagebox
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    raise ValueError("API_KEY not found. Make sure .env exists and contains API_KEY.")
print("Loaded API_KEY successfully")

#---------- API & Algorithm Functions ----------

def getSchoolNames():
    return profiles.keys()

def mainAlgorithm(school):

    school_zipcode = profiles[school]["zipcode"]
    print(school_zipcode)

    # Contains an array with the dates of the next 2 days
    next_two_days = getNextTwoDays()

    # Gets all the weather data for the attributes
    twoDayWeatherData = getWeatherAttributesNextTwoDays(school_zipcode, next_two_days)

    # Finds averages and combines the data.
    twoDayAttributeAverages = calculateTwoDayAttributeAverages(twoDayWeatherData, next_two_days)

    
    schoolThresholdValues = getSchoolThresholdValues(school)

    print(json.dumps(schoolThresholdValues,indent=4))

    schoolName = schoolThresholdValues.get
    print(json.dumps(twoDayAttributeAverages,indent=4))

    #There will always be 2 keys, representing Day 1 and 2.
    #Index 0 of keysForDays is the date for Day 1 and Index 1 is for Day 2
    keysForDays = list(twoDayAttributeAverages.keys())

    #This returns a tuple with 2 boolean values, first is Day 1 result and second is Day 2 result
    isSnowDayResults = compareThresholds(twoDayAttributeAverages, schoolThresholdValues, keysForDays)

    print(isSnowDayResults)

    return (keysForDays,isSnowDayResults)

def getNextTwoDays():

    today = datetime.now().date()
    next_two_days = [today + timedelta(days=1), today + timedelta(days=2)]
    return next_two_days

def getWeatherAttributesNextTwoDays(school_zipcode, next_two_days):
    
    

    url = f"https://api.openweathermap.org/data/2.5/forecast?zip={school_zipcode},US&appid={API_KEY}&units=imperial"

    response = requests.get(url)
    data = response.json()

    # Define relevant hours for school (6AM to 3PM)
    relevant_hours = range(6, 16)

    # Group forecast by relevant day
    daily_data = {}

    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        day = dt.date()
        hour = dt.hour

        if day not in next_two_days:
            continue  # skip days beyond next 2

        if day not in daily_data:
            daily_data[day] = {"temps": [], "winds": [], "snows": []}

        if hour in relevant_hours:
            temp = item["main"]["temp"]
            wind = item["wind"]["speed"]
            snow = item.get("snow", {}).get("3h", 0)

            daily_data[day]["temps"].append(temp)
            daily_data[day]["winds"].append(wind)
            daily_data[day]["snows"].append(snow)

    return daily_data

def calculateTwoDayAttributeAverages(twoDayWeatherData, next_two_days):
    # Calculate daily averages and max for only the next 2 days

    twoDayAttributeAverages = {}

    for day in next_two_days:
        values = twoDayWeatherData.get(day, {"temps": [], "winds": [], "snows": []})
        if values["temps"]:
            avg_temp = sum(values["temps"]) / len(values["temps"])
            max_wind = max(values["winds"])
            total_snow = sum(values["snows"])

            #Dictionary containing the info for both days
            twoDayAttributeAverages[day.strftime("%Y-%m-%d")] = {"Total Snowfall" : round(total_snow,1),
                                                                 "Average Temperature" : round(avg_temp, 1),
                                                                 "Maximum Wind Speed" : round(max_wind,1),
                                                                  }
    return twoDayAttributeAverages


def getSchoolThresholdValues(school):
    return profiles[school]["thresholds"]


def compareThresholds(twoDayAttributeAverages, schoolThresholdValues, keysForDays):
    #All thresholds must be breached for a snow day to occur.
    # Day 1 = Tomorrow; Day 2 = Day after Tomorrow

    #School Thresholds
    school_totSnow = schoolThresholdValues["Total Snowfall"]
    school_avgTemp = schoolThresholdValues["Average Temperature"]
    school_maxWind = schoolThresholdValues["Maximum Wind Speed"]
    
    #Day 1 comparisons
    day1_totSnow = twoDayAttributeAverages[keysForDays[0]]["Total Snowfall"] 
    day1_avgTemp = twoDayAttributeAverages[keysForDays[0]]["Average Temperature"]
    day1_maxWind = twoDayAttributeAverages[keysForDays[0]]["Maximum Wind Speed"]
    
    global day1_thresholds
    day1_thresholds = {"Total Snowfall": day1_totSnow,"Average Temperature": day1_avgTemp,"Maximum Wind Speed": day1_maxWind}
    

    print(day1_totSnow >= school_totSnow)
    print(day1_avgTemp <= school_avgTemp)
    print(day1_maxWind >= school_maxWind)

    if day1_totSnow >= school_totSnow and day1_avgTemp <= school_avgTemp and day1_maxWind >= school_maxWind:
        day1_isSnowDay = True
    else:
        day1_isSnowDay = False

    #Day 2 comparisons
    day2_totSnow = twoDayAttributeAverages[keysForDays[1]]["Total Snowfall"] 
    day2_avgTemp = twoDayAttributeAverages[keysForDays[1]]["Average Temperature"]
    day2_maxWind = twoDayAttributeAverages[keysForDays[1]]["Maximum Wind Speed"]

    global day2_thresholds
    day2_thresholds = {"Total Snowfall": day2_totSnow,"Average Temperature": day2_avgTemp,"Maximum Wind Speed": day2_maxWind}

    if day2_totSnow >= school_totSnow and day2_avgTemp <= school_avgTemp and day2_maxWind >= school_maxWind:
        day2_isSnowDay = True
    else:
        day2_isSnowDay = False

    return (day1_isSnowDay, day2_isSnowDay)


#----------  File Stuff ----------

#Initializing file stuff
script_folder = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_folder, "schoolProfiles.json")

with open(json_file_path,"r") as f:
    profiles = json.load(f)

def addProfileToFile(schoolProfile):

    with open(json_file_path, "r") as f:
        existingProfiles = json.load(f)

    existingProfiles.update(schoolProfile)
    
    with open(json_file_path, "w") as f:
        json.dump(existingProfiles, f, indent=4)

#---------- Creating The GUI ---------- 

root = tk.Tk()
root.title("Snow Day Calculator")
root.geometry("500x700")

#---------- Frame 1: Intro ----------

frame_intro = tk.Frame(root)

label_intro_title = tk.Label(frame_intro, text="\nSnow Day Calculator",fg="blue",font=("Verdana",18,"bold"))
label_intro_title.pack()

label_intro_directions = tk.Label(frame_intro, text="The Snow Day Calculator will use the current weather data to predict if there will\nbe a snowday for your school.\n\n\n\nWould you like to enter custom threshold data for your school, or select an existing profile?")
label_intro_directions.pack()

# Create a frame to hold the 2 buttons
frame_intro_buttons = tk.Frame(frame_intro)

def press_button_intro_selectProfile():
    print("Profile")
    updateOptionMenuValues()
    frame_intro.pack_forget()
    frame_selectProfile.pack()

button_intro_selectProfile = tk.Button(frame_intro_buttons,text="Select Profile",width = 20, command=press_button_intro_selectProfile)
button_intro_selectProfile.pack(side="left",padx=10)

def press_button_intro_customInput():
    print("Custom")
    frame_intro.pack_forget()
    frame_customInput.pack()

button_intro_customInput = tk.Button(frame_intro_buttons,text="Custom Input",width = 20, command=press_button_intro_customInput)
button_intro_customInput.pack(side="left",padx=10)

frame_intro_buttons.pack(pady=50)

frame_intro.pack()

#---------- Frame 2a: Select Profile ----------

frame_selectProfile = tk.Frame(root)

label_selectProfile_title = tk.Label(frame_selectProfile, text="\nSnow Day Calculator",fg="blue",font=("Verdana",18,"bold"))
label_selectProfile_title.pack()

label_selectProfile_heading = tk.Label(frame_selectProfile,text="\nSelect a School Profile",font=("Verdana",14,"bold"))
label_selectProfile_heading.pack(pady=25)


school_names = getSchoolNames()
optionMenu_selectedOption = tk.StringVar()
optionMenu_selectedOption.set("none")
optionMenu = tk.OptionMenu(frame_selectProfile, optionMenu_selectedOption, *school_names)
optionMenu.pack(pady=10)


def updateOptionMenuValues():
    menu = optionMenu["menu"]
    menu.delete(0, "end")  # remove old options
    for school in getSchoolNames():
        menu.add_command(label=school, command=lambda value=school: optionMenu_selectedOption.set(value))


def press_button_selectProfile_confirm():
    print("Confirm")
    global schoolName
    schoolName = optionMenu_selectedOption.get()
    print(schoolName)

    if schoolName == "none":
        label_selectProfile_error.config(text="Please select a school.")
        return
    
    frame_selectProfile.pack_forget()
    frame_displayResults.pack()

    # The main algorithm calculates if there is a snowday the next 2 days.
    #It returns the dates for the next 2 days, and the True/False results for those days
    global nextTwoDates, isSnowDayResults
    nextTwoDates, isSnowDayResults = mainAlgorithm(schoolName)

    print(nextTwoDates)
    print(isSnowDayResults)

    createFrame3(nextTwoDates, isSnowDayResults)

button_selectProfile_confirm = tk.Button(frame_selectProfile,text="Confirm",width = 10, command=press_button_selectProfile_confirm)
button_selectProfile_confirm.pack(pady=10)

label_selectProfile_error = tk.Label(frame_selectProfile, fg="red",text="")
label_selectProfile_error.pack()


def press_button_selectProfile_back():
    print("Back")
    frame_selectProfile.pack_forget()
    frame_intro.pack()


button_selectProfile_back = tk.Button(frame_selectProfile,text="Back",width = 10, command=press_button_selectProfile_back)
button_selectProfile_back.pack(pady=100)

#---------- Frame 2b: Custom Input ----------

frame_customInput = tk.Frame(root)

label_customInput_title = tk.Label(frame_customInput, text="\nSnow Day Calculator",fg="blue",font=("Verdana",18,"bold"))
label_customInput_title.pack()

label_customInput_heading = tk.Label(frame_customInput, text="Enter the values for your school:")
label_customInput_heading.pack()

label_customInput_SchoolName = tk.Label(frame_customInput,text="\nEnter School Name")
label_customInput_SchoolName.pack()
entry_customInput_SchoolName = tk.Entry(frame_customInput)
entry_customInput_SchoolName.pack()

label_customInput_ZipCode = tk.Label(frame_customInput,text="\nEnter School Zipcode")
label_customInput_ZipCode.pack()
entry_customInput_ZipCode = tk.Entry(frame_customInput)
entry_customInput_ZipCode.pack()

label_customInput_Snowfall = tk.Label(frame_customInput,text="\nEnter Total Snowfall (inches) Threshold")
label_customInput_Snowfall.pack()
entry_customInput_Snowfall = tk.Entry(frame_customInput)
entry_customInput_Snowfall.pack()

label_customInput_Temp = tk.Label(frame_customInput,text="\nEnter Average Temperature (F) Threshold")
label_customInput_Temp.pack()
entry_customInput_Temp = tk.Entry(frame_customInput)
entry_customInput_Temp.pack()

label_customInput_Wind = tk.Label(frame_customInput,text="\nEnter Max Wind Speed (mph) Threshold")
label_customInput_Wind.pack()
entry_customInput_Wind = tk.Entry(frame_customInput)
entry_customInput_Wind.pack()

def press_button_customInput_submit():

    global schoolName, zipCode, snowfall, temp, wind
    schoolName = entry_customInput_SchoolName.get()
    zipCode = entry_customInput_ZipCode.get()
    snowfall = entry_customInput_Snowfall.get()
    temp = entry_customInput_Temp.get()
    wind = entry_customInput_Wind.get()

    print(schoolName)
    print(zipCode)
    print(snowfall)
    print(temp)
    print(wind)

    if not all([schoolName,zipCode,snowfall,temp,wind]):
        label_customInput_error.config(text="Please fill out all fields.")
        return
    
    isValidEntries = validateEntries(schoolName,zipCode,snowfall,temp,wind)
        
    if not isValidEntries:
        label_customInput_error.config(text="One or more fields are invalid.")
        return
    
    frame_customInput.pack_forget()
    frame_addProfile.pack()
    frame_addProfile_buttons.pack(pady=30)
            

def validateEntries(schoolName,zipCode,snowfall,temp,wind):
    if not isinstance(schoolName, str):
        return False
    
    if not (zipCode.isdigit() and len(zipCode) == 5):
        return False

    try:
        snowfall = float(snowfall)
        temp = float(temp)
        wind = float(wind)
    except ValueError:
        return False

    return True

button_customInput_submit = tk.Button(frame_customInput,text="Confirm", command=press_button_customInput_submit)
button_customInput_submit.pack(pady=10)

label_customInput_error = tk.Label(frame_customInput, fg="red",text="")
label_customInput_error.pack()

def press_button_customInput_back():
    print("Back")
    frame_customInput.pack_forget()
    frame_intro.pack()


button_customInput_back = tk.Button(frame_customInput,text="Back",command=press_button_customInput_back)
button_customInput_back.pack(pady=50)


#---------- Frame 2bb: Ask to Add to Profiles ----------

frame_addProfile = tk.Frame(root)

label_addProfile_title = tk.Label(frame_addProfile, text="\nSnow Day Calculator",fg="blue",font=("Verdana",18,"bold"))
label_addProfile_title.pack()

label_addProfile_heading = tk.Label(frame_addProfile,text="\n\n\n\nWould you like to add this school as a profile in the system?")
label_addProfile_heading.pack()

frame_addProfile_buttons = tk.Frame(frame_addProfile)

def press_button_addProfile(answer):
    print(answer)

    frame_addProfile.pack_forget()
    frame_displayResults.pack()

    global schoolProfile
    schoolProfile = {
        schoolName: {
            "zipcode": int(zipCode),
            "thresholds": {
                "Total Snowfall": float(snowfall),
                "Average Temperature": float(temp),
                "Maximum Wind Speed": float(wind) 
            }   
        }
    }
    
    print(json.dumps(schoolProfile,indent=4))

    if answer == "yes":
        addProfileToFile(schoolProfile)
        updateOptionMenuValues()
    profiles.update(schoolProfile)

    global nextTwoDates, isSnowDayResults
    nextTwoDates, isSnowDayResults = mainAlgorithm(schoolName)

    if answer == "no":
        del profiles[schoolName]

    print("*****")
    print(nextTwoDates)
    print(isSnowDayResults)

    createFrame3(nextTwoDates, isSnowDayResults)


button_addProfile_yes = tk.Button(frame_addProfile_buttons,text="Yes",width = 20, command=lambda: press_button_addProfile("yes"))
button_addProfile_yes.pack(side="left",padx=10)

def press_button_addProfile_no():
    print("No")


button_addProfile_no = tk.Button(frame_addProfile_buttons,text="No",width = 20, command=lambda: press_button_addProfile("no"))
button_addProfile_no.pack(side="left",padx=10)



#---------- Frame 3: Display Results ----------

# When button_selectProfile_confirm is pressed, the main algorithm method runs.

# Frame 3 is being created in a function because frame 3 can be created from a profile, or user input,
# So this function is called from Frame 2a and Frame 2b
def createFrame3(nextTwoDates, isSnowDayResults):

    
    day1_obj = datetime.strptime(nextTwoDates[0], "%Y-%m-%d")
    day1_formatted = day1_obj.strftime("%A, %B %#d") 

    day1_isWeekend = day1_obj.weekday() >= 5

    if day1_isWeekend:
        day1_result = "No School - Weekend!"
    elif isSnowDayResults[0]:
        day1_result = "No School - Snow Day!"
    else:
        day1_result = "Go to School..."

    label_displayResults_Day1.config(text=f"\n{day1_formatted}:   {day1_result}")



    day2_obj = datetime.strptime(nextTwoDates[1], "%Y-%m-%d")
    day2_formatted = day2_obj.strftime("%A, %B %#d") 

    day2_isWeekend = day2_obj.weekday() >= 5

    if day2_isWeekend:
        day2_result = "No School - Weekend!"
    elif isSnowDayResults[1]:
        day2_result = "No School - Snow Day!"
    else:
        day2_result = "Go to School..."

    label_displayResults_Day2.config(text=f"\n{day2_formatted}:   {day2_result}")

    




frame_displayResults = tk.Frame(root)

label_displayResults_title = tk.Label(frame_displayResults, text="\nSnow Day Calculator",fg="blue",font=("Verdana",18,"bold"))
label_displayResults_title.pack()

label_displayResults_heading = tk.Label(frame_displayResults,text="\nResults",font=("Verdana",14,"bold"))
label_displayResults_heading.pack()

label_displayResults_Day1 = tk.Label(frame_displayResults,text=f"Day1 Result PlaceHolder",font=("Verdana",12))
label_displayResults_Day1.pack(fill="x")

label_displayResults_Day2 = tk.Label(frame_displayResults,text=f"Day2 Result PlaceHolder",font=("Verdana",12))
label_displayResults_Day2.pack(fill="x")

def press_button_displayResults_runAgain():
    
    #Reset all the values to default
    optionMenu_selectedOption.set("none")

    frame_displayResults_Stats.pack_forget()
    button_displayResults_Stats.config(text="Show Stats")

    entry_customInput_SchoolName.delete(0, tk.END)
    entry_customInput_ZipCode.delete(0, tk.END)
    entry_customInput_Snowfall.delete(0, tk.END)
    entry_customInput_Temp.delete(0, tk.END)
    entry_customInput_Wind.delete(0, tk.END)
    label_customInput_error.config(text="")
    label_selectProfile_error.config(text="")

    frame_displayResults.pack_forget()
    frame_intro.pack()

    
 
button_displayResults_runAgain = tk.Button(frame_displayResults,text="Run Again?", command=press_button_displayResults_runAgain)
button_displayResults_runAgain.pack(pady=50)


#Expandable frame for the stats



frame_displayResults_Stats = tk.Frame(frame_displayResults, bd=1, relief="sunken")
label_displayResults_stats = tk.Label(frame_displayResults_Stats, text="PlaceHolder")
label_displayResults_stats.pack(padx=10, pady=10)

def press_button_displayResults_Stats():

    if schoolName in profiles:
        thresholds = profiles[schoolName]["thresholds"]
    else:
        thresholds = schoolProfile[schoolName]["thresholds"]

    print("schoolName:" + schoolName)
    print(thresholds)

    stats = (
        f"Thresholds for {schoolName}:\n"
        f"      Total Snowfall:                   {thresholds["Total Snowfall"]:>5}    in\n"
        f"      Average Temperature:       {thresholds["Average Temperature"]:>5}   F\n"
        f"      Maximum Wind Speed:     {thresholds["Maximum Wind Speed"]:>5}    mph\n\n"
        f"Forcast for Day 1:\n"
        f"      Total Snowfall:                    {day1_thresholds['Total Snowfall']:>5}    in\n"
        f"      Average Temperature:       {day1_thresholds['Average Temperature']:>5}   F\n"    
        f"      Maximum Wind Speed:     {day1_thresholds['Maximum Wind Speed']:>5}   mph\n\n"    
        f"Forcast for Day 2:\n"
        f"      Total Snowfall:                    {day2_thresholds['Total Snowfall']:>5}    in\n"
        f"      Average Temperature:       {day2_thresholds['Average Temperature']:>5}   F\n"    
        f"      Maximum Wind Speed:     {day2_thresholds['Maximum Wind Speed']:>5}   mph\n"        
            )
    label_displayResults_stats.config(text=stats,anchor="w", justify="left")

    if frame_displayResults_Stats.winfo_ismapped():  # If currently visible
        frame_displayResults_Stats.pack_forget()
        button_displayResults_Stats.config(text="Show Stats")
    else:
        frame_displayResults_Stats.pack()
        button_displayResults_Stats.config(text="Hide Stats")

button_displayResults_Stats = tk.Button(frame_displayResults, text="Show Stats", command=press_button_displayResults_Stats)
button_displayResults_Stats.pack(pady=15)















root.mainloop()