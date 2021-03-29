#TRY NOT TO UPDATE THIS

#---------------------CLI^---------------------------------
import pexpect
import re
#--------------------Process IOS---------------------------

BAMS = "bams.iptp.net"
ROUTER = "fredonia.pe"


class Device():
    def __init__(self, hostname, prompt="", no_bams=False):
        self.hostname = hostname
        self.bams = None
        self.device = None
        self.no_bams = no_bams
        if prompt:
            self.prompt = ".*".join(prompt.split("."))+".*#"
        else:
            self.prompt = ".*".join(self.hostname.split("."))+".*#"
        
    def login(self):
        print("Initializing")
        if not self.no_bams:
            self.bams = self.__login_bams()
        else:
            self.bams = pexpect.spawn('screen')
            self.bams.expect("$")
        print("Logged into bams")
            
        self.device = self.__login_device()
        print("Logged into router")
        
    def __login_bams(self):
        username = "danielpl"
    
        prompt = "$"

        # path to key should be fixed
        bams = pexpect.spawn('ssh -o "StrictHostKeyChecking no" -i "../../.ssh/id_rsa" %s@%s' % (username, BAMS))
        bams.expect(prompt)

        return bams
    
    def __login_device(self):
        router = self.bams
    
        router.sendline("ssh danielpl@%s" % self.hostname)
        router.expect("Password")

        password = open(".aijiidafji").read()
        router.sendline(password)
        router.expect("#")
        router.sendline("terminal len 0")
        router.expect("#")

        return router
    
    def show(self, command):
        assert self.device is not None
        self.device.sendline(command)
        self.device.expect(self.prompt)

        #I believe it is utf8 ...
        data = self.device.before.decode("utf8")
        # we remove first line as it is same as command
        data = re.sub(r'^[^\n]*\n', '', data)

        return data
    
    
if __name__ == ("__main__"):
	pass    
