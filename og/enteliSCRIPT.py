"""
enteliSCRIPT - Scripting command shell using enteliWEB BACnet WebService

Copyright (C) Delta Controls Inc. 2016
"""

# Python built-in modules
import sys
import csv
import cmd
import re
import os
import getpass
import datetime

# Third-party modules - may require the user to pip install
# <place here>

# Delta Controls modules
from . import common
from . import eweb_api
from . import enteliconfig as escfg

# ODBC
import pyodbc 


# Settings
SITE_NAME = "MainSite"
BASE_URL = "/enteliweb/api/.bacnet/"
SESSIONKEY = "enteliWebID"
SESSIONID = ""
CSRFTOKENKEY = "_csrfToken"
CSRFTOKEN = ""



class UnbufferedLogging(object):
    """
    Override the defalt python stdout to disable output buffering, and copy the output to a log file

    Credit to Magnus Lycka: https://mail.python.org/pipermail/tutor/2003-November/026645.html
    """
    def __init__(self, stream, file):
        self.stream = stream
        self.file = file
    
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
        self.file.write(data)
        self.file.flush()
    
    def __getattr__(self, attr):
        return getattr(self.stream, attr)





class enteliSCRIPT(cmd.Cmd):
    """
    enteliSCRIPT Console  
    Class for implementing the command shell

    See:
        - https://wiki.python.org/moin/CmdModule
        - https://docs.python.org/2/library/cmd.html
    """
    prompt = '$'
    intro = "enteliSCRIPT Delta Controls Inc. 2016 RP version: 2.03\r\n"
    vars = {}
    alias = {
        "cr": "create",
        "md": "modify",
        "mo": "modify",
        "de": "delete",
        "del": "delete",
        "sav": "savedb",
        "save": "savedb",
        "load": "loaddb",
        "saveobj": "save_objects",
        "loadobj": "load_object",
        "cp": "copy",
        "co": "copy",
        "cop": "copy",
        "exit": "bye"
    }
    doc_header = 'The available commands are'
    misc_header = 'misc_header'
    ruler = '-'

    def __init__(self, api: "eweb_api.EWEB_API"):
        """
        Basic initialization
        """
        self.eweb_api = api

        self.server = escfg.dftserver
        self.site = escfg.dftsite
        self.device = escfg.dftcp
        self.user = escfg.loginUN
        self.vars['$PROFILE'] = os.environ['USERPROFILE']

        super(enteliSCRIPT, self).__init__()


    def do_connect(self, line):
        """
        Auto find the current IP & use the predefined credentials to login to the enteliWEB API
        To update stored credentials edit enteliSCRIPT.py line 118 & 119
        Example:    connect
        """
        if (line == ""):
            # Custom code to enter in Technician local IP and login credentials
            import socket
            self.server = socket.gethostbyname(socket.gethostname())
            print("Server set to:" + self.server)
        
            username = escfg.loginUN
            password = escfg.loginUP
            result = self.eweb_api.Login(self.server, username, password)
        else:
            print("Invalid argument(s)")
            return
            
        if (result == True):
            self.user = username
            self.server = 'http://' + socket.gethostbyname(socket.gethostname())
            

    def parseReference(self, object):
        p = re.compile("(.*)([^0-9])([0-9]*)")
        p = p.match(object)
        if (p):
            return ((p.group(1) + p.group(2)).upper(), p.group(3))
        else:
            return None


    def do_setdevice(self, device):
        """
        Set the current device number
        Usage:      setdevice device
        Example:    setdevice 100
        """
        if (device == ""):
            print ("Current Device:", self.device)
            return

        self.device = device
        self.vars['$DEVID'] = device
        print ("Device set to:", device)


    def do_setsite(self, site):
        """
        Set the current site
        Usage:      setsite SiteName
        Example:    setsite MainSite
        """
        if (site == ""):
            print ("Current Site:", self.site)
            return

        self.site = site
        print("Current Site set to:", site)


    def do_create(self, line):
        """
        Create an Object

        Usage:      [create|cr] Object [object-name]
        Example:    create AI1 Meeting Room Temperature
                    cr AV1 Room Temp Setpoint
        """
        linecsv = line.split(";")
        lines = linecsv[0].split(' ', 1)
        if (len(lines) == 1 and lines[0] != ""):
            object = lines[0]
            name = object
        elif (len(lines) == 2):
            object = lines[0]
            name = lines[1]
        else:
            print ("Invalid argument(s)")
            return

        p = self.parseReference(object)
        if (p[0] in common.OBJECT_NAME_MAP):
            objectType = common.OBJECT_NAME_MAP[p[0]]
        else:
            print ("Unknown Object Type:", p[0])
            return
        """
        print(self.device,p[1],name)
        self.eweb_api.CreateObject(self.server, self.site, self.device, objectType, p[1], name)
        """

        if (len(linecsv) < 1):
            self.eweb_api.CreateObject(self.server, self.site, self.device, objectType, p[1], name)
            return
        else:
            propertyValueDict = {}
            for propValue in linecsv:
                regel = propValue.split()
                if (len(regel) < 1):
                    print ("Invalid argument(s)")
                else:
                    if regel[0] == object:
                        property = regel[1]
                        value = ' '.join(regel[2::])
                    else:
                        property = regel[0]
                        value = ' '.join(regel[1::])
                        propertyValueDict[property] = value
            """
            print ("CR ",self.device,objectType,p[1],propertyValueDict)
            result = self.eweb_api.PutMultiProperty(self.server, self.site, self.device, objectType, p[1], propertyValueDict)
            """
            self.eweb_api.CreateObjectM(self.server, self.site, self.device, objectType, p[1], name, propertyValueDict)


    def do_delete(self, line):
        """
        Delete an Object
        Usage:      [delete|de|del] Object
        Example:    delete AI1
                    del AO1
        """

        lines = line.split(' ', 1)
        if (len(lines) == 1):
            object = lines[0]
        else:
            print ("Invalid argument(s)")
            return

        p = self.parseReference(object)
        if (p[0] in common.OBJECT_NAME_MAP):
            objectType = common.OBJECT_NAME_MAP[p[0]]
        else:
            print ("Unknown Object Type:", p[0])
            return

        self.eweb_api.DeleteObject(self.server, self.site, self.device, objectType, p[1])
        

    def do_copy(self, line):
        """
        Delete an Object
        Usage:      [copy|co|cp] Object|toObjectInstance
        Example:    copy AI1|12|Name
                    cp AO1|1201|Name
        """

        lines = line.split('|', 3)
        if (len(lines) == 3):
            object = lines[0]
            toInstance = lines[1]
            name = lines[2]
        else:
            print ("Invalid argument(s)")
            return

        p = self.parseReference(object)
        if (p[0] in common.OBJECT_NAME_MAP):
            objectType = common.OBJECT_NAME_MAP[p[0]]
        else:
            print ("Unknown Object Type:", p[0])
            return

        self.eweb_api.CopyObject(self.server, self.site, self.device, objectType, p[1], toInstance, name)


    def do_modify(self, line):
        """
        Modify Object Property
        Usage:      [modify|md|mo] Object Property Value
        Example:    modify AO1 Object_Name FAN_STATUS
                    md AI1 COV_Increment 0.1
        """
        linecsv = line.split(";")
        lines = line.split()
        if (len(lines) < 3):
            print ("Invalid argument(s)")
            return
        if ((len(lines) > 2) and (len(linecsv) < 1)):
            object = lines[0]
            property = lines[1]
            value = ' '.join(lines[2::])
            p = self.parseReference(object)
            if (p[0] in common.OBJECT_NAME_MAP):
                objectType = common.OBJECT_NAME_MAP[p[0]]
            else:
                print ("Unknown Object Type:", p[0])
                return
            print (self.device,p[1],property,value)
            self.eweb_api.PutProperty(self.server, self.site, self.device, objectType, p[1], property, "String" , value)
        else:
            propertyValueDict = {}
            object = lines[0]
            p = self.parseReference(object)
            if (p[0] in common.OBJECT_NAME_MAP):
                objectType = common.OBJECT_NAME_MAP[p[0]]
            else:
                print ("Unknown Object Type:", p[0])
                return

            for propValue in linecsv:
                regel = propValue.split()
                if (len(regel) < 1):
                    print ("Invalid argument(s)")
                else:
                    if regel[0] == object:
                        property = regel[1]
                        value = ' '.join(regel[2::])
                    else:
                        property = regel[0]
                        value = ' '.join(regel[1::])

                propertyValueDict[property] = value
            """
            print ("MO ",self.device,objectType,p[1],propertyValueDict)
            """
            result = self.eweb_api.PutMultiProperty(self.server, self.site, self.device, objectType, p[1], propertyValueDict)
            
            
    def do_command(self, line):
        """
        Command Object to Auto
        Usage:      command object Auto
        Example:    command AO1 Auto
        """

        lines = line.split()
        if (len(lines) != 2):
            print ("Invalid argument(s)")
            return
        object = lines[0]
        command = lines[1]

        p = self.parseReference(object)
        if (p[0] in common.OBJECT_NAME_MAP):
            objectType = common.OBJECT_NAME_MAP[p[0]]
        else:
            print ("Unknown Object Type:", p[0])
            return

        if (command.lower() == "auto"):
            self.eweb_api.PutProperty(self.server, self.site, self.device, objectType, p[1], 'Manual_Override', "Null" , "")
            print ("Command ", p, ' ', command)
        else:
            print ("Unsupported Command:", command)


    def do_importcsv(self, line):
        """
        Import CSV file to create multiple objects
        Usage:      importcsv filename
        Example:    importcsv inputs.csv

        CSV Format: device, object-type, instance, object-name [,Property1] [,Property2] ...
        Example:
        device, object-type,  instance, object-name, description,      cov-increment, manual-override
        5700,   analog-value, 1000,     NewObject1,  Description blah, 0.1,           1
        5700,   analog-value, 1001,     NewObject2,  Description blah, 0.1,           2

        Note: The first 4 columns are mandatory
        """

        lines = line.split()
        if (len(lines) != 1):
            print ("Invalid argument(s)")
            return
        filename = lines[0]

        print ("Creating Object...")
        if (os.path.isfile(filename) == False):
            print ("File " + filename + " does not exist")
            return

        nameTitles = ['Object_Name', 'object-name']
        requiredFields = ['object-type', 'instance']
        with open(filename, 'r', encoding = "utf-8-sig") as csvfile:
            # Read the csv file to create object and update the properties
            reader = csv.DictReader(csvfile)
            for field in requiredFields:
                if (field not in reader.fieldnames):
                    print(field + " missing from " + filename)
                    return
            try:
                for row in reader:
                    #Apply variables
                    for item in row:
                        for var in self.vars:
                            row[item] = row[item].replace(var, self.vars[var])

                    #If device column is specified, use it, otherwise use the global device
                    if ('device' in row and row['device'] != ''):
                        device = row['device']
                    else:
                        device = self.device

                    name = ""
                    for nameTitle in nameTitles:
                        if (nameTitle in row):
                            name = row[nameTitle]
                            break
                    result = self.eweb_api.CreateObject(self.server, self.site, device, row['object-type'], row['instance'], name)
                    propertyValueDict = {}
                    for property in row:
                        if (property not in ['device', 'instance', 'object-type'] + nameTitles):
                            propertyValueDict[property] = row[property]
                    result = self.eweb_api.PutMultiProperty(self.server, self.site, device, row['object-type'], row['instance'], propertyValueDict)
            except csv.Error as e:
                print ('file %s, line %d: %s' % (filename, reader.line_num, e))


    def do_exportcsv(self, line):
        """
        Export the specified properties of the specified objecttype to a csv file (primitive top level properties only)
        Usage:      exportcsv filename object-type [properties|...]
        Example:    exportcsv ai.csv AI Object_Name COV_Increment Present_Value
                    exportcsv ai.csv AI object-name cov-increment present-value
        """

        lines = line.split()
        if (len(lines) < 2):
            print ("Invalid argument(s)")
            return
        filename = lines[0]
        objectType = lines[1]

        if (objectType in common.OBJECT_NAME_MAP):
            objectType = common.OBJECT_NAME_MAP[objectType]

        propertyList = lines[2:]

        print ("Exporting Object...")

        result = self.eweb_api.GetObjects(self.server, self.site, self.device)

        instanceList = []
        for key in result:
            if (key.find(objectType+',') == 0):
                instance = key.strip(objectType + ',')
                instanceList.append(instance)

        instanceList = sorted(instanceList, key=common.custom_key)
        try:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['device','object-type','instance'] + propertyList
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for instance in instanceList:
                    #print(objectType + ", " + instance + ":")
                    result = self.eweb_api.GetMultiProperty(self.server, self.site, self.device, objectType, instance, propertyList)
                    #for k, v in result.items():
                    #    print("    " + k + ":" + v.encode('cp850','replace').decode('cp850'))
                    result['device'] = self.device
                    result['object-type'] = objectType
                    result['instance'] = instance
                    writer.writerow(result)

        except IOError as e:
            print (filename + ":" + e.strerror)
        except Exception as e:
            print ("Unhandled exception while exporting csv: %s" % e)


    def do_list(self, line):
        """
        List sites or devices in the current site
        Usage:      list sites|devices
        Example:    list devices
        """

        if (line in ['device', 'devices']):
            devices = self.eweb_api.GetDevices(self.server, self.site)
            for device in devices:
                print ('        ' + device)
        elif (line in ['site', 'sites']):
            sites = self.eweb_api.GetSites(self.server)
            for site in sites:
                print('        ' + site)
        else:
            print("Invalid argument: " + line)
            print("See ?list")
            
            
    def do_savedb(self, line):
        """
        Saves the currect device database to a file
        Example:    savedb C:\enteliscript - Saves to specified path
        Example:    savedb - Saves to default python directory
        """
        sPath = line
        self.eweb_api.SaveDB(self.server, self.site, self.device, sPath)
        

    def do_loaddb(self, line):
        """
        Loads a database file in to the current device
        Example:    loaddb C:\enteliscript\device.zdd
        Example:    load device.zdd
        """
        file = line
        #print(file)
        self.eweb_api.LoadDB(self.server, self.site, self.device, file)


    def do_loadpg(self, line):
        """
        loads the text file in the PG object
        Example:    loadpg pg12|C:\enteliscript\pg2.txt
        Example:    loadpg 
        """
        lines = line.split("|",2)
        if (len(lines) != 2):
            print ("Invalid argument(s)")
            return
        file = lines[1]
        object = lines[0] 
        print(file)
        self.eweb_api.LoadPG(self.server, self.site, self.device, object, file)
        

    def do_save_objects(self, line):
        """
        saves objects
        Example:    save_objects AI12;BI;EV12
        Example:    saveobj AI12
        
        """
        lines = line.split()
        if (len(lines) != 1):
            print ("Invalid argument(s)")
            return

        self.eweb_api.SaveObj(self.server, self.site, self.device, line)


    def do_load_object(self, line):
        """
        Example:    load_object instance|file ref|object name
        Example:    load_objects 12|aaa.zob|newobjectname
        Example:    loadobj 12|aaa.zob|newobjectname
        
        """
        lines = line.split('|',2)
        #print (lines)
        if (len(lines) != 3):
            print ("Invalid argument(s)")
            #return
        else:
            object = lines[0]
            name = lines[2]
            file = lines[1]
            self.eweb_api.LoadObj(self.server, self.site, self.device, object, name, file)


    def do_server(self, line):
        """
        Set the server address to connect to
        Usage:      server http://xxx.xxx.xxx.xxx
        Example:    server https://rd-enteliweb-t2
        """

        if (line == ""):
            print (self.server)
        else:
            #trim extra "http://", and trim extra "/enteliweb"
            #line = line.replace("http://", "")
            #line = line.replace("https://", "")
            #line = line.replace("/enteliweb", "")
            self.server = line
            print ("Server set to:" + self.server)


    def do_login(self, line):
        """
        Login to the server
        Usage:      login [username] [password]
        Example:    login
                    login Admin
                    login Admin demopassword
        """

        lines = line.split(' ' , 2)

        if (len(lines) == 2):
            # Both username and password are specified
            username = lines[0]
            password = lines[1]
        elif (len(lines) == 1 and lines[0] != ""):
            # Only username specified
            username = lines[0]
            password = getpass.getpass("Password:")
        else:
            # None specified, prompt for both
            username = input("Username:")
            password = getpass.getpass("Password:")

        result = self.eweb_api.Login(self.server, username, password)
        if (result == True):
            self.user = username


    def do_info(self, line):
        """
        Show the current setup info
        Usage: info
        """

        print ("Server       :" + self.server)
        print ("Site         :" + self.site )
        print ("Device       :" + self.device)
        if (self.user == ""):
            print ("User         :Not Login" + self.user)
        else:
            print ("User         :" + self.user + "(" + SESSIONID + ")")

        if (len(self.vars) > 0):
            print ("-Variables-")
            for var in self.vars:
                print(var + (" " * max(0, 9-len(var))) + ":" + self.vars[var])


    def do_setvar(self, line):
        """
        Set variable value to be used in script or csv ($varName)
        Usage:      setvar VARNAME VARVALUE
        Example:    setvar ROOM HQ Conference Room
                    create AV1 $ROOM Setpoint
                    setvar ROOM (will erase the variable ROOM)
        """

        lines = line.split(' ', 1)
        if (len(lines) == 1 and lines[0] != ""):
            var = '$' + lines[0]
            if (var in self.vars):
                vars.remove(var)
        elif (len(lines) == 2):
            var = '$' + lines[0]
            value = lines[1]
            self.vars[var] = value
        else:
            print ("Invalid argument(s)")
            return


    def do_help(self, arg):
        """
        Show Help
        """

        cmd.Cmd.do_help(self, arg)
        if (arg == None):
            print ("@filename     - excutes the script file")
            print ("?command        - shows detail help\r\n")


    def do_exportpg(self, line):
        """
        Export one or more programs to text file
        Usage:      This command will export program files to text file
            Using zero for the program instance will export all programs to text
            exportpg Low_Instance|High_Instance|Folder_Path
        Example:    exportpg 1|10|C:
        """

        lines = line.split('|')
        if (len(lines) != 3):
            print ("Invalid argument(s)")
            return
        path = lines[2]
        path = r"C:\Users\PRamsey\Desktop\test"
        lowid = lines[0]
        highid = lines[1]

        site = self.site
        username = self.user
        con=pyodbc.connect('DSN=Delta ODBC 4', autocommit=True)
        cursor = con.cursor()
        
        if (lowid == "0"):
            sql = "Select INSTANCE, Object_Name, Program_Code From OBJECT_V4_PG Where (SITE_ID = '" + site + "') and (DEV_ID = "+ self.device + ")"
        else:    
            sql = "Select INSTANCE, Object_Name, Program_Code From OBJECT_V4_PG Where (SITE_ID = '" + site + "') and (DEV_ID = "+ self.device + ") and (INSTANCE between " + lowid + " and " + highid + ")"
            print (sql)
        cursor.execute(sql)

        for row in cursor:
            #CD into directory
            outputpath = path + str(self.device) + '_PG' + str(row[0]) + '_' + str(row[1]) + '.txt'
            with open(outputpath, "w", newline='') as f:
                print(row[2], file=f)
            f.close()

        # Close and delete cursor
        cursor.close()
        del cursor

        # Close Connection
        con.close()
        print ('ok')


    def do_replace(self, line):
        """
        replace string in multiple objects
        replace BO,AO,AI|Description|searchstring|replacestring
        replace object|property|search|replace
        replace BO|Description|AHU01|AHU05
        """
        lines = line.split('|')
        #for line in lines:
        #    print ("\n " ,line)
                   
        if (len(lines) == 4 and lines[0] != ""):
            objects =  lines[0]
            prop = lines[1]
            search = str(lines[2])
            replace = str(lines[3])
        else:
            print ("Invalid argument(s)")
            return

        objects = lines[0].split(',')

        site = self.site
        username = self.user
        con=pyodbc.connect('DSN=Delta ODBC 4', autocommit=True)
        cursor = con.cursor()

        for object in objects:
            sql = 'Update OBJECT_V4_' + object + ' SET  ' + prop + " = Replace(" + prop + ",'" + search + "', '" + replace + "') Where SITE_ID= '" + self.site + "' and DEV_ID= "+ self.device + " and " + prop+ " like '%" + search + "%'"
            print ("\n SQL: ",sql)
            cursor.execute(sql)
                         
            if (prop == "Description"):
                sql = 'Update ARRAY_V4_' + object+ "_Event_Message_Texts_Config  SET  Event_Message_Texts_Config = Replace(Event_Message_Texts_Config,'" + search + "', '" + replace + "') Where objRef like '" + self.device + ".%' and Event_Message_Texts_Config like '%" + search + "%'"
                print ("\n SQL: ",sql)
                cursor.execute(sql)
             
        # Close and delete cursor
        cursor.close()
        del cursor

        # Close Connection
        con.close()
        print ('ok')


    def do_replace_in_pg(self, line):
        """
        Use this to replace programming code in a single program
        replace_in_pg instance searchstring replacestring
        replace_in_pg 4|Room|Space
        Use pipe to seperate instance|search|replace
        Use zero instead of a specific instance to update all programs
        """
        lines = line.split('|')
        #for line in lines:
        #    print ("\n " ,line)
                   
        if (len(lines) == 3 and lines[0] != ""):
            instance = lines[0]
            search = str(lines[1])
            replace = str(lines[2]) 
        else:
            print ("Invalid argument(s)")
            return

        site = self.site
        username = self.user
        con=pyodbc.connect('DSN=Delta ODBC 4', autocommit=True)
        cursor = con.cursor()
        
        if (instance == "0"):
            sql = "Update OBJECT_V4_PG SET Program_Code = Replace( Program_Code , '" + search + "', '" + replace + "') Where (SITE_ID = '" + site + "') and (DEV_ID = "+ self.device + ")"
        else:    
            sql = "Update OBJECT_V4_PG SET Program_Code = Replace( Program_Code , '" + search + "', '" + replace + "') Where (SITE_ID = '" + site + "') and (DEV_ID = "+ self.device + ") and (INSTANCE = " + instance + ")"
        print ("\n SQL: ",sql)
        #print ("\n " ,sql)
        cursor.execute(sql)
        #for r in cursor:
        #    print(r)
             
        # Close and delete cursor
        cursor.close()
        del cursor

        # Close Connection
        con.close()
        print ('ok')


    def do_shell(self, line):
        """
        Run a shell command
        Usage:      shell|! [shellcommand]
        Example:    ! dir
                    ! del test.txt
        """

        print("running shell command:", line)
        output = os.popen(line).read()
        print(output)
        self.last_output = output


    def do_cwd(self, line):
        """
        Run a shell command
        Usage:      shell|! [shellcommand]
        Example:    ! dir
                    ! del test.txt
        """

        #if (lines[0] != ""):
            #self.eweb_api.directory(lines[0])
        #else
            #print("invalid:",line)
            #return    


    def do_pause(self, arg):
        """
        wait for enter
        Usage:      pause
        Example:    pause
        """
        input("Press Enter to continue...")


    def do_bye(self, line):
        """
        Exit
        """

        return True


    def default(self, line):
        # Special handling of @, to load and execute a stored script
        if (line[0] == "@"):
            filename = line[1:]
            if (not os.path.isfile(filename)):
                print ("File " + filename + " not found")
                return
            #file = open(filename, 'r', encoding = "utf-8-sig")
            file = open(filename, 'r')
            for line in file:
                if line[0] == "#":
                    continue
                print (line.strip('\n')) # Print the command
                print ("        ", end="")                     # Indent the output
                line = self.precmd(line)
                cmd.Cmd.onecmd(self, line)
            file.close()
        else:
            return cmd.Cmd.default(self, line)


    def precmd(self, line):
        #Handle upper case command
        lines = line.split(' ', 1)
        lines[0] = lines[0].lower()

        for k in self.alias:
            if (lines[0] == k):
                lines[0] = self.alias[k]
        lines[0] += ' '
        line = "".join(lines, )
        #Do search and replace on var
        for var in self.vars:
            line = line.replace(var, self.vars[var])

        return cmd.Cmd.precmd(self, line)


    def emptyline(self):
        self.do_help(None)





