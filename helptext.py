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

myinfo_cmd = '''Usage: myinfo <verb> <fieldname> <value>

Sets contact information for the profile. Available information which can be 
set is listed below:

FormattedName     GivenName         FamilyName        Nicknames+
AdditionalNames+  Prefix            Suffixes+         Gender
Social+           Mensago+          Bio               MailingAddresses+
Phone+            Anniversary       Birthday          Email+
Organization+     Title             Categories+       Websites+
Photo             Languages+        Notes             Attachments+
Custom+

Fields ending with a + are lists of multiple values.

Verbs used are `set`, `get`, `del`, and `check`. `get`, which is also performed
if no verb is specified, displays the value of a specific field. If no field
is specified, all fields are displayed. `del` deletes a field. `set` adds or
changes fields. `check` takes no arguments; it merely checks to make sure that
all personal information fields are valid and that no required fields are
missing. Values which have spaces must be enclosed by double-quotes (").

Detailed information fields can be found in the `myinfo_fields` topic.
'''

myinfo_fields = '''All fields are optional with the exception of
Mensago.<index>.Workspace and Mensago.<index>.Domain.

FormattedName - a person's first and last names with prefixes/suffixes

GivenName, FamilyName - in the US, a person's first and last names

Nicknames.<index> - a list of nicknames for the entity.

AdditionalNames.<index> - a list of additional names for an entity. For many,
  this is a person's middle name or names.

Prefix - A prefix for an entity, such as 'Dr' or 'Ms'.

Suffixes - A list of suffixes for an entity, such as 'Jr' or 'MD'

Gender - A freeform text field for the entity's gender

Social.<index>.Label - The name of a social media account. If used, the
  corresponding Value field is required

Social.<index>.Value - The URL of a social media account profile page. If a
  network does not provide profile pages, this should contain the user's handle.
  If used, the corresponding Label field is required.

Mensago.<index>.UserID - The alphanumeric 'friendly' part of an entity's Mensago
  address.

Mensago.Workspace - REQUIRED. The UUID identifier for an entity's address

Mensago.Domain - REQUIRED. The domain part of an entity's Mensago address

Bio - a short blurb of biographical information
'''

myinfo_fields2 = '''MailingAddresses - A dictionary of dictionaries of mailing address
  information. The name of the dictionary can have a * added to the end to
  indicate the preferred address.

MailingAddresses.<name>.POBox - Postal office box

MailingAddresses.<name>.StreetAddress - An entity's street address

MailingAddresses.<name>.ExtendedAddress - A second address line. Suite and
  apartment numbers typically use this line.

MailingAddresses.<name>.Locality - Usually the city in which the entity is
  located.

MailingAddresses.<name>.Region - In the US, this is the state in which the
  entity is located.

MailingAddresses.<name>.PostalCode - Postal office code for the address

Phone - An dictionary of phone numbers. The name of the key can have a *
  added to the end to indicate the preferred address.

Anniversary, Birthday - Dates in the format YYMMDD or MMDD.

Email - An dictionary of e-mail addresses. The name of the key can have a *
  added to the end to indicate the preferred address.

Organization.Name - The name of the organization.

Organization.Units - A list of units indicating hierarchy in the organization.
'''

myinfo_fields3 = '''Title - The entity's business title

Categories - A list of categories into which the entity has been grouped

Websites.<index>.Label - The name or type of website. If used, the corresponding
 Value field is required.

Websites.<index>.Value - The URL of the website. If used, the corresponding
 Label field is required.

Photo - a JPEG, PNG, or WEBP no larger than 500KiB. The `myinfo` command
  expects a file path to add or set this field.

Languages - a list of languages in ISO 639-3 format. A list of languages can
  be found at https://en.wikipedia.org/wiki/ISO_639-3 .

Notes - Freeform notes about the entity.

Attachments - A list of file attachments. The `myinfo` command expects a file
  path to add or set this field.

Custom - A dictionary of string fields.
'''

preregister_cmd='''Usage: preregister user_id [domain]

Preprovisions a workspace for a user. This command only works when logged in 
as the administrator. The user ID parameter is required, but it may be given 
a specific workspace ID if desired or set to `None` if an autogenerated 
workspace ID is acceptable. The domain may also be specified. If not specified
the default domain for the organization is used. The command returns a
workspace ID and a preregistration code. The user will perform the initial
login with either the workspace ID or the user ID and the registration code.
'''

profile_cmd = '''Usage: profile <action> <profilename>
Manage profiles. Actions are detailed below.

create <name> - create a new profile, which is just a name for identification
by the user. Profile names are not case-sensitive. Note that once created, it 
must be made active in order to interact with it. Each profile may have only 
ONE identity associated with it. Profile names may NOT contain whitespace or 
any of the following characters: < > : " ' / \ | ? *

delete <name> - delete a profile and any files associated with it. Because it
cannot be undone, this command requires confirmation from the user.

rename <oldname> <newname> - change the name of a profile.

list - prints a list of all available profiles

setdefault <name> - sets the profile to be loaded on startup. If only one
profile exists, this action has no effect.

set <name> - activates the specified profile and deactivates the current one.

get - displays the current profile's name and associated Mensago address. If
the profile command is issued without an action, this one is assumed.'''

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
