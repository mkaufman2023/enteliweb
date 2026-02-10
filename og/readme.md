# enteliSCRIPT

enteliSCRIPT is a scripting command shell for creating a device database. It uses enteliWEB's Interface Classs REST API to perform the commands.
THe API is a licensed feature of enteliWEB. Log in to enteliWEB and go to the Administration Support page to check *Web Services and Interface API* feature.

## Installation


#### enteliWEB - Web Services and Interface API
First off, ensure that your enteliWEB license has the -API option, as this is required for enteliSCRIPT.
This can be verified by looking at the Admin / Support page in enteliWEB.


#### Python 3.4 or higher
Go to https://www.python.org/downloads/ and download the latest Python 3.X.X

Run the installer. Choose 32bit or 64bit as appropriate.

During the install process, there is a checkbox option that says "add Python to Path".  
Check this, which will add the Python directories to the Windows Path, which is necessary for the command line tools to work.


#### Python *Requests* library
* Open a new DOS prompt
* Install command


    pip install requests


## Getting Start

Open a new DOS prompt

    python enteliSCRIPT.py


You can start issuing commands in the console.
Start by connecting to your enteliWEB server

    server 127.0.0.1 (or whatever your enteliWEB server address is)
    login
    setsite <Site Name>
    setdevice <Device Address>


To verify the connection

    list device


To create an object

    Create AV100 Room Set Point
    Modify AV100 Present_Value 22.2



## Commands

use ? to get available commands\
use ?<command> to get info on that command, example ?cr

#### Configuration


    server, login, setsite, setdevice, list, info, shell (!), help (?), bye

At any time use the command "info" to get your current connection state.


#### Operation

    create (CR), modify (MD), delete (DEL), command, setvar


#### File

    @filename, importcsv, exportcsv


#### Execute a saved script
Commands can be saved to a text file and executed by using the @ symbol.

    @filename


#### Import CSV
Multiple objects can be created by specifying their name and other property values in csv format.

    importcsv csvfilename


#### Export CSV
ExportCSV allows a user to output all objects of the same type in the current device in csv format.\
Users can specify addition properties to be included in the output.\
Note: Only top level properties are supported.

    exportcsv ai.csv AI Object_Name COV_Increment Description


#### Using Variables
Variables can be set to replace repeatedly used terms in script and csv

With the following create.txt

    create AI1 $ROOM (Temperature)
    create AI2 $ROOM (Humidity)
    create BI4 $ROOM (Motion)

The follow commands reuse create.txt for different room name

    setdevice 101
    setvar ROOM HeadQuarter Meeting Room 1
    @create.txt
    setdevice 102
    setvar ROOM HeadQuarter Meeting Room 2
    @create.txt

## Change Log

#### Version 1.1
  - Support TL Input_Ref
  - Preserve properties order in PutMultiProperty
#### Version 1.0
  - Initial Release.


## Development Info

python cmd console library:

  - https://wiki.python.org/moin/CmdModule
  - https://docs.python.org/3.4/library/cmd.html