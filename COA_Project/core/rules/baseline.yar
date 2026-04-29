/*
    C.O.A YARA Rules — Baseline malware detection
    ==============================================
    These rules detect common malware patterns
    Reference: https://yara.readthedocs.io
*/

rule Suspicious_Cryptominer
{
    meta:
        description = "Detects common cryptominer indicators"
        severity = "HIGH"
        author = "COA"

    strings:
        $miner1 = "stratum+tcp://" ascii wide
        $miner2 = "xmrig" ascii wide nocase
        $miner3 = "cryptonight" ascii wide nocase
        $miner4 = "monero" ascii wide nocase
        $pool1 = "pool.minexmr.com" ascii wide
        $pool2 = "xmr.pool" ascii wide

    condition:
        2 of them
}

rule Suspicious_Powershell_Obfuscation
{
    meta:
        description = "Detects obfuscated PowerShell commonly used in malware"
        severity = "CRITICAL"
        author = "COA"

    strings:
        $b64_1 = "FromBase64String" ascii wide
        $invoke = "Invoke-Expression" ascii wide nocase
        $iex = "IEX" ascii wide
        $download = "DownloadString" ascii wide nocase
        $hidden = "-WindowStyle Hidden" ascii wide nocase
        $bypass = "-ExecutionPolicy Bypass" ascii wide nocase
        $enc = "-EncodedCommand" ascii wide nocase

    condition:
        ($b64_1 and ($invoke or $iex)) or
        ($download and ($hidden or $bypass)) or
        $enc
}

rule Ransomware_Indicators
{
    meta:
        description = "Detects common ransomware patterns"
        severity = "CRITICAL"
        author = "COA"

    strings:
        $note1 = "your files have been encrypted" ascii wide nocase
        $note2 = "pay the ransom" ascii wide nocase
        $note3 = "bitcoin" ascii wide nocase
        $ext1 = ".locked" ascii wide
        $ext2 = ".encrypted" ascii wide
        $crypto1 = "CryptEncrypt" ascii
        $crypto2 = "CryptGenKey" ascii
        $shadow = "vssadmin delete shadows" ascii wide nocase

    condition:
        2 of ($note*) or
        (1 of ($ext*) and 1 of ($crypto*)) or
        $shadow
}

rule Suspicious_RemoteAccess
{
    meta:
        description = "Detects RAT (Remote Access Trojan) indicators"
        severity = "HIGH"
        author = "COA"

    strings:
        $rat1 = "reverse_tcp" ascii wide
        $rat2 = "meterpreter" ascii wide nocase
        $rat3 = "cobalt strike" ascii wide nocase
        $rat4 = "empire" ascii wide nocase
        $tool1 = "psexec" ascii wide nocase
        $tool2 = "mimikatz" ascii wide nocase
        $net1 = "\\\\.\\pipe\\" ascii

    condition:
        any of ($rat*) or
        2 of ($tool*, $net*)
}

rule Suspicious_Persistence
{
    meta:
        description = "Detects persistence mechanisms"
        severity = "MEDIUM"
        author = "COA"

    strings:
        $reg1 = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" ascii wide
        $reg2 = "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" ascii wide
        $task = "schtasks" ascii wide nocase
        $service = "sc create" ascii wide nocase
        $startup = "\\Startup\\" ascii wide

    condition:
        any of them
}

rule Suspicious_Antianalysis
{
    meta:
        description = "Detects anti-analysis / sandbox evasion"
        severity = "HIGH"
        author = "COA"

    strings:
        $vm1 = "vmware" ascii wide nocase
        $vm2 = "virtualbox" ascii wide nocase
        $vm3 = "vbox" ascii wide nocase
        $sandbox1 = "sandboxie" ascii wide nocase
        $debug1 = "IsDebuggerPresent" ascii
        $debug2 = "CheckRemoteDebuggerPresent" ascii
        $sleep = "Sleep" ascii

    condition:
        (2 of ($vm*, $sandbox*)) or
        ($debug1 and $debug2)
}

rule Known_Malicious_Strings
{
    meta:
        description = "Known-bad strings from common malware families"
        severity = "CRITICAL"
        author = "COA"

    strings:
        $s1 = "WannaCry" ascii wide nocase
        $s2 = "NotPetya" ascii wide nocase
        $s3 = "Emotet" ascii wide nocase
        $s4 = "TrickBot" ascii wide nocase
        $s5 = "Ryuk" ascii wide nocase
        $s6 = "AgentTesla" ascii wide nocase

    condition:
        any of them
}