def main():
    """
    Main routine

    The enteliSCRIPT shell accepts an API as one of its arguments
    By default, this is the EWEB API, however, as long as the API provides the same interface as the
    EWEB API, then it should still work as expected
    """

    if sys.hexversion < 0x03040000:
        sys.exit("Python 3.4 or newer is required to run this program.")

    clear = lambda: os.system('cls')
    clear()
    api = eweb_api.EWEB_API(SESSIONKEY, CSRFTOKENKEY, BASE_URL)
    shell = enteliSCRIPT(api)

    if (len(sys.argv) > 1):
        inputfile = sys.argv[1]
        shell.cmdqueue.append("@" + inputfile)

    shell.cmdloop()





if __name__ == "__main__":
    
    # Copy the console output to a log file
    TimeStamp = datetime.datetime.now().strftime("%d%m%y_%H%M%S")
    LogFile = os.path.join("Log", "%s_%s.log"%(os.path.basename(__file__), TimeStamp))
    
    # If the Log folder doesn't exist create it
    if not os.path.exists("Log"):
        os.mkdir("Log")
    
    f = open(LogFile, "w")
    sys.stdout = UnbufferedLogging(sys.stdout, f)
    
    # Run enteliSCRIPT
    try:
        main()
    except:
        e = sys.exc_info()[1]
        print (e)

    # close the log file
    f.close()
