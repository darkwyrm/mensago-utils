'''This module merely stores the extensive help text for different commands to 
ensure the code remains easy to read.'''

login_cmd = '''Usage: login [address]

Log into a server. The address used may be the regular Mensago 
address (catlover/example.com) or the workspace address 
(e.g. 557207fd-0a0a-45bb-a402-c38461251f8f). Because multiple domains could be 
hosted by the same server, it is necessary to give the entire workspace 
address. Note that if the address is omitted, the command is assumed to log 
into main account for the profile.

Examples:
login f009338a-ea14-4d59-aa48-016829835cd7/example.com
login CatLover/example.com
login
'''

logout_cmd = '''Usage: logout

Logs out of a server connection. This command does nothing and returns no 
error if not connected.
'''

preregister_cmd='''Usage: preregister <port_number> [user_id]

Preprovisions a workspace for a user. This command only works when logged in 
as the administrator. An optional user ID may be passed to the command. The
command returns a workspace ID and a preregistration code. The user will
perform the initial login with either the workspace ID or the user ID and the
registration code.
'''

profile_cmd = '''Usage: profile <action> <profilename>
Manage profiles. Actions are detailed below.

create <name> - create a new profile, which is just a name for identification
by the user. The profile may be named anything other than "default", which is
reserved. Profile names are case-sensitive, so "Default" is permitted. Note
that once created, it must be made active and either logging in or
registration is needed for the profile to be useful.

delete <name> - delete a profile and any files associated with it. Because it
cannot be undone, this command requires confirmation from the user.

rename <oldname> <newname> - change the name of a profile. Neither name may be
"default".

list - prints a list of all available profiles

setdefault <name> - sets the profile to be loaded on startup. If only one
profile exists, this action has no effect.

set <name> - activates the specified profile and deactivates the current one.'''

regcode_cmd = '''Usage: regcode <address> <code> [<password>]

Complete registration started by an administrator. This will involved setting 
a login password for the account. Like the `register` command, the desired 
password may be specified from the command line if shoulder-surfing is not a 
concern.
'''

register_cmd = \
'''Usage: register <domain> <name> userid=<userid> password=<password>

domain - The domain of the organization with which you wish to register.

name - Your name. Note that if you use first and last to enclose them in 
    double quotes, e.g. `register example.com "My Name"`. If set to None or
	none, no name will be assigned.

Register a new workspace account. This command requires a connection to a
server. A Mensago User ID may also be supplied. The workspace password may 
also be supplied on the command-line if shoulder-surfing is not a concern. 
Depending on the registration type set on the server, this command may return 
a status other than success or failure. If a server immediately creates a new 
workspace account, this command will print the new numeric address created.'''

resetdb_cmd = '''Usage: resetdb

WARNING: THIS COMMAND WILL CAUSE IRREVERSIBLE DATA LOSS. DO NOT RUN THIS UNLESS 
YOU KNOW WHAT YOU ARE DOING. Run this command at your own peril.

This developer command purges the Mensago database and resets it to a basic 
state of initialization. The server configuration is not changed. A new 
administrator account generated and the updated configuration is printed to 
the console. The workspace data hierarchy is also reset to a pristine state. 

NOTE: This command assumes you have filesystem permissions in the workspace 
directory hierarchy. Either run this utility with administrator permissions or 
set the filesystem permissions for the workspace directory accordingly.
'''

shell_cmd = '''Usage: shell <command>

Executes a command directly in the regular user shell. On Windows, this is 
Command Prompt. On UNIX-like platforms, this is the default shell, usually
bash.
Aliases: ` , sh'''

setinfo_cmd = '''Usage: setinfo <infotype> <value>

Sets contact information for the profile. Available information which can be 
set is listed below:
'''

setuserid_cmd = '''Usage: setuserid <userid>

Sets the user ID for the profile. This is the part before the slash in your 
Mensago address.

The user ID must be all one word -- no spaces -- but you may use any 
combination of letters, numbers, or symbols excluding the forward slash (/)
and double quote ("). You may also use non-English characters. It can be up to
128 characters, although user IDs of that length are not recommended.

Capitalization does not matter. If the user ID on your server is already
taken, you will need to choose another.

Once changed you will need to update your keycard.

Examples:

KingArthur
Аделина
Aslan_the_Lion
大和
karlweiß-52
'''
