Hi all,

Well that title is a slight long-winded mouth full!  But Announcing a new Plugin:

This is a plugin for a range of [size=150]Linksys/Cisco/Sipura VOIP Adapters[/size]:  Like this one:
![](http://www.aroundtheglobe.biz/wp-content/uploads/2013/07/Linksys_Sipura_SPA_3000-640x280.png)

These are stand-alone VOIP that provide VOIP access and a separate PTSN line for fallback.  Obviously a lot of Routers now incorporate VOIP however there are some benefits of a stand-alone device such as this one - which I won't go into here:

As far as I can gather this Plugin should be compatible with
Sipura: Models: **SPA-1001, SPA 2000, SPA-2002, SPA-2100, SPA-3000**
Linksys: Models: **PAP2, SPA-3000, SPA-3102**

Although can only test against my model which is SPA-3000

Essentially this Plugin creates a VOIP-Device within Indigo.  This device is then updated whenever there are incoming or outgoing phone calls.  CallerID information is received.
Enabling you to trigger actions on phone-calls, or actions on certain persons calling, or 'ring' Sonos devices (via Sonos plugin) etc.

On my setup - the Indigo Device is notified - before my phone starts ringing!
The reason it is this quick is the plugin connects to the SPA device directly via the syslog settings and is immediately updated if there is any calls.  There is essentially no lag.
In between calls - there is no communication.

**Usage:[/size]**

**Install and Setup**

**1. Install Plugin**

**2. Setup Plugin Config.**

![](https://s23.postimg.org/r2n1she7v/Plugin_Config_Page.png)
Options:

*Convert Phone Numbers to Names:*
This optionally converts via a lookup list, phone numbers in anyformat to string.  
ie.  5552232 can be converted to 'She who must be obeyed'
This conversion is then applied to the actions of the Plugin - include speaking CallerID and saving CallerID to indigo Variable.

The look list must be a file named: numbersConvert.txt  located in the folder you specify.
It should contain Single Line entries comma seperated
[i]eg[/i].
5552232,She who must be obeyed
5552222,Telemarketer
etc
![](https://s23.postimg.org/8lsn1ny9n/numbers_Convert.png)

If you change the file - you can reload the Plugin or press the 'Reload Caller ID txt file' to update.

[i]3.  Create New Device[/i]

Create a new Sipura VOIP Device.
NB this Plugin only supports single device.
![](https://s23.postimg.org/ndxct046z/Sipura_Plugin2.png)

Options:
**IP Address:**
Is IP address of VOIP Adapter  (actually not used currently)
**Port:**
Port for connection to the VOIP Adapter  (given Mac must be port from 1024-65535)
This is the same Port you use in the Sipura settings (explained below)
**Sip Server:**
The name of your VOIP server provider - or somepart of the name
[i]eg.[/i]
sip00.mynetfone.com.au
can be shortened to mynetfone.com.au
Enables the Plugin to distinguish incoming and outgoing calls


**4.  Device Custom States**
![](https://s28.postimg.org/gva9i99bh/Sipura_Plugin.png)

Once we have finished setting up - the new Device will have these custom states.
& will also right incoming CallerID to these Indigo Variables (which will be created)

![](https://s23.postimg.org/4o9yq00u3/Sipura_Variables.png)


**5. Device Triggers**

Presently there is a single Trigger - on incoming phone calls.

![](https://s23.postimg.org/xcmwt830b/Sipura_Plugin_Trigger.png)

**6. Device Actions**

Presently there is a single Action - which speaks aloud the incoming CallerId.
![](https://s30.postimg.org/4nl11hltd/Sipura_Action.png)

***[size=150]First off we need to setup the Sipura/SPA-Device[/size]***

In the SPA device, the following settings have to be made:

*System tab:*
Syslog Server: enter IP address of the machine Indigo is running on.
eg.
192.168.1.6:45000
Debug Server: same IP address as above.  The port number follows the IP address.
eg.
192.168.1.6:45000
(with 45000 being the port number)
Debug Level: 0 is OK.

*Line 1 and Line 2/PSTN tab:*
SIP Debug Option: select 'full excl. OPT|NTFY|REG'


Locate the Webpage of your Sipura/LinkSys Device - it looks like this.
![](https://s23.postimg.org/awqp5u917/Sipura_Page.png)
![](https://s23.postimg.org/nmuxixgzf/Sipura_Debug_System.png)
![](https://s23.postimg.org/7nc9zdkxn/Sipura_Debug_PSTN.png)
![](https://s23.postimg.org/5u9db1zqz/Sipura_Debug.png)


Once done should be ready to go!.


Glenn
