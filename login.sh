#!/bin/bash
RETURNED=1337
while [[ $RETURNED -ne 0 ]]; do
	echo "Type your name.surname OR id (matricola) without initial 's' OR nickname:"
	read name
	weeelab login $name
	RETURNED=$?
done

