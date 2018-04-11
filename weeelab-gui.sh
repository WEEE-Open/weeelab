#!/bin/sh

LOGIN=0
LOGOUT=1
title="WEEElab"

# First screen (Login or Logout)
login_or_logout() {
  dialog --title $title --yes-label "Login" --no-label "Logout" --shadow \
  --yesno "Select an option" 5 25
}

# Input box for username
read_username() {
  dialog --title $title --inputbox "Type your serial number:" 8 40 2
}

login_or_logout
action=$?
read_username
user=$?

# Login
if [ $action == $LOGIN ]; then
  echo login $user
  # weeelab login $user
# Logout
else
  echo logout $user
fi
