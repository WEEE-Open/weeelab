#!/bin/bash

title="WEEElab"
backtitle="Team_WEEE_Open"

# First screen (Login or Logout)
login_or_logout() {
    dialog --title $title --backtitle $backtitle \
    --yes-label "Login" --no-label "Logout" --shadow \
    --yesno "Select an option" 5 25
    if [[ $? -eq 255 ]]; then # ESC
        exit 255
    fi
}

# Input box for username
read_username() {
    dialog --title $title --backtitle $backtitle \
    --inputbox "Type your username:" 8 40 2>/tmp/weeelab-gui-username.$$
    if [[ $? -ne 0 ]]; then # Cancel
        exit 1
    fi
    if [[ $? -eq 255 ]]; then # ESC
        exit 255
    fi
}

login_or_logout
action=$?

result=1337
while [[ $result -ne 0 ]]; do
    if [[ $action -eq 0 ]]; then
        read_username
        user=`cat /tmp/weeelab-gui-username.$$`
        rm /tmp/weeelab-gui-username.$$
        weeelab login $user
        result=$?
        if [[ $result -ne 0 ]]; then
            dialog --title $title --backtitle $backtitle \
            --msgbox 'ERROR: User not found! Retry' 6 20
        fi
    else
        read_username
        user=`cat /tmp/weeelab-gui-username.$$`
        rm /tmp/weeelab-gui-username.$$
        dialog --title $title --backtitle $backtitle \
        --inputbox "What have you done?" 8 80 2>/tmp/weeelab-msg.$$
        msg=`cat /tmp/weeelab-msg.$$`
        rm /tmp/weeelab-msg.$$
        weeelab logout $user \"$msg\"
        result=$?
    fi
done
