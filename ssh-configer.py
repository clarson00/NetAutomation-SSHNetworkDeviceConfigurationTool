import csv
import os.path
import optparse
import sys
import platform
import subprocess
import paramiko
import threading
import time
import re
import getpass

def process_command_line(argv):
    global mode
    global directory


    class MyParser(optparse.OptionParser):
        def format_epilog(self, formatter):
            return self.epilog


    usage = '\n%prog list_file <options>\n'
    desc= 'This script accepts a CSV file of devices and the commands to send to the devices. File can be constructed in excel as follows: '\
    'Each column in the spreadsheet is a single device. '\
        'The first row should be the hostname.'\
        'The second row should be the IP.'\
        'All subsequent rows in a column can be command line argurmants to be sent to the device in the column.'\
        'Each devices output is logged to a separate file. '\


    parser =MyParser('\n'+usage,description=desc,epilog="""\nExamples:

    'ssh-config.py devices.csv'
    For every device in IP_list.txt execute the commands in the backup.txt file


    """)


    parser.add_option("-d",
                  action="store", dest="directory",
                  help="Use this directory for output")

    parser.add_option('-o',
                      type='choice',
                      action='store',
                      dest='mode',
                      metavar="OUTPUT_MODE",
                      choices=['IP', 'NAME',],
                      default='IP',
                      help=' Commands file output naming mode. IP = use IP in filename. NAME = use hostname in filename. Default is to use IP',)





    options, args = parser.parse_args()

### Set the directory to current directory unless option is set
    directory = os.getcwd()


    if options.directory != None:
        directory = options.directory

    if not os.path.exists(directory):
        os.makedirs(directory)

    if options.mode == "IP":
        mode = "IP"
    if options.mode == "NAME":
        mode = "NAME"







    return options, args

def open_file(args=None):
    # Create empty lists
    devices=[]
    devices1=[]

    if not args:
        file = raw_input("What is the path/filename?")
    else:
        file=args[0]

    try:
        with open(file) as csvfile:
            reader = csv.reader(csvfile, delimiter = ',', quotechar= '|')
            configs = list(reader)
            counter = len(configs[0]) -1
            #print configs

#Re-order from a list of rows into a list of columms. So now it will be 1 Device and config per row.

        while counter >= 0:
            for i in configs:
                device=i[counter]
                if device !="":
                    devices1.append(device.strip())
            counter -=1
            devices.append(devices1)
            devices1=[]
        csvfile.close()

    except IOError:
        print "\n* File %s does not exist! Please check and try again!\n" % file
        exit()

    devices.reverse()
    return devices



def is_valid_ip(ip):
    check = False
    a = ip.split('.')

    # print "This is ip in list: %s" % a
    if (len(a) == 4) and (1 <= int(a[0]) <= 223) and (int(a[0]) != 127) and (int(a[0]) != 169 or int(a[1]) != 254) and (0 <= int(a[1]) <= 255 and 0 <= int(a[2]) <= 255 and 0 <= int(a[3]) <= 255):
        check = True
    else:
        check = False

    return check



###### Open SSHv2 connection to devices and run command in command file
def open_ssh_conn(ip):
    #username=''
    #password=''
    #print ip
    err=[]

    try:

        session = paramiko.SSHClient()

        #This allows auto-accepting unknown host keys
        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        session.connect(ip[1], username=username, password=password)
        connection = session.invoke_shell()
        print "router %s config" % ip[0]

        #Setting terminal length for entire output - disable pagination
        connection.send("terminal length 0")
        connection.send("\n")

        #Entering enable mode
        connection.send("\n")
        connection.send("enable\n")
        connection.send(password + "\n")
        time.sleep(1)



        #Read commands from the list and send to device

        cmds = ip[2:]

        for x in cmds:
            connection.send(x + '\n')
        time.sleep(1)
        router_output = connection.recv(131072)

        print "****   Begin Configuration for: %s    ****\n"  %ip[0]
        print router_output
        print "\n****  Configuration for: %s  - Complete   ****" % ip[0]
        if re.search(r"% ", router_output) or re.search(r"Bad mask /", router_output):
            print "*** There was at least one IOS syntax error on device %s ***" % ip[0]
            errmsg = "Device Named: %s with IP: %s is believed to have errors. Please check the implementation log" % (ip[0],ip[1])
            err.append(errmsg)
        print "\n\n"


#log the router output to a file
        if mode =="IP":
            name_of_file = os.path.join(directory,ip[1] + "_"+ "log.txt")
        if mode=="NAME":
            name_of_file = os.path.join(directory,ip[0] + "_"+ "log.txt")
        filer = open( name_of_file , 'w+')
        filer.write(router_output)
        filer.close()

#update the session log (TO-DO. Cappture all the lines/copnfigs with errors or any errors and add to sessions log.

        #Closing the connection
        session.close()

        for x in err:
            print x


    except paramiko.AuthenticationException:
        print "* Invalid username or password. \n* Please check the username/password file or the device configuration!"
        print "* Closing program...\n"


    return

############# Check reachability function #############

def reachable(x):

    print "\n* Checking IP reachability. Please wait...\n"
    check2 = False
    print platform.system()

    for ip in x:

        ip  = ip[1].rstrip('\n')



        if platform.system() == "Windows":
            ping_reply = subprocess.call(['ping', '-n', '2', '-w', '2', ip])

        if platform.system()=="Linux":
            ping_reply = subprocess.call(['ping', '-c', '2', '-w', '2', ip])



        if ping_reply == 0:
            check2 = True
            continue

        elif ping_reply == 2:
            print "\n* No response from device %s." % ip
            check2 = False
            break

        else:
            print "\n\n# # # # # # # # # # # # # # # # # # # # # # # # # # # #\n"
            print "Ping to the following device has FAILED:", ip
            print "Please check reachability or IP and try again"
            print "\n# # # # # # # # # # # # # # # # # # # # # # # # # # # #\n\n\n"

            check2 = False
            sys.exit()

    if check2 == True:
        print '\n\n\n*** All devices are reachable....\n'

############# Mutlithread the task so many devices can be done in parallel #############

def create_threads(configs):
    threads = []
    for ip in configs:
        #ip = ip[1].rstrip("\n")
        th = threading.Thread(target = open_ssh_conn, args = (ip,))   #args is a tuple with a single element
        th.start()
        threads.append(th)

    for th in threads:
        th.join()

##### Get user login information
def user_creds():
    global username
    global password

    username = raw_input("username: ")
    password = getpass.getpass("password: ")



def main(argv=None):
    options, args = process_command_line(argv)
    configs=open_file(args)
    #clean_data(configs)
    for i in configs:
        if is_valid_ip(i[1]) == True:
            print "%s is a valid IP" % i[1]
        else:
           print "%s is NOT a valid IP. Please check configs and try again." % i[1]
           exit()

### Does user want to check reachability of IP? Is so, call reachable function
    while True:
        do_ping = raw_input("\n\n# Check Reachability via ping?: (Y)es/(N)o/(Q)uit ")
        try:
            if do_ping[:1].lower() == "y":
                reachable(configs)
                break
            elif do_ping[:1].lower() == "n":
                print "Reachability check skipped\n"
                break
            elif do_ping[:1].lower() =="q":
                print "Exiting per user request\n"
                sys.exit()

        except KeyboardInterrupt:
            print "\n\n* Program aborted by user. Exiting...\n"
            sys.exit()


    user_creds()
    create_threads(configs)

    return 0


if __name__ == "__main__":
    status=main()
    sys.exit(status)
