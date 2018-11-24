[[https://github.com/clarson00/cisco-config/blob/master/bob.jpg|alt=bob]]
# bancit.py - "Bobs" Awesome Network Configuration Implementation Tool
The bancit tool takes a CSV file of devices and configurations and pushes the them to the respective devices. The CSV file can be constructed in excel where each column is a single device with the first row in the column being the device name, the second row in the column being a reachable IP to send the configs over, and the 3rd row and beyond containing a configuration command per line. This is much like copying a cisco config into notepad for pasting into a device where each line is a configuration command except here line 1 should be the device name,  line 2 should be the device IP, and line 3 and beyond the commands to send to the device with each column being a different device.

This allows a person to configure several devices from one spreadsheet. We can include all the commands and any verification testing like sh int status, sh ip bgp, sh cdp neigh, etc. 

What I do for my changes is to create 2 spreadsheets. One is a pre/post implementation which backs up configs and runs sh ip route, or sh ip bgp, or sh int status, etc. whatever on the devices I am changing as well as any neighboring devices I need to check. Then I have my other spreadsheet which is just the actual changes.

I run the pre/post csv through the bancit.py script saving to a PRE-CHANGE directory. Then I run my implementation csv through the script and save to an IMPLEMENTATION directory. Lastly, I re-run the pre/port implementation CSV and save to a POST directory.

Once I am done, I use the proveit.py script to load up all the files in the PRE and POST directories side by side in excel with each device having its own tab. This allows me to compare the before and after. Using proveit.py with the -c switch will automatically compare the files and highlight the differences between the pre and post files right in the spreadsheet using different colored text to note additions, removals, changes between the pre and post files.

Future updates will allow the script to except a spreadsheet of devices and configure them via SSH (like it does now), or NETCONF, RESTCONF, or other API. In addition, I will add modules for Checkpoint, Fortigate, and other devices.
