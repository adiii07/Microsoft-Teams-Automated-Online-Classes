from selenium import webdriver
from selenium.common import exceptions
from datetime import datetime
from time import sleep
import pandas as pd
import sys

#reading timetable
timetable = pd.read_csv("timetable.csv", )
print(timetable)

#finding current day in timetable
date = datetime.today()
day_num = int(date.strftime('%w'))

# start and end timings
start_time = ['08:00', '09:00', '10:15', '11:15', '12:30', '13:30']
end_time   = ['09:00', '10:00', '11:15', '12:15', '13:30', '14:30']

in_meeting = False

# opening browser
session_data = 'user-data-dir=session_data'
options = webdriver.ChromeOptions()
options.add_argument(session_data)

browser = webdriver.Chrome(options=options)
browser.maximize_window()
browser.get("https://teams.microsoft.com/")
sleep(10)

# finding period number
def find_period_num():
    global current_time
    global period_num

    current_time = datetime.now().strftime("%H:%M")

    for i in range(6):
        if start_time[i] < current_time < end_time[i]:
            period_num = i+1
        elif "10:00" < current_time < "10:15":
            period_num = "break1"
        elif "12:15" < current_time < "12:30":
            period_num = "break2"
        elif current_time >= "14:30":
            period_num = "NoSchool"

    print('Debug: Period number is',period_num)


# finding current period
def get_period():
    global current_period
    find_period_num()

    if period_num != "NoSchool" and period_num != 'break1' and period_num != 'break2':
        current_period = timetable[str(period_num)][day_num]
        team_click()
    
    elif period_num == 'break1' or period_num == 'break2':
        team_click()

    elif period_num == "NoSchool":
        browser.quit()
        sys.exit("School is over!")


# handling break
def check_break():
    global current_period

    while period_num == 'break1' or period_num == 'break2':
        print('Debug: It is break')
        sleep(60)
        find_period_num()
    else:
        current_period = timetable[str(period_num)][day_num]
        print('Debug: Break is over')
        print('Debug: Current period is', current_period)


# handling free period    
def check_free_period():
    global current_period

    while pd.isnull(current_period):
        print("Debug: You have free period")
        sleep(60)
        find_period_num()
        current_period = timetable[str(period_num)][day_num]
    else:
        print('Debug: Free period is over')
        print('Debug: Current period is', current_period)
        check_break()

# clicking the team of current period
def team_click():
    global team_names

    check_break()
    check_free_period()
  
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
                print(f'Debug: {team_name} team selected')
            except exceptions.NoSuchElementException:
                browser.find_element_by_xpath('//*[@id="app-bar-2a84919f-59d8-4441-a975-2a8c2643b741"]').click()
                sleep(1)
                team.click()
                sleep(0.5)
                team.click()
            finally:
                sleep(3)
                join_meeting()
        else:
            print(f'Debug: {team_name} not current period')
                

# joining the meeting
def join_meeting():
    global in_meeting

    while in_meeting == False:
        try:
            join_button = browser.find_element_by_css_selector("span[ng-if='!ctrl.roundButton']")
        except exceptions.NoSuchElementException:
            sleep(15)
            print(f"Debug: {current_period} meeting has not started")
        else:
            join_button.click()
            in_meeting = True
            print(f"Debug: In {current_period} meeting")
    sleep(2)
    video_button = browser.find_element_by_class_name('style-layer')
    mic_button = browser.find_element_by_xpath('//*[@id="preJoinAudioButton"]/div/button/span[1]')
    pre_join = browser.find_element_by_class_name('button-col')

    if video_button.get_attribute('title') == 'Turn camera off' and mic_button.get_attribute('title') == 'Mute microphone':
        video_button.click()
        mic_button.click()
        sleep(1)
        pre_join.click()
    elif mic_button.get_attribute('title') == 'Mute microphone' and video_button.get_attribute('title') == 'Turn camera on':
        mic_button.click()
        sleep(1)
        pre_join.click()
    elif mic_button.get_attribute('title') == 'Unmute microphone' and video_button.get_attribute('title') == 'Turn camera off':
        video_button.click()
        sleep(1)
        pre_join.click()
    else:
        sleep(1)
        pre_join.click()
    
    sleep(20)
    browser.find_element_by_xpath('//*[@id="roster-button"]').click() # clicking participants
    leave_meeting()


#leaving the meeting
def leave_meeting():
    global current_time
    current_time = datetime.now().strftime("%H:%M")

    while current_time < end_time[period_num-1]:
        members = browser.find_elements_by_class_name("roster-list-title")
        for name in members:
            if 'Attendees' in name.get_attribute('aria-label'):
                participants = int(name.get_attribute('aria-label')[-2:])
            else:
                participants = int(members[0].get_attribute('aria-label')[-2:])

        if participants > 20:
            print(f'Debug: {current_period} period if going on')
            sleep(60)
        else:
            print('Debug: Leaving in 10 seconds')
            sleep(10)
            click_leave()
        
        current_time = datetime.now().strftime("%H:%M")
    else:
        print('Debug: Leaving in 10 seconds')
        sleep(10)
        click_leave()


#clicking leave button
def click_leave():
    global leave_meeting

    try:
        leave_button = browser.find_element_by_xpath('//*[@id="hangup-button"]')
        browser.find_element_by_xpath('/html').click()
        sleep(2)
        leave_button.click()
        print('Debug: Clicked leave')
    except exceptions.NoSuchElementException:
        print('Debug: Meeting is over')
    finally:
        in_meeting = False
        get_period()

get_period()
