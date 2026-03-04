Snow Day Calculator Documentation:

The Snow Day Calculator is a microservice that attempts to predict if the next 2 calendar days
will be a snow day. The service allows the user to choose from premade school "profiles".
A school profile consists of the school's preferences for when a snow day should happen. These profiles
contain threshold values for snowfall amount, average temperature, and max wind speed. Additionally,
the user can choose to input their own school by entering their school name, zipcode, and preferred
threshold values. If they desire, they can add their school's profile to the system.

Then, the service retrieves the current weather data between the hours of 6am to 3pm for the next 
two calendar days and determines the forecast values for snowfall amount, average temperature, and 
max wind speed. Then, the school's threshold values are compared to the forecast values and a prediction
is made for the next 2 days.

The service displays the results and allows the user to view the stats of their school profile and the
weather data from the API. The service allows for the user to run the service again without closing and
reopening the GUI.

Note: There is a bug where if the user chooses "No" when asked if they want to save the profile to the system,
it still gets added regardless. I am currently working on fixing the bug, but could not get it solved in 
time for the deadline of this assignment.