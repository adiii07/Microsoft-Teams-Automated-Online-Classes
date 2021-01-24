from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
from datetime import datetime
from time import sleep
import pandas as pd

#opening browser
session_data = 'user-data-dir=session_data'
options = webdriver.ChromeOptions()
options.add_argument(session_data)

browser = webdriver.Chrome(options=options)
browser.maximize_window()
browser.get("https://teams.microsoft.com/")
sleep(5)

#reading timetable
timetable = pd.read_csv("timetable.csv")
print(timetable)

#finding current day in timetable
date = datetime.today()
day_num = int(date.strftime('%w'))

#finding current time
hour = datetime.now().hour
minute = datetime.now().minute
current_time = "{}:{}".format(hour, minute)

start_time = ['8:00', '9:00', '10:15', '11:15', '12:30', '13:30']
end_time   = ['9:00', '10:00', '11:15', '12:15', '13:30', '14:30']

# finding period number
for i in range(6):
    if start_time[i] < current_time <= end_time[i]:
        period_num = i+1
    elif "10:00" < current_time <= "10:15":
        period_num = "break1"
    elif "12:15" < current_time <= "12:30":
        period_num = "break2"
    elif current_time >= "14:30":
        period_num = "NoSchool"
    
in_meeting = False

# finding current period
def get_period():
    global current_period

    if period_num != "break1" and period_num != "break2" and period_num != "NoSchool":
        current_period = timetable[str(period_num)][day_num]
        check_free_period()

    elif period_num == "break1":
        print("Debug: It is first break")
        while period_num == "break1":
            if current_time > "10:15":
                current_period = timetable[str(period_num)][day_num]
                check_free_period()
            else:
                sleep(60)
                print("Debug: It is still break")

    elif period_num == "break2":
        print("Debug: It is second break")
        while period_num == "break2":
            if current_time > "12:30":
                current_period = timetable[str(period_num)][day_num]
                check_free_period()
            else:
                sleep(60)
                print("Debug: It is still break")

    elif period_num == "NoSchool":
        print("Debug: School is over")
        browser.quit()

# checking if free period    
def check_free_period():

    if current_period == "NaN":
        print("Debug: You have free period")
        while current_period == 'NaN':
            sleep(600)
            print("Debug: It is still free period")
    else:
        print('Debug: Current period is {}'.format(current_period))
        team_click()
       
# clicking the team of current period
def team_click():
    global team_name

    try:
        subject_team = browser.find_elements_by_class_name("team")[1::2]
    except exceptions.NoSuchElementException:
        sleep(15)
        subject_team = browser.find_elements_by_class_name("team")[1::2]

    for team in subject_team:
        team_name = team.get_attribute("data-tid").lower()
        if current_period in team_name:
            try:
                team.click()
                sleep(0.5)
                team.click()
                print('Debug: {} team selected'.format(team_name))
            except exceptions.NoSuchElementException:
                browser.find_element_by_xpath('//*[@id="app-bar-2a84919f-59d8-4441-a975-2a8c2643b741"]').click()
                sleep(1)
                team.click()
                print("Debug: Clicked team second try")
                team.click()
    sleep(3)
    join_meeting()

# joining the meeting
def join_meeting():
    global in_meeting
    global leave_button

    while in_meeting == False:
        try:
            join_button = browser.find_element_by_css_selector("span[ng-if='!ctrl.roundButton']")
        except exceptions.NoSuchElementException:
            print("Debug: {} meeting has not started".format(current_period))
            sleep(15)
        else:
            join_button.click()
            in_meeting = True
            print("Debug: In {} meeting".format(current_period))
    sleep(2)
    video_button = browser.find_element_by_class_name('style-layer')
    mic_button = browser.find_element_by_xpath('//*[@id="preJoinAudioButton"]/div/button/span[1]')
    pre_join = browser.find_element_by_class_name('button-col')

    if video_button.get_attribute('title') == 'Turn camera off' and mic_button.get_attribute('title') == 'Mute microphone':
        video_button.click()
        mic_button.click()
        sleep(1)
        pre_join.click()
    elif mic_button.get_attribute('title') == 'Mute microphone':
        mic_button.click()
        sleep(1)
        pre_join.click()
    else:
        sleep(1)
        pre_join.click()
    sleep(5)

    leave_button = browser.find_element_by_xpath('//*[@id="hangup-button"]')
    leave_meeting()

#leaving the meeting
def leave_meeting():
    global in_meeting
    participants = 29

    if current_time >= end_time[period_num - 1] and participants < 30:
        sleep(1)
        try:
            leave_button.click()
        except (exceptions.ElementNotInteractableException, exceptions.ElementClickInterceptedException):
            browser.find_element_by_xpath('/html').click()
            sleep(2)
            browser.find_element_by_xpath('/html').click()
            sleep(1)
            leave_button.click()
            print('Debug: Clicked leave second try')
        finally:
            in_meeting = False
    else:
        print("{} period is going on".format(current_period))
        sleep(600)

    get_period()       


get_period()
